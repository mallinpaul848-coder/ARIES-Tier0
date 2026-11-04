# ARIES Power and Trading Microbenchmark

Run locally in PowerShell:

    python .\tools\aries_power_trade_bench.py --events 100000 --warmup 2000 --output .\reports\aries-power-trading-microbench.json

This compares the deterministic market-event action rule with the same rule plus
ARIES PRISE/digital-root/vortex descriptors. It records per-event software
latency, throughput, action-count parity, process CPU time, and Linux package
energy when a readable RAPL counter exists. Missing energy remains null.

Scope limits: this is a synthetic local microbenchmark, not exchange tick-to-trade
latency, broker/network performance, strategy profitability, GPU power, or
whole-data-center savings. PRISE descriptors are measured as additional
feature-computation overhead and do not alter the trading action. GitHub-hosted
hardware results apply only to that runner.

A genuine HFT evaluation must replay timestamped market data through a
production-like feed handler, risk gate, order gateway, and exchange/simulator
acknowledgement path, measuring p50/p99/p99.9 end-to-end latency, drops, queue
depth, throughput, and risk-control correctness. Power claims require isolated
hardware and calibrated telemetry.


## Native C++20 comparison

The native decision-path microbenchmark is built with CMake:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
    cmake --build build --config Release --parallel
    ctest --test-dir build --output-on-failure
    ./build/aries_power_trade_bench 500000

It compares the baseline action path with the same path plus integer PRISE-style,
digital-root, and vortex descriptors. It checks action-count parity and reports
overall throughput/CPU time plus latency percentiles from a 1-in-256 event
sample. The sample still includes clock-call overhead; throughput is the
stronger aggregate measure. This is a single-process synthetic benchmark, not
a production trading gateway and not a calibrated energy test.

GitHub Actions runs the CMake build, all CTest regression tests, and a 500,000
event benchmark, then uploads the JSON report. Do not interpret a green CI
build as proof of HFT advantage or energy savings; those require controlled
hardware, real feed replay, end-to-end order-path measurements, and calibrated
power telemetry.
