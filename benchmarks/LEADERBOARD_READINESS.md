# ARIES external validation and leaderboard readiness

## Latest public validation

- **Latest strict public inference benchmark:** PASS — [GitHub Actions run](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503195895), commit `80e9773a34136826e5a9c7b8ee0b2d55602043e3`.
- **Latest strict benchmark report:** [Download JSON evidence](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503195895/artifacts/11865794630) (retained for 30 days).
- **Live endpoint checks:** 4/4 returned HTTP 200: `/health`, `/`, `/diagnostics`, and `/v1/models`.
- **Live chat quality checks:** 3/3 returned non-empty responses and passed their assertions: exact-output control, 17 × 19 = 323, and the API-health-check explanation.
- **Measured live chat latency from a GitHub-hosted runner:** minimum 276.36 ms; median 279.09 ms; maximum 358.10 ms. These are end-to-end HTTP measurements and include network/service overhead.
- **Other workflows on the same commit:** [API tests PASS](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503059069), [end-to-end API integration PASS](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058967), and [RTL external smoke test PASS](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503059087).
- **Public scorecard:** [10-case scorecard run](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502634925) reported 10/10 exact matches (100% on that small ARIES-authored set), mean latency 180.602 ms, median 127.793 ms, minimum 112.687 ms, maximum 326.689 ms.
- **Public endpoint:** https://aries-tier0-api-6qjh.onrender.com
- **Backend:** ARIES-authored native character n-gram baseline and narrow deterministic task engine; no hosted inference API key is required.

The strict public benchmark runs automatically on changes to benchmark or native inference code, and can also be started manually from GitHub Actions. It saves a JSON report as a workflow artifact. Historical failures remain in GitHub Actions for auditability; the latest run above is green.

**Interpretation limit:** The strict run's 3/3 pass means only that three deliberately narrow response assertions passed. The separate 10/10 scorecard is also only an ARIES-authored diagnostic set. Neither result is an independent model-quality certification, a MMLU/GSM8K/BBH/LiveBench result, or an official leaderboard score. These are useful deployment and regression checks, not evidence of broad LLM capability.

## What has been exercised

1. The live deployment's health, root/readiness, diagnostics, and model-list routes.
2. Public chat-completions requests returning non-empty generated text.
3. Three strict response-quality assertions against the deployed endpoint.
4. A repeatable 10-case diagnostic benchmark with measured per-request latency and exact-match checks.
5. Native runtime/container verification and API integration tests in GitHub Actions.
6. A deterministic, explicitly scoped rule engine for selected arithmetic and structured prompts.
7. A generated HTML/JSON/CSV scorecard stored as a GitHub Actions artifact, plus a strict benchmark JSON artifact.

## Official leaderboard status

**Official model leaderboard submission: NOT SUBMITTED.** The API and regression validation is currently passing, but this does not automatically submit or rank the model on an independent leaderboard.

The [Hugging Face Open LLM Leaderboard submission instructions](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting) require a public model that loads through supported Transformers AutoClasses, compatible public weights (the instructions specify Safetensors), a model card, and compliance with the leaderboard's supported evaluation setup. See also the [official FAQ](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/faq).

The deployed ARIES character n-gram baseline is not a Transformers foundation model and is not eligible as a normal Open LLM Leaderboard entry. A third-party GGUF used by the optional local launcher must not be relabeled as ARIES-trained weights. The current GitHub integration has no verified public model-hub upload or leaderboard submission confirmation, so an accepted entry cannot be claimed.

## Model repository loading check

A reusable loader smoke test has been added at [`benchmarks/verify_hf_model.py`](./verify_hf_model.py). Once the actual public Hugging Face model repository exists, run:

```bash
python -m pip install -U transformers torch safetensors
python benchmarks/verify_hf_model.py YOUR_HF_ORG/aries-v1 --revision MODEL_COMMIT_SHA
```

The script attempts to load `AutoConfig`, `AutoTokenizer`, and `AutoModelForCausalLM`, then reports the detected architecture and parameter count. It is a packaging check only; it does not train weights, prove ownership, measure benchmark quality, or submit a leaderboard request. No concrete Hugging Face model repository ID or uploaded ARIES weights have been verified in this repository yet.

## Remaining requirements for an official model leaderboard entry

1. Train or otherwise establish provenance for an ARIES-owned model suitable for the chosen leaderboard and record dataset licenses and training details.
2. Export actual model weights and tokenizer/configuration to a public model repository in a supported format.
3. Verify model and tokenizer loading with supported Transformers AutoClasses.
4. Run a standard, reproducible evaluator against a pinned model revision and publish complete results and limitations.
5. Submit that exact model revision through the official process and verify the actual queue status and result. This submission step requires access to the model-hosting/leaderboard account; GitHub Actions passing alone cannot do it.

Until those steps and a real submission confirmation exist, the official entry status remains **not submitted**.

## Local software

The repository includes a local inference wrapper and a standalone native runtime. The wrapper can serve a compatible GGUF locally; that is a serving implementation, not proof that those GGUF weights were trained by ARIES. The standard-library character n-gram runtime is ARIES-authored but intentionally small and limited. Neither should be represented as a state-of-the-art general-purpose model.
