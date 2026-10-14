# ARIES Launchpad

ARIES Launchpad is a small self-hosted dashboard and service monitor for the ARIES API. It is a starting point for owning the control panel and deployment configuration. It is not a full cloud provider: it does not provision servers, build arbitrary Git repositories, create DNS/TLS, or supply model weights. You provide the machine and Docker Engine.

## Windows startup

1. Install Docker Desktop and start it.
2. Download and extract the repository ZIP.
3. Open PowerShell in the extracted platform folder.
4. Copy .env.example to .env and edit it with a real, authorized OpenAI-compatible inference endpoint and exact model ID. Add a key only if the provider requires it. Keep .env private.
5. Run: docker compose --env-file .env up --build -d
6. Open http://localhost:8090 for the dashboard and http://localhost:8090/api/status for diagnostics.
7. Logs: docker compose logs -f aries-api aries-launchpad. Stop: docker compose down.

Without a configured model backend, the dashboard runs but explicitly reports inference as not ready. A successful health check is not proof of model capability.

## Public hosting

To expose this platform outside your computer, deploy the Compose stack on a server you control and configure a domain and TLS reverse proxy. This stack does not automatically deploy to Render or make a local computer public.

## External verification

GitHub Actions workflow: .github/workflows/aries-launchpad-tests.yml. It syntax-checks the dashboard and exercises its HTTP health, HTML, and status endpoints using a deliberately unavailable mock backend. This verifies the platform control panel, not the public ARIES model inference.

A real external inference test passes only when POST /v1/chat/completions returns HTTP 200 and a non-empty assistant message. Use repeated samples and record hardware/model details before publishing performance claims.
