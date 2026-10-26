# ARIES Reasoning Benchmark

Run the deterministic smoke suite:

```bash
python -m unittest discover -s tests -p "test_reasoning_benchmark.py" -v
```

The benchmark library exposes `run_benchmark(answer_fn, backend_name=...)` so the same test
set can be passed to the current ARIES backend and a candidate backend. Save the return value
with `write_report(report, "reports/aries-reasoning-quality.json")`.

## Comparison rules

- Keep test prompts, system instructions, decoding parameters, hardware, and network conditions
  fixed when comparing backends.
- Report overall and per-category exact-match accuracy, errors, and latency distribution.
- Run repeated trials and disclose sample counts; use a held-out set for final comparisons.
- Do not present this small smoke suite as MMLU, GSM8K, BBH, human evaluation, or third-party validation.
- Do not claim model learning or intelligence improvement until paired baseline/candidate results
  demonstrate a reproducible gain without unacceptable regressions.
