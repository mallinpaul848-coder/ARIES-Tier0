# ARIES Tier 0 — Licensing Readiness Checklist

This is a technical and commercial preparation checklist, not legal advice or a claim that the product is already cleared for licensing.

## Release identity and reproducibility
- [ ] Select and tag a release commit; record SHA, date, build environment, and supported platforms.
- [ ] Demonstrate a clean install on a machine not used for development.
- [ ] Run health, readiness, API, deterministic-correctness, model-output, failure-handling, and load tests.
- [ ] Preserve raw test outputs and the exact commands/configuration needed to reproduce them.
- [ ] Document known limitations, deployment requirements, upgrade/rollback, monitoring, and backup procedures.

## Ownership and legal review
- [ ] Create a software bill of materials (SBOM) and dependency inventory.
- [ ] Audit licenses for source dependencies, model weights, tokenizers, datasets, and bundled assets.
- [ ] Confirm that each component may be used commercially and sublicensed under the proposed deal.
- [ ] Identify any third-party API, hosting, or runtime dependencies and whether they can be replaced.
- [ ] Document authorship, assignment/contractor records, prior contributions, and any open-source obligations.
- [ ] Obtain qualified legal review of IP ownership, confidentiality, export/privacy/security obligations, and proposed license terms.

## Buyer diligence room
- [ ] Product overview and architecture diagram.
- [ ] Reproducible deployment guide and buyer-run acceptance-test procedure.
- [ ] Versioned benchmark reports with raw data, test conditions, failures, and limitations.
- [ ] Security review, vulnerability handling policy, dependency inventory/SBOM, and incident process.
- [ ] Support/maintenance plan, service levels if offered, roadmap, and known-issues register.
- [ ] Proposed deal scope: source-code license, object-code license, private deployment, support, exclusivity, field-of-use limits, or IP assignment.
- [ ] Pricing and acceptance criteria tied to measurable deliverables rather than unverified performance claims.

## Evidence discipline
- Do not describe the product as third-party validated until an independent report is complete and linked.
- Do not promise benchmark superiority or uptime without evidence for the exact release and conditions.
- Do not include credentials, private keys, customer data, or confidential source in the data room.
- Have counsel review the final agreement and the chain of title before signing.

## Current status
The repository contains a buyer brief, due-diligence checklist, and evaluation harness. This checklist remains open until each item is supported by a concrete artifact or documented decision.
