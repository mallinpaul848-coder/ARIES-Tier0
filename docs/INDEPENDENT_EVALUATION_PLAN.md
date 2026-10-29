# ARIES AI / MALLIN Platform — Independent Evaluation Protocol

Status date: 2026-10-28

## Current evidence (do not overstate)
- GitHub Actions reported successful API tests, RTL external smoke test, and end-to-end API integration test on commit `3008f9e0680eeb8feefb7f1a2a00c1e52cdea630`.
- The next GitHub Pages workflow was changed to skip deployment when this repository is private, avoiding a known configuration failure. The latest run completed as **skipped**, not as a deployment. The current public web deployment is on Vercel: https://aries-ai-mallin-chat.vercel.app
- The primary GitHub repository is private. Keep proprietary PRISE implementation private.
- The private repository contains a model checkpoint at `published/aries-core-v1/model.safetensors` (about 21 MB), plus a config, tokenizer, tokenizer config, README, and training evidence. This is a real artifact to inspect, but it is a small experimental GPT-2-style model and should not be represented as a validated frontier model.
- The Hugging Face evaluation repository https://huggingface.co/paulmallin777/aries-core-v1-evaluation currently contains only `.gitattributes`; the model artifact has not been published there.
- The model card says the base training corpus license/provenance still needs verification. Do not publicly redistribute the weights until data rights and the intended license are confirmed.
- CI results are software integration checks, not independent model-performance validation or certification. The live chat backend has not yet been independently confirmed to generate meaningful answers in this audit.

## Release prerequisites
1. Confirm the checkpoint is the exact model intended for evaluation and record its immutable revision and SHA-256 checksums.
2. Verify the provenance and redistribution rights of every training-data source and confirm the model license. Do not publish weights while this is unresolved.
3. Prepare a separate evaluation artifact containing only what the evaluator needs: weights, config, tokenizer files, inference entry point, license/terms, model card, intended-use limits, and reproducible instructions. Do not include private PRISE source, credentials, secrets, or unrelated files.
4. If weights must remain proprietary, provide them to a named evaluator through controlled access/NDA rather than public release.
5. Provide a clean environment specification with pinned package versions and exact inference command.
6. Record host hardware, OS, accelerator/runtime, precision/quantization, batch size, context length, warmup, concurrency, and measurement methodology.

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
- Do not claim NIST certification; NIST AI RMF is a risk-management framework, not an AI model performance certificate.
- Publish limitations, missing tests, hardware details, variance where relevant, and failures as well as successes.

## Deployment acceptance
- Confirm a public hosted URL from a clean browser/client.
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
