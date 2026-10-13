# ARIES Tier 0 — API and External Test Setup

ARIES Tier 0 currently provides a FastAPI service with health, model-listing, and OpenAI-compatible chat-completions routes. GitHub Actions validates the API contract and RTL smoke test. **Those checks are not proof of model quality or a public inference benchmark.**

## Deploy the API

[Deploy ARIES to Render](https://render.com/deploy?repo=https://github.com/mallinpaul848-coder/ARIES-Tier0)

The Render blueprint creates a free web service named `aries-tier0-api` from this repository. After deployment, Render displays the public HTTPS URL.

## Required backend configuration

In the Render service's **Environment** settings, configure:

- `ARIES_UPSTREAM_BASE_URL`: base URL of a real, authorized OpenAI-compatible inference API. It may end with `/v1`; do not include `/chat/completions` or the full `/v1/chat/completions` path. ARIES now handles either base-URL style.
- `ARIES_MODEL_ID`: exact model identifier accepted by that backend. This is required.
- `ARIES_UPSTREAM_API_KEY`: secret key for that backend, if required. Keep it in Render's secret environment settings; never commit it to GitHub.
- `ARIES_UPSTREAM_TIMEOUT_SECONDS`: defaults to `90`.

The repository does not contain model weights or a configured inference provider. Without a working upstream backend, model ID, and any required credential, health checks may pass but chat inference will not work. Do not advertise the API as inference-ready until a real chat response is verified.

## Run public endpoint checks

After deployment and backend configuration:

1. Open [ARIES Public Endpoint Smoke Test](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/public-endpoint-smoke-test.yml).
2. Select **Run workflow**.
3. Enter the public Render HTTPS base URL (for example, `https://your-service.onrender.com`) and start it.

The workflow checks health, readiness, the model list, and a real chat-completions response. It records one end-to-end latency sample; that sample is not a statistically valid benchmark or leaderboard result.

## Current verification

- GitHub API contract tests: check the latest run linked below.
- RTL external smoke workflow: check the latest run linked below.
- Live public endpoint and actual model inference: not yet verified.
- External AI benchmark/leaderboard submission: not completed.

[View API test workflow runs](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/api-tests.yml)

Only publish measured performance after repeatable tests against a live, working model endpoint.
