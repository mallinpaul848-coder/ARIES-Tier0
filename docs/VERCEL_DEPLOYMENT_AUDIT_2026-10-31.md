# MALLIN AI Vercel Deployment Audit

Audit date: 2026-10-31
Project: aries-ai-mallin-chat
Production URL: https://aries-ai-mallin-chat.vercel.app/
Repository: https://github.com/mallinpaul848-coder/ARIES-Tier0

## Verified current state
- Vercel production deployment dpl_4SR8vBNdXCxhCKL5fHibF3bzKUPk reached READY.
- The production alias aries-ai-mallin-chat.vercel.app resolves to that deployment.
- GET / returned HTTP 200 and the refreshed MALLIN chat interface.
- GET /api/status returned HTTP 200. The upstream ARIES API reported health=ok, local_model_loaded=true, backend=local-llama-cpp, model id aries-local-smollm2-135m, inference_configured=true, and general_chat_ready=true.
- GET /api/chat returned HTTP 405 with Allow: POST, as expected for a chat endpoint that accepts POST only. This does not test a generated answer.
- The current upstream model is reported as local SmolLM2-135M-Instruct. It is a small local model and is not equivalent in capability to GPT-class frontier models.

## Implemented in this release
- Rebuilt root index.html as a responsive GPT-style chat shell with new conversations, local browser history, prompt suggestions, voice input/output, copy controls, and a connection status indicator.
- Added api/chat.js as a same-origin Vercel serverless proxy to the ARIES API. This avoids browser cross-origin requests directly to Render.
- Added api/status.js to report API health, model configuration, and general-chat readiness without exposing credentials.
- Added docs/CLAUDE_ARIES_PRIZE_RESEARCH_HANDOFF.md as a research handoff for PRISE and the six remaining Millennium Prize Problems.
- The chat proxy accepts POST only, bounds message count/content/token count, times out upstream requests, and applies a best-effort in-memory per-instance rate limit.

## Risks and remaining work
1. **Actual chat generation is not yet independently smoke-tested through the deployed /api/chat POST route.** A GET request cannot validate this route. Send a real prompt in the browser and record status, response text, model id, and latency.
2. **Model capability:** status reports a local 135M-parameter SmolLM2 model. A working model is not the same as GPT-level reasoning, knowledge, context length, multimodality, or tool use. Benchmark quality on a fixed test set before making capability claims.
3. **Backend availability:** the web client is on Vercel, but inference remains on the ARIES Render service. A free backend may sleep, restart, or be resource constrained. Vercel READY does not guarantee backend uptime.
4. **Rate limiting:** the in-memory limit in api/chat.js is best effort and resets across serverless instances/restarts. Production public access needs shared rate limiting, abuse monitoring, quotas, and optionally sign-in.
5. **Public access / cost abuse:** the chat proxy is unauthenticated. Before opening access at scale, add usage controls and an abuse policy. Never place provider keys in browser code.
6. **Conversation persistence:** conversation history is stored in the visitor's localStorage only. It is not synced across devices and can be cleared by the browser.
7. **No streaming yet:** the current proxy returns the completed upstream response; it does not stream tokens progressively.
8. **No attachments or multimodal input:** the current API contract accepts text message content. File uploads, image understanding, audio transcription, and image generation are not implemented by this release.
9. **Deployment reproducibility:** this production release was uploaded directly to Vercel as source files, not proven to be a Git-connected automatic deployment. Keep GitHub and Vercel source synchronized; preferably connect the project to the repository/branch and configure a repeatable build/deploy pipeline.
10. **Testing:** add automated smoke tests for GET /api/status, POST /api/chat, timeout behavior, upstream errors, rate limits, and mobile UI. Add a post-deploy production check to CI.

## Release acceptance checklist
- [ ] POST a real chat prompt through https://aries-ai-mallin-chat.vercel.app/api/chat and verify a non-empty answer.
- [ ] Verify answer quality across arithmetic, multi-step reasoning, knowledge, coding, instruction following, and adversarial prompts.
- [ ] Measure TTFT, total latency, P50/P95/P99, errors, and throughput on documented hardware and deployment conditions.
- [ ] Confirm the exact backend model and revision; publish its license/provenance.
- [ ] Add shared rate limiting and usage controls before high-volume public launch.
- [ ] Implement streaming, server-side conversation persistence, and attachment handling only after the backend supports them.
- [ ] Configure Git-connected deployments and automated post-deploy smoke tests.
- [ ] Keep claims limited to measured, reproducible results.

## Deployment claim boundary
This audit verifies that the frontend and status proxy are deployed and that the upstream API currently reports a loaded local model. It does not certify end-to-end generated answers, GPT parity, continuous uptime, third-party validation, or a solution to any Millennium Prize Problem.
