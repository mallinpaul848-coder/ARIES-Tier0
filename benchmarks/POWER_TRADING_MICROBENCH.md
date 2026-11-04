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
