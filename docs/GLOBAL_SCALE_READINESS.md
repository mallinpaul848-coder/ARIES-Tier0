# ARIES AI / MALLIN Platform — Global Scale Readiness

## Purpose
Define a safe, measurable path from the current ARIES-Tier0 service to geographically distributed production deployment. This document is a rollout specification, not evidence that global infrastructure has already been provisioned.

## Global rollout model
1. **Keep one canonical API contract**: `/health`, `/diagnostics`, `/v1/models`, and `/v1/chat/completions` (where implemented).
2. **Stateless API replicas**: run multiple instances behind a managed HTTPS load balancer. Keep session state outside individual replicas or explicitly document session affinity.
3. **Regional deployment**: deploy to at least two regions first, then expand based on measured demand, data-residency requirements, and provider availability. Use health-checked routing and a documented failover policy.
4. **Model backend**: configure a real, authorized inference backend per environment. Do not treat an API shell, mock response, or upstream proxy as an independently trained ARIES model.
5. **Capacity protection**: configure per-client rate limits, request/body limits, concurrency caps, queue limits, timeouts, retries with backoff, and circuit breakers. Avoid unbounded retries and unbounded queues.
6. **Observability**: record request count, success/error rate, p50/p95/p99 latency, time-to-first-token, tokens/second, queue depth, saturation, and per-region availability. Exclude secrets and sensitive prompt content from logs.
7. **Rollout gates**: do not increase traffic until smoke tests, load tests, failure tests, and rollback checks pass in the target environment.

## Suggested environment-specific parameters
These are starting points to tune under load, not universal production values. Use the deployment platform's supported configuration mechanism and keep secrets in its secret store.

| Parameter | Initial policy | Notes |
|---|---|---|
| `ARIES_ENV` | `staging` then `production` | Separate environments; never test load against production without approval. |
| `ARIES_UPSTREAM_BASE_URL` | Explicit HTTPS inference endpoint | Required only when the service proxies to an upstream model. |
| `ARIES_MODEL_ID` | Exact deployed model identifier | Verify that `/v1/models` reports the model actually served. |
| `ARIES_REQUEST_TIMEOUT_SECONDS` | 30 | Tune to measured model response times and streaming behavior. |
| `ARIES_MAX_CONCURRENCY` | Start at 8 per instance | Raise only after saturation and error-rate tests. |
| `ARIES_MAX_REQUEST_BYTES` | 1 MiB | Set a product-appropriate limit and reject oversize requests. |
| `ARIES_RATE_LIMIT_RPM` | Start at 60 per API key | Replace with tier-specific quotas after capacity tests. |
| `ARIES_RETRY_MAX_ATTEMPTS` | 2 for transient upstream failures | Use exponential backoff and jitter; do not retry non-idempotent work blindly. |
| `ARIES_LOG_LEVEL` | `INFO` in production | Never log API keys or raw secrets. |

These names are proposed conventions. Confirm that the application reads each variable before relying on it; unsupported environment variables do nothing.

## Minimum release gates
- API contract tests pass against the deployed endpoint.
- `/health` and `/diagnostics` are green, and readiness confirms a real configured model backend.
- A deterministic baseline and representative quality set are recorded with commit SHA, model ID, hardware, region, concurrency, warm/cold state, and raw result artifacts.
- Load test reports throughput and p50/p95/p99 latency at 1, 2, 4, 8, and 16 concurrent clients (or a documented safe limit), with errors and timeouts included.
- Failure tests cover upstream timeout, unavailable region, rate limiting, and restart/recovery.
- Rollback to the previous known-good deployment is rehearsed.
- Data retention, privacy, access controls, cost alerts, and incident ownership are documented.

## Capacity math
For planning only, Little's Law gives approximate in-flight work as `concurrency ≈ arrival rate × average response time`. Streaming generation capacity must also be measured in tokens/second and is constrained by the model backend, not merely by the API server's lightweight C/C++ kernels. Do not extrapolate single-kernel nanosecond timings to end-to-end model latency.

## Current status
Global deployment, multi-region routing, autoscaling, external validation, and production capacity are **not confirmed by this document**. Validate the live cloud configuration and measured results before advertising them. The next implementation step is to inspect the existing deployment files, add provider-specific regional infrastructure configuration, and run staged load tests using authorized infrastructure credentials.