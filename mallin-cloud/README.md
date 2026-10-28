# MALLIN Cloud

ARIES-owned, self-hostable deployment platform MVP for publishing static websites from public GitHub repositories without Vercel.

## Run with Docker

1. Copy `.env.example` to `.env` and set a strong random `MALLIN_ADMIN_TOKEN`.
2. Run `docker compose up -d --build`.
3. Open `http://localhost:8787`.
4. Paste the admin token and enter a public GitHub repository URL, branch and site slug.

See the repository root README and `mallin-cloud/render.yaml` for deployment notes. This MVP runs npm build scripts from submitted repositories; deploy only trusted repositories on an isolated server. Use HTTPS and a firewall before public exposure. The host must remain running; the software does not provide its own global hosting network.
