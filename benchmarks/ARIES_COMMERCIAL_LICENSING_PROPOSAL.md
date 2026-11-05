# ARIES Tier 0 — Commercial Evaluation and Licensing Proposal

**Prepared for:** Prospective technology partner  
**Prepared by:** ARIES Tier 0  
**Status:** Discussion draft — subject to technical diligence, ownership review, and definitive written agreements  
**Version:** 1.0

---

## Executive proposal

ARIES Tier 0 is a self-hostable software platform combining an HTTP API, deterministic task-handling paths, a compact local language-model path, diagnostics, and performance measurement tools.

We are inviting qualified technology teams to evaluate ARIES in two potential application areas:

- **Data-center software efficiency:** evaluate whether deterministic routing and fast-path handling can reduce CPU work or energy per equivalent successful task in a buyer-selected workload.
- **Low-latency trading infrastructure:** evaluate deterministic event preprocessing and routing components under controlled market-data replay and buyer-defined latency and correctness requirements.

The proposed commercial path is a limited technical evaluation, followed by a scoped proof of concept if the results justify it, and then a field-limited commercial license. This proposal does not claim that energy savings, HFT suitability, profitability, or superiority over competing systems have already been independently established.

## 1. What is being offered

Subject to a technical and legal review, the evaluation package may include:

- A pinned ARIES Tier 0 source revision or agreed executable build.
- API and deployment documentation.
- Deterministic task-handler and gateway components included in the agreed evaluation scope.
- Benchmark scripts and test protocols.
- A controlled evaluation configuration.
- Technical Q&A during the agreed evaluation period.

The exact modules, source access, model files, deployment rights, and documentation will be listed in an evaluation schedule before access is granted. Third-party model weights and dependencies are subject to their own license terms and are not represented as ARIES-owned intellectual property.

## 2. Evaluation track A — Data-center efficiency

### Evaluation question

Can ARIES complete the buyer's selected workload with less CPU time or measured energy per equivalent successful task than the buyer's current baseline?

### Proposed test

1. Select a representative, repeatable workload with defined expected outputs.
2. Pin the ARIES build, baseline build, model revision, dependencies, and configuration.
3. Run both systems on matched hardware with equivalent resource limits.
4. Warm up both systems and alternate or randomize test order.
5. Measure successful task count, exact-output rate, CPU time, CPU utilization, memory, throughput, and latency percentiles.
6. Where hardware telemetry is available, measure package/DRAM energy and calibrated wall power separately.
7. Report raw data, run-to-run variation, failures, and limitations.

### Acceptance metrics to agree with the buyer

- Exact successful tasks and error rate.
- CPU seconds per successful task.
- Requests or tasks per second.
- P50/P95/P99 latency.
- Joules per successful task, only where supported by valid energy telemetry.
- Whole-server watts and kWh, only where measured with calibrated instrumentation.

A reduction in CPU time is a useful compute-efficiency signal, but is not automatically an equivalent reduction in electricity consumption. No savings percentage is promised before the buyer-controlled test.

## 3. Evaluation track B — Low-latency trading infrastructure

### Evaluation question

Can the agreed ARIES components perform a defined preprocessing or routing function while meeting the buyer's correctness, throughput, and tail-latency requirements?

### Proposed test

1. Agree on the precise role of ARIES in the pipeline; do not assume it replaces exchange connectivity, a matching engine, risk controls, or a broker.
2. Use timestamped historical or synthetic market-event replay in a controlled environment.
3. Compare the buyer's baseline and ARIES-assisted path on matched hardware and configuration.
4. Measure feed-to-decision latency and, where available, decision-to-simulator-acknowledgement latency.
5. Report P50/P95/P99/P99.9 latency, throughput, queue depth, dropped or late events, CPU time, memory, and risk-control correctness.
6. Exercise overload, malformed input, restart, and failure-recovery cases.

A local microbenchmark is not exchange-grade HFT validation. No claim of trading profitability, exchange certification, or production readiness is made by this proposal.

## 4. Proposed commercial stages

### Stage 1 — Limited evaluation

