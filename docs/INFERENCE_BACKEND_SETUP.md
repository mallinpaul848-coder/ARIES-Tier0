# ARIES Tier 0 inference backend setup

The API now proxies OpenAI-compatible chat-completion requests to a real upstream model server. It does not contain model weights and does not create a public endpoint by itself.

## Required environment variables

- `ARIES_UPSTREAM_BASE_URL`: base URL of a reachable OpenAI-compatible API, without the trailing `/v1`. Example for a local server: `http://127.0.0.1:8000`.
- `ARIES_MODEL_ID`: exact model identifier accepted by that server.
- `ARIES_UPSTREAM_API_KEY`: optional bearer token if the server requires one. Keep this secret; never commit it to GitHub.
- `ARIES_UPSTREAM_TIMEOUT_SECONDS`: optional request timeout (default 90 seconds).

The proxy calls `{ARIES_UPSTREAM_BASE_URL}/v1/chat/completions`.

## Run locally on Windows

From the repository root in PowerShell:

```powershell
py -m pip install -r requirements.txt
$env:ARIES_UPSTREAM_BASE_URL = "http://127.0.0.1:8000"
$env:ARIES_MODEL_ID = "YOUR-REAL-MODEL-ID"
# Only set this if your local/remote provider requires a key:
# $env:ARIES_UPSTREAM_API_KEY = "YOUR-SECRET-KEY"
py -m uvicorn api.main:app --host 127.0.0.1 --port 8080
```

Then check the API in a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-RestMethod http://127.0.0.1:8080/v1/models
```

A chat test:

```powershell
$body = @{
  model = $env:ARIES_MODEL_ID
  messages = @(@{ role = "user"; content = "Reply with exactly: ARIES inference test passed" })
  max_tokens = 40
  temperature = 0
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/v1/chat/completions -ContentType "application/json" -Body $body
```

## Important limitations

- The upstream must already be running and reachable; the API cannot invent model output.
- A local `127.0.0.1` backend is not publicly accessible from the internet.
- To run public external benchmarks, deploy this API and its model backend to a public HTTPS host, configure secrets in that host's environment settings, and verify `/v1/models` and `/v1/chat/completions` from outside the host.
- Do not publish API keys, private model weights, or personal data.
- Latency and throughput must be measured from actual requests; this repository makes no benchmark-performance claim.
