# ARIES AI / MALLIN Platform — Validation Status (2026-10-27)

## Scope and evidence

This report records observed GitHub Actions artifacts. It distinguishes project-owned tests from external validation and does not treat kernel microbenchmarks as end-to-end AI response latency.

### CI results

| Test | Observed result | Evidence |
|---|---|---|
| Full performance suite | Passed: Python performance job and C++ gateway build/smoke job | [Run 40460458113](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40460458113) |
| Public endpoint smoke test | Passed; five endpoint checks returned HTTP 200 | [Run 40454375518](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40454375518) |
| Local Hugging Face checkpoint smoke evaluation | Completed; model loaded/generated; small CPU task subset evaluated | [Run 40459398384](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40459398384) |
| PRISE reasoning matrix against hosted API | Workflow completed successfully, but many individual cases timed out | [Run 40501268902](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/40501268902) |

## Performance measurements

The full performance suite reported two in-process kernel measurement sets:

- Set A: median 120 ns, p95 121 ns, p99 180 ns, mean 122.7 ns.
- Set B: median 90 ns, p95 91 ns, p99 120 ns, mean 92.4 ns.
- In-process API test: median 3.645 ms, p95 3.937 ms, p99 4.205 ms, mean 3.708 ms, approximately 269.66 requests/s over 250 successful requests.

**Important:** the API test explicitly records `network_latency_tested: false`. These figures do not include HTTP network or hosted-server latency and must not be marketed as end-to-end chat latency. Kernel figures describe the measured kernel path only, not full model inference.

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
