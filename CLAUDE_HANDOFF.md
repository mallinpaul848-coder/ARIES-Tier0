# Claude Code Handoff — ARIES AI / MALLIN Platform

## Source of truth
- Repository: `mallinpaul848-coder/ARIES-Tier0`
- Primary branch: `main`
- Start by syncing the latest `main` branch. Do not rely on ZIPs or stale local copies.
- Read `AGENTS.md` first and obey its architecture-preservation rules.
- Latest known UI update: the `aries-chat.html` cosmic video background and mode selectors were committed on `main`. Verify the actual current branch state before editing.

## Owner's target
Improve the complete ARIES AI / MALLIN Platform into a usable demo-ready web app and API, preserving the owner's existing architecture and confidential intellectual property. Keep the mentor-style voice implementation discreet in public-facing copy. The user wants a space/Earth live-video background, chat interface, voice input, read-aloud answers, response styles, free modes, and clearly gated paid reasoning modes.

## Mandatory first steps
1. Inspect the repository tree, recent commits, README/docs, CI workflows, API routes, chat UI, and tests.
2. Map what actually works versus placeholders. Do not assume a model artifact exists; inspect files and inference code.
3. Run the existing relevant tests and report exact commands, results, and environment. Do not claim tests passed unless run.
4. Create a short prioritized plan before broad edits; make small, reversible changes and use a feature branch for significant changes.

## Priority order
1. Fix the end-to-end chat path: API health/readiness, model discovery, non-empty answers, errors, and browser-to-API connectivity.
2. Inspect the actual inference backend/model artifacts. If this is a small n-gram/native baseline, describe it accurately and do not present it as a modern general-purpose LLM.
3. Make chat history, response modes, accessibility, mobile layout, voice input/output, loading states, and errors reliable.
4. Treat Fast/Balanced/PRISE selectors as real modes only if the backend implements and tests their behavior. Otherwise label them as preview/UI-only.
5. Keep paid reasoning disabled until real authentication, server-side entitlement checks, billing, quotas, and a compatible reasoning backend exist. Never imply a menu lock is payment security.
6. Verify the background video URL and playback behavior; provide a graceful poster/fallback. Check that the owner has a license suitable for commercial website/app use before shipping the stock clip.
7. Improve automated tests, CI, security, dependency hygiene, deployment instructions, and an easy Windows launch path.
8. Add reproducible benchmark scripts and reports. Separate native-kernel microbenchmarks from end-to-end generative-model latency; never fabricate performance or third-party validation.

## Hard boundaries
- Do not delete or replace Claude Code integration, core math/PRISE modules, native code, RTL, API contracts, or model routing without explicit approval.
- Do not put secrets, API keys, customer data, or proprietary source code into public artifacts, logs, or commits.
- Do not silently switch to a third-party inference provider.
- Do not claim deployment, model training, external validation, leaderboard submissions, commercial billing, or successful inference without evidence.
- Do not make unsupported claims of Gemini feature parity. Build original, clearly documented functionality.
- Do not make expensive/destructive production changes or change billing/security settings without asking first.

## Required completion report
Provide:
- Files changed and rationale
- Tests actually run, with pass/fail and logs or CI links
- What works, what remains broken, and exact reproduction steps
- Security/privacy and licensing caveats
- Deployment status and a short next-step checklist
- Measured performance with hardware, workload, sample count, and methodology

Start with an audit and diagnosis, then fix the highest-impact verified issue.