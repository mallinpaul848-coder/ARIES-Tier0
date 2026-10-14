# ARIES Local Inference Runtime

This repository includes a one-click Windows launcher for a local, OpenAI-compatible inference server. It uses the official `llama.cpp` runtime and downloads public Qwen2.5 0.5B instruct weights on first run. It does not need an OpenAI API key or paid hosted inference.

## Windows quick start

1. Download the repository ZIP from https://github.com/mallinpaul848-coder/ARIES-Tier0 and extract it.
2. Open the extracted folder, then open `software`.
3. Double-click `START_ARIES_LOCAL_INFERENCE.bat`.
4. If prompted, allow Windows Package Manager (`winget`) to install `llama.cpp`. If `winget` is unavailable, install llama.cpp from https://github.com/ggml-org/llama.cpp/releases and run the launcher again.
5. Leave the terminal window open while the server runs. On first run, the model download can take several minutes.
6. Open http://127.0.0.1:8080 in your browser. The API health route is http://127.0.0.1:8080/health.

The runtime exposes an OpenAI-compatible API. To test a chat completion, send a POST request to `http://127.0.0.1:8080/v1/chat/completions` with JSON similar to:

```json
{
  "model": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
  "messages": [{"role": "user", "content": "Reply with exactly: ARIES inference works."}],
  "max_tokens": 64
}
```

The model is a small smoke-test model; it is not a frontier model and this setup is not evidence of benchmark leadership. Speed depends on the computer's CPU, RAM, and GPU. The published model card lists the model under the Apache-2.0 license: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF

## Important limits

- The launcher starts a model on the computer where it is run. It does **not** automatically connect that model to the public Render endpoint.
- The Render API currently needs a configured backend URL and model ID; if a provider requires authentication, its API key must be set privately in Render's Environment settings. Never paste API keys into chat or commit them to GitHub.
- Do not expose a local inference server to the public internet without authentication, TLS, request limits, and an appropriate host.
- The server launcher and API integration are ARIES repository software. The downloadable Qwen weights are third-party weights, not ARIES-trained proprietary weights.
- Public external validation is not complete until a real model produces a non-empty chat response at the public endpoint and measured results are published. GitHub workflow passes for code tests do not, by themselves, establish model quality or leaderboard results.
