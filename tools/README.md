# ARIES Native Tools

## Dependency-free diagnostic benchmark

`aries_bench.py` uses only the Python standard library. It does not require Lighteval, Hugging Face Evaluate, pytest, or third-party Python packages.

### Run against the deployed API (Windows PowerShell)

```powershell
$env:ARIES_BASE_URL = "https://aries-tier0-api-6qjh.onrender.com"
python .\tools\aries_bench.py --limit 10 --output aries-benchmark-results.json
```

If the model backend requires a bearer token, set it without putting it in source control:

```powershell
$env:ARIES_API_KEY = "YOUR_PROVIDER_KEY"
python .\tools\aries_bench.py --limit 10
```

For a local API, use:

```powershell
python .\tools\aries_bench.py --base-url http://127.0.0.1:8000 --model aries
```

The report includes endpoint health, model-list output, per-case responses, exact-match results, and observed request latency. The default test set is a small ARIES-authored diagnostic; it is **not** an official MMLU, GSM8K, BBH, or leaderboard result.

## Important architecture boundary

This tool removes dependence on third-party *benchmarking frameworks*. It does not turn the current ARIES API into a standalone foundation model. The API code currently forwards chat requests to an upstream OpenAI-compatible model backend, so genuine self-contained inference would additionally require a model architecture, trained weights, a tokenizer, inference/runtime implementation, and sufficient compute. Do not describe upstream-backed inference as fully independent.
