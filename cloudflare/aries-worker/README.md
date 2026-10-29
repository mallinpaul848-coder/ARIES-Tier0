# ARIES AI free hosted inference (Cloudflare Workers AI)

This is a free-tier deployment target for ARIES's general-chat API. It runs remotely; it does not use the owner's PC or home internet.

## Deploy after creating a free Cloudflare account

1. Open https://dash.cloudflare.com/ and sign in.
2. Open **Workers & Pages** → **Create** → **Connect to Git** (wording may vary).
3. Connect the GitHub account that can access `mallinpaul848-coder/ARIES-Tier0` and select that repository.
4. Set the worker's root/build directory to `cloudflare/aries-worker`.
5. Use `npx wrangler deploy` as the deploy command. The directory's `wrangler.toml` binds the Workers AI service as `env.AI`.
6. Deploy and copy the resulting `https://aries-mallin-ai.<your-account-subdomain>.workers.dev` URL.
7. Test `https://YOUR-WORKER-URL/health`; it should return JSON with status `ok`.

Workers AI free allocation is 10,000 Neurons per day as published by Cloudflare. When the daily allowance is exhausted, chat requests can fail until reset. This is not an unlimited-uptime or unlimited-usage guarantee.

## Connect the website

The worker implements an OpenAI-compatible `POST /v1/chat/completions` endpoint and allows browser requests from the existing ARIES Vercel domains. To complete the website hookup, configure the website's backend/base URL to the new worker endpoint and redeploy the website. Do not put Cloudflare API tokens in browser code.

## Important security/production notes

- The public endpoint is quota-limited by the provider but has no per-user authentication yet. Before promoting it for large public traffic, add abuse controls/rate limiting.
- This is a hosted third-party model, not a claim that the ARIES-owned local model is independently running on Cloudflare.
- Verify the deployed worker's `/health` and a real chat completion before announcing launch.
