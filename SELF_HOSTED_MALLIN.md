# MALLIN AI / ARIES Tier Zero — Self-hosted app

## Windows quick start

1. Install Python 3.11 or newer.
2. Extract the repository to a writable folder.
3. Double-click `software/START_MALLIN_SELF_HOSTED.bat`.
4. Open `http://127.0.0.1:10000/app` in the browser if it does not open automatically.
5. Keep the terminal window open while using the app.

The launcher creates a local virtual environment, prepares the built-in ARIES native baseline, and starts the API and web interface on the same computer. The web interface uses the same-origin API; it does not send chat requests to Render, Vercel, or a configured hosted API by default.

## Local-first operation and limits

- The interface and gateway are served from the machine running the launcher.
- The built-in native baseline and deterministic task engine work locally.
- Broad, high-quality generative answers require a locally installed model runtime and model weights. The bundled Docker build has a model download step; this Windows launcher does not silently download model weights.
- Python packages installed from `requirements.txt` are open-source dependencies. This is self-hosted, not a claim that the entire software supply chain has zero third-party components.
- Local URL access is private to this computer by default. Public access requires a machine and network configuration that you control, including firewall and router rules or a public IP. A registered domain is separate from the application software and may have a registration cost.

## Endpoints

- App: `/app`
- Health: `/health`
- Models: `/v1/models`
- Performance counters: `/performance`
- Math diagnostics: `/math/diagnostics`
