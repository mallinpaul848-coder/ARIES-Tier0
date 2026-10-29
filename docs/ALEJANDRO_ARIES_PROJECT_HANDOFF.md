# ARIES AI / MALLIN Platform — Project Handoff for Alejandro

**Last reviewed:** 29 October 2026  
**Public website:** https://aries-ai-mallin-chat.vercel.app/  
**GitHub repository:** https://github.com/mallinpaul848-coder/ARIES-Tier0  
**Known API URL:** https://aries-tier0-api-6qjh.onrender.com

## 1. What ARIES is

ARIES AI (also called MALLIN Platform or ARIES Tier 0) is a software project combining a browser chat interface, an OpenAI-compatible HTTP API, deterministic handlers for selected tasks, small-model inference options, benchmarking/CI, and experimental PRISE math research tools.

A working website is not by itself proof that the AI backend is working, that the model has high general capability, or that an independent organization has certified it.

## 2. Repository and key folders

The repository is private. Alejandro needs explicit GitHub access from the owner. Never share passwords, API tokens, or secret environment variables in this document or source code.

- software/ — native runtime, server, Windows launchers.
- tools/aries_bench.py — API and diagnostic benchmark.
- tools/aries_latency_bench.py — deterministic fast-path microbenchmark.
- software/latency_engine.py — cache and latency telemetry.
- aries_math/ — PRISE and mathematical research diagnostics.
- benchmarks/ — buyer brief, diligence pack, evaluation protocol and reports.
- .github/workflows/ — tests, endpoint checks and benchmark workflows.
- cloudflare/aries-worker/ — example Cloudflare Workers AI deployment.
- aries-chat.html — local browser chat page.
- README.md — main technical documentation.

Check the latest main-branch commit and latest Actions runs before relying on older reports.

## 3. Public website and deployment

Website: https://aries-ai-mallin-chat.vercel.app/

The Vercel project is named aries-ai-mallin-chat. Its production deployment reported READY when checked on 29 October 2026, and the website HTML loaded. The page has a purple galaxy design, chat composer, connection settings, voice input where browser-supported, spoken replies, and copy/new-chat controls.

READY means the website is deployed; it does not guarantee that chat generation works end to end.

The current webpage's default API endpoint is https://aries-tier0-api-6qjh.onrender.com. Test a real chat completion after every deployment.

## 4. API endpoints to check

Known API URL: https://aries-tier0-api-6qjh.onrender.com

Documented endpoints include:

- GET / — readiness/model information.
- GET /health — health check.
- GET /diagnostics — native model status.
- GET /v1/models — model listing.
- POST /v1/chat/completions — chat generation.
- GET /performance — latency/cache telemetry, if present in the deployed revision.
- GET /math/diagnostics, POST /math/analyze, POST /math/prise, POST /math/sat — research endpoints, if present in the deployed revision.

Documentation does not prove every route exists in the live container. Verify current deployment and rebuild status.

### Quick PowerShell test

~~~powershell
$base = "https://aries-tier0-api-6qjh.onrender.com"
Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/v1/models"

$body = @{
  model = "aries-native-ngram"
  messages = @(@{ role = "user"; content = "Calculate 17 times 19 and show the steps." })
  max_tokens = 120
  temperature = 0.2
} | ConvertTo-Json -Depth 6

Invoke-RestMethod "$base/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body
~~~

The model ID is an example; use the ID returned by /v1/models if it differs.

## 5. Model/runtime caveat

The repository has multiple documented configurations. These are different paths and must not be described as one identical model:

- A character n-gram baseline and deterministic handlers for selected tasks.
- A Docker deployment intended to run a compact quantized model with llama.cpp.
- A Windows self-hosted runtime documented with a Qwen2.5-1.5B-Instruct GGUF model.
- Example Cloudflare Workers AI code using Meta Llama 3.2 3B Instruct as a hosted third-party model.

Some documentation references SmolLM2-135M while another section describes Qwen2.5-1.5B. Confirm the actual live model by checking /v1/models, /diagnostics, service logs, environment settings, and deployed commit. The Cloudflare worker's source exists, but do not assume it is deployed or connected until its live /health and a real completion succeed.

Compact models can make mistakes and are not equivalent to frontier-scale models. Correct deterministic arithmetic on supported inputs does not prove broad general intelligence.

## 6. How to verify the website end to end

1. Open the public website.
2. Open the gear/settings control and click Test connection.
3. Open https://aries-tier0-api-6qjh.onrender.com/health
4. Open https://aries-tier0-api-6qjh.onrender.com/v1/models
5. Ask the chat: “What is 17 times 19? Show the calculation.”
6. Ask a general question such as “Explain why the seasons change.”
7. Confirm answers are non-empty and relevant, not fixed/repeated text.
8. Reload and repeat. Record timestamp, model ID, HTTP status, answer, and latency.

If health succeeds but chat fails, inspect browser developer tools for request status, CORS errors and response body. Check Render logs and deployed commit. Never publish secret environment variables.

## 7. Existing performance evidence and its limits

The repository README records a historical GitHub-hosted public inference run reporting four API checks with HTTP 200, three response-quality assertions passing, and latency of 276.36 ms minimum, 279.09 ms median, and 358.10 ms maximum on that particular run. A separate small project-authored diagnostic set previously scored 10/10 exact matches.

