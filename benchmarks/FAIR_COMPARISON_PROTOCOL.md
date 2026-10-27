# ARIES AI Fair Benchmark Protocol

**Status:** Protocol committed; comparative runs are not yet executed.  
**Purpose:** Make ARIES/MALLIN comparisons reproducible and fair rather than treating microbenchmarks or a few smoke requests as proof of model superiority.

## Rules for a valid comparison

1. **Separate the layers.** Report (a) tiny-kernel timing, (b) API/proxy overhead, (c) end-to-end hosted response latency, and (d) model quality separately. Never use a kernel result as a chat-latency claim.
2. **Same task set.** Use a versioned, licensed, documented prompt set with identical prompts, answer limits, stop rules, and scoring for every model. Publish task IDs and hashes; keep private evaluation answers out of model prompts.
3. **Comparable conditions.** Record exact model ID and immutable revision, quantization, inference engine/version, hardware/accelerator, precision, context/output limits, batch size, concurrency, region, network path, and all non-default settings. If these differ, label the comparison as non-controlled.
4. **Latency methodology.** Record at least 30 warm-up requests and at least 500 measured requests per configuration when practical. Preserve every raw sample. Report count, errors/timeouts, p50, p90, p95, p99, mean, min/max, tokens/sec, time-to-first-token (when streaming), and request throughput. State whether queueing, network, tokenization, and generation are included.
5. **Load test in stages.** Run concurrency 1, 2, 4, 8, 16, then increase only while the service remains stable. Use a fixed request mix and bounded duration; report offered load, completed load, error rate, timeout rate, and resource use. Do not infer production capacity from an in-process test client.
6. **Quality before speed claims.** Evaluate on multiple documented tasks, report accuracy/exact-match and completion rate separately, count timeouts and malformed answers as failures in the all-case score, and include confidence intervals where appropriate. A tiny smoke set is diagnostic only.
7. **Fair baselines.** Compare against named models only when exact versions and settings are recorded and access is permitted. Run models as close to simultaneously as practical, randomize order, repeat on multiple sessions, and report failures rather than silently dropping them. If model APIs or hardware differ, disclose that limitation.
8. **Independent review.** Provide a one-command runner, environment lockfile, dataset licenses/provenance, raw JSONL/CSV samples, scoring code, run logs, commit SHA, and artifact hashes. Have an independent reviewer rerun the procedure before using “third-party validated,” “leaderboard accepted,” or certification language.

## Required output schema

Each run should include:

- Run ID, UTC timestamp, git commit SHA, protocol version
- Model provider/name/revision and serving configuration
- Hardware/OS/runtime/dependency versions
- Dataset/task-set version, item count, license/provenance, and hash
- Warm-up count, measured count, concurrency, request/output limits
- Per-request latency, status, input/output token counts, finish reason, and score
- Summary percentiles, throughput, error/timeout/completion rates, quality scores, and confidence intervals
- Exact commands, logs, artifact hashes, known limitations, and reviewer identity (if independently reviewed)

Do not publish API keys, private source code, private prompts, personal data, or credential-bearing URLs.

## Current evidence boundary

The current repository evidence includes successful project CI performance tests, a 250-request in-process API test, a three-sample hosted inference smoke test, and a small authored reasoning matrix with substantial timeouts in the earlier run. Those results are useful engineering signals but do not establish a fair head-to-head model win, official Hugging Face leaderboard acceptance, NIST certification, independent third-party validation, or production-scale capacity.

## Release gate

A comparative result is publishable only after: (1) the exact public model/checkpoint and revision are pinned; (2) the same versioned test set is run on ARIES and each baseline; (3) raw results and failures are retained; (4) the evaluator treats incomplete cases as failures; (5) the concurrency test includes real network and inference; and (6) the report states whether an independent reviewer reproduced it.
