# ARIES Tier 0 — Native Inference, API, and External Tests

ARIES serves an OpenAI-compatible chat API with deterministic handlers for arithmetic, simple logic, weekday arithmetic, exact-output formatting, and supported math tools. The Docker image bundles SmolLM2-135M-Instruct Q4_K_M for local general chat when no upstream is configured. The character n-gram model remains a lightweight fallback, not the primary general-chat engine.

**Local chat model:** ARIES uses SmolLM2-135M-Instruct, quantized to Q4_K_M and executed with llama.cpp on CPU. This compact instruction model is intended for ordinary questions without requiring an external model API key; it can still make mistakes and is not equivalent to larger frontier models. Exact arithmetic and other supported deterministic tasks continue to use ARIES's own handlers.

## Public API

After Render deploys the latest commit, use the service URL shown in Render. The known service URL is:

`https://aries-tier0-api-6qjh.onrender.com`

- `GET /` — service readiness and model type
- `GET /health` — health check
- `GET /diagnostics` — native model status
- `GET /v1/models` — model listing
- `POST /v1/chat/completions` — generated response

No upstream or API key is required for local general chat. To use an external OpenAI-compatible provider instead, configure `ARIES_UPSTREAM_BASE_URL` and `ARIES_MODEL_ID`; set `ARIES_UPSTREAM_API_KEY` only if that provider requires one. Render must rebuild the Docker image before the local model is live.

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

## Local general-chat model

- Model file: [SmolLM2-135M-Instruct-Q4_K_M.gguf](https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF)
- Runtime: `llama-cpp-python` on CPU, one thread by default
- The build verifies the downloaded GGUF file by SHA-256 before using it.
- Model license: Apache-2.0. The container includes the full license at `/app/licenses/Apache-2.0.txt`.

The live service's `/diagnostics` and `/` endpoints report whether local inference loaded successfully. The deployment must pass the public endpoint check, including a general question-answer test, before the updated chat backend should be considered live.

## Self-hosted ARIES inference on Windows

ARIES can also run its own local chat inference without sending prompts to an external chat API. This separate runtime uses llama.cpp on your computer and downloads the Qwen2.5-1.5B-Instruct Q4_K_M model from its public model repository on first launch (roughly 1 GB; the download size can vary).

1. Download or clone this repository to your Windows PC.
2. Double-click `software\\START_ARIES_SELF_HOSTED.bat`. Keep the terminal open. The first launch installs the runtime and downloads model weights.
3. Open the ARIES chat page, open the gear/settings menu, set **ARIES API URL** to `http://127.0.0.1:8765`, then select **Test connection**.
4. Chat normally. To stop the local engine, press Ctrl+C in its terminal. Run the launcher again to restart it.

This mode runs inference on the computer where it is started and does not require a provider API key. It does require internet access for the initial package/model download and a Windows system with Python 3.10+ and enough RAM (8 GB or more recommended). The 1.5B model is a meaningful step up from the bundled 135M model, but it is still a compact model and can make mistakes. The local API listens only on `127.0.0.1` by default, so it is not exposed to the public internet. Keep the endpoint on localhost unless you intentionally configure a secure private network.

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

## Standard leaderboard evaluation

The `.github/workflows/leaderboard-benchmark.yml` workflow runs the Hugging Face Open LLM Leaderboard task group through the Hugging Face evaluation harness. The full `leaderboard` group covers IFEval, BBH, MATH Level 5, GPQA, MuSR, and MMLU-Pro. Results are saved as a downloadable Actions artifact with raw outputs, samples, model revision, and run metadata.

To run it, open **Actions → ARIES Standard Leaderboard Evaluation → Run workflow** and supply:
- **Model ID:** a public Hugging Face repository containing the actual model weights and tokenizer.
- **Revision:** the immutable Hugging Face commit SHA to evaluate.
- **Dtype:** a precision supported by the model.
- **Tasks:** use `leaderboard` for the full suite; a supported task/group and a nonzero limit can be used for a smoke test.
- **Chat template:** enable for instruction/chat models.

