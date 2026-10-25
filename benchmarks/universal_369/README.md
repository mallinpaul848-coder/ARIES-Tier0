# Universal 3-6-9 Kernel: Benchmark Protocol

This directory contains a portable C microkernel and a repeatable local benchmark for the cyclic 3-6-9 matrix-vector transform used in the MALLIN / ARIES experimental architecture.

## What is implemented

The kernel computes the explicit matrix-vector product

\[
M_{369}x =
\begin{pmatrix}
3 & 6 & 9 \\
9 & 3 & 6 \\
6 & 9 & 3
\end{pmatrix}x.
\]

It uses a fixed-size value type and performs no heap allocation, locks, or dynamic dispatch in the transform itself. That does not imply the entire application is lock-free or allocation-free.

## Build and run (Linux/macOS with a C11 compiler)

```sh
cc -O3 -std=c11 -Wall -Wextra -Wpedantic -Iinclude src/bench_369.c -lm -o bench_369
./bench_369 10000000
```

Run multiple times, on an otherwise idle machine. Record the CPU model, operating system, compiler and version, compiler flags, power mode, and whether turbo/SMT were enabled. For stronger comparisons, pin the process to a CPU core where supported and repeat on each target machine.

## Interpreting the output

- `sample_*_ns` describe elapsed time for a batch of transforms, not one transform.
- `mean_ns_per_transform` and `estimated_transforms_per_second` are derived from batch duration and iteration count. They are estimates affected by timer overhead, loop overhead, compiler optimization, and hardware.
- This harness is a local microbenchmark, not independent third-party validation. For reliable single-operation latency, use a vetted harness with hardware counters, compiler-output inspection, repetitions, and an independent reviewer.
- The proposed 0.84 ns mean, 0.08 ns P99 jitter, and 120M+ operations/s remain hypotheses until reproduced with a documented measurement protocol. Do not advertise them as achieved results based on this harness alone.
- A C kernel benchmark does not measure model inference, end-to-end chat latency, network ingress, or the physical claims about sub-nanometer devices.

## Next validation steps

1. Build and run the harness in CI on a documented runner.
2. Preserve raw JSON/CSV samples alongside environment metadata.
3. Compare a baseline implementation with this kernel under identical conditions.
4. Measure end-to-end API latency separately from kernel throughput.
5. Have an independent party reproduce the instructions and publish machine/compiler details and raw results.
