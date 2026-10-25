# ARIES Independent Validation Request Packet

## Purpose
Request an independent technical evaluation of the ARIES / MALLIN AI Tier Zero system. This document is a request template, not a claim that an evaluator has accepted the work or that any certification has been obtained.

## System under review
- Product/system name: ARIES AI / MALLIN AI Tier Zero
- Repository: https://github.com/mallinpaul848-coder/ARIES-Tier0
- Code revision under review: record the exact immutable commit SHA before testing
- Model artifact and revision: record the exact model file hashes and immutable revision
- Deployment tested: record whether local native inference, a hosted API, or both
- Evaluator and organization: to be completed by the independent evaluator
- Evaluation date and environment: to be completed by the evaluator

## Requested evaluation scope
Please state which tests are included and excluded, and independently reproduce results where practical.

1. **Artifact integrity and reproducibility**
   - Verify model/config/tokenizer files, hashes, licenses, dataset provenance, dependencies, and software bill of materials.
   - Distinguish the model's own inference from any upstream API or external service.
2. **Capability and answer quality**
   - Use a documented, held-out test set covering arithmetic, reasoning, instruction following, factual questions, coding (if claimed), and generalization.
   - Publish prompts, scoring rules, sample sizes, failures, uncertainty, and any contamination checks.
3. **Latency and throughput**
   - Record hardware, software versions, warm-up, request mix, concurrency, timeouts, errors, token counts, and raw measurements.
   - Report time-to-first-token and generation throughput when applicable, plus P50/P95/P99 latency and successful requests per second.
4. **Robustness, safety, and security**
   - Evaluate prompt injection, unsafe outputs, privacy leakage, refusal behavior, malformed inputs, rate limits, dependency vulnerabilities, and failure recovery.
5. **NIST AI RMF mapping**
   - Review evidence against GOVERN, MAP, MEASURE, and MANAGE outcomes in the NIST AI RMF and, where relevant, the Generative AI Profile.
   - Identify evidence, gaps, risk owners, and recommended mitigations. Do not describe this mapping as NIST approval or certification.

## Required report
Please provide:
- Evaluator identity, independence statement, conflicts of interest, and funding/compensation disclosures.
- Exact revisions, hashes, hardware, environment, methods, test sets, and scoring code.
- Results including negative results and failed tests, limitations, reproducibility instructions, and raw data where licensing/privacy permits.
- Findings categorized by severity, with remediation recommendations and retest results.
- Explicit statement of whether the report is an independent assessment, formal certification, or neither.

## Evidence checklist for the project owner
- [ ] Freeze and hash the exact code/model revision.
- [ ] Verify rights and licenses for all training and evaluation data.
- [ ] Prepare model/system card, SBOM, risk register, privacy/security controls, and incident/rollback procedures.
- [ ] Run and archive the production load report.
- [ ] Run held-out quality evaluation on a licensed corpus not used for training.
- [ ] Publish exact limitations and all relevant failed or incomplete tests.
- [ ] Select an evaluator with relevant competence and genuine independence.
- [ ] Obtain written scope, price, timeline, and deliverables before authorizing paid work.

## Important limitation
Repository checks, project-run benchmarks, a public model download/load smoke test, and a NIST AI RMF self-assessment are not by themselves independent third-party validation. The NIST AI RMF is a voluntary risk-management framework; this packet does not imply that NIST has reviewed, tested, certified, endorsed, or approved ARIES.
