# ARIES Tier 0 — Native Inference, API, and External Tests

ARIES now includes an independently authored, provider-free inference service. The Docker deployment trains a small character n-gram baseline from `software/deployment_corpus.txt` during image build, plus a transparent deterministic task engine for basic arithmetic, simple logic, weekday arithmetic, exact-output formatting, and a tiny verified fact table. It serves an OpenAI-compatible chat endpoint. It does not require a third-party model API key or upstream URL.

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

The public workflow runs the 10-case ARIES-authored diagnostic suite and stores measured responses, exact-match scores, and latency as a downloadable GitHub Actions artifact. The rule engine handles some narrow cases directly, so its score measures this authored software test suite—not general LLM intelligence. It is not an official academic benchmark or independent certification.

## External verification

- [Public endpoint workflow](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/public-endpoint-check.yml)
- [API tests](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/api-tests.yml)
- [All GitHub Actions runs](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions)

The public endpoint workflow must pass against the live service before claiming that the deployment is working. The endpoint smoke test verifies availability and non-empty generated text only. Real capability evaluation requires a larger trained model, suitable compute, a defined test suite, repeated measurements, and published methodology.

## Native runtime components

- `software/native_runtime.py` — training, loading, and character n-gram generation
- `software/native_reasoner.py` — auditable deterministic task handlers for supported narrow tasks
- `software/public_native_server.py` — public HTTP API for the native baseline
- `software/data_pipeline.py` — text normalization and corpus hashes
- `tools/aries_bench.py` — endpoint diagnostics and small exact-match suite
- `platform/` — self-hosted Launchpad dashboard

The native deployment is a working software baseline, not a full cloud platform. It cannot create DNS/TLS, guarantee always-on free hosting, or create a capable pretrained model from a tiny demonstration corpus.


## Latest external validation status

The latest strict public inference run **passed**: [GitHub Actions run](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058912). All four public API checks returned HTTP 200 and all three response-quality assertions passed. Measured chat latency was 276.36 ms minimum, 279.09 ms median, and 358.10 ms maximum from a GitHub-hosted runner. The JSON evidence is available [here](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058912/artifacts/11865749543).

On the same commit, [API tests](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503059069), [end-to-end API integration](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503058967), and [RTL external smoke tests](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38503059087) also passed. The [10-case diagnostic scorecard](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/runs/38502634925) previously reported 10/10 exact matches on its small ARIES-authored prompt set.

**Leaderboard status: NOT SUBMITTED.** These checks validate API availability and a few narrow responses, not broad model quality or official leaderboard ranking. The deployed ARIES-owned character n-gram baseline is not a supported Transformers foundation model for the normal Open LLM Leaderboard submission path. Official submission still requires a suitable public model repository with supported weights/config/tokenizer, AutoClass loading verification, standard evaluation, and an actual submission/queue confirmation. See the [leaderboard readiness checklist](https://github.com/mallinpaul848-coder/ARIES-Tier0/blob/main/benchmarks/LEADERBOARD_READINESS.md) and the [official submission guide](https://huggingface.co/docs/leaderboards/en/open_llm_leaderboard/submitting).
