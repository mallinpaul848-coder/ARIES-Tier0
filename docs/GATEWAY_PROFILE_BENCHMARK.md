# Gateway X Mallin–PRISE Profiling Benchmark

## Purpose

This benchmark measures the cost of computing the Mallin–PRISE request profile. It is deliberately isolated from model inference.

Included in the measured function call:

- whitespace normalization and text feature extraction;
- PRISE heuristic classification;
- digital-root, Phase-8, and Helixo feature calculation;
- SHA-256 prompt fingerprint generation;
- result-object construction.

Excluded:

- HTTP request handling;
- queue waiting and scheduling;
- model prefill and token generation;
- downstream verification and response serialization.

Therefore, these numbers are **gateway profiling overhead**, not end-to-end chat latency and not evidence of sub-nanosecond inference.

## Run

From the repository root:

```bash
python tools/benchmark_gateway_profile.py --repeats 100
```

Save a machine-readable report:

```bash
python tools/benchmark_gateway_profile.py --repeats 100 --output reports/gateway-profile.json
```

Use a controlled prompt corpus:

```bash
python tools/benchmark_gateway_profile.py --prompts-file benchmarks/gateway-prompts.txt --repeats 100
```

The prompt file is UTF-8, one prompt per line. Blank lines and lines beginning with `#` are ignored.

## Comparison protocol

1. Pin the exact Git commit for every run.
2. Use the same machine, Python version, power profile, prompt corpus, and repeat count.
3. Close unrelated CPU-heavy processes and record CPU model, OS version, and thermal/power conditions.
4. Run at least five independent benchmark processes per variant.
5. Compare medians across processes, plus within-run P50/P95/P99 and raw samples.
6. Do not mix this isolated measurement with HTTP, queue, or model latency.

For A/B/C comparisons:

- A: baseline gateway without Mallin–PRISE profile computation;
- B: profile computation enabled, with routing behavior otherwise unchanged;
- C: profile computation plus selective routing.

Measure full-request latency separately using the same model and request corpus. Report TTFT, total response time, throughput, timeout/error rate, and P50/P95/P99 at concurrency 1, 2, 4, and 8. Keep cache hits and cache misses in separate result groups.

## Interpretation

A faster profile function does not automatically make the chat service faster. The feature is beneficial only if the work it avoids exceeds its own computation cost and does not overload a slower route. Preserve correctness checks and compare tail latency, not only averages.

No performance claim should be marked validated until the raw report, exact commit, environment, and reproducible command are retained.

## CI artifact

The API test workflow runs this isolated benchmark after the full pytest suite and uploads `gateway-profile-report.json` as the `mallin-prise-gateway-profile` artifact. Each report includes Python/platform/machine metadata and raw samples. The artifact is a CI-runner measurement; compare runs only when runner hardware and software environments are comparable. The report does not include end-to-end inference timings.

## Paired full-vs-route-only profiler experiment

The current benchmark runs each prompt in both modes, alternates which mode runs first on each repeat, warms both modes, and retains raw nanosecond samples:

- **Full diagnostics:** includes the complete Mallin–PRISE profile and diagnostic fields.
- **Route-only:** computes the routing and PRISE decisions while omitting non-routing descriptors and prompt fingerprint hashing.

Run it with:

```bash
python tools/benchmark_gateway_profile.py --repeats 100
```

The report includes separate P50/P95/P99 summaries, raw samples, prompt-corpus SHA-256, and environment metadata. The paired run reduces order bias but is still a single-process microbenchmark; repeat it in several fresh processes and compare the distributions before treating a small difference as robust.

The route-only path is used by the native gateway request path. The full diagnostics remain available to diagnostic callers. The equivalence tests assert that routing and PRISE decisions are unchanged between modes for the tested prompt corpus. They do not prove that all possible prompts receive equivalent behavior.

## Local-model contention telemetry

The local inference adapter now exposes three distinct measurements in the chat response's `aries_native` object:

- `local_model_inference_ns`: total time measured inside the adapter, including lock wait.
- `local_model_lock_wait_ns`: time waiting to acquire the model's inference lock.
- `local_model_compute_ns`: time from lock acquisition through model response extraction.

Use these to diagnose concurrent-request latency. A high lock-wait fraction suggests serialized inference contention; a high compute duration suggests model prefill/generation dominates. These are server-side elapsed-time measurements, not hardware cycle counts. Do not infer throughput improvements from the telemetry alone.

The current model adapter retains its lock because the underlying model object is not assumed thread-safe. Do not remove the lock or enable concurrent calls into the same model instance without a separate correctness and stability test.
