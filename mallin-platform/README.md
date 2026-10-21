# MALLIN Platform

## Self-hosted deployment

This service provides a public HTTPS gateway, a platform status dashboard, a protected admin-token check, and an OpenAI-compatible chat proxy to ARIES. It runs on a Linux server you control using Docker Compose and Caddy.

## Requirements

- Linux VPS or dedicated server with Docker Engine and the Docker Compose plugin
- A domain you control, with DNS records pointing to the server
- Inbound TCP ports 80 and 443 open
- A strong private admin token

## Launch

From this directory on your server, create a file named .env containing:

```dotenv
MALLIN_DOMAIN=platform.your-domain.example
MALLIN_ADMIN_TOKEN=replace-with-a-long-random-secret
ARIES_API_URL=https://aries-tier0-api-6qjh.onrender.com
```

Then run:

```sh
docker compose up -d --build
```

Open https://platform.your-domain.example. The dashboard reports whether ARIES is reachable. API docs are at /docs, health is at /health, and status is at /api/status.

## API

- GET /health — platform health
- GET /api/status — platform and ARIES API status
- POST /api/admin/check — verifies the configured bearer token
- POST /v1/chat/completions — forwards chat requests to ARIES

## Independence

This is a self-hostable platform runtime, not yet a cloud-provider account or source-code build farm. The gateway and dashboard run on your own server after deployment. The current ARIES inference target remains ARIES_API_URL; to remove Render from the inference path, run ARIES inference on a server you control and point ARIES_API_URL at it. A server and DNS are required for a public production launch. Keep .env private and never commit it.
