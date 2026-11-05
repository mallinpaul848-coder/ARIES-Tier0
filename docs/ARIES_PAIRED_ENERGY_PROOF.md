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

## Build a fair ablation baseline

The native gateway now supports `ARIES_DISABLE_FAST_PATH=1`. This disables only
the `FastPathEngine` stage. The known-question route, PRISE math router, local
model, and other gateway code remain enabled. This is an **ablation comparison
of the fast-path stage**, not a comparison of all ARIES software against an
unrelated vendor or an entire data-center workload.

Build one image from the same commit, then start two instances on the same
physical Linux host with identical model files, CPU limits, memory limits,
environment, and power policy. Only the ablation flag and listening port differ:

```bash
docker build -t aries-ablation:local .
docker run -d --name aries-baseline -p 9000:10000 \
  -e PORT=10000 -e ARIES_DISABLE_FAST_PATH=1 \
  aries-ablation:local
docker run -d --name aries-candidate -p 10000:10000 \
  -e PORT=10000 -e ARIES_DISABLE_FAST_PATH=0 \
  aries-ablation:local
```

Check `/performance` on both instances: baseline must report
`fast_path_enabled: false`, candidate must report `true`. Keep the same model
and all other configuration identical. Do not run both instances with
different CPU/memory limits. For a clean result, repeat with longer phases
and alternate test order; record the Docker image digest and host details.

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

- The harness alternates baseline/candidate order between repeats. Both containers remain resident on the same host; only one receives the measured request batch at a time. This controls hardware differences but leaves both services resident, so repeat on a dedicated host and document that limitation.
- Both variants receive the same five deterministic arithmetic prompts in the same mix. The `2+2` known-question shortcut is excluded because it bypasses the FastPathEngine ablation being evaluated.
- It requires every request in both variants to succeed and match its expected numeric answer exactly. Equal counts alone are insufficient.
- It reports gross joules and a matched-duration no-request idle sample for
  each active phase, then reports idle-adjusted joules per successful request.
  The idle sample runs immediately after the active phase for the same wall
  duration, while both containers remain running.
- Negative idle-adjusted energy is preserved as measurement noise and cannot
  support a savings claim.
- It refuses to call savings proven if RAPL is unavailable, idle-adjusted
  energy is non-positive, or successful/exact work differs.

## Interpretation

A lower energy-per-exact-answer result for the candidate would support only this
specific claim: on the measured host and workload, enabling the ARIES fast-path
stage reduced the reported energy domains per completed exact task. It would
not establish general LLM inference efficiency, HFT exchange-path suitability,
or whole-facility energy savings. A result with no difference, mixed domain
direction, or higher energy must be reported as such.

## What this does not prove

RAPL covers only the reported on-chip energy domains; it is not whole-system
wall power. The adjacent idle-window subtraction is an estimate: thermal,
frequency, and background-load drift can affect it. Treat gross and adjusted
readings as separate evidence, repeat the experiment, and use a calibrated
external wall-power meter for a data-center electricity claim. Report meter
accuracy, idle-adjusted and total joules, throughput, latency, and quality. For HFT, additionally measure
production-path tail latency and CPU/NIC/kernel counters. A CI run that merely
compiles this tool is not energy evidence.

Windows does not expose Linux powercap RAPL paths. Use a Linux test host or
capture calibrated external-meter data with a separately validated procedure.
