# ARIES / MALLIN AI — Permanent Engineering Rules

Claude Code is a permanent engineering assistant for this repository. Apply these rules to every change and every layer; do not treat Claude-assisted development as a one-off feature or replace ARIES with a different product.

## Architecture-wide coverage

Review and preserve interfaces across the UI, HTTP/API routes, OpenAI-compatible request/response handling, inference adapters, local runtime, upstream provider, bounded tool calling, deterministic reasoning, PRISE, MALLIN mathematics, digital-root and 3/6/9 operations, Phase-8, vortex/Helixo modules, packaging, launchers, diagnostics, security, benchmark tooling, and CI.

## Required change process

1. Trace the full call path and identify callers, data contracts, configuration, tests, and performance-sensitive sections before editing.
2. Establish a reproducible baseline before optimizing. Record hardware/runtime/model/revision, test commands, correctness, latency percentiles, throughput, and resource limits where measurable.
3. Make the smallest coherent change that improves a measured quality, correctness, safety, maintainability, or performance metric.
4. Run relevant unit/integration tests, compile checks, and benchmark comparisons. Preserve raw machine-readable results and test failures.
5. Compare before/after results using the same workload and environment. Do not claim a performance gain unless measurements demonstrate it; never substitute targets or estimates for measurements.
6. Update documentation and deployment configuration when behavior or required settings change.

## Preserve ARIES and MALLIN

- Keep existing PRISE, deterministic math, MALLIN research modules, APIs, and user-facing application capabilities intact unless a tested migration explicitly replaces them.
- Treat 3/6/9, digital roots, Phase-8, vortex, and Helixo as deterministic features or research heuristics where appropriate, not as proof of unsupported scientific claims.
- Do not claim P vs NP or Millennium Prize problems are solved without a rigorous, independently checkable proof.
- Do not silently route deterministic requests to a generative model when the native engine can return an exact verified answer.
- Do not publish a small fallback model as if it were a stronger ARIES model. Clearly identify the actual model, weights, tokenizer, revision, and evaluation results.

## Tool calling and security

- Model tool calls are untrusted requests. Keep tools server-defined, allow-listed, schema-validated, bounded by a small round limit, and covered by adversarial tests.
- Never execute model-generated shell commands, arbitrary Python, SQL, or arbitrary URLs.
- Do not trust client-supplied tool definitions or permissions. Bound request sizes, timeouts, response sizes, and retained conversation history.
- Never log or commit API keys, tokens, private prompts, or other secrets.

## Leaderboard and performance integrity

- Use pinned immutable model revisions and named standard evaluation tasks. Save raw outputs, samples, metadata, and aggregate scores as artifacts.
- Validate that a submission repository contains the actual model weights and tokenizer before launching expensive evaluations.
- Distinguish official benchmark results from ARIES-authored smoke tests. Report exact task set, revision, hardware, software versions, precision, limits, and failed tasks.
- Do not game benchmarks, leak evaluation answers into training, or present API-proxy results as weights for a model ARIES owns.
- Optimize toward the best reproducible score across accuracy, reasoning, instruction following, robustness, and latency; keep a correctness gate so speed optimizations cannot silently reduce quality.

## Completion standard

A change is complete only when its tests and relevant checks have been run, results are reported accurately, and links point to the actual committed files or workflow artifacts. If a test cannot run in the available environment, say exactly which one and leave a runnable command or CI job.