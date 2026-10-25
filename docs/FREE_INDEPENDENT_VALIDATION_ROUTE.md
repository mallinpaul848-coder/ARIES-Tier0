# Free Open-Source Validation Route for ARIES

## Goal and honest status

This is a no-fee route to produce reproducible public benchmark evidence using open-source tools and community review. It is not a promise of a formal certification, a NIST evaluation, a leaderboard acceptance, or an independent report. A project-run benchmark is still project-run; it becomes independent only when an unaffiliated reviewer reproduces or runs the tests and publishes their own methods and findings.

## Route A — run open benchmarks against the exact local checkpoint

The free [EleutherAI Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) supports local Hugging Face-compatible models and provides standardized task definitions.

1. Clone this repository and pin the exact commit SHA being tested.
2. Verify the model files and licenses. Record SHA-256 hashes for model weights, config, tokenizer, and evaluation data.
3. Use a clean Python environment and install the harness with its Hugging Face backend:
   `python -m pip install "lm_eval[hf]"`
4. First check whether the local checkpoint loads through the standard Transformers classes:
   `python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; p='published/aries-core-v1'; t=AutoTokenizer.from_pretrained(p); m=AutoModelForCausalLM.from_pretrained(p); print('LOAD_OK',sum(x.numel() for x in m.parameters()))"`
5. If and only if loading succeeds, run a small smoke evaluation first, then a documented benchmark. Example (task availability depends on the installed harness version):
   `lm-eval run --model hf --model_args pretrained=published/aries-core-v1,dtype=float32 --tasks hellaswag --device cpu --batch_size 1 --limit 20 --output_path reports/aries-hellaswag-smoke.json`
6. Record the complete console output, command, environment, commit SHA, artifact hashes, hardware, and any errors. A 20-example smoke test is a pipeline check, not a publishable full benchmark score. Use the full supported test set for a score, and publish all settings and results.

Do not modify model weights or prompts after seeing the test results without creating a new version and rerunning. Avoid test-set leakage. Report unsupported tasks and failed runs rather than silently dropping them.

## Route B — request free public leaderboard evaluation

The [Hugging Face Open LLM Leaderboard submission instructions](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting) require a public model repository and standard Transformers loading, a supported architecture, suitable weight format (Safetensors), a complete model card, and a pinned revision. The platform's current eligibility rules may change, and submission does not guarantee acceptance or a ranking.

Steps:
1. Create a public model repository and upload the model weights, config, tokenizer files, accurate model card, license, and training-data provenance.
2. Test loading with `AutoConfig`, `AutoTokenizer`, and `AutoModelForCausalLM` at the exact public revision.
3. Pin the revision SHA and submit through the official leaderboard instructions.
4. Save the queue status and final results. If the model is rejected or unsupported, retain the reason and use Route A.

Do not upload the model until rights to redistribute the training data and resulting artifacts have been checked. The current model card explicitly says the base corpus license still needs verification. Resolve that first.

## Route C — invite an independent community reviewer

Share the repository, exact revision, and this [independent validation request packet](INDEPENDENT_VALIDATION_REQUEST.md) with an unaffiliated ML researcher or community evaluation group. Ask them to run the same pinned benchmark independently, document conflicts of interest, and publish raw outputs and limitations. A voluntary review may be free, but availability and acceptance are not guaranteed. Do not describe an offer or request as completed validation.

## What the current artifacts establish

The repository describes `published/aries-core-v1` as an experimental 5.27-million-parameter GPT-2-style causal LM. The README says the training-corpus license needs verification and makes no independent benchmark claim. Therefore, the immediate gates are:

- [ ] Verify training data and redistribution rights.
- [ ] Confirm standard tokenizer/model loading works from the local folder.
- [ ] Run and archive a full, reproducible open benchmark on a pinned revision.
- [ ] Publish the report with hardware, hashes, commands, raw results, and limitations.
- [ ] Obtain independent reproduction or a public leaderboard result before claiming external validation.

## Claims policy

Use precise wording:
- Before independent reproduction: “Open-source benchmark run by the project.”
- After an independent party reproduces it: “Independently reproduced by [reviewer] on [date], using [revision and method].”
- After leaderboard acceptance: state the exact leaderboard and result URL.

Do not call ARIES “NIST validated,” “NIST certified,” “third-party certified,” “fastest,” “sub-nanosecond AI inference,” or a P-vs-NP solution without evidence that specifically supports that claim.
