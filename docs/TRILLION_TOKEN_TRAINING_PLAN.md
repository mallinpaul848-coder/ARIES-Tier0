# ARIES trillion-token training: execution plan and evidence standard

## Fixed target

The long-term target is **1,000,000,000,000 processed training tokens**. This document and any configured target value are plans, not evidence that training has reached the target.

## Stage 1 — reliable single-run accounting

- Keep a cryptographic SHA-256 fingerprint of the exact corpus file.
- Count actual token IDs fed into training batches; report this separately from corpus size and unique-token estimates.
- Save model, optimizer, scheduler, and trainer state checkpoints at regular intervals.
- Write a valid JSON evidence manifest that records processed tokens, optimizer steps, corpus hash, device, model shape, and status.
- Resume only when the corpus fingerprint matches the previous run.
- Test checkpoint recovery and compare counts before scaling.

## Stage 2 — corpus and data governance

- Build a documented, diverse, legally usable corpus with source URLs or dataset identifiers, licenses, dates, and deduplication procedure.
- Record both raw corpus token occurrences and estimated unique tokens after deduplication.
- Keep held-out evaluation data separate from training data.
- Never count a dataset's advertised size as tokens actually consumed by a training run.

## Stage 3 — distributed training readiness

- Select a model size and tokenizer based on measured hardware memory and throughput.
- Add multi-GPU/distributed training only after single-worker checkpoint recovery and token accounting pass tests.
- Use durable checkpoint storage, run identifiers, failure recovery, and monitoring for throughput, loss, memory, and hardware utilization.
- Verify multi-worker token accounting does not double-count replicas or gradient-accumulation bookkeeping.
- Estimate cost and duration from a measured pilot run; do not present estimates as measured results.

## Stage 4 — staged scaling

- Run a short smoke test, then a measured pilot, then progressively larger runs.
- After each run, preserve logs, config, code commit, corpus hashes, checkpoint identifiers, training loss, validation loss, throughput, elapsed time, and hardware details.
- Maintain a cumulative ledger across runs, with run IDs and checkpoint lineage. Do not add overlapping/replayed token ranges twice.
- Track **processed token occurrences** separately from **unique corpus tokens**. Repeated epochs count as processed training tokens, but not as new unique data.
- Publish the final evidence and model card only after independent checks.

## Acceptance criteria for claiming the target

A trillion-token completion claim requires auditable run logs and checkpoint lineage whose verified cumulative processed-token count reaches at least 1,000,000,000,000. The record must disclose repeated epochs, dataset deduplication method, model configuration, compute hardware, and evaluation results. A configured target, workflow dispatch, uploaded checkpoint, or repository commit alone does not meet this standard.

## Current limitations

The existing small GPT-2-style trainer is an experimental baseline. A CPU-only GitHub Actions job and the current small model/corpus workflow are not sufficient by themselves to establish a trillion-token training run. The pipeline must be tested and scaled on suitable compute. Do not claim the target has been reached until the evidence meets the criteria above.
