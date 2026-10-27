# ARIES AI / MALLIN Platform — Validation Status (2026-10-27)

## Scope and evidence

This report records observed GitHub Actions artifacts. It distinguishes project-owned tests from external validation and does not treat kernel microbenchmarks as end-to-end AI response latency.

### CI results

| Public inference benchmark (latest) | Passed 3/3 scripted response checks; HTTP 200 responses; latency 183.88 ms, 398.89 ms, and 214.13 ms; median 214.13 ms | [Run 40504471930](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40504471930) |
| Test | Observed result | Evidence |
|---|---|---|
| Full performance suite (earlier run) | Passed: Python performance job and C++ gateway build/smoke job | [Run 40460458113](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40460458113) |
| Full performance suite (after evaluator fix) | Passed: Python performance job and C++ gateway build/smoke job | [Run 40504141441](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40504141441) |
| API proxy integration (after evaluator fix) | Passed: health, configured readiness, model listing, and response forwarding through a deterministic mock backend; local CI proxy round-trip 2.74 ms | [Run 40504141498](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40504141498) |
| Public endpoint smoke test | Passed; five endpoint checks returned HTTP 200 | [Run 40454375518](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40454375518) |
| Local Hugging Face checkpoint smoke evaluation | Completed; model loaded/generated; small CPU task subset evaluated | [Run 40459398384](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40459398384) |
| PRISE reasoning matrix against hosted API | Workflow completed successfully, but many individual cases timed out | [Run 40501268902](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40501268902) |

## Performance measurements

## Latest rerun — commit 1ef3cf201e783768395dd270d7b1f0ca030fcf31

The latest full performance workflow passed. It measured 20,000 iterations for each tiny Python operation and 250 in-process API requests:

- Digital-root operation: median 120 ns, p95 130 ns, p99 200 ns, mean 126.2 ns.
- Phase-8 modulo operation: median 90 ns, p95 100 ns, p99 130 ns, mean 94.0 ns.
- In-process FastAPI test client: median 3.648 ms, p95 4.387 ms, p99 4.766 ms, mean 3.763 ms, 250/250 successful requests, approximately 265.76 requests/s.
- C++ gateway compiled and its smoke test passed.
- API proxy integration passed all configured checks; the test returned the expected response through a deterministic mock backend in 2.74 ms.

These are project CI measurements. The API numbers exclude external network, deployed hosting, and LLM inference. The 2.74 ms integration result is a local mock-backend proxy test, not a live model latency measurement. Python operation timings include timer overhead; the observed values do not establish sub-nanosecond execution.


The full performance suite reported two in-process kernel measurement sets:

- Set A: median 120 ns, p95 121 ns, p99 180 ns, mean 122.7 ns.
- Set B: median 90 ns, p95 91 ns, p99 120 ns, mean 92.4 ns.
- In-process API test: median 3.645 ms, p95 3.937 ms, p99 4.205 ms, mean 3.708 ms, approximately 269.66 requests/s over 250 successful requests.

**Important:** the API test explicitly records `network_latency_tested: false`. These figures do not include HTTP network or hosted-server latency and must not be marketed as end-to-end chat latency. Kernel figures describe the measured kernel path only, not full model inference.

## Latest public inference sample

The latest public benchmark completed three chat samples against the hosted ARIES endpoint. All three returned HTTP 200 and passed the workflow's scripted assertions (3/3). Recorded latencies were 183.88 ms, 398.89 ms, and 214.13 ms; median 214.13 ms. The tested model ID was `aries-local-smollm2-135m`, and the report identified a local SmolLM2 instruction model with a deterministic task engine and optional OpenAI-compatible backend. This is a small smoke sample, not a high-concurrency load test or independent model-quality benchmark.

## Hosted endpoint smoke test

Five HTTP endpoint checks returned 200. Recorded response times were approximately 187.76 ms, 204.43 ms, 496.73 ms, 199.24 ms, and 199.83 ms. These are single-run endpoint smoke timings, not a statistically powered load test or an availability/SLA guarantee.

## PRISE matrix findings

The artifact contains 20 authored cases. Ten returned non-empty responses and all ten matched their expected exact answers. Ten cases timed out at roughly 60 seconds each. Therefore:

