# ARIES full model validation

This directory documents the repeatable validation pipeline in
`.github/workflows/aries-full-model-validation.yml`.

## What the pipeline tests

1. **Repository regression:** runs `pytest` and measures the deterministic fast path.
2. **Checkpoint integrity:** loads the local `published/aries-core-v1` config, tokenizer and weights; checks deterministic greedy generation; then attempts the full HellaSwag test split with lm-evaluation-harness.
3. **Public API diagnostics:** calls the deployed ARIES API and runs the ten-case authored diagnostic suite using `tools/aries_bench.py`.

## Run and retrieve evidence

- Open [ARIES Full Model Validation on GitHub Actions](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/aries-full-model-validation.yml).
- Open the newest run and download the `aries-full-model-validation-<run-id>`, `aries-software-validation-<run-id>`, and `aries-public-endpoint-validation-<run-id>` artifacts.
- Reports are evidence only when the workflow has completed. A failed checkpoint job means no valid HellaSwag score is available.

## Interpretation

The deployed `aries-native-ngram` endpoint is a character n-gram baseline plus deterministic task handling; it is not the local Transformer checkpoint. Endpoint HTTP timings include network and service overhead. The deterministic microbenchmark measures tiny CPU operations, not language-model inference. Neither can substantiate sub-nanosecond AI inference.

The authored ten-case endpoint diagnostic is a small smoke/functional test, not an official leaderboard score or independent model-quality certification. HellaSwag is reported separately for the local checkpoint and is not a general intelligence score.