- **Term:** [30–60] days, to be agreed.
- **Purpose:** technical inspection and agreed non-production testing.
- **Rights:** limited, non-transferable evaluation access for named personnel and agreed systems.
- **Restrictions:** no redistribution, sublicensing, public disclosure of confidential materials, or production deployment unless separately authorized.
- **Deliverable:** joint evaluation report containing agreed metrics, raw results, limitations, and a go/no-go recommendation.
- **Fee:** [to be negotiated].

### Stage 2 — Proof of concept

- **Term and scope:** defined in a separate statement of work.
- **Workload:** buyer-selected and jointly documented.
- **Acceptance:** thresholds, measurement procedure, test environment, and review period agreed before testing begins.
- **Deliverables:** configured proof of concept, test artifacts, integration notes, and final results.
- **Fee and payment milestones:** [to be negotiated].

### Stage 3 — Commercial license

If the proof of concept meets the agreed criteria, the parties may negotiate a commercial license covering:

- Named ARIES components and version.
- One defined field of use: data-center operations or trading infrastructure.
- Permitted deployment environments and capacity.
- Territory and term.
- License fee and payment schedule.
- Support, maintenance, and update rights.
- Security, confidentiality, audit, and incident obligations.
- Usage reporting, renewal, suspension, and termination.
- Any approved source-code access, sublicensing, or exclusivity.

The recommended starting point is a non-exclusive, field-of-use-limited license. Broader exclusivity, perpetual rights, sublicensing, source ownership, or assignment would require separate express negotiation and consideration.

## 5. Intellectual-property principles

The intended commercial structure is a license to defined ARIES materials, not an automatic sale or transfer of the underlying platform.

The definitive agreement should distinguish:

- **Background IP:** pre-existing ARIES software, architecture, methods, documentation, and know-how, subject to confirmation of ownership and third-party rights.
- **Licensed materials:** only the specific components and versions listed in the agreement.
- **Buyer materials:** buyer data, systems, credentials, and confidential information remain the buyer's property.
- **Custom development:** ownership and license rights for bespoke work must be expressly agreed in writing.
- **Feedback and improvements:** treatment must be specified before work begins.
- **Third-party materials:** model weights, libraries, datasets, and other dependencies remain subject to their own terms.

No representation is made that every repository component or model asset is exclusively owned by ARIES. A commercial rights and chain-of-title review is a pre-signing requirement. Both parties should have qualified counsel review the final agreement.

## 6. Evidence currently available and boundaries

ARIES has repository-based test and benchmark infrastructure, including API diagnostics, functional tests, alternative-endpoint comparison tooling, and native HTTP benchmark workflows.

A recent GitHub-hosted native HTTP test completed 1,000 requests at each of four concurrency settings (1, 4, 8, and 16) with no HTTP failures in that run. The observed peak throughput was at concurrency 4; throughput declined at higher concurrency. This was a loopback test on a hosted runner using a compact local model. It is not a controlled competitor comparison, exchange-network HFT result, or energy measurement.

The repository also contains an energy-measurement harness designed to use same-host hardware energy counters when available. A trustworthy physical energy result has not yet been established. Whole-server electricity claims require calibrated wall-power measurement.

Independent third-party validation remains pending. All buyer-facing performance claims should be limited to the exact version, hardware, workload, and conditions documented in the relevant raw report.

## 7. Information requested from a prospective evaluator

To prepare a meaningful evaluation, the prospective partner would identify:

- The intended track: data-center efficiency, trading infrastructure, or both.
- The workload and current baseline system.
- Available test hardware and operating environment.
- Required latency, throughput, correctness, and energy metrics.
- Security, deployment, and source-access requirements.
- Evaluation decision-makers and expected procurement process.

No confidential customer information is required for an initial discussion.

## 8. Proposed next step

A 30–45 minute technical scoping discussion to select one evaluation track, define a measurable workload, and determine whether a limited evaluation agreement is appropriate.

**Contact:** [Licensor legal entity / authorized representative]  
**Email:** [Business contact email]  
**Date:** [Proposal date]

---

*This document is a non-binding commercial discussion draft, not an offer capable of acceptance and not legal advice. No license is granted until a definitive written agreement is signed by authorized representatives. Fees, rights, obligations, acceptance criteria, and delivery dates remain subject to negotiation.*
