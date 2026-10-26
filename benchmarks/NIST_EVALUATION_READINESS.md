# ARIES NIST Evaluation and Trustworthiness Readiness

## Current status — not NIST validated

As of this repository review, there is no verified NIST-issued result, score, participation record, or certification for ARIES. This document is a readiness plan, not an endorsement, submission, or claim of compliance.

NIST's AI Risk Management Framework is a voluntary risk-management framework, not a product certification by itself. NIST evaluation programs require program-specific registration, eligible system submissions, and scoring runs. Participation and results must be verified on the official platform.

## Evidence currently available in this repository

- Project-authored API smoke tests and latency reports.
- Automated API and integration checks described in the repository's benchmark documentation.
- An experimental approximately 5.27-million-parameter GPT-2-style checkpoint and a workflow for local load/generation testing.
- A capped 25-example HellaSwag run is configured in CI; this is not a full benchmark and a workflow definition is not proof that a run passed.
- A separate public inference API has been reported as using a native character n-gram backend. Its results must not be attributed to the experimental Transformer checkpoint.

## Required work before any external submission

1. **Freeze the system under test.** Record model revision, source commit, inference code, dependencies, tokenizer, generation parameters, hardware, and a checksum manifest.
2. **Document provenance and rights.** Record training-data sources, filtering, licenses, exclusions, model-weight license, and third-party components. Do not submit until rights are reviewed.
3. **Publish an accurate system card.** Describe intended use, limitations, known failure modes, safeguards, data provenance, and evaluation methods.
4. **Build a repeatable evaluation package.** Include held-out task suites, exact dataset versions, pre-registered metrics, raw outputs, confidence intervals where applicable, and independent replication instructions.
5. **Test safety and robustness.** Include prompt injection, misuse, privacy leakage, hallucination, bias/fairness where applicable, resilience, and fail-safe behavior; document residual risks and mitigations.
6. **Separate performance from trustworthiness.** Report latency, throughput, reliability, and resource use separately from quality, safety, privacy, and fairness.
7. **Select an applicable NIST program and track.** Check the official NIST AI Challenges portal for currently open evaluations and track-specific rules. Create an account/team, accept required agreements, register the system, submit the required artifact or endpoint, and await the official scoring run.
8. **Archive official evidence.** Preserve the submission ID, track, timestamps, immutable system revision, official result page/report, and any restrictions on public disclosure.

## Official references

- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI Resource Center: https://airc.nist.gov/
- NIST AI Challenges portal: https://ai-challenges.nist.gov/
- NIST evaluation platform submission guidance: https://ai-challenges.nist.gov/help/submissions
- NIST GenAI overview: https://ai-challenges.nist.gov/genai_overview.html

## Claim policy

Until an official result is published, use only this wording: **“ARIES has project-run engineering tests; NIST evaluation has not been verified or completed.”** Do not use “NIST certified,” “NIST validated,” or “NIST approved.”
