# Adaptive Quantum-Inspired Compute for ARIES Tier Zero

## Purpose

Define a private, testable path for improving classical compute efficiency and quantum-circuit experimentation without claiming that classical software removes physical limits or provides quantum advantage.

This document is an engineering plan, not a report of completed implementation or measured speedups. Keep proprietary PRISE/MALLIN mathematics, credentials, customer data, and private model artifacts out of logs and public benchmark artifacts.

## Design principles

1. **Choose the representation by workload.** Use a full state vector only when the circuit size fits the configured memory budget. Investigate stabilizer/Clifford methods for circuits within their supported gate set, and tensor-network/MPS methods when entanglement structure makes them appropriate.
2. **Fail safely.** Estimate memory before allocation; enforce explicit qubit, RAM, wall-time, and circuit-depth budgets. Reject unsupported circuits rather than silently returning approximate or misleading results.
3. **Separate exact and approximate results.** Every output must state the simulation method, approximation settings, resource use, and whether the result is exact within floating-point tolerance or approximate.
4. **Benchmark against a relevant baseline.** Compare identical problem instances, hardware, versions, seeds, and stopping criteria. Report quality as well as runtime.
5. **No unsupported advantage claims.** A classical simulator is not quantum hardware. Quantum-inspired heuristics are not evidence of quantum speedup. Any hardware experiment must identify the actual provider, device, date, and configuration.
6. **Preserve a stable fallback.** Keep the existing simulator and established classical solver available. A candidate is eligible for default routing only after correctness, quality, memory, and latency tests pass.

## Proposed routing interface

A future orchestration layer may select among these methods:

- `statevector_exact`: small circuits, full amplitude representation.
- `clifford_stabilizer`: circuits composed of supported Clifford operations.
- `tensor_network`: circuits and models where contraction cost is acceptable under a bounded bond dimension.
- `classical_optimization`: exact solver for tractable instances, otherwise documented heuristics such as simulated annealing or QUBO methods.
- `unsupported`: resource budget or method constraints cannot be satisfied.

The router must not imply that these methods are interchangeable. A solver's output should include method, exactness/approximation status, runtime, peak memory when measurable, random seed, objective value, and verification result.

## Benchmark plan

### Quantum simulation correctness

- Zero-qubit and one-qubit boundary cases.
- Norm/probability normalization after every supported operation.
- Known gate identities and inverse operations.
- Bell-state correlations and deterministic basis cases.
- Random small circuits cross-checked against the existing state-vector implementation.
- Clifford-only circuits cross-checked against exact state vectors at sizes where both are practical.
- Tensor-network results compared with exact results on small instances, with error reported as a function of bond-dimension cap.
- Invalid gate, malformed circuit, exceeded memory budget, and exceeded depth budget cases.

### Optimization quality and cost

Use fixed, versioned problem instances for scheduling, graph routing, and QUBO formulations. Record:
- objective value and constraint violations;
- feasibility rate across multiple seeds;
- best, median, and spread of objective values;
- wall-clock time, CPU/thread count, and peak memory;
- baseline algorithm and stopping rule.

For small instances, compare with an exact optimum. For larger instances, compare against named, versioned baselines and do not label a heuristic result “optimal” without proof.

### Performance and release gates

Record P50/P95/P99 latency, throughput, peak memory, failures, and correctness. Separate cold-start from warm-run measurements. Publish no sub-nanosecond inference claim based on Python timers or a microbenchmark of a helper function. Do not accept a faster candidate if its answers are less correct or its quality is materially worse.

## Learning and improvement loop

1. Store each experiment as a versioned record with source, parameters, seed, code revision, metrics, and result verification.
2. Classify failures (correctness, quality, resource exhaustion, timeout, or regression).
3. Generate an improvement proposal; do not automatically deploy it.
4. Run unit, regression, adversarial, and held-out evaluations.
5. Require explicit approval before merging changes, changing model weights, or switching the production default.
6. Preserve rollback metadata and the previous known-good configuration.

Coverage metrics describe what has been indexed, not what the model understands or has mastered. Learning records must be durable and auditable; in-memory-only records are not persistent learning.

## Implementation sequence

1. Add resource estimates and memory-budget rejection to the existing simulator.
2. Strengthen simulator tests and add cross-check fixtures for small circuits.
3. Add a benchmark harness with machine-readable JSON results and deterministic seeds.
4. Prototype one specialized method at a time (Clifford/stabilizer first, then tensor-network only with a suitable library and license review).
5. Add QUBO/annealing experiments behind a feature flag and compare them with exact/established solvers.
6. Add persistent experiment history and review-gated candidate selection.
7. Integrate any candidate into request routing only after the release gates pass.

## Security and licensing

Keep the repository private. Do not upload source code, private formulas, model weights, secrets, or raw user prompts to external benchmark services. Review dependency licenses and data rights before adding libraries or datasets. Use synthetic or authorized benchmark instances by default.
