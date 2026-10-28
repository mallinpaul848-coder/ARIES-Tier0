# MALLIN Platform — Release and Independent Review Checklist

## Current release scope
This repository contains the ARIES AI / MALLIN Platform application, API, native and PRISE-related modules, benchmarks, and deployment helpers. The chat page includes an optional, browser-synthesized ambient instrumental pad. Audio starts only after the visitor presses Play, has a volume control and Pause button, and should reduce while speech synthesis is speaking. This is an original synthesized tone bed, not a recorded music track.

## Review status
This checklist is a preparation artifact, not an independent certification. No reviewer is represented as having accepted, completed, or endorsed an evaluation unless their own published report or written response is linked here.

| Review area | Reproducible evidence to collect | Status |
|---|---|---|
| Source integrity | Commit SHA, clean checkout, dependency lock/config, source manifest | Pending release capture |
| Automated regression | Exact Python version, `python -m pytest -q`, complete logs | Run on clean runner before release |
| API correctness | Health/readiness, model discovery, valid and invalid chat requests, non-empty answers | Must be verified against current deployment |
| UI and browser | Desktop/mobile; keyboard accessibility; API failure path; voice input/output; ambient play/pause/volume; music ducking | Browser QA not yet recorded |
| Performance | Raw JSON, commit SHA, host/runner, request count, concurrency, warm/cold conditions, errors, p50/p95/p99 | Use existing performance workflow; attach raw artifacts |
| Model provenance | Actual model ID, weights/config/tokenizer hashes, license, inference backend and hardware | Verify actual runtime; do not infer from UI labels |
| Security | Secret scan, dependency audit, auth/authorization review, CORS, rate limits, input-size limits, data retention | Independent security review pending |
| Licensing | Confirm rights to any external video/background assets and model weights for commercial distribution | Owner must verify stock-video license |
| External evaluation | Written scope, version/commit evaluated, methodology, results, limitations, reviewer identity/publication | Pending independent reviewers |

## Suggested clean-checkout procedure

1. Record the exact commit SHA and repository state.
2. Use a clean machine or CI runner and document OS, Python version, CPU/GPU, RAM, and network conditions.
3. Install only the dependencies declared by the repository instructions.
4. Run the existing test suite and preserve complete logs, including failures.
5. Run the public API performance workflow and retain the JSON report and GitHub Actions run URL. Report failed requests and timeouts; never drop them silently.
6. Separately measure native-kernel microbenchmarks and end-to-end model/API latency. Do not present kernel timings as generative-model latency.
7. Test the chat UI on desktop and mobile. Confirm audio is silent before Play, controls work, the background sound reduces during spoken replies, and the page remains usable if Web Audio or speech APIs are unavailable.
8. Have an independent reviewer reproduce the procedure from the recorded commit and publish their own findings.

## Release gates

- Do not call the app production-ready until clean-checkout tests, API end-to-end checks, deployment smoke tests, licensing review, and security checks are recorded.
- Do not describe a project-owned diagnostic as an official benchmark, certification, or third-party result.
- Do not claim that all reviews are complete or that reviewers have been prevented from reviewing the software. Independent review remains the reviewer's decision.
- Keep API keys, credentials, customer data, and proprietary material out of public reports.
- Keep paid reasoning disabled until authentication, server-side entitlement checks, billing, quotas, and a supported reasoning backend are implemented and tested.

## Reviewer handoff packet

Provide reviewers with:
- Repository URL and exact commit SHA
- Scope and explicit exclusions
- Environment and setup instructions
- Commands and complete raw output
- Benchmark JSON and workflow URL
- Model and dependency provenance
- Known limitations and unresolved failures
- Instructions for reporting discrepancies

Reviewer findings should be recorded with date, reviewer/organization (if they consent to attribution), tested commit, methodology, result, and a link to the original report.
