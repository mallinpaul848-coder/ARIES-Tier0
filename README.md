# ARIES Tier 0 — Native Inference, API, and External Tests

ARIES now includes an independently authored, provider-free inference service. The Docker deployment trains a small character n-gram baseline from `software/deployment_corpus.txt` during image build and serves an OpenAI-compatible chat endpoint. It does not require a third-party model API key or upstream URL.

**Important capability limit:** this built-in model is a tiny character n-gram baseline, not a modern large language model. It proves that ARIES's own software can train, load, and serve a model without a hosted inference provider. It is not evidence of Tier-0 capability, strong reasoning, or leaderboard-level performance. Responses may be incoherent and quality tests may score poorly. Do not advertise it as equivalent to a modern LLM.

## Public API

After Render deploys the latest commit, use the service URL shown in Render. The known service URL is:

`https://aries-tier0-api-6qjh.onrender.com`

- `GET /` — service readiness and model type
- `GET /health` — health check
- `GET /diagnostics` — native model status
- `GET /v1/models` — model listing
- `POST /v1/chat/completions` — generated response

No `ARIES_UPSTREAM_BASE_URL`, `ARIES_MODEL_ID`, or provider API key is required for this native baseline. Render must finish rebuilding the Docker image before the new routes and model are live.

Example PowerShell request:

```powershell
$body = @{
  model = "aries-native-ngram"
  messages = @(@{ role = "user"; content = "Explain what ARIES can do." })
  max_tokens = 100
  temperature = 0.2
} | ConvertTo-Json -Depth 5

Invoke-RestMethod "https://aries-tier0-api-6qjh.onrender.com/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body
```

## Run the same native software on Windows

From the repository root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\software\run_windows.ps1
```

This prepares the corpus, trains a local baseline, and starts the API at `http://127.0.0.1:8000`. In another PowerShell window, run:

```powershell
python .\tools\aries_bench.py --base-url http://127.0.0.1:8000 --model aries-native --limit 10 --output .\reports\native-benchmark.json
```

The benchmark writes actual responses, exact-match scores, and latency measurements. It is an ARIES-authored diagnostic suite, not an official academic benchmark or independent certification.

## External verification

- [Public endpoint workflow](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/public-endpoint-check.yml)
- [API tests](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/api-tests.yml)
- [All GitHub Actions runs](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions)

The public endpoint workflow must pass against the live service before claiming that the deployment is working. The endpoint smoke test verifies availability and non-empty generated text only. Real capability evaluation requires a larger trained model, suitable compute, a defined test suite, repeated measurements, and published methodology.

## Native runtime components

- `software/native_runtime.py` — training, loading, and character n-gram generation
- `software/public_native_server.py` — public HTTP API for the native baseline
- `software/data_pipeline.py` — text normalization and corpus hashes
- `tools/aries_bench.py` — endpoint diagnostics and small exact-match suite
- `platform/` — self-hosted Launchpad dashboard

The native deployment is a working software baseline, not a full cloud platform. It cannot create DNS/TLS, guarantee always-on free hosting, or create a capable pretrained model from a tiny demonstration corpus.
