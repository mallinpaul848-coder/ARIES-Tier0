# ARIES-Tier0 — Third-Party Validation Status

Updated: 2026-10-17

## Status summary

**Automated reproducibility check: PASS. Independent third-party review/certification: NOT YET OBTAINED.**

The GitHub-hosted runner executed the repository's new ARIES Unified Runtime Validation workflow successfully:
- Run: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39018969712
- Commit: `4c4b895f5a9439c9a51527c882bf8d0b918e4c73`
- Result: all workflow steps passed; API health and a known arithmetic response passed; 1,000/1,000 concurrent HTTP requests returned valid responses; 0 errors.
- Artifact: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39018969712/artifacts/12095917485

## Measured latency

The GitHub-hosted `ubuntu-latest` runner reported the following for the local loopback API and the repository's deterministic reasoning/rule engine:

| Metric | Result |
|---|---:|
| Requests | 1,000 |
| Successful valid responses | 1,000 |
| Errors | 0 |
| Minimum HTTP latency | 21.961 ms |
| Mean HTTP latency | 638.035 ms |
| Median (P50) | 267.678 ms |
| P95 | 2,698.186 ms |
| P99 | 4,258.430 ms |
| Maximum | 5,253.262 ms |
| Total test duration | 6.679 s |
| Throughput | 149.73 requests/s |

These measurements are from one CI run and are sensitive to runner load and scheduling. The high P95/P99/max show that this run does **not** establish a sub-second latency guarantee under concurrency. The benchmark includes HTTP/client/server overhead; it is not a pure hardware instruction latency measurement.


## Public deployment smoke test (separate from local CI)

A separate GitHub-hosted workflow also passed against the deployed Render API on 2026-10-17:
- Run: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39018955533
- Public endpoint: `https://aries-tier0-api-6qjh.onrender.com`
- Result: public native API returned non-empty responses; the 10-case authored diagnostic suite scored 10/10 exact matches.
- Mean request latency: 102.796 ms; median: 102.838 ms; minimum: 94.245 ms; maximum: 110.448 ms.
- Raw JSON artifact: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39018955533/artifacts/12095449796

This is a real external HTTP smoke/diagnostic test from a GitHub-hosted runner against the deployed URL. The 10 prompts are authored in the project and overlap with explicit deterministic handlers, so it is **not an independent evaluation of general model capability**. It verifies endpoint behavior for this small case set only. The public deployment test ran on commit `31f937ca01430181375c046184cd13f5a1f2f1be`; verify the deployment revision separately before attributing the result to later code.

## What was actually tested

- Python compilation for the unified runtime and existing ARIES runtime modules.
- API startup and health endpoint.
- One exact arithmetic regression case (`What is 2 + 2?` -> `4`).
- Concurrent HTTP requests and response shape.
- Latency distribution, throughput, and error count.
- Artifact retention for public inspection.

## What is still required for genuine third-party validation

1. An independent reviewer who did not author the code or test suite reviews the implementation and benchmark methodology.
2. A reviewer independently runs the published steps and posts results, including commit SHA, environment, command lines, raw logs/report, and any deviations.
3. A larger, preregistered test set with held-out prompts and exact scoring rules is evaluated. Avoid using only examples hard-coded in the deterministic reasoner.
4. Load testing is repeated at several concurrency levels (1, 10, 25, 50, 100), with warm-up, multiple repetitions, error-rate reporting, and confidence intervals.
5. The deployed public endpoint is tested separately from loopback CI, with its exact URL, date, HTTP results, and deployment commit recorded.
6. If model-quality claims are desired, use suitable external standard benchmarks and a supported, loadable model artifact. The current ARIES implementation is a deterministic rule engine plus a small character n-gram baseline, not a modern general-purpose foundation model.

## Reproduce the current CI check

Open the [public workflow run](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39018969712), inspect its logs, and download the artifact. The workflow can be rerun from the [Actions page](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/aries-unified-runtime.yml).

## Claim boundary

This report records a successful automated integration test on a GitHub-hosted runner. It is **not** an independent certification, academic benchmark result, Open LLM Leaderboard submission, proof of general intelligence, or evidence of sub-nanosecond end-to-end inference. Any future independent review should be linked here without altering the raw results.


## Standard benchmark run: HellaSwag

A completed GitHub Actions workflow ran the full HellaSwag test split through EleutherAI's `lm-evaluation-harness` against the repository's small experimental Transformer checkpoint `published/aries-core-v1`:
- Workflow: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39017873547
- Evaluator job: checkpoint loading and full HellaSwag evaluation; completed successfully.
- Reported examples/likelihood requests: 10,042 HellaSwag examples (40,168 choice likelihood requests).
- Accuracy (`acc`): **25.67% ± 0.44 percentage points**.
- Normalized accuracy (`acc_norm`): **25.74% ± 0.44 percentage points**.
- Artifact: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/39017873547/artifacts/12095249773

This is a standardized benchmark executed by the project workflow using a third-party evaluation harness, but it is **not an independent third-party audit**: the workflow was initiated by the project repository. The score is close to the four-choice chance level of 25%, so it does not demonstrate strong HellaSwag commonsense performance. It is a result for the small Transformer checkpoint, not for the separately deployed n-gram API. The tested commit was `f16a1787c47d6e0221c5a35dea29f98171508a48`; it must not be attributed to later code without rerunning.
