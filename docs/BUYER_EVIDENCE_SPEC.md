# ARIES Technical & Commercial Evidence Specification

**Status:** Validation plan. Targets are not achieved results unless a dated report and raw measurements demonstrate them.

## 1. Architecture and evidence boundaries

ARIES is evaluated as four distinct layers:

1. **Deterministic execution core:** Exact arithmetic, bounded rule evaluation, fixed-capacity data structures, and C/C++ hot paths. Reproducibility applies only to named operations under documented inputs, configuration, ordering, compiler, and hardware conditions.
2. **Intelligent orchestration:** PRISE, Vortex, digital-root, and related routing/preprocessing logic. Each component must demonstrate measurable value against an equivalent baseline; mathematical descriptors are not assumed to improve inference.
3. **Language-model subsystem:** `aries-local-smollm2-135m`, evaluated independently for response quality, inference latency, throughput, failure rate, and resource use. A deterministic kernel does not make token generation deterministic or correct.
4. **Audit and verification:** Source commit, build metadata, configuration, workload, raw samples, failures, and machine-readable reports.

## 2. Claim-to-test traceability

| Claim | Evidence required | Acceptance criteria |
|---|---|---|
| Zero-allocation hot paths | Instrumented allocator counters around named functions; initialization excluded; 10,000 or more steady-state calls | Zero dynamic heap allocations within the measured function boundary. This does not imply zero allocations in the whole process. |
| Low-latency kernels | Isolated repeated measurements; named CPU, compiler, flags, timer, warm-up, and sample count | Report min, mean, P50, P95, P99, max, and raw samples. Any numeric target is a target until reproduced. |
| Reproducible execution | Fixed corpus/configuration; repeated serial runs; bitwise comparison where representation permits; race/order tests for concurrent code | 100% matching outputs within the explicitly tested deterministic scope. |
| Bounded queue behavior | Full/empty boundary tests, wraparound, producer/consumer contract tests | No lost, duplicated, reordered, or corrupted items within the documented SPSC contract. Do not call an SPSC queue MPMC. |
| Throughput and tail latency | Sustained endpoint workload at stated concurrency; warm-up; repeated trials | Report successful RPS, failures, timeouts, P50/P95/P99/max and run-to-run variation. Do not label a small sample as a reliable tail-latency guarantee. |
| Language-model performance | Same model, prompts, decoding parameters, hardware, and serving conditions | Report API round-trip latency, response quality, failures, and token metrics only when token counts are supplied by the server or measured by a documented tokenizer. |
| Energy efficiency | Direct power measurement or validated hardware telemetry over a defined workload | Report joules per successful request and measurement uncertainty. Estimates must be labeled and are not procurement-grade measurements. |

## 3. Benchmark protocol

Every report must record:

- UTC timestamp, repository commit (when available), source/build identifier.
- CPU architecture/model, logical CPU count, operating system, runtime version, and memory when detectable.
- Target URL (without credentials), model identifier, prompt corpus/version, request count, concurrency, timeout, warm-up policy, and decoding parameters.
- Timer method, percentile definition, raw latency observations, response status, failures, and timeouts.
- Hardware and hosting conditions, including whether the test is local or remote.
- Any exclusions and the reason for each exclusion.

### Separate experiments

1. **Kernel experiment:** Compare equivalent deterministic operations (same inputs and outputs) on the same host. Report correctness alongside latency and allocation counts.
2. **Endpoint experiment:** Measure complete HTTP requests to the same model-serving workload. Report API latency and throughput separately from kernel timing.
3. **Model-quality experiment:** Use a fixed, versioned prompt set and explicit scoring rules. Do not treat exact-match toy prompts as a general intelligence score.
4. **Energy experiment:** Run only when power telemetry is available and the measurement boundary is stated.

The endpoint harness in `tools/aries_evidence_bench.py` measures end-to-end HTTP completion latency. It does not measure model-only compute time or TTFT for non-streaming responses. TTFT and generated tokens/second remain null unless measured with a streaming/token-aware protocol.

## 4. Interpretation and external alignment

Reports may borrow applicable measurement concepts from MLPerf Inference. Use of similar metrics is not MLPerf certification, an official MLPerf submission, or third-party validation. Any external evaluation must name the evaluator, workload, hardware, date, and published evidence.

## 5. Commercial position

ARIES is designed to combine deterministic bounded execution with a separately evaluated probabilistic language model. Potential value includes lower overhead for selected operations, reproducible bounded behavior, observable routing, and improved auditability where controlled tests demonstrate those benefits.

Do not claim that the architecture eliminates hallucinations, guarantees correctness, makes the entire language model deterministic, or produces lower cost/energy without comparative evidence. Nanosecond kernel measurements are not end-to-end AI response latency.

## 6. Reproduction

From the repository root, with the ARIES API already running:

```bash
python tools/aries_evidence_bench.py --base-url http://127.0.0.1:10000 --requests 30 --concurrency 1 --output reports/endpoint-run.json
python -m unittest tests.test_deterministic_core -v
```

Use concurrency 1 first on CPU-limited hosts. Higher concurrency is an intentional load test and may overload small/free instances.

See `reports/README.md` for the report contract. Empty or missing measurements must remain null; do not replace them with zero.
