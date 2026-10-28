# MALLIN public site on your own hardware — no web-hosting company

## Goal

Make the MALLIN **static website** reachable by ordinary browsers over a direct HTTPS IP URL, from hardware/network you control. This uses no Vercel, Render, Netlify, tunnel, hosted web server, or IPFS pinning service.

## The only permanent-ish no-hosting path

Run the site on an always-on Linux device you own or control (for example, a dedicated small computer or a Linux home server), connected to a home/business internet connection that permits inbound public traffic. Configure your router to forward TCP ports 80 and 443 to it. Use a stable, public IPv4 address so the shareable link does not change.

This is not possible to complete entirely from ChatGPT: I cannot access your router, confirm your ISP's public-IP status, or power up your hardware remotely.

## Install

1. Copy the complete `mallin-decentralized` folder to a supported Ubuntu server you control. This installer expects Ubuntu with systemd and Snap.
2. Ask your router/ISP for a public (preferably static) IPv4 address. Compare the router's WAN address with your public address; if they differ, the connection may be behind CGNAT. Ask the ISP for a public address. CGNAT commonly prevents direct inbound port forwarding. Reference: https://help.ui.com/hc/en-us/articles/30076583334935-Setting-Up-Public-Access-to-Local-Resources-in-UniFi
3. Configure your router's DHCP reservation so the server keeps a stable LAN IP.
4. Forward **TCP 80 and TCP 443 only** from the router to that server's LAN IP. Do not expose SSH, ADB, or router administration to the internet.
5. On the server, run (replace the example values with your real public IPv4 and an email for certificate account notices):
   ```bash
   sudo bash install-public-ip-https.sh YOUR_STATIC_PUBLIC_IPV4 YOUR_EMAIL_ADDRESS
   ```
6. From a phone with Wi-Fi turned **off**, open `https://YOUR_STATIC_PUBLIC_IPV4/`. Confirm the browser displays a valid secure connection and the purple MALLIN page.
7. Check renewal: `systemctl status mallin-certbot-renew.timer`; run a staging renewal test only after the service is working and read the output before using any forced production renewal.

## Why direct-IP HTTPS is possible now

Let's Encrypt announced general availability of short-lived IP-address certificates in January 2026. Certbot 5.4+ supports IP certificates via its webroot plugin; these certificates are valid for about six days, so automated renewal is essential. The installer configures a 12-hour renewal check and an Nginx reload hook. The certificate authority is a TLS certificate issuer, **not a hosting provider**.

Sources:
- https://letsencrypt.org/2026/03/11/shorter-certs-certbot
- https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability

## Reliability limits

- “Permanently available” cannot be guaranteed literally. Power outages, router/ISP outages, hardware faults, and a changed IP can take the site offline.
- If your ISP uses CGNAT and will not assign a public address, direct hosting without any relay or outside host is not possible over that connection.
- A static IP gives a stable URL without a domain. A public IPv4 address must be globally routable and reachable on ports 80/443.
- This web server serves only HTML/CSS/JS/PWA files. The current chat UI is a front-end demo and does **not** include model weights or compute; real ARIES AI responses require a model running on hardware you control.
- This is a small static site, not an enterprise multi-node platform. For higher availability, you would need redundant power, connectivity, hardware and failover, usually across more than one location.

## No pretending

Publishing the code to GitHub is not the same as launching it. This setup still must be installed on your hardware, given router access, and externally tested. Do not say the site is live until the external phone test succeeds.
