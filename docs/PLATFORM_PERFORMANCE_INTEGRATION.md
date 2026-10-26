# ARIES / MALLIN platform performance integration plan

## Objective
Improve end-to-end latency, tail latency, throughput, correctness, and reliability
across the platform. No subsystem is considered an optimization merely because it
is quantum-inspired, helical, vortex-based, self-learning, or mathematically novel.
It must pass correctness checks and beat a measured baseline on the same workload.

## Integration layers
1. Request/API: validate inputs, measure queue time and handler time, preserve errors,
   and keep deterministic handlers ahead of general model inference where appropriate.
2. Inference: measure cold start separately from warm requests; record model ID/revision,
   hardware, quantization, prompt/output token counts, concurrency, and memory.
3. PRISE/reasoning and self-learning: run as optional stages behind a feature flag;
   compare with the baseline on identical prompts and retain a candidate only if
   quality is non-regressing and latency remains within an explicit budget.
4. Quantum and quantum-inspired experiments: keep the classical state-vector simulator
   separate from the request path until workload-specific tests show a benefit.
   Simulator cost grows exponentially with qubit count, so it is not a default fast path.
5. Vortex/helical/math adapters: use private reviewed adapters and public interfaces;
   do not log or publish proprietary formulae or intermediate secrets.
6. Benchmarking: repeat cold/warm tests; report min, mean, P50, P90, P95, P99, max,
   requests/sec, error rate, and exact task score. Run concurrency levels 1, 2, 4, 8
   only after sequential baseline is stable.

## Acceptance gates
- Correctness tests pass for every candidate.
- Compare baseline and candidate on the same hardware, build, model, prompt set,
  concurrency, and warm/cold conditions.
- Report absolute latency and percentage change, not just a single average.
- Reject faster-but-wrong candidates.
- Keep the current stable route as fallback and support immediate rollback.
- Do not claim quantum advantage, self-awareness, third-party validation, or superiority
  without independent reproducible evidence.

## Privacy
Keep repository private. Keep proprietary Mallin/PRISE math out of benchmark logs,
public artifacts, and public reports. Publish only aggregate metrics and reviewed
interfaces if the owner explicitly approves.
