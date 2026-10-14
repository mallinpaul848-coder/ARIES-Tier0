# ARIES public endpoint test — 2026-10-14

**Result: FAIL for public model inference.** The endpoint itself responds to all four diagnostic routes, but it does not have a model backend configured.

Measured from a GitHub-hosted runner on 2026-10-14:

| Route | HTTP | Observed latency |
|---|---:|---:|
| `/health` | 200 | 138.12 ms |
| `/` | 200 | 72.96 ms |
| `/diagnostics` | 200 | 55.52 ms |
| `/v1/models` | 200 | 124.82 ms |

The API reported `inference_configured: false`, no model ID, and zero listed models. Three chat samples were requested by the benchmark but skipped because no backend/model was configured. Therefore there is no measured chat latency, throughput, quality score, or leaderboard result.

Raw JSON report: [`2026-10-14-public-endpoint.json`](2026-10-14-public-endpoint.json)

Automated run and downloadable artifact: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38501291057

## Required to pass

Configure a real model-serving backend in Render's private Environment settings: `ARIES_UPSTREAM_BASE_URL` and the exact `ARIES_MODEL_ID`; set `ARIES_UPSTREAM_API_KEY` only if the provider requires it. Redeploy, then rerun **ARIES Public Inference Benchmark**. Pass criteria: all four routes return HTTP 200 and all three chat requests return HTTP 200 with non-empty assistant content.

This report intentionally does not claim a model leaderboard submission. The Hugging Face Open LLM Leaderboard requires an actual public model repository that loads through supported Transformers AutoClasses with Safetensors and model metadata. The current Qwen GGUF launcher is third-party starter weights, not an ARIES-trained model. See https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting.
