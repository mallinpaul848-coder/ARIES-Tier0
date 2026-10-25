# Independent model evaluation

This workflow evaluates the separately published experimental causal language model in `published/aries-core-v1` using EleutherAI's open-source Language Model Evaluation Harness. It does **not** evaluate the hosted API's separate `aries-local-smollm2-135m` backend.

## What it does

- Loads the published model and tokenizer using Hugging Face Transformers with remote code disabled.
- Checks that the tokenizer vocabulary matches the model's input embedding size.
- Runs a reproducible smoke-sized sample (25 examples per task) of ARC-Easy and HellaSwag using a pinned evaluation-harness version.
- Uploads the raw JSON results and logged samples as a GitHub Actions artifact.

## Run

Open **Actions → ARIES Independent LM Evaluation → Run workflow**, or open a pull request that changes `published/aries-core-v1/**`.

## Interpretation

This is an independent-tool evaluation, not an endorsement or certification by EleutherAI, Hugging Face, or a third-party lab. The 25-example limit is for a smoke evaluation and is not a leaderboard score. Do not compare these results directly with full-set leaderboard scores. For a leaderboard submission, follow the current official submission rules and run the complete approved evaluation on a fixed public revision.

The model card currently describes this as an experimental, small GPT-2-style model trained from random initialization. The workflow reports measured results without assuming competitive quality.