Evidence links:
- Public inference run: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058912
- JSON artifact: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058912/artifacts/11865749543
- API tests: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503059069
- API integration: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058967
- RTL smoke tests: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503059087
- All Actions runs: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions

Treat these as historical until the latest workflow and current live commit are verified. These checks are not independent certification and do not establish broad model quality. Latency varies by model, hardware, network, load, and methodology. A small project-authored exact-match suite is not an official academic benchmark.

To obtain current evidence: open GitHub → Actions → ARIES Performance Metrics → latest run; download the report artifact and preserve the JSON, run URL, commit SHA, timestamp, model ID, and environment.

### Latency claim boundaries

The deterministic rule/cache microbenchmark is not full generative inference. Python nanosecond timestamps do not prove sub-nanosecond inference. Do not claim sub-nanosecond AI generation, frontier-model superiority, guaranteed throughput, or performance improvements unless current reproducible tests directly establish them.

## 8. PRISE and research scope

PRISE is a research scoring framework using Priority, Risk, Impact, Systemic, and Emergent factors. The project also contains experimental digital-root/3-6-9 features, torus/Helixo-inspired representations, signal diagnostics, and bounded SAT tools.

These are software experiments, not proof that P = NP or P ≠ NP, solutions to Millennium Prize Problems, or proof of quantum computation. Exhaustive SAT checks are exponential and suitable only for small instances. Use precise scientific language and cite source/tests for specific claims.

## 9. Hugging Face and independent validation

Project-authored tests and CI are different from independent certification. The main README states that the ARIES-owned model has not been submitted to the standard Open LLM Leaderboard flow.

That flow requires a real, supported public model repository with model weights, configuration, tokenizer, immutable revision, compatibility checks, and completed evaluation. Do not submit an upstream model under the ARIES name or describe upstream scores as ARIES results.

Official references:
- Evaluation results: https://huggingface.co/docs/hub/eval-results
- Open LLM Leaderboard: https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about
- Submission instructions: https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting

A GitHub Actions pass is not NIST certification, Hugging Face endorsement, an independent audit, or an official leaderboard placement. Distinguish clearly between prepared, submitted, accepted, and independently validated.

## 10. Security and operations

- Never commit passwords, access tokens, API keys, customer data, or unlicensed weights.
- Store secrets in hosting-provider environment settings, never browser JavaScript.
- Add rate limiting and abuse controls before promoting an unrestricted public API.
- The example Cloudflare worker documentation notes that authentication/rate limiting needs more work and free usage is quota-limited.
- Do not promise unlimited free use or guaranteed 24/7 uptime on a free hosting tier.
- Preserve raw benchmark outputs and commit SHAs; do not edit results to inflate scores.
- Verify model and dataset licenses before redistribution.
- Review the repository for secrets before sharing an archive.

Render free services may spin down or have resource limits. A public URL is not a guarantee of permanent always-on hosting. Local mode requires the computer and process to remain running and is not the same as a public hosted service.

## 11. Recommended next steps

1. Ensure Alejandro has repository access.
2. Check the latest main-branch commit and CI status.
3. Test the public website and API end to end.
4. Confirm which model is actually running; reconcile runtime documentation.
5. Fix any API/chat failures, redeploy, and repeat tests.
6. Add public API rate limiting and abuse protections.
7. Run current performance tests and archive raw JSON evidence.
8. Publish an ARIES model artifact only if the actual model is ready and legally distributable.
9. Follow the official evaluation submission process and accurately report its status.
10. Keep buyer materials factual about features, measured results, limitations, licenses, hosting costs, and reproducibility.

## 12. Commercial context

ARIES can be presented as a software project with a chat interface, API, research modules, and test/benchmark infrastructure. No sale price, multi-billion-dollar valuation, acquisition offer, or buyer interest is established by the code or deployment alone. Serious valuation requires diligence on IP ownership, code quality, model rights, reproducibility, security, operating costs, customers, and independently measured advantages.

## 13. Key links

- Website: https://aries-ai-mallin-chat.vercel.app/
- Repository: https://github.com/mallinpaul848-coder/ARIES-Tier0
- Actions: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions
- Performance workflow: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/aries-performance.yml
- Public endpoint workflow: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/public-endpoint-check.yml
- API tests: https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/api-tests.yml
- Buyer brief: https://github.com/mallinpaul848-coder/ARIES-Tier0/blob/main/benchmarks/BUYER_BRIEF.md
- Buyer due diligence: https://github.com/mallinpaul848-coder/ARIES-Tier0/blob/main/benchmarks/BUYER_DUE_DILIGENCE.md
- Independent evaluation protocol: https://github.com/mallinpaul848-coder/ARIES-Tier0/blob/main/benchmarks/INDEPENDENT_EVALUATION_PROTOCOL.md

**Bottom line for Alejandro:** The website deployment exists and the repository contains substantial software, research, and test infrastructure. The immediate engineering priority is to verify the current model and prove public chat works end to end on the latest deployment. Keep every performance and scientific claim tied to current reproducible evidence.
