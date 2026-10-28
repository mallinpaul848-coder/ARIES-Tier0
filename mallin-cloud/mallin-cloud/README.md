# MALLIN Cloud — ARIES-owned deployment platform MVP

A self-hosted starting point for a Vercel-like workflow, without using Vercel. It provides a deployment dashboard, health endpoint, deployment history, and versioned static-site publishing from public GitHub repositories.

## Preview

The dashboard is `index.html`. It can be opened directly for a UI-only preview; API actions require the server below.

## Launch on a Linux server

Requirements: a Linux server or VPS with Docker Engine and Docker Compose, a public IP or hostname, and a domain/DNS + HTTPS reverse proxy for production.

```bash
cd mallin-cloud
cp .env.example .env
openssl rand -hex 32
# Put the generated secret into .env as MALLIN_ADMIN_TOKEN (do not commit .env)
docker compose up -d --build
```

Open `http://SERVER-IP:8787/` on a trusted network to preview. Configure HTTPS, firewall restrictions, and backups before public exposure. The service restarts after host reboots and persists deployments in a Docker volume, provided the host and Docker daemon remain running.

## Endpoints

- `GET /health`
- `GET /api/deployments`
- `POST /api/deploy` with `Authorization: Bearer <MALLIN_ADMIN_TOKEN>` and JSON `{ "repo":"https://github.com/owner/repo", "branch":"main", "project":"site-name" }`
- `GET /sites/<project>/`

## Deliberate MVP limits

- Static sites only. The repository must already contain `index.html` at its root or in `dist/`, `build/`, or `out/`.
- It deliberately does **not** run arbitrary npm build scripts from submitted repositories. Add isolated ephemeral build workers before enabling build commands from untrusted repositories.
- No serverless functions, automatic Git webhooks, managed domains/TLS, multi-tenant isolation, billing, global edge network, or SLA yet.
- This is not commercial Vercel feature parity. Public availability requires a running host and network; no source code can guarantee permanent uptime without redundant infrastructure and operations.

## Security

Use a long random admin token, keep `.env` out of Git, restrict inbound access, place behind HTTPS, and deploy only trusted public repositories. Build output is treated as static files. Do not run the service as root.
