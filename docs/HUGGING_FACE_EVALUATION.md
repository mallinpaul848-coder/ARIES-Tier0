# ARIES Hugging Face Evaluation Plan

## Status and scope

The repository contains an experimental GPT-2-style causal language model, not a claim of competitive general-purpose intelligence. The GitHub Actions workflow `.github/workflows/hf-evaluation.yml` runs a reproducible CPU smoke evaluation on a small fixed subset of HellaSwag, ARC-Easy, and WinoGrande, stores raw results as a workflow artifact, and records the code revision and environment.

This is **not** an independent third-party score, an Open LLM Leaderboard result, or proof that ARIES outperforms another model. Small subset scores have high uncertainty and must not be advertised as leaderboard results.

## Run the reproducible baseline

1. Open GitHub Actions and choose **Hugging Face model evaluation (reproducible CPU baseline)**.
2. Select **Run workflow** on the intended branch.
3. Open the run and download the `aries-hf-evaluation-<run number>` artifact.
4. Preserve the workflow URL, commit SHA, raw JSON, environment metadata, and failed-step logs with any report.

The workflow deliberately runs locally in GitHub Actions without uploading source code or private math to Hugging Face. The current evaluation subset is capped at 25 examples per task to keep cost/time bounded. For a publication-quality result, run the complete official task splits, multiple seeds where relevant, compare to named baselines using identical settings, and report confidence/limitations.

## Hugging Face third-party evaluation route

The Hugging Face Open LLM Leaderboard requires a public model repository, a model and tokenizer that load through standard Transformers AutoClasses, Safetensors weights, and a completed model card. Submission triggers evaluation on Hugging Face infrastructure; it is a separate step after model upload and public accessibility checks.

Before public upload, the owner must confirm the training corpus's license, attribution, and redistribution rights. The model card currently explicitly says the base corpus license must be checked. Until that is resolved, publish only to a private Hub repository and do not submit to a public leaderboard.

Official submission guidance: https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting
Official evaluation overview: https://huggingface.co/docs/hub/eval-results
