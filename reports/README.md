# ARIES Evidence Reports

This directory stores generated, timestamped benchmark evidence. Do not commit placeholder performance numbers or fabricate missing measurements.

## Endpoint report

Generate with:

```bash
python tools/aries_evidence_bench.py --base-url http://127.0.0.1:10000 --requests 30 --concurrency 1 --output reports/aries-endpoint-evidence.json
```

The JSON report includes:

- `schema_version`, UTC timestamp, Git commit when discoverable, target, and hardware profile.
- Exact benchmark configuration and measurement scope.
- Health and model-discovery results.
- Per-request status, end-to-end latency, response presence, and server-reported token usage when available.
- Summary success rate, successful requests/second, min/mean/P50/P95/P99/max latency.

## Null and interpretation rules

- Missing measurements are `null`, never zero.
- This non-streaming harness does not measure TTFT.
- Model-only compute latency, allocation counts, and energy remain null unless a separate instrumented test supplies them.
- Token rate derived from server-reported completion tokens divided by full HTTP latency is explicitly an end-to-end approximation, not isolated decode speed.
- Small-sample P95/P99 values are descriptive only. Repeat tests and increase sample sizes before making tail-latency claims.
- Endpoint latency includes network, queueing, server processing, and response transfer.
- These project-generated reports are not independent certification or official MLPerf results.

Never include API keys, authorization headers, or private prompt data in committed reports.
