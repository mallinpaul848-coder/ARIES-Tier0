# ARIES browser-local inference route

This document specifies a route that reduces dependence on hosted compute by running compatible inference on each visitor's own device.

## Architecture

- Serve the static web application as static files from any static host or a local folder.
- Download a user-selected, legally distributable quantized model to the user's device only after clear consent.
- Run inference inside the browser using WebGPU when available, with a compatible WebAssembly CPU fallback.
- Keep prompts, conversation history, and model execution in the browser by default.
- Route existing ARIES deterministic math and task endpoints to browser-local implementations where feasible.
- Do not silently send prompts to Render, Cloudflare, OpenAI, or another inference API.
- Clearly show when a requested feature is unavailable locally instead of silently falling back to a remote service.

## Suggested implementation phases

### Phase 1 — static shell
Create a static build of the existing MALLIN interface, with no required API origin. Add a local status panel for WebGPU, memory, model download, and inference readiness.

### Phase 2 — browser inference adapter
Add a dedicated adapter module behind a small interface:
- `isSupported()`
- `loadModel(modelManifest)`
- `generate(messages, options)`
- `unload()`
- `getStatus()`

Use a maintained browser inference runtime compatible with WebGPU/WebAssembly and a model format it supports. Pin versions, review licenses, and verify model provenance. Do not claim the inference runtime or model is authored by ARIES.

### Phase 3 — device model management
Provide a model catalogue containing model name, quantization, file size, license, source, SHA-256 checksum, minimum memory guidance, and supported runtime version. Require user consent before downloads. Store model files locally using browser-managed storage where supported. Provide delete/unload controls.

### Phase 4 — ARIES integration
Connect PRISE and deterministic math routes to the local chat orchestration layer. Keep deterministic calculations separately testable. Add regression tests for arithmetic, multi-turn context, refusal to use remote network, offline reload, model load failure, and insufficient device memory.

### Phase 5 — offline distribution
Publish a downloadable static bundle and installation guide. Once the site and model are cached, supported devices can continue inference offline. The first download still requires an internet connection unless the user receives an offline bundle.

## Privacy and independence rules

- Default remote inference to disabled.
- No API keys embedded in frontend code.
- No telemetry or prompt uploads by default.
- No external provider fallback when local inference fails.
- Network requests are limited to explicitly selected static assets/model downloads and optional user-enabled updates.
- Document all open-source dependencies and their licenses.

## Honest limits

- This does not make inference hardware-free. Each user supplies CPU/GPU, RAM, storage, power, and browser.
- Performance and model quality vary by device and model size.
- WebGPU is not available on every browser/device; CPU fallback can be much slower.
- A static host can distribute the interface but does not execute server-side inference.
- Public shared conversations, centralized accounts, and server-side tools need additional infrastructure.
- A browser tab cannot guarantee always-on background processing.
- This architecture is a design plan until code, browser tests, model downloads, and offline behavior are implemented and verified.

## Acceptance tests

1. Load the static app with network disabled after initial asset/model download.
2. Ask a multi-turn general question and verify a non-empty model-generated answer.
3. Inspect browser network activity and verify prompts are not sent to remote AI endpoints.
4. Disable WebGPU and test supported CPU fallback.
5. Test low-memory and unsupported-browser handling.
6. Verify model SHA-256 and license metadata.
7. Run ARIES math/task regression tests and compare outputs with the existing API implementation.
8. Record device, browser, runtime, model hash, prompt tokens, generated tokens, load time, TTFT, tokens/second, peak memory, and failures.

## User-facing statement

"ARIES can run locally on compatible devices. Your prompts stay on your device by default. Model downloads and any optional online features are disclosed. Device capability and model size determine speed and quality."
