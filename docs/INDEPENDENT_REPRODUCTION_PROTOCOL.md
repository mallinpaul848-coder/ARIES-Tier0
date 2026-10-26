# ARIES Independent Reproduction Protocol

## Purpose and scope

This protocol lets an external evaluator reproduce the project-owned ARIES API performance diagnostic against the configured endpoint. It is not an official academic benchmark, an independent certification, or a claim that ARIES outperforms another model. Results describe only the tested endpoint, model, date, request set, and runtime conditions.

## Automated test matrix

The GitHub Actions workflow `.github/workflows/aries-performance.yml` runs the benchmark harness checks and an API diagnostic, then repeats the concurrency matrix five times at concurrency levels 1, 2, 4, and 8. Each matrix run uses the benchmark harness's 15 authored arithmetic, reasoning, instruction-following, knowledge, and short-context cases. That is up to 300 completion requests in the matrix, plus the separate diagnostic run. Actual totals can be lower if the endpoint errors, a run times out, or reports are not produced.

Workflow results and downloadable artifacts:
- Performance workflow: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/aries-performance.yml
- Public API: https://aries-tier0-api-6qjh.onrender.com

## Reproduce on your own machine

Requirements: Python 3.12 recommended; network access to the endpoint; a terminal with the repository checked out.

```bash
python -m py_compile tools/aries_bench.py tools/aries_combined_bench.py
python tools/aries_bench.py --base-url https://aries-tier0-api-6qjh.onrender.com --model auto --timeout 75 --limit 15 --concurrency 1 --output reports/aries-independent-single-run.json
python tools/aries_combined_bench.py --base-url https://aries-tier0-api-6qjh.onrender.com --model auto --timeout 75 --repeats 5 --output reports/aries-independent-matrix.json
```

The matrix script supports repeat counts from 1 through 5 and concurrency levels 1, 2, 4, and 8. Requests target a live public service; performance may vary with service cold starts, load, network, model routing, and provider changes. Do not run aggressive tests against any endpoint you do not own or have permission to test.

## Required evidence to retain

For each evaluation, preserve:
1. Git commit SHA and workflow run URL.
2. UTC timestamp, endpoint URL, advertised/selected model ID, and test configuration.
3. Full JSON reports and GitHub Actions logs/artifacts.
4. HTTP completion success, exact-match outcomes by category, latency distribution, throughput, and all timeout/error counts.
5. Hardware/runtime information where it is actually measurable. Hosted endpoint tests do not by themselves establish the inference server's hardware.
6. Any missing reports, skipped cases, or failed steps. Do not silently omit failures.

## Interpretation rules

- Exact match is a strict metric for these small authored cases, not a general measure of intelligence.
- API latency is end-to-end request latency and must not be conflated with a nanosecond-scale C/C++ kernel microbenchmark.
- A passing project-owned workflow confirms that the configured checks ran successfully; it does not constitute third-party validation.
- Compare systems only under disclosed, reasonably matched hardware, model, prompt, concurrency, token limits, and sampling settings.
- Report confidence intervals or run-to-run variability for formal claims; do not claim universal speedup from a single run.
- The Humanity's Last Exam (HLE) probe is separate and gated by dataset access. No HLE score exists unless the evaluation successfully loads authorized data, evaluates examples, and writes a result report.

## Suggested independent review

Ask an evaluator to check out the recorded commit, run the commands above, inspect the raw JSON and workflow logs, repeat the test on a separately controlled environment, and publish both successful and failed runs with the exact setup. A neutral report should include limitations and comparisons, not just best-case measurements.