The current ARIES public API benchmark is not a substitute for this evaluation. The public API currently serves a quantized GGUF model; the Open LLM Leaderboard submission flow requires a public, loadable Hugging Face model repository with compatible model weights and tokenizer. Do not submit the upstream SmolLM2 model under the ARIES name. First publish the actual ARIES model artifact and immutable revision, then evaluate that exact repository. A successful local evaluation is not itself acceptance onto the public leaderboard; submit through the [official Open LLM Leaderboard instructions](https://huggingface.co/docs/leaderboards/open_llm_leaderboard/submitting).

Official task definitions and reproducibility guidance: [Open LLM Leaderboard](https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about).

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

## Multitrillion-token ARIES training

The resumable trainer is in [training/aries_trillion_token_trainer.py](training/aries_trillion_token_trainer.py). It uses causal next-token training on an actual UTF-8 corpus, supports checkpoints/resume, mixed precision on CUDA, distributed workers via `torchrun`, and writes `training_evidence.json` with the corpus hash, measured token exposures, step count, loss, throughput, and hardware details. The 3/6/9 feature is an experimental bounded embedding modulation; it is not a proof of P=NP.

To launch the GPU training workflow, open **Actions → ARIES Multitrillion Token Training → Run workflow**. This workflow requires a Linux x64 self-hosted runner labeled `gpu` with a CUDA-capable GPU. The corpus path must point to a licensed text file available on that runner; it is not downloaded from an arbitrary URL. The default target is 3,000,000,000,000 token exposures, but the default run is deliberately limited to 3 optimizer steps as a safety smoke run. Set **max_steps** to `0` only when you intend to run until the target is reached. A successful workflow dispatch alone is not proof of completion: check the uploaded `training_evidence.json` for `status: TARGET_REACHED` and the measured cumulative count. Repeated passes over a small corpus count as repeated exposures, not unique tokens.

The GitHub-hosted runner does not provide the dedicated GPU capacity needed for this training. This change adds the workflow and trainer path; it does not start or claim a multitrillion-token training run, create model weights, or guarantee the target can be completed. Training time and compute/storage requirements depend on the selected model size, corpus, hardware, and measured throughput.

## ARIES / MALLIN SAT research lab

The `python/` directory includes a standard-library-only graph-spectral lab and a deterministic experiment runner:

```bash
cd python
python -m unittest -v test_aries_sat_lab.py test_aries_sat_experiment_runner.py
python aries_sat_lab.py --self-test
python aries_sat_experiment_runner.py --self-test
python aries_sat_experiment_runner.py --variables 8 --instances 30 --seed 7
python aries_sat_experiment_runner.py --tool features --formula '[[1,-2],[2,3]]'
python aries_sat_experiment_runner.py --tool exact --formula '[[1],[-1]]'
```

The runner calculates exact satisfiability labels by exhaustive enumeration only for small instances; it has a safety limit because this method scales exponentially. Its experiment fingerprint supports repeatability checks. The graph features are invariant under variable-ID renaming for the implemented graph encoding. The digital-root, Vortex, Phase-8, and harmonic summaries are proposal encodings and are not claimed to be mathematically canonical or useful SAT decision rules.

These tools are empirical diagnostics. AUC measures classification performance on the sampled distribution, not worst-case algorithmic complexity. Neither these experiments nor the submatrices they analyze prove or disprove P vs NP. Helixo and PRISE require precise formal definitions before they can be evaluated.

GitHub Actions runs both test modules and deterministic smoke checks when the SAT lab files change. Inspect the workflow result under the repository's Actions tab; commits and configured CI are not the same as a verified passing run.



## ARIES performance metrics

The **ARIES Performance Metrics** GitHub Actions workflow runs on pushes that change the benchmark, can be started manually, and runs every 12 hours. It probes the configured public API, selects the first advertised model when `--model auto` is used, executes the 10-case diagnostic suite, and saves a JSON report as a downloadable Actions artifact.

Measured report fields include:
- API health and model-list response status and latency
- Completion request success rate and non-empty response count
- Exact-match score overall and by diagnostic category (arithmetic, reasoning, instruction following, and basic knowledge)
- Minimum, mean, P50, P90, P95, P99, and maximum request latency
- Total benchmark wall time and completed requests per second
- Per-case HTTP status, response text, latency, and token counts when the API returns usage data

Run the same test locally:

```powershell
python tools/aries_bench.py --base-url https://aries-tier0-api-6qjh.onrender.com --model auto --limit 10 --concurrency 1 --output reports/aries-public-performance.json
```

Workflow: [ARIES Performance Metrics](https://github.com/mallinpaul848-coder/ARIES-Tier0/actions/workflows/aries-performance.yml). Open the latest run and download the `aries-performance-*` artifact to inspect the JSON measurements. Latency and throughput are endpoint measurements under that run's network, host, model, and load conditions; they are not hardware-independent guarantees. The 10-case accuracy score is a small project-owned diagnostic, not an official academic benchmark or independent certification.


## Independent validation and buyer evaluation

- [Buyer brief](benchmarks/BUYER_BRIEF.md) — concise product overview, demo path, evidence inventory, and commercial evaluation options.
- [Buyer due-diligence pack](benchmarks/BUYER_DUE_DILIGENCE.md) — deployment checks, evaluation matrix, licensing checklist, and evidence requirements.
- [Independent evaluation protocol](benchmarks/INDEPENDENT_EVALUATION_PROTOCOL.md) — controlled comparison method for ARIES and authorized OpenAI-compatible alternatives.
- [Alternative endpoint benchmark harness](tools/aries_alternative_benchmark.py) — same prompts across configured endpoints; captures success/error counts, smoke accuracy, P50/P95/P99, maximum latency, wall-clock throughput, and raw per-case results.
- [Prize-problem finite diagnostics](aries_math/prize_problem_lab.py) — bounded SAT oracle, sampled Navier–Stokes field diagnostics, finite Yang–Mills spectrum checks, and explicit proof obligations.
- [Independent validation CI](.github/workflows/independent-validation.yml) — compilation, unit tests, and research smoke tests.
- [Manual alternative comparison workflow](.github/workflows/alternative-comparison.yml) — run a reproducible API comparison and download its JSON report.

Run tests locally:

```bash
python -m unittest discover -s tests -p 'test_prize_problem_lab.py' -v
python -m unittest discover -s tests -p 'test_aries_alternative_benchmark.py' -v
```

Run the public ARIES smoke comparison:

```bash
python tools/aries_alternative_benchmark.py --target aries=https://aries-tier0-api-6qjh.onrender.com,aries-native-ngram --rounds 3 --output reports/aries-alternative-comparison.json
```

These tests are finite diagnostics and project-authored smoke checks. They do not establish P = NP, global Navier–Stokes regularity, a Yang–Mills mass gap, independent certification, or an official leaderboard ranking. For a credible buyer evaluation, preserve raw reports, pinned revisions, model identifiers, licensing/provenance, and the actual test environment.
