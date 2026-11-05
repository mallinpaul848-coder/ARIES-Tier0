# ARIES Tier 0 — Licensing Execution Plan

**Status:** Commercial preparation plan; not a representation that ARIES is independently validated or legally cleared for licensing.

## 1. Commercial objective

Prepare ARIES Tier 0 for paid evaluation and field-limited commercial licensing while preserving the owner's underlying intellectual property unless a separately negotiated assignment is intentionally chosen.

Target two distinct markets:

1. **Data-center software efficiency:** deterministic task routing, cache/fast-path handling, request orchestration, and measurable reduction in CPU time or joules per equivalent successful task.
2. **Low-latency trading infrastructure:** deterministic preprocessing, event classification/routing, and gateway components evaluated on controlled market-data replay and production-like order-path tests.

These are target use cases, not claims of proven savings, production HFT readiness, or customer adoption.

## 2. Recommended deal structure

Use a staged commercial path:

- **Stage A — Evaluation agreement:** short, paid or mutually agreed limited evaluation; named users; defined test environment; no production use; no redistribution; confidentiality; return/destruction of confidential materials; evaluation end date.
- **Stage B — Proof-of-concept statement of work:** fixed scope, buyer-selected workloads, baseline/candidate comparison, success criteria, test ownership, deliverables, fees, and acceptance window.
- **Stage C — Commercial field-of-use license:** define the exact software version and components; permitted field (data-center operations or trading infrastructure); territory; term; deployment limits; support; maintenance; security obligations; audit/reporting; fees; and termination.
- **Stage D — Optional expansion:** additional business units, deployment capacity, fields of use, source access, exclusivity, or sublicensing only by written amendment and additional consideration.

Prefer a **non-exclusive, field-of-use-limited license** as the starting position. Do not grant broad exclusivity, perpetual rights, source ownership, assignment, or sublicensing by default.

## 3. IP-preservation principles for counsel to implement

The agreement should clearly distinguish:

- **Background IP:** pre-existing ARIES code, architecture, methods, documentation, and know-how owned by the licensor.
- **Licensed materials:** only the identified release, modules, interfaces, and documentation expressly listed in the agreement.
- **Customer materials:** buyer data, prompts, configurations, credentials, and systems remain the buyer's property.
- **Feedback and improvements:** define ownership and permitted use before work begins; avoid accidental assignment of the underlying platform.
- **Custom work:** specify whether custom deliverables are licensed, assigned, or jointly developed. No ownership transfer by implication.
- **Third-party components:** list licenses and model/data restrictions; do not promise rights the licensor does not hold.

Have qualified IP counsel verify chain of title, contributor assignments, dependency/model licenses, open-source obligations, confidentiality, liability, export/privacy/security requirements, and enforceability before signing.

## 4. Evidence gates before making commercial claims

### Data-center efficiency

Required buyer-facing metrics:

- Equivalent successful tasks and exact-output rate.
- CPU time and CPU utilization per successful task.
- Gross and idle-adjusted energy per successful task where trustworthy hardware counters exist.
- Calibrated wall-power/PDU measurements for whole-server electricity claims.
- Matched hardware, model, configuration, request mix, warmup, concurrency, and repeated randomized A/B trials.
- Confidence intervals, variance, failures, and raw machine-readable reports.

Do not translate CPU-time reduction into a percentage of electricity savings without direct energy measurements.

### Low-latency trading

Required buyer-facing metrics:

- Timestamped replay of representative market data.
- End-to-end feed-to-decision and decision-to-acknowledgement latency, including P50/P95/P99/P99.9.
- Throughput, queue depth, dropped/late events, CPU utilization, memory, and process CPU time.
- Deterministic action parity and risk-control correctness.
- Matched baseline, hardware, compiler/build, network topology, and exchange simulator or approved test venue.
- Failure/recovery, overload, and tail-latency tests.

A local synthetic event microbenchmark is an engineering diagnostic, not proof of exchange-grade HFT performance or profitability.

## 5. Buyer package contents

Maintain a versioned diligence folder containing:

1. One-page buyer brief with narrowly worded, evidence-backed claims.
2. Product architecture and data-flow diagram.
3. Pinned release commit, build instructions, deployment guide, and clean-machine acceptance test.
4. API specification and operational runbook.
5. Test matrix, raw JSON benchmark reports, logs, scripts, and environment metadata.
6. Separate data-center and trading evaluation protocols.
7. SBOM/dependency inventory and model-weight/data license review.
8. Security overview, vulnerability disclosure contact/process, and known-issues register.
9. Support, maintenance, update, and service-level proposal.
10. Draft evaluation agreement, proof-of-concept SOW, and commercial license for legal review.

Never place credentials, private keys, customer data, or confidential source code in a public buyer pack.

## 6. Commercial offer design

Offer a clear progression rather than an unsupported headline valuation:

- Paid technical evaluation.
- Fixed-scope proof of concept.
- Annual or multi-year non-exclusive field-of-use license.
- Optional deployment/support/maintenance fees.
- Optional expanded capacity, additional fields, source escrow, or exclusivity priced and negotiated separately.

Tie acceptance and any performance-based payment to metrics, workloads, and test procedures written into the SOW. Do not promise a savings percentage or latency advantage before the corresponding test has passed.

## 7. Immediate execution checklist

- [ ] Freeze and identify the release candidate by commit SHA.
- [ ] Verify clean installation and reproduce all buyer-demo commands.
- [ ] Complete SBOM and model/dependency commercial-rights review.
- [ ] Confirm authorship, assignments, and ownership chain.
- [ ] Separate and label data-center, trading, and general-chat evidence.
- [ ] Preserve raw benchmark artifacts and publish reproducibility instructions.
- [ ] Prepare a sanitized buyer demo and data room.
- [ ] Obtain IP counsel review of the evaluation agreement, SOW, and license.
- [ ] Approach prospects with a limited evaluation proposal, not unsupported savings claims.

## 8. Current evidence boundaries

The GitHub-hosted native HTTP benchmark is a loopback diagnostic on a hosted runner. It is not an exchange-network HFT test or an energy measurement. The paired energy harness requires trustworthy same-host RAPL counters and equal exact successful work; whole-server claims additionally require calibrated wall-power measurement. Independent third-party validation remains pending until an external evaluator completes and documents the work.

**Recommended positioning:** “ARIES Tier 0 is an independently testable, self-hostable software platform available for controlled technical evaluation and discussion of field-limited commercial licensing. Performance and energy outcomes are workload- and environment-dependent and will be established through buyer-controlled acceptance testing.”
