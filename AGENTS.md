# ARIES AI — Architecture Preservation Rules

These rules apply to coding assistants and automated agents working in this repository.

## Hard boundaries
- Do not refactor, overwrite, rename, or delete core ARIES files without explicit authorization from the repository owner.
- Preserve the existing inference architecture, routing, deterministic parameters, API contracts, and RTL design.
- Do not replace native/local inference with a third-party API, or replace an API backend with local inference, unless explicitly authorized.
- Do not change unrelated files to fix a build or test failure.
- Do not add duplicate launchers, duplicate project structures, or extra server layers as a workaround without authorization.
- Never place API keys, tokens, or other secrets in source code, logs, test fixtures, or commits. Use environment variables or repository secrets.

## Required workflow before edits
1. Inspect the current implementation and the failing test/log first.
2. Identify the exact file(s) implicated and the smallest proposed change.
3. Preserve existing public routes and behavior unless the requested fix explicitly requires a change.
4. If the fix would require a broad refactor, architecture change, secret, or destructive operation, stop and request authorization.

## Required verification after authorized edits
- Run the narrow relevant test(s), then applicable regression tests.
- Report commands run and actual pass/fail results; do not imply tests were run when they were not.
- Report measured latency and benchmark results only from actual runs, with the environment and methodology.
- Never claim model training, trillion-token training, third-party validation, leaderboard submission, or successful inference without verifiable evidence.
- If tests fail, report the failure and diagnose it rather than hiding or weakening the test.

## Scope and capability honesty
The native character n-gram baseline is a small software baseline, not a modern large language model. Do not describe it as a trillion-token-trained model or claim general LLM-level intelligence. Deterministic fast-path and microbenchmark timings are not evidence of generative model inference latency or sub-nanosecond AI inference.

## Priority
Preserve the owner's architecture and existing functionality. Make only the smallest authorized, reversible change needed to solve the reported problem.
