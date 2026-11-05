# ARIES HTTP Gateway Benchmark: Evidence Gap and Next Protocol

## Current verified state

The current native gateway container has a successful CI smoke test. The test builds the Docker image, starts the API on loopback, checks `/health`, readiness, diagnostics, and `/v1/models`, then sends two real `/v1/chat/completions` requests. The local `aries-local-smollm2-135m` model loads in independent/local mode without an external AI API key; the test verifies a non-empty greeting and that a capital-of-France question includes Paris.

This is functional end-to-end evidence only. The smoke test does not collect a latency distribution, sustained throughput, tail latency, overload behavior, or energy.

## Existing HTTP benchmark is a different target

`.github/workflows/aries-http-latency-validation.yml` starts `software/native_runtime.py serve` with a small CI-only n-gram model trained from a tiny authored corpus. It sends sequential loopback requests and reports min/mean/median/P90/P95/P99/max and throughput.

That workflow is useful as a legacy native-runtime baseline, but it does not exercise `software/public_native_server.py`, its FastPathEngine, its routing chain, or the local SmolLM2 model. Do not combine its numbers with public-gateway or model-inference measurements.

## Required next benchmark: current public gateway

Build and run the same Docker image used by the native smoke test, then benchmark its actual `/v1/chat/completions` endpoint on loopback. Preserve the tested commit SHA, image digest, runner details, model ID, and configuration in the JSON report.

Run distinct workloads so cache effects are visible:

1. Repeated supported deterministic prompts (warm-cache path).
2. Unique supported deterministic prompts (cache misses).
3. General chat prompts that reach the local model (model-inference path).
4. Mixed workload with a documented request mix.

For each workload, perform warm-up, then measure concurrency 1, 4, 8, and 16. Record every request's latency and outcome; report P50, P90, P95, P99, P99.9, max, successful requests/second, HTTP status counts, error rate, empty-response count, and exact-answer checks where applicable. Report model-generation time separately from total client-observed HTTP latency when the API response metadata supports it.

Use bounded test duration and request counts. Add a controlled overload phase separately; do not expose a public service to an unbounded load test. Capture timeouts and failures rather than silently dropping them.

## Power and HFT interpretation

GitHub-hosted runner timings are useful for repeatable CI regression detection, not exchange-grade HFT qualification. A loopback Python HTTP benchmark does not measure NIC, kernel-bypass, exchange-network, market-data feed, order-routing, or production co-location latency.

No energy-saving claim follows from latency alone. To quantify data-center energy efficiency, compare baseline and candidate on the same physical host, with identical workload, model, hardware, power policy, and completed useful work. Record supported CPU package/DRAM energy counters or calibrated external wall-power measurements, plus throughput and latency. Report joules per successful task and disclose unsupported domains and measurement limitations.

## Acceptance rules

- Do not label component timings as HTTP latency.
- Do not label CI loopback results as production/HFT qualification.
- Do not claim energy savings without measured energy for equal completed work.
- Keep baseline and candidate runs on the same host and configuration.
- Preserve raw per-request records and machine-readable JSON artifacts.
- Keep the PR draft until results have been reviewed; do not merge or deploy based on a benchmark design alone.
