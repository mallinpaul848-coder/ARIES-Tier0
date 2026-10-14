# ARIES-Tier0 benchmark policy

## Permanent microbenchmark

The `ARIES Permanent Microbenchmark` GitHub Actions workflow compiles
`benchmarks/aries_microbenchmark.cpp`, runs a deterministic integer micro-operation,
and archives the report and raw timestamp-counter samples. It runs on relevant
pushes and pull requests, on a weekly schedule, and manually through
**Actions → ARIES Permanent Microbenchmark → Run workflow**.

## What it does and does not establish

- The operation is a tiny deterministic integer expression.
- Each sample includes timestamp-counter and fence overhead.
- The timestamp counter is not guaranteed to equal current core cycles on every
  virtualized runner; do not convert ticks to nanoseconds without a defensible
  calibration for that runner.
- Hosted runners are noisy and may migrate or be interrupted. Compare repeated
  distributions and record the runner/compiler/commit alongside the report.
- This does **not** measure the ARIES model, tokens per second, end-to-end API
  latency, or prove sub-nanosecond execution.
- The existing reported hosted-runner minimum of 20.038 ns and median of
  30.261 ns remain the historical measurements supplied in the benchmark report.
  They must not be overwritten by new measurements.

## Model/API benchmark is separate

The public API benchmark must continue to report endpoint checks, prompt assertions,
and latency separately. Model quality and official leaderboard evaluation require
their own reproducible test suite and must not be inferred from this microbenchmark.

## Retention and permanence

Each successful workflow run uploads a uniquely named artifact with 90-day
retention. Git history permanently stores this benchmark source and workflow,
but GitHub Actions artifacts expire according to the retention setting.
