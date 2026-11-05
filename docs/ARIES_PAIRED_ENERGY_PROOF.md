# ARIES Paired Energy Proof

This is the measurement harness for a real same-machine baseline-versus-ARIES
energy comparison. It does not manufacture a savings result.

## Requirements

- Linux host with both implementations running locally on that same host.
- A baseline endpoint and ARIES candidate endpoint, both exposing
  `/v1/chat/completions`.
- Readable Linux powercap energy counters (`/sys/class/powercap/**/energy_uj`)
  for CPU package and, where supported, DRAM energy.
- Same hardware, power policy, model/configuration, and fixed request mix.
- Do not point the URLs at remote cloud services: host RAPL counters would
  measure the wrong machine.

## Example

```bash
python3 tools/aries_power_proof.py \
  --baseline-url http://127.0.0.1:9000 \
  --candidate-url http://127.0.0.1:10000 \
  --requests 600 --repeats 6 --concurrency 1 --warmup 30 \
  --output reports/aries-power-proof.json
```

Run a separate concurrency-appropriate test (for example concurrency 4) after
the serial test. Keep the raw JSON, commit SHA, host details, model checksum,
power policy, and service launch commands together.

## Acceptance rules

- The harness alternates baseline/candidate order between repeats.
- Both variants receive the same six deterministic prompts in the same mix.
- It checks HTTP success and exact output counts before accepting a comparison.
- It reports joules per successful request for each available RAPL domain.
- It refuses to call savings proven if RAPL is unavailable or successful/exact
  work differs.

## What this does not prove

RAPL covers only the reported on-chip energy domains; it is not whole-system
wall power. For a data-center electricity claim, repeat with a calibrated
external wall-power meter and report meter accuracy, idle-adjusted and total
joules, throughput, latency, and quality. For HFT, additionally measure
production-path tail latency and CPU/NIC/kernel counters. A CI run that merely
compiles this tool is not energy evidence.

Windows does not expose Linux powercap RAPL paths. Use a Linux test host or
capture calibrated external-meter data with a separately validated procedure.
