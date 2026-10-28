#!/usr/bin/env python3
"""MALLIN static site server with a fixed asset allowlist.

Demo/self-hosting helper only. It intentionally has no write routes, upload
endpoints, directory listing, or model backend. Use HTTPS and an audited
production server before handling sensitive traffic.
"""
from __future__ import annotations
import argparse
import mimetypes
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
    "/sw.js": ("sw.js", "text/javascript; charset=utf-8"),
}
SECURITY_HEADERS = [
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
    ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
    ("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https: http:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"),
]

class Handler(BaseHTTPRequestHandler):
    server_version = "MallinStatic/1.0"
    sys_version = ""

    def log_message(self, fmt, *args):
        # Avoid logging request contents; keep only basic HTTP event/status.
        print("%s [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def do_POST(self):
        self.send_error(405, "Static site only")

    def do_PUT(self):
        self.send_error(405, "Static site only")

    def do_DELETE(self):
        self.send_error(405, "Static site only")

    def do_GET(self):
        self._serve(head_only=False)

    def do_HEAD(self):
        self._serve(head_only=True)

    def _serve(self, head_only: bool):
        path = urlsplit(self.path).path
        entry = ASSETS.get(path)
        if entry is None:
            self.send_error(404, "Not found")
            return
        filename, content_type = entry
        file_path = ROOT / filename
        try:
            # Allowlist above plus strict resolved-parent check.
            if file_path.resolve().parent != ROOT.resolve():
                self.send_error(404, "Not found")
                return
            body = file_path.read_bytes()
        except OSError:
            self.send_error(404, "Asset not available")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        for key, value in SECURITY_HEADERS:
            self.send_header(key, value)
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

def main():
    parser = argparse.ArgumentParser(description="Serve only the MALLIN static website files.")
    parser.add_argument("--bind", default="127.0.0.1", help="127.0.0.1 for local testing, 0.0.0.0 for LAN/router access")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if not (1 <= args.port <= 65535):
        parser.error("port must be between 1 and 65535")
    httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    print("MALLIN static site server")
    print("Local test: http://127.0.0.1:%d/" % args.port)
    if args.bind == "0.0.0.0":
        print("Listening on all network interfaces at port %d." % args.port)
        try:
            infos = socket.getaddrinfo(socket.gethostname(), None, type=socket.SOCK_STREAM)
            seen = set()
            for info in infos:
                ip = info[4][0]
                if ip not in seen and not ip.startswith("127."):
                    seen.add(ip)
                    print("Possible LAN address: http://%s:%d/" % (ip, args.port))
        except OSError:
            pass
        print("WARNING: HTTP only; no TLS. Use this for a demo and do not enter passwords or private data.")
        print("For public access, your router/ISP must permit inbound connections. See SELF-HOST-NO-THIRD-PARTY.md.")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping MALLIN server.")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    main()
