# MALLIN — self-hosted website without a hosting company

This is the direct route that avoids Vercel, Render, Netlify, hosted tunnels, and hosted IPFS pinning. It serves the static MALLIN front-end from hardware you control. It does not deploy anything automatically and it is not a complete AI inference server.

## The workable no-hosting option

Use an Android phone you own, connected to your home Wi-Fi, as the always-on web server. The phone must stay powered, online, and running the server. This avoids using a PC as the server and avoids a hosted web deployment provider.

### A. Test the website on your own Wi-Fi first

1. Download the MALLIN site files and this `self-host` folder onto the Android phone.
2. Install Termux from its official source. Use only one Termux distribution/source consistently because Android rejects APK updates signed by different keys: https://github.com/termux/termux-app#installation
3. Open Termux and run:
   ```sh
   pkg update
   pkg install python
   ```
4. In Termux, change directory to the folder containing `server.py`, `index.html`, `styles.css`, `app.js`, `manifest.webmanifest`, and `sw.js`.
5. Run:
   ```sh
   python server.py --bind 0.0.0.0 --port 8080
   ```
6. Use the URL printed by the script to open the app on the phone or another device on the same Wi-Fi. Both devices must be on the same network.

### B. Make it reachable from the public internet without a host

This is possible only if your internet connection accepts inbound traffic and your router lets you configure port forwarding.

1. In your router admin page, reserve a stable private/LAN IP for the Android phone.
2. Verify your router's WAN address is a public IP. If it is in a private range (10/8, 172.16/12, 192.168/16) or carrier-grade NAT range (100.64.0.0/10), inbound IPv4 port forwarding will not work unless your ISP changes the service or provides a publicly reachable address. Do not use a hosted tunnel if avoiding third-party relay services is a hard requirement.
3. Add a router rule for TCP external port 8080 to the phone's LAN IP, internal port 8080. Limit exposure to this single port; do not forward router admin, ADB, SSH, or other device-management ports.
4. From a device on a different network (for example, with Wi-Fi disabled), test `http://YOUR_PUBLIC_IP:8080/`. Do not test only from the same Wi-Fi; some routers do not support NAT loopback.
5. If your public IP changes, the URL changes. For a stable numeric URL, ask your ISP whether it can provide a static public IP. A custom domain is not required if you are content to share the numeric IP address and port.

## Important security limits

- The included server is a minimal static demo server, not a production web server. It is **HTTP only**, with no TLS. Anyone on the network path could read or modify the traffic. Do not enter account passwords, private conversations, API keys, or sensitive information.
- Public exposure makes the server reachable by internet scanners. Only the static files are served; there are no upload/write routes. Keep the exposed port limited and stop the server if not in use.
- Modern PWA/service-worker installation requires a secure context (HTTPS, except localhost). The direct-IP HTTP setup is therefore a basic public preview, not a finished secure production website.
- A domainless HTTPS option is technically possible using a publicly reachable IP and short-lived IP certificates, but it needs automated certificate issuance/renewal and an HTTPS server configured for those certs. This kit does not configure that yet.
- If your ISP uses CGNAT and will not provide a public address, then a no-relay, publicly reachable website from your own equipment is not possible over that connection. You would need public IPv4/IPv6 reachability or permit a relay/hosted service.
- Turning off the phone, closing/killing Termux, battery restrictions, Wi-Fi disconnection, or a power outage takes the site offline. Therefore this is not “permanent” without an always-on device and reliable connection.

## Windows alternative

If you prefer Windows, put the static site files and `server.py` in the same folder and double-click `START-ON-WINDOWS.cmd`. Python 3 must already be installed. The router and public-IP constraints above remain the same.

## AI capability status

This is only the website front-end. The current ARIES/MALLIN page explicitly says it has no bundled language model and returns a demo message until configured to connect to a model endpoint. If all external AI APIs are also prohibited, you need to run ARIES model inference on hardware you control; this site does not add model weights or compute.

## How the network requirement was verified

The static site itself can run locally, but remote reachability depends on your ISP and router. Residential connections may use dynamic addresses or carrier-grade NAT; if no public address reaches your router, ordinary port forwarding cannot publish the service. See the ISP/router explanation from Ubiquiti: https://help.ui.com/hc/en-us/articles/30076583334935-Setting-Up-Public-Access-to-Local-Resources-in-UniFi
