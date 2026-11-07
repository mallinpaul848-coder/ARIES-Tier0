# ARIES Licensing Evidence Ledger

**Purpose:** buyer-facing inventory of reproducible software evidence. This document intentionally excludes confidential internal research methods.

**Repository:** `mallinpaul848-coder/ARIES-Tier0`  
**Evidence snapshot:** 2026-11-06 (UTC run timestamps shown in GitHub Actions)  
**Change under test:** `optimize/fastpath-lock-overhead`, commit `661a402e9374586819d788bceb6118514511623c`, PR #52.

## 1. Evidence verified in GitHub Actions

### A. Pull-request CI

The PR-triggered workflow results associated with commit `661a402e9374586819d788bceb6118514511623c` returned seven completed successful workflows:

- ARIES Launchpad Platform Tests
- MALLIN Foundation Tests
- ARIES Tier Zero Vector Kernel Benchmark
- ARIES RTL External Smoke Test
- ARIES API Tests
- ARIES End-to-End Platform Validation
- ARIES Native Inference Tests

Run records: [GitHub Actions](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions).

### B. Native inference container smoke test

The native-inference workflow successfully built the container and ran it with a 512 MB Docker memory limit. It verified:

- `/health` returned HTTP 200.
- Readiness and diagnostics reported local inference loaded.
- `/v1/models` returned a model.
- A chat greeting returned non-empty text.
- The general question “What is the capital of France?” returned “The capital of France is Paris.”
- The configured backend in this test was local llama.cpp with `aries-local-smollm2-135m`; no upstream chat provider was configured.

Source: [Native inference workflow run #259](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/42316333727).

**Scope limit:** this is a container/API smoke test with two simple chat prompts, not a broad model-quality evaluation or proof of production readiness. The 512 MB figure is the test container memory cap, not measured memory consumption.

### C. Public API end-to-end diagnostic

The PR-triggered end-to-end workflow exercised the configured public endpoint with a 10-case ARIES-authored diagnostic suite. The recorded serial and concurrency-4 results were:

| Metric | Serial | Concurrency 4 |
|---|---:|---:|
| Cases completed | 10/10 | 10/10 |
| Exact matches | 10/10 (100%) | 10/10 (100%) |
| Latency samples | 10 | 10 |
| Mean latency | 148.837 ms | 138.166 ms |
| P50 latency | 145.039 ms | 139.504 ms |
| P90 latency | 167.424 ms | 147.988 ms |
| P95 latency | 175.372 ms | 155.189 ms |
| P99 latency | 181.730 ms | 160.950 ms |
| Maximum latency | 183.319 ms | 162.390 ms |
| Completed throughput | 6.718 req/s | 24.929 req/s |

Source: [End-to-end validation run #56](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/42316333748).

**Scope limit:** this is a small, project-authored diagnostic run against the configured public endpoint. Ten prompts are not a statistically strong production benchmark. The run itself explicitly states that it is not independent third-party validation and is not an official MMLU, GSM8K, BBH, or leaderboard score. These endpoint measurements do not establish that the lock simplification in PR #52 caused a latency improvement; the public endpoint was not rebuilt from this PR as part of that test.

### D. Native vector-kernel microbenchmark

A separate C vector-kernel comparison in the PR-triggered workflow measured 20,000 samples per implementation across five blocks:

| Metric | Baseline | Candidate |
|---|---:|---:|
| Mean | 233.12 ns | 230.16 ns |
| P50 | 60 ns | 60 ns |
| P95 | 1,302 ns | 1,292 ns |
| P99 | 1,422 ns | 1,422 ns |
| Maximum | 41,522 ns | 16,915 ns |

Correctness passed at absolute tolerance `1e-12`.

Source: [Vector-kernel benchmark run #154](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/42316333831).

**Scope limit:** this is a separate vector-kernel microbenchmark, not a measurement of the Python fast-path lock change or the complete chat model. The workflow itself cautions that five blocks in one process are not five independent machine/process runs and that no speedup should be assumed from this alone.

## 2. Status of the current latency change

PR #52 proposes replacing non-recursive re-entrant locks with ordinary locks and removing redundant prompt-normalization work in `software/latency_engine.py`.

- The PR-triggered CI workflows listed above completed successfully.
- The dedicated 200,000-iteration before/after benchmark for this exact Python change has **not yet been recorded**.
- No claim of a measured latency improvement is made here.
- The change should only be merged after its focused tests and controlled before/after measurements confirm correctness and no meaningful P95/P99 regression.

PR: [#52 — Optimize deterministic fast-path lock overhead](https://github.com/mallinpaul848-coder/ARIES-Tier0/pull/52).

## 3. Licensing evidence still required

### Data-center efficiency

Required controlled comparison against a named baseline on the same hardware and workload:

- joules per successful request and watt-hours per 1,000 requests;
- wall power, CPU package energy where available, utilization, memory, and thermal state;
- throughput and P50/P95/P99 latency at matched quality and concurrency;
- idle power and warm/cold-start behavior;
- repeated runs, raw logs, hardware/software versions, and uncertainty ranges.

No verified annual energy-savings figure or percentage is claimed yet. Annual savings must be calculated only after measured energy per equivalent successful workload is available.

### High-frequency trading / event processing

This is a separate workload and needs its own benchmark:

- event processing P50/P95/P99/P99.9 latency;
- sustained and burst throughput;
- CPU time, memory, and power per million events;
- dropped, duplicated, reordered, and late events;
- deterministic replay and correctness under load;
- overload behavior and recovery.

No exchange-grade or production HFT performance claim is made yet. Testing must use a clearly specified event workload and compare against a named baseline.

### Reliability and answer quality

- Expand the authored diagnostic set and include adversarial and out-of-distribution prompts.
- Record exact-match and task-specific quality, refusals, malformed outputs, timeouts, and error rates.
- Run repeated concurrency/load tests and preserve raw request/response records with secrets removed.
- Evaluate on recognized public benchmarks only when the exact ARIES model artifact, revision, tokenizer, and evaluation setup are reproducible.

## 4. Evidence governance

Every buyer-facing claim should link to a dated workflow run, immutable commit, raw artifact, test definition, hardware/runtime description, and measurement method. Separate project-operated CI from independent third-party validation. Do not present microbenchmarks as end-to-end model performance, do not present authored test accuracy as general intelligence, and do not infer energy savings or HFT suitability without direct workload measurements.
