# ARIES / MALLIN Tier Zero — HFT and Data-Center Licensing Evidence Plan

**Status:** Validation plan; not a performance certification or a claim of measured energy savings.  
**Audience:** Prospective quantitative-finance, infrastructure, cloud, and data-center licensees.

## 1. Commercial objective

Prepare two evidence-backed licensing tracks for ARIES / MALLIN Tier Zero:

1. **Low-latency deterministic gateway track:** bounded deterministic request routing, fast-path task handling, predictable queueing, observability, and safe integration around latency-sensitive systems.
2. **Data-center efficiency track:** reduce avoidable inference calls and CPU work, then measure energy per useful completed task under controlled workloads.

The same software may support both tracks, but each requires separate acceptance tests and customer-specific validation.

## 2. Current implementation facts to validate

The current gateway source includes:

- A deterministic fast path and bounded LRU cache before local-model inference.
- A local GGUF inference adapter using llama.cpp with a lock around model generation.
- Per-operation latency telemetry exposed through `/performance`.
- Chat response metadata that distinguishes fast-path, local-model, and upstream execution.
- A project-owned diagnostic benchmark with 15 authored cases and configurable concurrency.

These are source-code observations, not proof of production performance. The current diagnostic benchmark is explicitly a small project-owned smoke suite, not an independent academic benchmark.

## 3. HFT-oriented validation

### Scope

Initially position ARIES as a **latency-sensitive software gateway / deterministic pre-processing component**, not as an exchange, broker, trading strategy, market-data feed handler, or certified order-entry system.

Do not claim exchange-grade HFT suitability until a qualified customer validates the complete deployment path, including their NIC, kernel, runtime, risk controls, venue connectivity, and market-data conditions.

### Test matrix

Run on documented, fixed hardware and software configurations:

- Warm and cold process starts.
- Deterministic fast-path hit, miss, and unsupported-request fallback.
- Single request and controlled concurrency levels.
- Fixed-size and varied-size payloads.
- Sustained runs long enough to expose thermal and scheduling effects.
- CPU affinity / pinned-core variants where supported.
- Baseline gateway versus ARIES gateway under the same workload.

Capture:

- End-to-end and server-side p50, p90, p95, p99, p99.9, and maximum latency.
- Throughput and completed-request rate.
- Queue wait, execution time, and timeout / rejection counts.
- CPU cycles, instructions, context switches, cache misses, and migrations where hardware counters are available.
- Correctness and deterministic-output checks.
- Hardware, OS, compiler, runtime, configuration, commit SHA, and raw results.

For latency-sensitive integration, report the complete distribution and tail behavior. Do not present a single minimum or average as representative latency.

## 4. Data-center energy validation

### Primary metrics

Measure energy on the same host and under the same workload before and after each optimization:

- Joules per successful request.
- Joules per exact-match successful task.
- Joules per generated token for model-backed tasks.
- CPU package energy and DRAM energy when supported by platform counters.
- Average and peak power, CPU utilization, memory use, throughput, and latency.
- Idle energy and workload energy separately.

### Measurement sources

Prefer calibrated external wall-power measurement for whole-system energy. Where available, supplement it with platform energy counters such as Intel RAPL or AMD energy telemetry. Use accelerator vendor telemetry only when an accelerator is actually part of the tested configuration.

Record counter availability, sampling interval, meter accuracy, and measurement limitations. Do not compare different measurement domains as if they were equivalent.

### Controlled protocol

1. Freeze hardware, firmware, OS, power policy, model file, and software commit.
2. Establish idle baseline and warm-up procedure.
3. Replay a fixed, versioned workload with fixed request mix and concurrency.
4. Run baseline and ARIES variants in alternating order to reduce drift bias.
5. Repeat enough times to report variation and confidence intervals.
6. Report absolute joules and normalized joules per successful task.
7. Verify output quality and error rates so energy savings are not achieved by doing less useful work.
8. Publish raw machine-readable results and reproduction instructions.

A valid savings claim must compare equivalent successful work at an agreed quality threshold. Lower power alone is not an efficiency improvement if throughput or correctness falls more.

## 5. Optimization sequence

Prioritize changes that can be measured and safely rolled back:

1. Instrument queue wait, routing, model inference, serialization, and total request time separately.
2. Preserve the deterministic fast path; add tests for cache correctness, eviction, and concurrent access.
3. Add bounded admission control and explicit overload behavior around the serialized local-model worker.
4. Avoid duplicate work for identical in-flight deterministic requests only where result equivalence and cancellation semantics are safe.
5. Tune model context, batch size, thread count, and output-token limits using a fixed quality/latency/energy matrix.
6. Evaluate CPU affinity and hardware-specific builds only on repeatable target systems.
7. Compare every change against a recorded baseline and reject regressions in correctness, tail latency, or energy per successful task.

Do not remove the llama.cpp model lock without proving the selected backend/context is safe for concurrent generation.

## 6. Mallin / PRISE contribution and IP boundary

Treat PRISE, Mallin routing, and related mathematical components as candidate implementation IP. Expose only the interface and evidence required by a licensee. Keep proprietary derivations, weights, internal heuristics, and implementation details out of public benchmark reports unless the owner deliberately approves disclosure.

A customer-facing evaluation should describe observable behavior and reproducible test conditions, not imply that a mathematical framework guarantees speed or energy savings.

## 7. Licensing package

Prepare a controlled evaluation package containing:

- Product overview and integration boundary.
- Versioned API specification and deployment requirements.
- Benchmark methodology, workload definitions, and raw result files.
- Reproduction scripts and hardware / software manifest.
- Correctness, security, reliability, and failure-mode test results.
- Third-party dependency and model-license inventory.
- IP ownership and provenance review.
- Support, update, audit, and confidentiality terms.

Potential commercial structures to evaluate with counsel and customers:

- Time-limited paid evaluation license.
- Per-server / per-node production license.
- Enterprise site or fleet license.
- Optional support, integration, and performance-validation services.

Pricing and exclusivity should be negotiated only after evidence, scope, and IP ownership are reviewed.

## 8. Release gates

No public claim of HFT-grade performance or quantified data-center savings until all relevant gates pass:

- Reproducible baseline and optimized runs on named hardware.
- Correctness and workload equivalence demonstrated.
- Tail-latency and overload behavior documented.
- Energy measured with a stated meter / counter and uncertainty.
- Independent reproduction or customer validation where commercially material.
- All figures traceable to raw results, commit SHA, and test configuration.

## 9. Current claim discipline

At this stage, ARIES has source-level mechanisms that may reduce unnecessary inference for supported deterministic tasks. The magnitude of latency improvement, throughput impact, and energy savings remains **unquantified for this licensing program**. HFT suitability remains **unvalidated**. This document defines the work required to establish those facts.
