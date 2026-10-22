# ARIES latency and throughput targets

These are engineering targets, not claimed benchmark results.

| Metric | Target | Measurement rule |
|---|---:|---|
| Time to first token (TTFT) | 1.8 ms | Measure request start to first streamed generated token. Report warm and cold results separately and state whether network time is included. |
| Throughput | 1,450 generated tokens/sec/GPU | Count generated tokens divided by generation elapsed time on a named GPU and model, recording precision, batch size, prompt/output lengths, and concurrency. |
| Harmonic routing overhead | Minimize; report measured values | Time the ingest, transform, and synthesis stages independently using a monotonic high-resolution clock; report sample count and P50/P90/P95/P99/max. |
| Request reliability | Zero lost requests in the declared test | Record submitted, completed, failed, timed out, and duplicate requests at each concurrency level. |

## Measurement boundaries

The public API benchmark includes client-to-server networking, queueing, model inference, and response handling. It cannot be compared directly with an in-process routing microbenchmark. TTFT requires a streaming client and must stop at the first received content token; a non-streaming completion duration is not TTFT. Token throughput requires token usage or streamed token counts; requests/sec is not tokens/sec.

The C++ static memory pool and the Python dispatcher do not, by themselves, establish these targets. The current Python pipeline is a small deterministic signal transformation, not a language-model token generator or a general-purpose P-vs-NP solver. AVX-512, GPU utilization, CPU pinning, and lock-free queue benefits must be confirmed on the actual runtime and hardware.

## Reporting

Publish targets alongside measured values, sample count, hardware/model, warm/cold state, concurrency, error rate, and test command. Never substitute a target for a measured value or report an unverified speedup multiplier.
