# MALLIN Platform — ARIES AI browser-local language model

MALLIN now has a browser-local inference path: visitors can load a compact open-weight language model and run inference in their own WebGPU-capable browser. The website itself does not need an AI inference server.

## Start chat with a real language model

1. Open the MALLIN static site from a secure HTTPS origin.
2. In **Run the language model in this browser**, select a model.
3. Click **Load browser AI model** and let the first-time download finish.
4. Wait until the status says **Local model ready**, then send a prompt.

Available models:
- **SmolLM2 360M Instruct, Q4F32**: compact starter model, lower memory use.
- **Llama 3.2 1B Instruct, Q4F32**: larger starter model, generally stronger but uses more memory.

These are real, pretrained public starter models, **not ARIES custom model weights**. This code does not claim the browser models are independently evaluated or certified as ARIES.

## How it works

- Inference runs locally in the visitor's browser via WebLLM/WebGPU, rather than sending prompts to an AI chat API.
- The runtime and model weights are downloaded on the first run and may be cached by the browser/runtime for later use.
- This requires a compatible modern browser, WebGPU support, adequate GPU memory, a secure HTTPS context, and network access for the initial runtime/model download.
- The first model download is sizeable. Once model assets are cached, some previously loaded models may work offline, depending on the browser cache and storage.
- The app intentionally has no automatic hosted inference fallback. If local inference fails, it reports the failure instead of pretending a canned response is model output.

Official references:
- WebLLM is an in-browser LLM inference engine using WebGPU: https://webllm.mlc.ai/docs/
- Supported prebuilt models and model IDs: https://github.com/mlc-ai/web-llm/blob/main/src/config.ts
- WebLLM model loading / chat completion: https://webllm.mlc.ai/docs/user/basic_usage.html

## Hosting and permanence

A static site can be published to permanent decentralized storage, but that does not itself run a central model. Browser-side inference removes the need for central AI compute; each visitor runs the model. Gateway availability and the runtime/model download sources remain external network dependencies unless those assets are also packaged and published.

## Remaining limitations

- This is not yet ARIES's custom trained model; no custom ARIES weights are bundled in this repo path.
- The site source has been updated, but the permanent Arweave upload has not been confirmed.
- Browser execution has been syntax-checked; full inference still needs a real browser/GPU run test. Do not claim that test passed until it has.
