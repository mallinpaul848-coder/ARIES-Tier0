# ARIES trillion-token training: readiness and evidence

## Current status

**Not trained to 1 trillion tokens.** The existing ARIES repository reports a small experimental Transformer checkpoint and a separate character n-gram API baseline. Neither is evidence of a trillion-token pretraining run.

A trillion tokens is a data/compute milestone, not a model setting. Never report the target as completed just because it appears in a config file. Count tokens with the final tokenizer, then separately log tokens actually consumed by completed optimizer steps and bind that log to immutable checkpoint hashes.

## Experimental streaming trainer

The repository now includes \`training/aries_trillion_token_trainer.py\`, a small PyTorch causal-language-model trainer with streaming corpus reads, causal attention, gradient clipping, optional CUDA mixed precision, optional torchrun/DDP execution, resumable checkpoints, corpus SHA-256 checks, and a JSON evidence report.

Install PyTorch in a Python 3.11+ virtual environment, then run a safe smoke test from the repository root:

\`\`\`powershell
python -m pip install "torch>=2.2,<3.0"
python training\\aries_trillion_token_trainer.py --corpus data\\licensed_corpus.txt --output-dir artifacts\\aries-streaming-trainer --max-steps 3
\`\`\`

The default \`byte\` tokenizer runs offline and counts UTF-8 byte IDs plus an end-of-line ID. Those are byte-token exposures, not GPT/BPE token counts. For a tokenizer-based run, install \`transformers\` and \`tokenizers\`, then use \`--tokenizer hf:gpt2\` (or the exact tokenizer intended for the model). Pin the tokenizer revision for reproducible production runs.

A run writes \`checkpoint.pt\` and \`training_evidence.json\` in the output directory. Resume with \`--resume-from-checkpoint latest\`. The default is deliberately only three optimizer steps; its evidence should say \`PARTIAL_TARGET_NOT_REACHED\`. To deliberately run until a specified target, set \`--max-steps 0\` and \`--target-training-tokens 1000000000000\`. That may run for a very long time and does not make a small or repetitive corpus high quality. Repeated epochs count as training exposures, not new unique corpus tokens.

The optional 3-6-9 pattern is bounded experimental embedding modulation, not an established improvement. The projection layer is a learned neural feature transform; it does not solve P=NP. GitHub Actions runs smoke tests only and is not used for large-scale pretraining.

## First action: audit your licensed corpus

Install Python 3.11+ and dependencies in a virtual environment:

\`\`\`powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install transformers tokenizers
\`\`\`

Place only text data you are authorized to use under \`data\\licensed_corpus\\\`, then run from the repository root:

\`\`\`powershell
python tools\\token_audit.py --corpus data\\licensed_corpus --tokenizer gpt2 --target-tokens 1000000000000 --output reports\\token-audit.json
\`\`\`

For a quick smoke test, add \`--max-files 2\`. The audit records per-file token counts and SHA-256 hashes, a manifest hash, failures, and the remaining corpus-token deficit. The first tokenizer download requires internet access. Replace \`gpt2\` with the exact tokenizer used by the model before treating the count as authoritative.

**Important:** the script counts tokens available in files; it does not train the model, deduplicate semantic near-duplicates, certify data rights, or claim tokens have been processed by training.

## Required training evidence

A genuine pretraining run should produce, at minimum:

- Dataset manifests, provenance, license review, deduplication report, and immutable dataset version.
- Exact tokenizer repository/revision and special-token configuration.
- Architecture/configuration and source commit hashes.
- Hardware type/count, distributed strategy, precision, measured throughput, utilization, power/cost records where available.
- Per-step or per-checkpoint \`tokens_seen\`, optimizer step, training loss, held-out validation loss, elapsed time, learning rate.
- Restart/recovery records and final model/checkpoint SHA-256 hashes.
- Independent evaluations on held-out data and recognized public benchmarks, with methodology and raw results.

Do not add token counts from repeated epochs and label them as unique corpus tokens. Report both unique corpus tokens and training token exposures. Keep failed/replayed work visible in the logs.

## Compute reality check

For a dense Transformer, a common first-order estimate is \`training FLOPs ≈ 6 × parameter_count × token_count\`. It is only an estimate and omits important architecture, sequence-length, communication, and operational overhead. For a 5.27-million-parameter model, 1T tokens is roughly \`3.16 × 10^19\` training FLOPs by this approximation, but that does not make the resulting model competitive: model capacity, data quality, optimization, and evaluation matter.

A larger model has proportionally higher compute demand. Large-scale training generally requires dedicated accelerator infrastructure, distributed training, checkpointing, and a budget. Do not expect GitHub Actions or a free web host to perform a full trillion-token pretraining run.

Reference for the approximate dense-model compute rule: [ComputingPower.org training estimates](https://computingpower.org/research/llm-training-cost-estimates). Actual project cost must be estimated from the chosen model, measured hardware throughput, utilization, and current provider quotes.

## Acceptance criteria for claiming completion

Mark trillion-token training complete only when a signed-off report can verify:

1. \`tokens_seen >= 1,000,000,000,000\` from training logs, not merely the corpus audit.
2. Logs reconcile with completed optimizer steps and the final checkpoint.
3. Validation loss is reported on held-out data with the tokenizer and dataset versions pinned.
4. The checkpoint can be loaded from a clean environment and generates non-empty output.
5. Benchmark methodology, raw measurements, hardware and limitations are published.

Until all criteria are met, status remains **NOT COMPLETE / NOT VERIFIED**.
