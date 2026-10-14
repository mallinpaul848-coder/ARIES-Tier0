# ARIES external validation and leaderboard readiness

## Public inference endpoint

- **Endpoint:** https://aries-tier0-api-6qjh.onrender.com
- **Latest recorded public endpoint benchmark:** [GitHub Actions run 38510422674](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38510422674)
- **Machine-readable report:** [2026-10-14-public-endpoint.json](./reports/2026-10-14-public-endpoint.json)
- **Measured from a GitHub-hosted runner at 2026-10-14T02:51:15Z:**
  - `/health`: HTTP 200, 154.78 ms
  - `/`: HTTP 200, 146.95 ms
  - `/diagnostics`: HTTP 200, 174.62 ms; native backend reported configured, 2,164 trained characters
  - `/v1/models`: HTTP 200, 126.27 ms; model ID `aries-native-ngram`
  - Chat requests: 3/3 returned successful responses; 3/3 narrow assertions passed
  - Chat end-to-end latency: minimum 116.29 ms, median 131.01 ms, maximum 147.99 ms
- **Other automated checks:** [API tests](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38510448842), [end-to-end integration](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38510448787), and [RTL smoke test](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38510448857) passed.

These are deployment and regression checks, not independent certification of broad language-model capability. The endpoint currently serves ARIES's native character n-gram baseline and narrow task engine; it is not the experimental Transformer checkpoint described below.

## Experimental Transformer checkpoint

- **Training/export workflow:** [Run 38511413963](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38511413963) completed successfully.
- **Training log:** 141.0151 seconds; reported training loss 6.508822067260742; 5,273,088 parameters.
- **Local artifact checks:** model and tokenizer reloaded; a generation smoke test succeeded.
- **Public GitHub artifact directory:** [published/aries-core-v1](https://github.com/mallinpaul848-coder/ARIES-Tier0/tree/main/published/aries-core-v1).
- **Workflow artifact (30-day retention):** [download](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38511413963/artifacts/11869839365).
- **Hugging Face upload:** NOT COMPLETED. The workflow reported that `HF_TOKEN` was not configured. Do not paste a token into an issue or chat. If you choose to publish, add a Hugging Face write token under [GitHub Actions repository secrets](https://github.com/mallinpaul848-coder/ARIES-Tier0/settings/secrets/actions) as `HF_TOKEN`, and verify the resulting public model page and files.
- The enhanced wrapper adds seven short educational math notes to the base corpus. This is not evidence of novel mathematics, proof of a Millennium Prize problem, or competitive model quality. Confirm training-data licensing/provenance and test for memorization before distributing weights.

## Proprietary source boundary

This repository is public. Keep raw derivations, proprietary operators, private corpora, unpublished proofs, and secret credentials outside it—preferably in a separate private repository or local directory. The current `.gitignore` excludes common private paths and secret patterns, but ignore rules do not remove previously committed files.

The supplied experimental `BioBinaryFrequencyAttention` implementation should **not** be added to this public repository if it contains trade-secret implementation details. Keep it private and only publish an adapter/configuration and artifacts you have reviewed and have the right to release. The current main-branch tree does not contain `aries_core/bio_binary_engine.py`, but deleting a file from the latest tree does not erase its earlier public Git history. If the historical version contains sensitive trade secrets, history rewriting and force-pushing (or GitHub Support for cached references) may still be necessary. No claim is made here that history has been scrubbed.

The frequency-modulation mechanism is a research hypothesis. It has not been demonstrated to improve model quality and does not itself establish a new mathematical result.

## Official leaderboard status

**Official leaderboard submission: NOT SUBMITTED. No official rank is claimed.**

The public endpoint checks and GitHub Actions tests do not submit ARIES to a leaderboard. The native n-gram endpoint is not a standard Transformers foundation-model submission. The experimental Transformer checkpoint has not been verified as uploaded to a public Hugging Face model repository, and no official leaderboard queue/acceptance result is recorded.

For a legitimate submission:
1. Establish training-data provenance and licensing.
2. Publish the reviewed model weights, tokenizer, config, and accurate model card to a public model repository.
3. Verify loading using supported Transformers AutoClasses at a pinned revision.
4. Run a supported, reproducible evaluator and publish its complete results.
5. Submit that exact revision through the leaderboard's official process and verify the actual queue/result.

Official references: [Open LLM Leaderboard submission instructions](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting) and [FAQ](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/faq). An account token and an explicit official submission/confirmation are required for steps that need account access; a passing CI workflow is not a substitute.

## Public model-loading check

After an actual public model repository exists, run:

```bash
python -m pip install -U transformers torch safetensors
python benchmarks/verify_hf_model.py YOUR_HF_ORG/aries-v1 --revision MODEL_COMMIT_SHA
```

This is a packaging check only; it does not measure quality or submit the model to a leaderboard.
