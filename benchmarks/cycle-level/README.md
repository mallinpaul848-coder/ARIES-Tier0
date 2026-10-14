# ARIES Tier 0 cycle-level microbenchmark

This harness measures one deterministic integer transformation inside a timestamp window on **Linux x86-64**. It is for local CPU microbenchmarking, not for measuring the deployed ARIES HTTP API, transformer inference, or a full dispatch workflow.

## Build and run

```bash
cmake -S benchmarks/cycle-level -B build/cycle-benchmark -DCMAKE_BUILD_TYPE=Release
cmake --build build/cycle-benchmark --parallel
./build/cycle-benchmark/aries_benchmark --warmup 200000 --iterations 1000000
```

The program selects the first logical CPU available to the process and attempts to pin the calling thread to it. It reports TSC-rate calibration and raw Min/P50/P99/Max/Mean samples. Root is not normally needed for affinity to CPUs already allowed by the process; containers and hosted CI runners may restrict affinity.

## Important measurement limits

- Each sample includes timestamp and fence overhead. Values are reported raw; no unmeasured overhead is subtracted.
- The TSC rate is a wall-clock calibration of the timestamp counter, not necessarily the instantaneous core clock frequency.
- The operation is a tiny integer expression. Results do not describe the ARIES server, model generation, networking, or end-to-end inference.
- A minimum shown below 1 ns is **not proof** that the operation's true latency is sub-nanosecond. Use repeatable batches, inspect generated assembly, report CPU/compiler/OS details, and compare against an empty-window baseline before drawing that conclusion.
- GitHub-hosted runner results are smoke-test evidence only; runner hardware and scheduling vary. For publishable comparisons, repeat on identified, controlled hardware and archive raw results and environment metadata.

The CI workflow checks that the program builds and emits expected report fields. It does not certify model quality or establish an official leaderboard score.
