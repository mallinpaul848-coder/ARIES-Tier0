#!/usr/bin/env bash
# MALLIN direct-IP HTTPS installer for Ubuntu/Debian-like Linux.
# Hosts ONLY the static website, on hardware/network you control.
# Requires your router/ISP to deliver public inbound TCP ports 80 and 443.
set -Eeuo pipefail

SITE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WEBROOT="/var/www/mallin"
NGINX_SITE="/etc/nginx/sites-available/mallin"
NGINX_LINK="/etc/nginx/sites-enabled/mallin"
IP="${1:-}"
EMAIL="${2:-}"

usage() {
  echo "Usage: sudo bash install-public-ip-https.sh <your-stable-public-ipv4> <email-for-certificate-account>"
  echo "Example: sudo bash install-public-ip-https.sh 203.0.113.20 admin@example.net"
  echo "The example IP is reserved for documentation and will not work as a real server address."
}
if [[ -z "$IP" || -z "$EMAIL" ]]; then usage; exit 2; fi
if [[ "$EUID" -ne 0 ]]; then echo "Run with sudo." >&2; exit 2; fi
if ! python3 - "$IP" <<'PY'
import ipaddress, sys
try:
    ip = ipaddress.ip_address(sys.argv[1])
    assert ip.version == 4 and ip.is_global
except Exception:
    print("Provide a real, globally routable IPv4 address (not private, loopback, or documentation-only).", file=sys.stderr)
    sys.exit(1)
PY
then exit 2; fi

for f in index.html styles.css app.js manifest.webmanifest sw.js; do
  [[ -f "$SITE_DIR/$f" ]] || { echo "Missing site asset: $SITE_DIR/$f" >&2; exit 3; }
done
if [[ "$IP" == "203.0.113."* || "$IP" == "198.51.100."* || "$IP" == "192.0.2."* ]]; then
  echo "That address belongs to an example-only range. Supply your actual public IP." >&2; exit 2
fi

echo "Installing Nginx, Snap, and official Certbot package..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx snapd python3 ca-certificates
systemctl enable --now nginx
snap install core >/dev/null 2>&1 || true
if ! snap list certbot >/dev/null 2>&1; then snap install --classic certbot; fi
ln -sfn /snap/bin/certbot /usr/local/bin/certbot
CERTBOT="/snap/bin/certbot"
"$CERTBOT" --version
VERSION="$("$CERTBOT" --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1)"
python3 - "$VERSION" <<'PY'
import sys
parts = tuple(int(x) for x in sys.argv[1].split("."))
if parts < (5,4,0):
    print("Certbot 5.4.0 or newer is required for IP-address certificates with webroot.", file=sys.stderr)
    sys.exit(1)
PY

install -d -m 0755 "$WEBROOT"
for f in index.html styles.css app.js manifest.webmanifest sw.js; do install -m 0644 "$SITE_DIR/$f" "$WEBROOT/$f"; done
install -d -m 0755 "$WEBROOT/.well-known/acme-challenge"

if [[ -f /etc/nginx/sites-available/default && ! -f /etc/nginx/sites-available/default.mallin-backup ]]; then
  cp -a /etc/nginx/sites-available/default /etc/nginx/sites-available/default.mallin-backup
fi

write_http_config() {
  cat > "$NGINX_SITE" <<'NGINXHTTP'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root /var/www/mallin;
    index index.html;
    server_tokens off;
    location ^~ /.well-known/acme-challenge/ {
        default_type text/plain;
        try_files $uri =404;
    }
    location / {
        try_files $uri $uri/ =404;
    }
}
NGINXHTTP
  rm -f /etc/nginx/sites-enabled/default
  ln -sfn "$NGINX_SITE" "$NGINX_LINK"
}
write_http_config
nginx -t
systemctl reload nginx

echo ""
echo "Requesting an HTTPS certificate for the IP address $IP."
echo "This requires public TCP port 80 to reach this server so the CA can validate it."
"$CERTBOT" certonly --non-interactive --agree-tos --email "$EMAIL" \
  --preferred-profile shortlived --webroot --webroot-path "$WEBROOT" \
  --ip-address "$IP" --cert-name "$IP" \
  --deploy-hook "/usr/bin/systemctl reload nginx"

CERT_DIR="/etc/letsencrypt/live/$IP"
[[ -s "$CERT_DIR/fullchain.pem" && -s "$CERT_DIR/privkey.pem" ]] || {
  echo "Certificate files were not created at $CERT_DIR; refusing to enable HTTPS configuration." >&2
  exit 4
}

cat > "$NGINX_SITE" <<NGINXHTTPS
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root $WEBROOT;
    server_tokens off;
    location ^~ /.well-known/acme-challenge/ {
        default_type text/plain;
        try_files \$uri =404;
    }
    location / {
        return 301 https://\$host\$request_uri;
    }
}
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;
    root $WEBROOT;
    index index.html;
    server_tokens off;
    ssl_certificate $CERT_DIR/fullchain.pem;
    ssl_certificate_key $CERT_DIR/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https: http:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" always;
    location / {
        try_files \$uri \$uri/ =404;
    }
    location ~ /\. {
        deny all;
    }
}
NGINXHTTPS

nginx -t
systemctl reload nginx

# Give short-lived IP certificate renewals a dedicated recurring check.
cat > /etc/systemd/system/mallin-certbot-renew.service <<'UNIT'
[Unit]
Description=Renew MALLIN IP HTTPS certificate if due

[Service]
Type=oneshot
ExecStart=/snap/bin/certbot renew --quiet --deploy-hook /usr/bin/systemctl\ reload\ nginx
UNIT
cat > /etc/systemd/system/mallin-certbot-renew.timer <<'TIMER'
[Unit]
Description=Check MALLIN IP certificate renewal every 12 hours

[Timer]
OnBootSec=10min
OnUnitActiveSec=12h
Persistent=true

[Install]
WantedBy=timers.target
TIMER
systemctl daemon-reload
systemctl enable --now mallin-certbot-renew.timer

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow 80/tcp
  ufw allow 443/tcp
fi

echo ""
echo "MALLIN STATIC SITE INSTALLED."
echo "URL: https://$IP/"
echo "Certificate lifetime is about six days; the local renewal timer checks every 12 hours."
echo ""
echo "REQUIRED OUTSIDE THIS SCRIPT:"
echo "  1. Set your router to forward TCP 80 and 443 to this server's LAN IP."
echo "  2. Make sure your ISP gives you this globally routable public IPv4 address."
echo "  3. Reserve a fixed LAN IP for this server in the router."
echo "  4. Test https://$IP/ using a phone on cellular data, not the home Wi-Fi."
echo ""
echo "This serves the front-end only, not a language model. Keep Linux patched and do not expose SSH/ADB to the internet."
