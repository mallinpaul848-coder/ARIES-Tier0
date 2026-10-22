# Independent / Third-Party Alternative Benchmark Protocol

## Goal
Provide a repeatable harness for comparing ARIES with alternative OpenAI-compatible chat endpoints. The harness does not assume an alternative is installed or that API credentials exist. Run only against endpoints you are authorized to test.

## Invocation
Set optional API keys in environment variables; never place keys in CLI arguments, repository files, or reports.

```bash
python tools/aries_alternative_benchmark.py \
  --target aries=https://aries-tier0-api-6qjh.onrender.com,aries-native-ngram \
  --rounds 3 --timeout 60 --output reports/alternative-comparison.json
```

Add a candidate with the same format, for example `--target candidate=http://127.0.0.1:8000,local-model`. If a target requires a key, set `ARIES_BENCH_KEY_<NAME>` with the upper-case target name and non-alphanumeric characters replaced by underscores. Example: `ARIES_BENCH_KEY_CANDIDATE`.

## Protocol
- Same eight prompt cases, request schema, timeout, token cap, and scoring rules for every target.
- Fixed temperature 0; three rounds by default; sequential requests to avoid unintentionally favoring one endpoint with concurrency.
- Record per-case HTTP status, elapsed time, response length, error, and a narrow case-specific correctness flag.
- Summarize successful requests, failures, correctness fraction, mean, P50, P95, P99, max, and requests/second using wall-clock duration.
- The correctness prompts are smoke diagnostics, not a general intelligence benchmark. Extend the test set and use a recognized evaluator for broader quality comparisons.
- Save JSON locally and preserve the target URL, model ID, run time, and tool version. Review output for sensitive data before sharing.

## Interpretation
Network location, model size, quantization, prompt formatting, warm-up, provider queueing, and generation settings affect results. For a buyer comparison, publish raw data and repeat the test on a buyer-controlled host. Do not compare unlike model tasks or present these results as independent certification.
