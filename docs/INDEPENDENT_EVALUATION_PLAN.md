# ARIES AI / MALLIN Platform — Independent Evaluation Protocol

Status date: 2026-10-28

## Current evidence (do not overstate)
- GitHub Actions reported successful runs for API tests, RTL external smoke test, and end-to-end API integration test on commit `6476ad0eadf11594a24e3ed1eba3ec36fb9f922e`.
- GitHub Pages deployment failed during the Configure Pages step; no Pages artifact was uploaded.
- The primary repository is private. Do not make it public as a shortcut; proprietary PRISE implementation should remain private.
- The Hugging Face evaluation repository exists at https://huggingface.co/paulmallin777/aries-core-v1-evaluation, but the repository inspection found no model weights, config, tokenizer, or model card. Therefore a standard independent model benchmark cannot yet be run against it.
- These CI results are software integration checks, not independent model-performance validation or certification.

## Release prerequisites
1. Select the exact model checkpoint intended for evaluation and record its immutable revision and SHA-256 checksums.
2. Prepare a separate evaluation artifact that contains only what the evaluator needs: model weights, config, tokenizer files, inference entry point, license/terms, model card, intended-use limits, and reproducible run instructions. Do not include private PRISE source, credentials, secrets, or unrelated repository files.
3. If model weights are proprietary, provide them to a named evaluator through a controlled access/NDA process instead of publishing them publicly. Confirm redistribution and dataset rights first.
4. Provide a clean environment specification with pinned package versions and the exact inference command.
5. Record the host hardware, OS, accelerator/runtime, precision/quantization, batch size, context length, warmup, concurrency, and measurement methodology.

## Minimum reproducible test suite
- Functional smoke tests: health/readiness, model listing, non-empty chat response, multi-turn conversation, invalid request handling, and timeout/error handling.
- Latency: at least 100 warm requests per configuration where feasible; report sample count, median/P50, P90, P95, P99, min/max, and measurement conditions. Separate cold start from warm latency and report time-to-first-token separately if streaming is supported.
- Throughput: report successful requests/second and tokens/second at stated concurrency; include error rate and timeout rate.
- Quality: use a named, versioned, licensed benchmark with a documented prompt template, scoring method, and raw per-example outputs. Do not compare against other models unless tested with the same benchmark version and comparable settings.
- Integrity: record model revision, dataset revision, runner commit, dependency lockfile, run timestamp, and SHA-256 checksums of artifacts and raw results.
- Re-run the same command in a clean environment and retain logs and machine-readable JSON/CSV outputs.

## Reporting rules
- Label internal CI as internal software testing.
- Label owner-run benchmarks as self-reported measurements.
- Label independent results only after an unaffiliated evaluator has reproduced the procedure and issued a report.
- Do not claim a leaderboard rank until an official leaderboard accepts and publishes the submission.
- Do not claim NIST certification: NIST AI RMF is a risk-management framework, not an AI model performance certificate.
- Publish limitations, missing tests, hardware details, confidence/variance where relevant, and failures as well as successes.

## Deployment acceptance
- A public hosted URL must be checked from a clean browser/client.
- Verify the chat endpoint returns a meaningful, non-empty model-generated answer; HTTP 200 on `/health` alone is not proof the model works.
- Verify the deployment does not depend on the owner's computer or home internet.
- Do not describe a site as permanently available without an uptime/hosting commitment.

## External reviewer request — send only after prerequisites are met
Ask the evaluator to:
1. Confirm the artifact identity and checksums.
2. Run the published protocol on their own infrastructure.
3. Return the exact environment, commands, raw outputs, aggregate metrics, failures, and a signed or attributable report.
4. State explicitly what was and was not independently verified.

No reviewer request has been sent by this document, and no independent certification is implied.
