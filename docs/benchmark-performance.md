# ARIES performance reports: how to read the results

The scheduled GitHub Actions benchmark measures the currently configured public ARIES API from a GitHub-hosted Linux runner. It is a small smoke/diagnostic suite, not a frontier-model leaderboard evaluation.

## Metrics

- **Minimum / P50 / P90 / P95 / P99 / maximum latency:** elapsed request times from this runner. P50 is the median; P95 means 95% of measured requests completed at or below that value.
- **Mean latency:** arithmetic average of measured request times; unusually slow requests can raise it.
- **Requests per second:** completed requests divided by elapsed benchmark time for the measured workload. This depends on concurrency, model, prompt length, network, cold starts, and server capacity.
- **Answer exact-match:** number and fraction of the fixed test prompts whose normalized output matches the expected answer. This is not a general intelligence score and may penalize semantically correct wording.
- **Endpoint status and errors:** distinguish API reachability from successful model inference. A healthy `/health` response alone does not prove chat is answering correctly.

## What this benchmark does not establish

It does not compare ARIES against other providers under controlled identical hardware and prompts, measure GPU token throughput, establish sub-nanosecond or zero latency, prove zero hallucinations, or prove a polynomial-time solution to P vs NP. Do not publish a speedup multiplier unless the raw runs, hardware, model versions, concurrency, token counts, and methodology are recorded for both systems.

## Durable history

The workflow writes each successfully generated JSON report to `reports/aries-public-performance.json` and uploads a run artifact as a convenience copy. The JSON history in Git is the long-lived record; commits should be inspected for date, runner, request count, errors, latency percentiles, and exact-match results. A failed or unreachable endpoint is a result to investigate, not a performance pass.

## Run manually

Open [ARIES Performance Metrics](../actions/workflows/aries-performance.yml) and choose **Run workflow**. The workflow runs metric-helper checks and probes the configured public endpoint. Results are available in the Actions run summary/artifacts and in the committed report when the benchmark produced one.
