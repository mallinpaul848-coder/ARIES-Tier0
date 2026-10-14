# ARIES Local Inference Runtime

This adds a standalone, self-hosted inference API. It does **not** require an OpenAI API key or a paid hosted inference endpoint. It loads a GGUF model on the computer running the process and exposes an OpenAI-compatible chat route.

## Windows quick start

1. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/ (enable **Add Python to PATH**).
2. Open the repository folder and double-click `software/START_ARIES_LOCAL_INFERENCE.bat`.
3. The launcher installs the runtime, downloads a small public Qwen2.5 0.5B instruct GGUF model into `models/aries-model.gguf`, then starts the API.
4. Open http://127.0.0.1:8080/health. A successful load reports `"status": "ok"`.
5. Send a test request to `POST http://127.0.0.1:8080/v1/chat/completions` with JSON:
   ```json
   {"model":"aries-local-gguf","messages":[{"role":"user","content":"Reply with exactly: ARIES inference works."}],"max_tokens":64}
   ```

The first model download is several hundred MB and requires internet access. Runtime speed depends on the computer's CPU/RAM/GPU. A small 0.5B model is a smoke-test model, not a frontier model and not evidence of benchmark leadership.

## Configuration

Environment variables:

- `ARIES_GGUF_MODEL_PATH`: path to a compatible local GGUF file; default `models/aries-model.gguf`.
- `ARIES_LOCAL_MODEL_ID`: model label returned by `/v1/models`.
- `ARIES_HOST`: bind address; defaults to `127.0.0.1` to avoid accidental public exposure.
- `ARIES_PORT` or platform `PORT`: port; defaults to `8080`.
- `ARIES_CONTEXT_SIZE`: context window; default 4096.
- `ARIES_THREADS`: CPU threads; defaults to detected CPU count.
- `ARIES_GPU_LAYERS`: GPU layers; default 0 for CPU compatibility.
- `ARIES_GGUF_URL`: override the model download URL.

Do not expose this server to the public internet without authentication, TLS, request limits, and an appropriate hosting machine. The default is local-only.

## API checks

- `GET /health` — 200 only when the model loaded; otherwise 503 and a diagnostic.
- `GET /v1/models` — returns the loaded model, or an empty list if unavailable.
- `POST /v1/chat/completions` — performs real local model inference and reports measured inference seconds.

This runtime is separate from the Render gateway. It does not automatically add a model to Render: a GGUF file must be available on the host and the runtime dependencies must be installed there. Render's free web service is not a suitable assumption for loading a multi-hundred-megabyte model without checking memory, storage, and build limits.

## What this is / is not

The API server and model-loading code are ARIES repository software. The downloadable Qwen model is third-party model weights, not ARIES-owned trained weights. For a genuinely ARIES-trained model, supply/train model weights and evaluate them independently. Do not describe the Qwen smoke-test model as ARIES proprietary weights or claim leaderboard results without measured submissions.
