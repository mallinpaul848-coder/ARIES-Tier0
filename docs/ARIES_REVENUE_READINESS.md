# ARIES AI Revenue Readiness

## Product model

ARIES can start with a free public demo and voluntary supporter payments. Add paid tiers only after usage metering and access control are implemented and tested.

- **Free demo:** limited usage; prefer user-owned inference credits where supported.
- **Supporter:** optional one-time or recurring contribution to fund open development and independent benchmarks.
- **Pro / Team:** future commercial tiers for measured usage, team workflows, and support. Do not advertise gated features until entitlement enforcement is live.

## Hosted payment-link configuration

The companion app in `mallin-gateway/` exposes a public `/monetization/plans` catalogue and a Support / Plans panel. Set these deployment environment variables to hosted checkout URLs:

- `ARIES_SUPPORT_URL`
- `ARIES_PRO_URL`
- `ARIES_TEAM_URL`
- `ARIES_CONTACT_EMAIL` (optional; supplies a mailto contact link)

Hosted checkout links can accept payments, but **they do not automatically grant, revoke, or meter access to paid features**. Before selling feature access, implement verified payment webhooks, subscription state, cancellation/refund handling, account identity mapping, entitlements, and spend caps.

## Launch sequence

1. Deploy the app with sign-in enabled; never use `AUTH_DISABLED=1` in production.
2. Configure only the supporter link initially, then test the complete checkout flow with the provider's test mode.
3. Keep model-provider API keys and payment secrets in the hosting provider's secret manager, never in the repository or browser.
4. Measure cost per request, latency percentiles, failure rates, and daily spend limits on the real deployed backend.
5. Add Pro / Team entitlements and quotas before promising paid access.
6. Publish honest third-party benchmark results with model, dataset, sample count, hardware/provider, date, and confidence intervals.

## Cost and reliability rules

- Do not promise that hosted inference or free hosting will remain free; provider credits and limits can change.
- Price commercial usage above measured inference, hosting, payment-processing, support, and tax costs.
- Add abuse protection, per-user quotas, usage accounting, spend alerts, privacy terms, and a refund/contact policy before launch.
- Keep the free tier's limits explicit and avoid claiming that ARIES is as capable as a proprietary model unless independent evaluations support that claim.