- Overall completed-case exact-match rate: 10/10 (100%) — **not** 10/20 overall.
- Case completion rate: 10/20 (50%).
- All-case pass rate counting timeouts as failures: 10/20 (50%).
- The artifact's reported mean latency (about 30.15 seconds) is dominated by timeouts; the median among all cases is 445.61 ms.
- This is a small, project-authored diagnostic, not an official reasoning benchmark or independent validation.

Next engineering action: investigate why repeated API requests stall after some successful calls; add bounded per-request timeouts, retries only where safe, and explicit failed-case accounting; rerun the matrix and a controlled concurrent load test.

## Local checkpoint task scores

The CPU smoke evaluation used only 25 examples per task. Reported scores were ARC Easy 0.32, HellaSwag 0.32, and WinoGrande 0.40. This sample is too small to support competitive-quality claims. The run also emitted dataset-loader compatibility warnings; resolve those and rerun with a larger, documented sample before using scores externally.

The local checkpoint config describes a GPT-2-style model with 4 layers, 256 hidden dimensions, 4 attention heads, context length 256, and vocabulary size 8,000. This is a compact checkpoint; it should not be described as equivalent to a frontier-scale general-purpose model without evidence.

## External validation and publication status

As of this report, the available artifacts do **not** establish:

- acceptance on an official Hugging Face leaderboard;
- independent NIST testing or certification;
- an independently administered third-party benchmark;
- a published public Hugging Face model repository verified by immutable revision;
- large-scale production load capacity or a service-level guarantee.

The repository contains a workflow for verifying a public Hugging Face model, but it requires the actual public model repository ID (and an immutable revision is recommended). Publishing to a user-owned Hugging Face account requires a write token stored as a GitHub Actions secret named `HF_TOKEN`; do not paste tokens into chat or commit them to the repository.

## Release gate

Before presenting ARIES as externally validated, publish the exact model/checkpoint and revision, record license and data provenance, run the public-checkpoint verifier against that revision, expand standardized task evaluation, fix timeout behavior, run staged concurrency tests with server/network latency included, and obtain independent evaluator confirmation. Keep source code and credentials out of public artifacts.

## Evidence links

- [Full performance suite](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40460458113)
- [Public endpoint smoke test](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40454375518)
- [Hugging Face CPU smoke evaluation](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40459398384)
- [PRISE reasoning matrix](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40501268902)

## Latest code commit

The evaluator timeout/reporting correction is committed as `1ef3cf201e783768395dd270d7b1f0ca030fcf31`. It reduces the default per-case timeout to 20 seconds, records incomplete cases separately, and exits unsuccessfully when any case is incomplete or fails exact match. The latest workflow runs above passed their configured CI jobs; a fresh hosted-model PRISE matrix rerun and public Hugging Face publication have not been confirmed.

Latest public inference artifact: [download report from run 40504471930](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40504471930/artifacts/12733334776).


## Fair comparison protocol added (2026-10-27)

A reproducible head-to-head protocol is now committed at [benchmarks/FAIR_COMPARISON_PROTOCOL.md](https://github.com/mallinpaul848-coder/ARIES-Tier0/blob/main/benchmarks/FAIR_COMPARISON_PROTOCOL.md). It requires the same versioned task set, pinned model revisions, recorded hardware/configuration, raw request-level samples, p50/p95/p99 latency, throughput/error/timeout rates, staged concurrency, and separate quality/completion scores. The protocol is in place; a controlled ARIES-versus-GPT/Gemini/Claude comparison has not yet been run.

## Latest PRISE rerun status

Workflow [40504141562](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40504141562) is still running at the last check in the reasoning-matrix job. Its evaluation step has not completed, so no final score is asserted here. The evaluator now uses a 20-second per-case timeout and is configured to fail incomplete cases.

## Hugging Face publication check

The private repository [paulmallin777/aries-core-v1](https://huggingface.co/paulmallin777/aries-core-v1) exists, but a live repository listing shows only `.gitattributes`; model weights, configuration, and tokenizer are not yet published there. The GitHub publish workflow requires the repository secret `HF_TOKEN` with Hugging Face write access. Never paste the token into chat or commit it.
