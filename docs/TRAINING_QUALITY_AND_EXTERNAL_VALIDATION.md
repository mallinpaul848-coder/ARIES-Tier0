# ARIES training quality improvement

## What this adds

- `training/aries_quality_eval.py` evaluates a saved ARIES causal-LM checkpoint on a distinct held-out corpus.
- Reports mean next-token cross-entropy, perplexity, next-token accuracy, measured validation throughput, checkpoint hash, corpus hashes, model step, and recorded training-token count.
- Refuses to evaluate when the validation corpus SHA-256 equals the training corpus SHA-256.
- `.github/workflows/aries-quality-evaluation.yml` syntax-checks the scripts on relevant pull requests and can run a measured evaluation on an owner-managed self-hosted runner.

## How to run

On a machine with Python, PyTorch, a compatible ARIES checkpoint, and a licensed held-out text file:

```bash
python training/aries_quality_eval.py \
  --checkpoint artifacts/aries-multitrillion/checkpoint.pt \
  --validation-corpus data/heldout.txt \
  --max-batches 100 \
  --output artifacts/aries-quality-evaluation.json
```

Use a held-out file that was not used for training. The evaluator checks the full-file SHA-256 against the checkpoint's recorded training corpus hash. This detects an identical file, not semantic overlap or leakage from copied passages; dataset provenance and deduplication still matter.

## How this improves intelligence work

Training loss alone cannot show whether a model generalizes. Held-out loss/perplexity provide a repeatable signal for comparing checkpoints. Next-token accuracy is reported as a diagnostic and is not a standalone quality score. Use the same held-out corpus, tokenizer, sequence length, and evaluation settings for each comparison.

For capability claims, pair these language-model diagnostics with separate, fixed tests for arithmetic, logic, instruction following, factual questions, coding, refusal behavior, and robustness. Keep the prompts and scoring rules versioned and report every attempted case, not just successful examples.

## Scale and scientific limits

A configured trillion-token target is not evidence that the target was processed. The training manifest must show measured cumulative token exposures, run duration, throughput, loss, checkpoint hashes, hardware, and corpus provenance. Repeated epochs count as token exposures but are not unique tokens. The included byte tokenizer counts bytes-as-token-IDs, not standard BPE tokens.

The experimental 3/6/9 embedding modulation is not assumed to improve learning. Compare it against an otherwise identical baseline using fixed seeds and the same training/validation data. Do not claim a P-versus-NP solution from these features or benchmarks.

## External validation path

After a real checkpoint exists, package it in a public model repository with the model config, tokenizer files, weights (preferably safetensors), license, model card, dataset provenance, and exact immutable revision. Run `benchmarks/verify_hf_model.py` against that public revision to verify download, load, and generation. That script is a packaging smoke test, not third-party certification or a leaderboard result. A genuinely independent evaluator must run its own tests and publish its methods and results.
