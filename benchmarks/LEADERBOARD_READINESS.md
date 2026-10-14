# ARIES external validation and leaderboard readiness

## Latest public validation

- **Public endpoint check:** PASS — [GitHub Actions run #15](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502266753)
- **Native runtime verification:** PASS — [GitHub Actions run #19](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502266749)
- **Public endpoint:** https://aries-tier0-api-6qjh.onrender.com
- **Backend:** ARIES native character n-gram baseline; the deployed baseline does not require a hosted inference API key.
- **Diagnostic sample:** 10/10 non-empty chat responses; 8/10 exact-match passes (80.0% on this small authored test set).
- **Measured end-to-end request latency from a GitHub-hosted runner:** mean 199.03 ms; median 154.495 ms; minimum 125.532 ms; maximum 317.593 ms.
- **Report artifact:** [Download public diagnostic benchmark JSON](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502193395/artifacts/11866576867).

Latency is end-to-end HTTP timing and includes network, service, and possible cold-start overhead. The 10 prompts are a small ARIES-authored diagnostic, not a standard benchmark. The reported 80% is not MMLU, GSM8K, BBH, LiveBench, or an official leaderboard score. Do not present it as one.

## What has been independently exercised

1. The public deployment's health, root/readiness, diagnostics, and model-list routes.
2. A real public chat-completions request returning non-empty generated text.
3. A 10-case external diagnostic benchmark with measured latency and exact-match checks.
4. Native runtime/container verification in GitHub Actions.
5. A deterministic, explicitly scoped rule engine for selected arithmetic and structured prompts. This rule engine is not a general-purpose LLM.

## Official leaderboard status

**No official model leaderboard submission or ranking is claimed.** Public API uptime and a small smoke benchmark do not qualify as a model-quality evaluation.

For the Hugging Face Open LLM Leaderboard, ARIES needs a public, reproducible model repository with actual model weights, tokenizer/configuration, supported Transformers loading, a complete model card, and compatibility with the leaderboard's supported evaluation setup. The tiny character n-gram model currently deployed on the public endpoint is not a competitive Transformers foundation model and cannot be submitted as one. A third-party GGUF used with the optional local launcher must not be relabeled as ARIES-trained weights.

Official instructions:
- https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting
- https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/faq

## Next requirements for an honest leaderboard entry

1. Train or otherwise establish the provenance of an ARIES-owned model; record dataset licenses and training details.
2. Export actual weights and tokenizer/configuration to a public model repository in a supported format.
3. Run a standard, reproducible evaluator against a pinned model revision and publish full results and limitations.
4. Submit that exact model revision through the leaderboard's official process, if it meets current eligibility rules.
5. Report the leaderboard's actual response and score; until then, label the entry **not submitted**.

## Local software

The repository also includes a local inference wrapper and a standalone native runtime. The wrapper can serve a compatible GGUF locally; that is a serving implementation, not proof that those GGUF weights were trained by ARIES. The standard-library character n-gram runtime is ARIES-authored but intentionally small and limited. Neither should be represented as a state-of-the-art general-purpose model.
