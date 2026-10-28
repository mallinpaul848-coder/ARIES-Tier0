# ARIES AI / MALLIN Platform — self-hosted access without hosting providers

This route uses a Windows PC and internet connection you control. It does not require Render, Vercel, GitHub Pages, a tunnel provider, a paid cloud host, or a third-party AI API.

## 1. Run it locally first

1. Download the repository ZIP from the repository's Code menu and extract it.
2. Install Python 3.11+ if it is not installed.
3. Double-click `software/START_MALLIN_SELF_HOSTED.bat`.
4. Open `http://127.0.0.1:10000/app`.
5. Keep the command window open while using ARIES.

The first run installs Python packages from the project's requirements file, so it needs an internet connection. Subsequent starts use the local environment. The native baseline is not equivalent to a large general-purpose language model; higher-quality generative chat requires model weights and a compatible local runtime.

## 2. Use it from another device on your home Wi-Fi

1. Keep the server running on the Windows PC.
2. Open Command Prompt on that PC and run `ipconfig`.
3. Find the active Wi-Fi/Ethernet adapter's IPv4 address (usually `192.168.x.x` or `10.x.x.x`).
4. On your phone connected to the same Wi-Fi, open `http://PC-IP:10000/app`, replacing `PC-IP` with that address.

If Windows Firewall prompts you, allow private-network access only. Do not expose the service to public networks until you have added authentication and HTTPS.

## 3. Public access directly through your own internet connection

This is possible only if your ISP/router allows inbound connections and your connection has a reachable public IP.

- Reserve a fixed LAN address for the PC in your router.
- Configure a router port-forward rule to the PC only after the app has proper authentication, HTTPS, request limits, and secure update practices.
- Confirm whether your ISP blocks inbound connections or uses carrier-grade NAT. If it uses carrier-grade NAT, ordinary port forwarding will not work; ask the ISP whether a public IPv4 address is available. Do not buy anything unless you choose to.
- A changing public IP makes the address change. A memorable domain is optional and may cost money; this setup does not depend on a domain.

**Security warning:** The current local gateway is a development/self-hosting baseline, not a hardened public production service. Do not port-forward it to the open internet as-is. Keep it on localhost or your trusted home network until authentication, TLS/HTTPS, rate limits, and security review are complete.

## Honest constraints

- No hosting provider means the PC must stay powered on, awake, and connected.
- No external AI API means inference must run on your own hardware using locally installed model weights. Model quality and speed depend on your hardware and model.
- This guide does not claim that a public endpoint is already live or that an independent certification has been issued.
