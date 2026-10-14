# ARIES external validation and leaderboard readiness

## Latest public validation

- **Latest public scorecard workflow:** PASS — [GitHub Actions run #1](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502634925).
- **Scorecard artifact:** [Download JSON, HTML scorecard, and CSV case results](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502634925/artifacts/11866179182) (retained until 2027-01-12).
- **Latest diagnostic results:** 10/10 non-empty responses; 10/10 exact-match passes (100.0% on the small authored diagnostic set).
- **Measured end-to-end HTTP latency from a GitHub-hosted runner:** mean 180.602 ms; median 127.793 ms; minimum 112.687 ms; maximum 326.689 ms.
- **Public endpoint check:** PASS — [GitHub Actions run #15](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502266753). A later endpoint validation also passed on commit `1851c354`: [run](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502370882).
- **Native runtime verification:** PASS — [GitHub Actions run #19](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502266749).
- **Public endpoint:** https://aries-tier0-api-6qjh.onrender.com
- **Backend:** ARIES-authored native character n-gram baseline and narrow deterministic task engine; no hosted inference API key is required.

The scorecard workflow runs on pushes affecting its benchmark software, can be run manually, and is scheduled weekly. It emits downloadable JSON, HTML, and CSV evidence. Latency is end-to-end HTTP timing and includes network, service, and possible cold-start overhead.

**Interpretation limit:** 100% means only 10/10 exact matches on these 10 ARIES-authored diagnostic prompts. It is not an independent model-quality certification, not MMLU/GSM8K/BBH/LiveBench, and not an official leaderboard score. The scorecard is an ARIES-maintained diagnostic report, not an external ranking.

## Latest strict response-quality validation

- **Strict public benchmark:** FAIL — [GitHub Actions run](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502970352).
- **Measured result:** all 4 public HTTP checks returned success and all 3 chat requests returned non-empty responses, but only 2 of 3 answer-quality assertions passed.
- **Failed case:** the public deployment gave an irrelevant character n-gram continuation for the API health-check explanation prompt. This correctly fails the stricter benchmark; HTTP 200 and non-empty text are not sufficient evidence of answer quality.
- **Report artifact:** [Download strict benchmark JSON](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502970352/artifacts/11866463431).
- **Fix committed:** the ARIES native deterministic engine now includes an explicit health-check explanation and supports the phrase “multiplied by”; regression tests were added. A new public benchmark is triggered by future native inference code changes to verify whether the deployed service has picked up the fix.
- **Official leaderboard:** still **not submitted**. A passing small diagnostic is not an official leaderboard score.

## What has been exercised

1. The public deployment's health, root/readiness, diagnostics, and model-list routes.
2. Public chat-completions requests returning non-empty generated text.
3. A repeatable 10-case diagnostic benchmark with measured per-request latency and exact-match checks.
4. Native runtime/container verification and API integration tests in GitHub Actions.
5. A deterministic, explicitly scoped rule engine for selected arithmetic and structured prompts. This is not a general-purpose LLM.
6. A generated HTML/JSON/CSV scorecard stored as a GitHub Actions artifact.

## Official leaderboard status

**No official model leaderboard submission or ranking is claimed.** Public API uptime and a small smoke benchmark do not qualify as a model-quality evaluation.

The Hugging Face Open LLM Leaderboard submission instructions require a public model that loads through supported Transformers AutoClasses, compatible public weights (the instructions specify Safetensors), a model card, and compliance with the leaderboard's supported evaluation setup. See the [official submission guide](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting) and [FAQ](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/faq).

The deployed ARIES character n-gram baseline is not a Transformers foundation model and is not eligible as a normal Open LLM Leaderboard entry. A third-party GGUF used by the optional local launcher must not be relabeled as ARIES-trained weights.

## Remaining requirements for an official model leaderboard entry

1. Train or otherwise establish provenance for an ARIES-owned model and record dataset licenses and training details.
2. Export actual weights and tokenizer/configuration to a public model repository in a supported format.
3. Verify model and tokenizer loading with supported Transformers AutoClasses.
4. Run a standard, reproducible evaluator against a pinned model revision and publish complete results and limitations.
5. Submit that exact model revision through the official process and report the actual queue status and result. Until that happens, the official entry status remains **not submitted**.

## Local software

The repository includes a local inference wrapper and a standalone native runtime. The wrapper can serve a compatible GGUF locally; that is a serving implementation, not proof that those GGUF weights were trained by ARIES. The standard-library character n-gram runtime is ARIES-authored but intentionally small and limited. Neither should be represented as a state-of-the-art general-purpose model.
