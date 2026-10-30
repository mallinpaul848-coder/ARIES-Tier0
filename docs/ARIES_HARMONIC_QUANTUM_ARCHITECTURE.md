# ARIES harmonic and quantum-computing integration

## Integration rule

Use Mallin/PRISE concepts as optional, measurable transforms. Keep ordinary chat
on the shortest path; invoke deeper analysis only when the request requires it.

## Architecture guidance

| Layer | Integration | Measurement |
|---|---|---|
| Gateway | Bounded routing; avoid duplicate parsing and analysis | HTTP p50/p95/p99 |
| Chat inference | Direct path for ordinary prompts; PRISE for complex prompts | TTFT, tokens/s, total time |
| Math/reasoning | Digital-root and Vortex descriptors as optional tools | Equivalence tests and runtime |
| Native kernels | Keep only equivalent predicates/lookups that win paired benchmarks | ns/op and correctness |
| Cache | Bounded cache for deterministic, context-independent results only | hit rate, memory, latency |
| Retrieval | Harmonic features may supplement semantic ranking, never replace relevance tests | recall and precision |
| Scheduling | PRISE priority may guide queue classes without serializing independent tasks | queue wait and throughput |
| Streaming | Emit first token without waiting for optional analysis | TTFT |

## Quantum experiments

`aries_math/quantum_harmonic.py` implements small Hadamard, phase, CNOT, and
measurement operations using a classical state vector. Digital roots can be mapped
to a phase for experiments. This is simulation on ordinary CPU hardware, not a
quantum processor and not evidence of quantum advantage. State storage grows as
2**qubits; the simulator is capped at 12 qubits and must remain outside production
chat inference.

A real hardware adapter may be added later behind an optional interface. Record
backend, device, circuit, shots, queue time, execution time, and classical baseline.
The normal CPU deployment must remain functional without quantum hardware.

## Merge gates

1. No speed claim without paired measurements on the same hardware, model, prompts,
   warm-up, concurrency, and output limit.
2. Enable a harmonic optimization only after equivalence tests and a measured win
   without answer-quality regression.
3. Keep quantum simulation off the latency-critical path unless evidence shows a
   practical benefit.
4. This integration does not prove the Universal Harmonic Theorem or solve the
   Millennium Prize problems.