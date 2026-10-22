# ARIES Independent Website

ARIES can serve its website and run local model inference on your own Windows computer without Render, Vercel, or a hosted chat API.

## Start

1. Open the repository folder on Windows.
2. Double-click `software\\START_ARIES_SELF_HOSTED.bat`.
3. On first run, the launcher installs the local Python runtime dependencies and downloads the open model weights (about 1 GB).
4. When the model finishes loading, your browser opens the website at `http://127.0.0.1:8081/`.
5. Keep the launcher window open while using ARIES. Press Ctrl+C to stop both local servers.

The website uses the built-in CSS galaxy background and has no remote wallpaper dependency. Chat requests go to `http://127.0.0.1:8765`; inference runs on this computer.

## Independence and requirements

- Website files, web server, and inference API run on the user's computer.
- Chat prompts are not sent to an external AI API by this local runtime.
- The initial model and Python packages are downloaded from their published repositories; after download, the model runs locally.
- Python 3 and a compatible Windows CPU environment are required. The first install needs internet access.
- The site is private to this computer by default. It is not a public internet website and does not create a domain, public DNS, or internet-facing server.
- To make the site publicly reachable under your own domain, you still need a domain name and a computer/server plus secure networking. Do not expose the local API directly to the internet without authentication, TLS, and rate limits.
