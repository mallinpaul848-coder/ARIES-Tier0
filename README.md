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


## Unified PRISE mathematics (research module)

Added `aries_math/prise_unified.py` with digital-root/3-6-9 features, torus geometry, Helixo spiral coordinates, sample-signal diagnostics, Euler characteristic and finite Euler-product helpers, PRISE weighted scoring, and a small-instance exhaustive SAT baseline. See [module documentation](aries_math/README.md) and [automated tests](tests/test_prise_unified_math.py).

Run the focused test suite from the repository root:

```powershell
python -m unittest tests.test_prise_unified_math -v
```

Scientific scope: the research module is connected to the native chat request path through explicit deterministic tool routing. It does not prove P = NP or P != NP. The SAT baseline is exponential by design, and no sub-nanosecond latency claim is made. The sample signal routines are diagnostics, not a rigorous general Helmholtz-Hodge decomposition. See the module documentation for limitations.


### Public PRISE mathematics endpoints

The native server now exposes these additive endpoints after the latest container rebuild:

- `GET /math/diagnostics` — lists the research operators and scientific scope.
- `POST /math/analyze` — JSON body `{"payload":"ARIES sample"}`; returns byte/checksum, digital-root and toroidal features.
- `POST /math/prise` — JSON body with `name`, `priority`, `risk`, `impact`, `systemic`, and `emergent` values from 0 to 1; returns the weighted PRISE score.
- `POST /math/sat` — JSON body `{"clauses":[[1,-2],[2]],"variable_count":2}`; runs bounded exhaustive CNF-SAT for up to 24 variables by default.

PowerShell example:

```powershell
Invoke-RestMethod "https://aries-tier0-api-6qjh.onrender.com/math/diagnostics"
$body = @{ name="Dispatch delay"; priority=0.8; risk=0.5; impact=0.9; systemic=0.6; emergent=0.4 } | ConvertTo-Json
Invoke-RestMethod "https://aries-tier0-api-6qjh.onrender.com/math/prise" -Method Post -ContentType "application/json" -Body $body
```

These routes are served by the same public container, but will not exist until the deployment has rebuilt successfully. SAT uses exponential brute force and is limited to small test cases; no P-vs-NP proof or sub-nanosecond timing is claimed.


## Create a portable ARIES ZIP archive

From the repository root on Windows PowerShell:

```powershell
python .\tools\package_aries.py
```

This writes `aries_sub_nanosecond_model.zip` in the repository root. The archive includes source, benchmark code, configuration, and available checkpoint assets, while excluding Git metadata, virtual environments, common caches, and common credential files. It also embeds `EXPORT_MANIFEST.json` with file sizes and SHA-256 hashes.

To choose another output location:

```powershell
python .\tools\package_aries.py --output "$env:USERPROFILE\Desktop\aries_sub_nanosecond_model.zip"
```

Inspect the archive before sharing it; automated exclusions are not a guarantee that every secret or licensed file is removed. Packaging does not measure latency, certify model quality, publish to Hugging Face, or submit to a leaderboard.


## Low-latency deterministic fast path and measured telemetry

ARIES includes `software/latency_engine.py`:

- Bounded thread-safe LRU cache for deterministic rule-engine results only. Unknown prompts still fall back to the character n-gram generator.
- Case-sensitive cache keys so exact-output prompts don't accidentally reuse a differently cased answer.
- `GET /performance` reports cache use, monotonic timer metadata, and rolling latency percentiles collected from real chat requests.
- Chat completions include `aries_native.inference_ns`, `fast_path_elapsed_ns`, and `fast_path_cache_hit`.
- `tools/aries_latency_bench.py` compares direct rule solving, cache-disabled routing, unique-prompt cache misses, and repeated-prompt cache hits on the machine where it runs.

Run from the repository root in PowerShell:

```powershell
python -m pytest -q tests/test_latency_engine.py tests/test_native_reasoner.py
python tools/aries_latency_bench.py --iterations 20000 --output reports/aries-latency-benchmark.json
```

The [ARIES Latency Engine Tests and Microbenchmark workflow](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/aries-latency-bench.yml) runs the tests and uploads the measured JSON report for its specific GitHub-hosted runner.

**Latency measurement boundary:** times are represented in nanoseconds using Python's `perf_counter_ns()`; this does not guarantee nanosecond timer resolution, much less sub-nanosecond inference. The microbenchmark measures a deterministic rule/cache path—not generative model inference, external API latency, or CPU cycles. The current character n-gram model remains a small baseline, not a modern LLM. Do not market the report as proof of sub-nanosecond AI inference.


## Latest validation and comparison report

See [ARIES external validation and model comparison — 2026-10-14](benchmarks/ARIES_VALIDATION_COMPARISON_2026-10-14.md) for the latest passing GitHub Actions checks, measured cache/rule-engine timing, public endpoint diagnostic results, comparison to a current leading public model index, and the remaining official leaderboard publication steps.


## Browser chat on Windows

A simple browser chat page is available at [aries-chat.html](aries-chat.html). For the easiest launch, download/extract the repository ZIP, ensure Python is installed, then double-click `software/START_ARIES_CHAT.bat`. It starts the native API and a local web server, then opens the chat at `http://127.0.0.1:8081/aries-chat.html`. Keep both opened terminal windows running while chatting.

If Windows blocks the launcher, open PowerShell in the repository folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\software\run_windows.ps1
```

Then in a second PowerShell window from the repository root run:

```powershell
python -m http.server 8081 --bind 127.0.0.1
```

Open `http://127.0.0.1:8081/aries-chat.html`. The page connects to `http://127.0.0.1:8000`. This UI uses the existing native character n-gram baseline; it does not turn that baseline into a modern LLM, and response quality may be limited. The browser chat is local to your PC and is not automatically published as a public website.
