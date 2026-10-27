# ARIES Tier 0 — Third-Party Validation Status

**Status: PREPARED FOR INDEPENDENT EVALUATION — NOT YET THIRD-PARTY VALIDATED**

Last reviewed: 2026-10-27

## What is verified by the repository
- The repository contains an automated GitHub Actions workflow for project-authored unit tests and finite-instance research diagnostic smoke tests.
- The repository contains a model-agnostic OpenAI-compatible API comparison harness and a manually triggered workflow to collect a JSON report.
- The repository contains a documented evaluation protocol and buyer due-diligence checklist.

These are developer-provided test infrastructure. They do not constitute independent verification, certification, or an official benchmark result. Do not advertise them as such.

## Evidence still required for an independent validation claim
1. A successful, current CI run tied to the exact release commit, with logs and retained artifacts.
2. A frozen release candidate identified by Git commit SHA, model ID/revision, dependency lockfile, and build instructions.
3. A comparison run with an independently selected candidate system, identical prompt set/settings, timestamped raw JSON, and documented hardware/network conditions.
4. Review by an evaluator not responsible for building ARIES, including the evaluator's identity/organization, methodology, conflicts disclosure, signed report or public report URL, and date.
5. Separate tests for API reliability, model answer quality, latency/throughput, security/dependencies, license compliance, and installation/reproducibility.
6. Any public claim limited to the exact tested version, conditions, and metrics.

## External evaluation pathway
- **NIST:** use the NIST AI Risk Management Framework and TEVV resources as assessment guidance. This repository does not have NIST certification or endorsement.
- **Hugging Face:** publish an actual model artifact and model card only if distribution rights and artifacts are ready; use a reproducible evaluation and publish the exact model revision and results. A Hugging Face repository or leaderboard submission alone is not a certification.
- **Independent evaluator:** invite a university lab, qualified testing firm, or buyer engineering team to run the frozen release in a clean environment and publish or sign the results.

## Claims that are not supported by this evidence
Do not claim third-party validation, official leaderboard placement, superiority to GPT/Gemini/Claude/Grok, production-scale reliability, a proven sub-nanosecond end-to-end AI response, or solutions to P vs NP, Navier–Stokes global regularity, or the Yang–Mills mass gap unless separate evidence directly supports the exact claim.

## Release gate
A release is eligible to be labeled **independently evaluated** only after items 1–4 above are completed and the external report is linked here. Until then, use: **“ARIES Tier 0 — reproducible evaluation package prepared; independent validation pending.”**
