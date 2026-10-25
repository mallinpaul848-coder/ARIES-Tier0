# ARIES / MALLIN NIST AI RMF Readiness Assessment

## Status and scope

**Status: self-assessment scaffold; not NIST-validated, certified, endorsed, or approved.**

This document maps evidence ARIES should collect against the NIST AI Risk Management Framework (AI RMF) 1.0 and the NIST AI 600-1 Generative AI Profile. NIST describes these as voluntary risk-management resources. Using them or running this checklist does not mean NIST has tested or approved ARIES.

References:
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Generative AI Profile (AI 600-1): https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- NIST AI Resource Center: https://airc.nist.gov/

## Evidence checklist

Mark each item only when a durable artifact exists and has been reviewed. A checked box is a project assertion, not a NIST finding.

### GOVERN — ownership and accountability
- [ ] Named system owner, intended users, intended use, prohibited use, and escalation contact.
- [ ] Documented review and release process; versioned change log and risk acceptance.
- [ ] Software bill of materials (SBOM), dependency/license inventory, and vulnerability handling policy.
- [ ] Data governance: dataset sources, license/consent, retention, privacy, deletion, and access controls.
- [ ] Human oversight and incident response procedures.

### MAP — context and risk identification
- [ ] System card describing architecture, model artifacts, API/proxy distinction, dependencies, and deployment.
- [ ] Intended-use analysis and foreseeable misuse scenarios.
- [ ] Risk register covering hallucination, harmful content, privacy leakage, bias, prompt injection, insecure output/tool use, availability, and model/data supply chain.
- [ ] Stakeholder and impact analysis for the actual deployment context.

### MEASURE — tests and metrics
- [ ] Reproducible, version-pinned capability evaluation on held-out data, including scoring rules and all attempted cases.
- [ ] Safety and adversarial evaluation: prompt injection, jailbreaks, harmful requests, sensitive-data leakage, and robustness.
- [ ] Fairness/bias and accessibility evaluation appropriate to the intended use.
- [ ] Security tests, dependency scanning, secret scanning, and API authentication/rate-limit checks.
- [ ] Production load report with environment, request mix, concurrency, latency percentiles, failures, throughput, and raw results.
- [ ] Model artifact hashes, dataset hashes/provenance, tokenizer/config, hardware, seeds, and exact revision recorded.
- [ ] Known limitations and confidence/uncertainty documented; test set leakage assessed.

### MANAGE — mitigations and monitoring
- [ ] Risk owners and mitigation decisions recorded with dates.
- [ ] Monitoring for errors, abuse, drift, latency, outages, and privacy/security incidents.
- [ ] Rollback, model-disable, data-incident, and user-reporting procedures tested.
- [ ] Periodic reassessment schedule and release gates defined.

## Current known evidence and gaps

- Repository contains a small experimental GPT-2-style causal LM package under `published/aries-core-v1`; its README reports 5,273,088 parameters and 100,000 training steps. These are repository-declared facts, not independent verification.
- A project-operated production endpoint load test exists at `.github/workflows/aries-production-load.yml`. Run it against an authorized endpoint and archive the JSON output before asserting current production performance.
- A public model packaging smoke-test workflow exists at `.github/workflows/aries-huggingface-verification.yml`. It tests download/load/generation only and is not a quality benchmark.
- A held-out language-model evaluator exists at `training/aries_quality_eval.py`; a real checkpoint, licensed held-out corpus, and completed artifact are required.
- No evidence in this checklist establishes NIST review, NIST certification, NIST endorsement, third-party certification, or leaderboard acceptance.

## Independent review packet

Before requesting external review, assemble:
1. Exact model and code commit SHAs.
2. Model card/system card, license, data provenance, and SBOM.
3. Raw benchmark reports and complete test definitions.
4. Risk register, mitigations, unresolved risks, and incident procedures.
5. Reproduction instructions and environment details.
6. Reviewer identity/organization, independence statement, methods, limitations, and signed/published findings.

## Completion rule

Do not describe ARIES as “NIST validated,” “NIST certified,” “NIST approved,” or “NIST endorsed” unless an applicable official program explicitly performs that evaluation and provides documentary evidence supporting the exact claim. A completed internal mapping should be described as “assessed against selected NIST AI RMF guidance,” with scope, gaps, and date stated.
