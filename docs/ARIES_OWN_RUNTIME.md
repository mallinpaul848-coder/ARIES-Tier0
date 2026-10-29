# ARIES own-runtime deployment

## Goal
Run ARIES on hosted infrastructure, independent of the owner's PC and home internet. The browser UI calls a hosted API; the API serves ARIES deterministic math/reasoning routes and a local GGUF instruction model through llama.cpp.

## Existing components
- `Dockerfile` installs `llama-cpp-python`, downloads a pinned SmolLM2-135M-Instruct GGUF artifact, verifies its SHA-256, and starts `software/public_native_server.py`.
- `software/public_native_server.py` combines ARIES task routing and math handlers with a local model runtime. An upstream API is optional.
- `software/native_runtime.py` is an experimental character n-gram baseline, not a modern general-purpose language model.
- `scripts/aries_public_smoke.py` checks health, diagnostics, model listing, and real non-empty chat responses.

**Model ownership distinction:** ARIES routing, math tools, inference server, and deployment code are project software. SmolLM2 weights are separately licensed third-party model weights. This does not establish that ARIES has trained its own foundation model. A genuinely ARIES-trained model requires a documented training corpus, training run, model artifact, license review, and evaluation.

## Deployment checklist
1. Deploy this repository's Dockerfile on persistent hosted infrastructure. The current `render.yaml` selects Render's free plan; free services can spin down while idle and are not suitable for a strict always-on promise.
2. Ensure the host provides `PORT`; the server defaults to 10000.
3. Confirm the command is `python software/public_native_server.py`. Do not substitute `api/main.py` unless its different configuration contract is intended.
4. The local GGUF path does not require `ARIES_UPSTREAM_API_KEY`. If an upstream model is configured, store its key as a secret and never commit it.
5. After deployment, run `python scripts/aries_public_smoke.py --base-url https://YOUR-API-HOST`.
6. Test a general question and a deterministic calculation in the public browser. A passing `/health` check alone does not prove chat inference works.

## Reliability and evaluation
- Use a paid always-on service or another host with persistent web services and sufficient RAM/CPU. Select resources using measured memory and load.
- Add external uptime monitoring and alerting.
- Record smoke-test output with commit SHA, deployment ID, date, service plan, and commands.
- Separate client/network latency from server inference latency. This smoke test is not a formal benchmark.
- Do not claim 100% uptime, third-party certification, quantum computation, or superiority to commercial models without independent evidence.
