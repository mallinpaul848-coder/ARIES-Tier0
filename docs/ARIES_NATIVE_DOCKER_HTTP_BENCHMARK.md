# ARIES Native Docker HTTP Benchmark

This workflow builds the repository Docker image, starts the actual ARIES native
HTTP gateway under a 512 MB container memory limit, confirms a non-empty local
model greeting, and measures repeated deterministic arithmetic requests over
loopback HTTP at concurrency 1, 4, and 8.

The measured fast-path workload is intentionally a repeated, warmed arithmetic
cache hit. It is useful for observing HTTP + JSON + gateway + cache-hit latency;
it is not representative of unique prompts or neural-model generation. The
general-model greeting is a separate smoke test and is excluded from the
latency percentiles.

Reports include success counts, latency percentiles through P99.9, throughput,
host/runtime metadata, and raw JSON. Any correctness or request failure makes
the benchmark fail.

## Evidence boundary

- This is project-operated GitHub Actions CI on a hosted runner.
- It is not independent third-party certification or exchange production
  qualification.
- It does not measure energy, watts, joules/request, CPU package/DRAM energy,
  NIC/kernel latency, or external network performance.
- Hosted-runner results are useful for repeatable regression tracking, not
  absolute hardware comparisons.
- A power-saving claim still requires equal-work baseline/candidate runs on the
  same physical host with valid energy instrumentation.
