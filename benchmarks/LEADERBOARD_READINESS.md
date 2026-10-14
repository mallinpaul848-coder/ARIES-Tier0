# ARIES external benchmark and leaderboard readiness

## Automated public API test

Run the GitHub Actions workflow named **ARIES Public Inference Benchmark**. It probes the public endpoint's health, root, diagnostics and model list, then makes three real chat requests if a backend/model is configured. The JSON report records HTTP statuses, request latency, response presence, and a latency summary. A run passes only when all required routes return HTTP 200 and all three chat responses are non-empty.

The report is uploaded as a workflow artifact even when the public test fails. Latency is the measured end-to-end request time from a GitHub-hosted runner, not model-only token latency. It includes network and host cold-start effects and must be labeled accordingly.

## Leaderboard submission status

**Not submitted. No leaderboard score is claimed.** The public endpoint test is not a model leaderboard evaluation.

The Hugging Face Open LLM Leaderboard submission instructions require a public model repository with model/tokenizer loading through supported Transformers AutoClasses, Safetensors weights, a complete model card, and a supported model architecture. See https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting and its FAQ at https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/faq.

The current local launcher uses a third-party Qwen GGUF as a starter inference backend. Running it behind an ARIES API does not make those weights an ARIES-trained model and is not enough to submit ARIES as an original model. To claim an ARIES model leaderboard result, publish actual ARIES model weights and tokenizer/config under a public model repository, ensure the architecture is supported, then submit that exact revision and report the evaluator's result. Do not relabel third-party weights as ARIES-owned.

## Independent inference engine

The repository includes a local inference wrapper and a llama.cpp-based Windows launcher. llama.cpp supports OpenAI-compatible chat endpoints (see https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md). This is ARIES's serving layer, not a new foundation model trained from scratch. The launcher has not been verified on the user's PC, and local inference does not automatically configure the Render service.

## Public endpoint blocker

The Render API requires a real upstream model endpoint and exact model ID in its private environment. Until the public chat endpoint returns HTTP 200 with a non-empty assistant response repeatedly, external model inference remains blocked. Do not publish benchmark scores before a successful report exists.
