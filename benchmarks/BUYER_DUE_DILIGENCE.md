# ARIES Independent Evaluation and Buyer Due-Diligence Pack

## Product summary

ARIES Tier 0 is a self-hostable software stack combining an HTTP chat API, deterministic task handlers, a compact local-language-model path, performance telemetry, and experimental mathematical research diagnostics. The native deterministic path and generative model are separate and must be measured separately.

## What a buyer can evaluate now

- Deploy the API and run health/readiness and chat smoke tests.
- Re-run the project-authored functional suite and inspect per-case results.
- Benchmark latency, throughput, error rate, and response checks on a controlled host.
- Compare ARIES with any available OpenAI-compatible alternative using the same prompts, timeout, concurrency, and scoring rubric.
- Inspect finite SAT solver results, sampled Navier–Stokes diagnostics, and finite Yang–Mills spectrum diagnostics with explicit limits.
- Review source, test history, pinned revisions, model artifacts, licenses, and reproducibility instructions.

## Third-party alternatives: fair-comparison protocol

Use identical hardware where possible, fixed model revisions, identical prompt sets, temperature 0 where supported, equivalent token limits, warm-up policy, concurrency, timeout, and repeated trials. Report provider/model/revision, region, date, hardware, request count, warmups, failures/timeouts, P50/P95/P99, throughput, output-quality score, and cost per 1,000 successful requests where price data is available.

Keep these categories separate:
1. Deterministic task correctness.
2. General language/model quality on established evaluations.
3. Local inference latency.
4. End-to-end API latency including network and hosting.
5. Operational reliability and deployment effort.
6. Research-module finite-instance diagnostics.

Do not compare cache-hit microseconds with model-generation latency. Do not call a project-authored prompt suite an independent benchmark. Do not infer a general intelligence rank from narrow exact-match tests.

## Recommended evaluation matrix

| Evaluation | Primary metric | Required evidence |
|---|---|---|
| API reliability | success/error rate | timestamped JSON, status codes, repeated run |
| Latency/throughput | P50/P95/P99, requests/sec | wall-clock measurements and concurrency |
| Deterministic tasks | exact match | fixed test corpus, expected outputs |
| General language quality | recognized task suite | pinned model revision, evaluator config, full output artifact |
| SAT | correctness on bounded instances | exhaustive oracle for small formulas, seeds, formula hashes |
| Navier–Stokes | numerical residual diagnostics | grid, spacing, finite-difference method, test fields |
| Yang–Mills | finite-spectrum diagnostics | operator definition, eigenvalue source, tolerance |
| Reproducibility | run-to-run agreement | commit SHA, environment, command, artifact hashes |
| Security/operations | dependency/license/config review | SBOM or dependency inventory, deployment checklist |

## Buyer-facing claims policy

Supported claims must be tied to current artifacts and exact revisions. Describe ARIES as an independently testable software baseline with deterministic utilities and experimental research tools. Only claim a benchmark score when the corresponding raw report exists. No official leaderboard rank, independent certification, P-vs-NP proof, Navier–Stokes global regularity proof, or Yang–Mills mass-gap proof is implied by the current modules.

## Commercial diligence checklist

- [ ] Confirm ownership and licensing of every code, model, and training-data component.
- [ ] Confirm whether the buyer wants source-code license, deployment/support, private customization, or IP assignment.
- [ ] Provide a reproducible install and clean-machine acceptance test.
- [ ] Share raw benchmark reports and exact source/model revisions.
- [ ] Run buyer-selected prompts and a buyer-controlled deployment test.
- [ ] Define support, update, security-fix, uptime, and acceptance terms in writing.
- [ ] Keep secrets, customer data, and unpublished research out of public reports.
