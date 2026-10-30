# ARIES independent mode

## What changed

The API now defaults to **independent local-only inference**:

- `ARIES_INDEPENDENT_MODE` defaults to `1`.
- In that mode, upstream provider configuration is ignored and chat prompts are not sent to an external AI API.
- If a compatible local GGUF model is installed, chat uses the local `llama.cpp` adapter.
- Without local model weights, built-in deterministic ARIES routes and the native character n-gram baseline remain available; these are not a capable general-purpose LLM.
- The server reports `independent_mode`, `local_model_loaded`, and `general_chat_ready` in `/diagnostics`.

## Windows self-hosted start

1. Download and extract this repository.
2. Install Python 3.11 or newer.
3. Run `software/START_MALLIN_SELF_HOSTED.bat`.
4. Open `http://127.0.0.1:10000/app`.
5. Keep the computer awake and the terminal open while using the app.

The launcher installs the Python packages listed in `requirements.txt` on first run. The local API does not need Render, Vercel, Cloudflare, Oracle, or an external AI API.

## Install local model weights

Place a GGUF instruction model that you are licensed to use on the machine. Set the model path before launching:

```powershell
$env:ARIES_GGUF_MODEL_PATH = "C:\\path\\to\\your-model.gguf"
$env:ARIES_INDEPENDENT_MODE = "1"
.\\software\\START_MALLIN_SELF_HOSTED.bat
```

Model quality, RAM use, and speed depend on the chosen weights and hardware. A small model may give limited answers. Do not assume the repository's native character n-gram baseline is equivalent to a modern LLM.

## Explicitly opting into a remote provider

Independent mode is intentionally the default. Only an operator who deliberately wants an external provider may set `ARIES_INDEPENDENT_MODE=0` and configure the upstream environment variables. Do not set this for an independent deployment.

## What independence does and does not mean

This removes the external AI inference API requirement. It does **not** make the machine, operating system, CPU, memory, electricity, network, Python packages, model runtime, or model weights appear from nowhere. The current local inference adapter uses the open-source `llama-cpp-python` runtime and a separately licensed GGUF model file; these are local components, not software written from scratch by the ARIES project.

A public always-on service still needs a computer or server that stays powered and connected. A local installation is not automatically public. Before exposing the API to the internet, add authentication, HTTPS/TLS termination, request-size limits, rate limits, logging controls, and security review. The current self-hosted gateway is not a hardened public production service.

## Verify

After starting the server, inspect:

- `GET /health` — process health
- `GET /diagnostics` — independent-mode and local-model state
- `GET /v1/models` — advertised model and inference readiness
- `GET /performance` — measured in-process latency counters

A healthy process does not prove general chat is ready. Confirm `local_model_loaded: true` and `general_chat_ready: true`, then send several real questions and inspect the returned `aries_native` metadata. Keep raw benchmark reports with the exact model file hash and machine details.
