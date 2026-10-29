# MALLIN Platform — ARIES AI browser-local language model

MALLIN now has a browser-local inference path so it does not require a hosted AI chat API or a language-model server. Visitors' browsers run the model through WebLLM/WebGPU.

## Use the live model UI

1. Open the site from a secure HTTPS origin.
2. Choose the compact **SmolLM2 360M Instruct, Q4F32** or larger **Llama 3.2 1B Instruct, Q4F32** model.
3. Click **Load browser AI model**, or send a normal chat prompt and the model will begin loading automatically.
4. Wait until the model status says ready. Your prompt is then processed locally by the model.

The first load downloads model weights and the WebLLM runtime and may take several minutes / hundreds of MB. The model will need a WebGPU-capable browser and sufficient GPU memory. Some devices will be unsupported. A simple arithmetic expression can still use the local calculator without loading the model.

## What model actually runs?

The two choices are real, pre-trained open-weight WebLLM-supported models, not ARIES's custom weights. The website must not be described as running a custom-trained ARIES model unless those custom model artifacts are actually created and incorporated. No certification or benchmark result is claimed.

WebLLM is documented as an in-browser LLM inference engine using WebGPU with an OpenAI-compatible chat API:
- https://webllm.mlc.ai/docs/
- https://webllm.mlc.ai/docs/user/basic_usage.html
- Supported model configuration: https://github.com/mlc-ai/web-llm/blob/main/src/config.ts

## Hosting / no third-party inference server

The site contains no hosted AI inference endpoint and sends chat prompts to no AI API. Model inference happens on each visitor's hardware. However, the first visit still retrieves the WebLLM runtime and model artifacts from external repositories (esm.run, the MLC model library host, and Hugging Face). That is a code/model download dependency, not a hosted inference API. Eliminating even those external download sources requires publishing the runtime, compiled WebGPU libraries, and model weights as permanent assets too; those assets are much larger than the HTML and may require paid permanent storage.

## Deployment status

The self-contained permanent-site export is at `permaweb/mallin-platform.html`. The one-file upload helper is at `permaweb/PUBLISH-MALLIN-PERMAWEB.html`. These files are prepared, but an Arweave transaction has not been confirmed. A permanent public URL must not be claimed until a real upload returns a transaction ID and the page is opened successfully from a separate browser.

## Current limitations

- No central model server is running, by design. Each visitor runs model inference on their own compatible browser/hardware.
- This browser model is not the project's custom ARIES weights.
- Full model inference has been syntax-checked but still needs a real browser/WebGPU integration test.
- If users expect a centrally hosted shared inference engine while also banning any server/device and all external compute, those requirements conflict: some machine must execute the model.
