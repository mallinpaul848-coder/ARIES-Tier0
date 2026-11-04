#!/usr/bin/env python3
"""ARIES local power/market-event microbenchmark.

Measures a synthetic, deterministic market-data decision pipeline. This is NOT
exchange tick-to-trade latency, a trading strategy, or evidence of profitability.
Package energy is reported only when Linux RAPL telemetry is readable.
"""
from __future__ import annotations
import argparse, json, os, platform, statistics, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from aries_math.prise_research_engine import DigitalRootSystem, PRISEProfile, vortex369
    PRISE_AVAILABLE = True
except Exception:
    DigitalRootSystem = PRISEProfile = None
    vortex369 = None
    PRISE_AVAILABLE = False

def percentile(values, p):
    if not values: return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p / 100.0
    lo, hi = int(pos), min(int(pos) + 1, len(ordered) - 1)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo), 3)

def rapl_energy_counter():
    for root in (Path("/sys/class/powercap"), Path("/sys/devices/virtual/powercap")):
        if not root.exists(): continue
        for energy in root.glob("**/energy_uj"):
            try:
                name_file = energy.parent / "name"
                name = name_file.read_text().strip().lower() if name_file.exists() else ""
                if "package" not in name and "pkg" not in name and energy.parent.name not in {"intel-rapl:0", "amd-rapl:0"}:
                    continue
                maximum_file = energy.parent / "max_energy_range_uj"
                maximum = int(maximum_file.read_text().strip()) if maximum_file.exists() else 0
                return energy, maximum
            except (OSError, ValueError):
                continue
    return None

def read_energy(sensor):
    if sensor is None: return None
    try: return int(sensor[0].read_text().strip())
    except (OSError, ValueError): return None

def energy_delta_uj(before, after, maximum):
    if before is None or after is None: return None
    if after >= before: return after - before
    return (maximum - before) + after if maximum > 0 else None

def make_event(i):
    return (((i * 37) % 401) - 200, ((i * 19) % 2001) - 1000, (i * 13) % 101, 1 + ((i * 29) % 10000))

def baseline_decision(event):
    delta, imbalance, risk, size = event
    if risk >= 90: return 0
    if delta > 12 and imbalance > 150: return 1
    if delta < -12 and imbalance < -150: return -1
    return 0

def aries_feature_decision(event):
    delta, imbalance, risk, size = event
    action = baseline_decision(event)
    if PRISE_AVAILABLE:
        profile = PRISEProfile(priority=min(size, 10000) / 10000.0, risk=risk / 100.0,
            impact=min(abs(delta), 200) / 200.0, systemic=min(abs(imbalance), 1000) / 1000.0,
            emergent=((size % 9) + 1) / 9.0)
        score_bucket = int(profile.score() * 1000)
        root = DigitalRootSystem.compute(abs(delta) + abs(imbalance) + risk + size)
        vortex = vortex369(abs(delta) + risk + 1)
    else:
        score_bucket = int((size + abs(delta) + abs(imbalance)) / (1 + risk) * 1000)
        root, vortex = (abs(delta) + abs(imbalance) + risk + size) % 9, (abs(delta) + risk) % 6
    return action, score_bucket, root * 10 + vortex

def run_variant(events, use_aries):
    samples, counts, checksum = [], {1: 0, -1: 0, 0: 0}, 0
    cpu_start, wall_start = time.process_time_ns(), time.perf_counter_ns()
    for event in events:
        start = time.perf_counter_ns()
        if use_aries:
            action, score_bucket, descriptor = aries_feature_decision(event)
            checksum = (checksum + score_bucket + descriptor) & 0xFFFFFFFF
        else:
            action = baseline_decision(event)
            checksum = (checksum + sum(event)) & 0xFFFFFFFF
        samples.append(float(time.perf_counter_ns() - start))
        counts[action] += 1
    wall_ns, cpu_ns = time.perf_counter_ns() - wall_start, time.process_time_ns() - cpu_start
    return {
        "events": len(events), "wall_time_ms": round(wall_ns / 1e6, 3),
        "process_cpu_time_ms": round(cpu_ns / 1e6, 3),
        "events_per_second": round(len(events) / (wall_ns / 1e9), 3) if wall_ns else None,
        "event_latency_ns": {"min": round(min(samples), 3), "mean": round(statistics.fmean(samples), 3),
            "p50": percentile(samples, 50), "p95": percentile(samples, 95),
            "p99": percentile(samples, 99), "max": round(max(samples), 3)},
        "action_counts": {"buy": counts[1], "sell": counts[-1], "reject_or_hold": counts[0]},
        "checksum": checksum
    }

def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True,
            text=True, timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError): return None

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events", type=int, default=100000)
    p.add_argument("--warmup", type=int, default=2000)
    p.add_argument("--output", default="reports/aries-power-trading-microbench.json")
    a = p.parse_args()
    if not 1 <= a.events <= 5000000: p.error("--events must be between 1 and 5000000")
    if not 0 <= a.warmup <= 100000: p.error("--warmup must be between 0 and 100000")
    for i in range(a.warmup):
        e = make_event(i); baseline_decision(e); aries_feature_decision(e)
    events = [make_event(i + a.warmup) for i in range(a.events)]
    sensor = rapl_energy_counter()
    maximum = sensor[1] if sensor else 0
    e0 = read_energy(sensor)
    baseline = run_variant(events, False)
    e1 = read_energy(sensor)
    aries = run_variant(events, True)
    e2 = read_energy(sensor)
    b_uj, a_uj = energy_delta_uj(e0, e1, maximum), energy_delta_uj(e1, e2, maximum)
    parity = baseline["action_counts"] == aries["action_counts"]
    report = {
        "schema_version": "1.0", "suite": "ARIES Power and Market-Event Microbenchmark",
        "suite_type": "local synthetic software microbenchmark; not HFT exchange certification",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.getenv("GITHUB_SHA") or git_commit(),
        "hardware": {"platform": platform.platform(), "processor": platform.processor() or None,
            "machine": platform.machine(), "logical_cpu_count": os.cpu_count(), "python": platform.python_version()},
        "configuration": {"events": a.events, "warmup_events": a.warmup, "single_process": True},
        "comparison": {"baseline": baseline, "aries_prise_feature_path": aries, "action_counts_match": parity,
            "latency_change_percent": round((aries["event_latency_ns"]["mean"] / baseline["event_latency_ns"]["mean"] - 1) * 100, 3) if baseline["event_latency_ns"]["mean"] else None,
            "throughput_change_percent": round((aries["events_per_second"] / baseline["events_per_second"] - 1) * 100, 3) if baseline["events_per_second"] else None},
        "energy": {"sensor": str(sensor[0]) if sensor else None,
            "scope": "Linux package energy counter; includes unrelated activity during each measured section",
            "baseline_package_energy_joules": round(b_uj / 1e6, 6) if b_uj is not None else None,
            "aries_package_energy_joules": round(a_uj / 1e6, 6) if a_uj is not None else None,
            "baseline_joules_per_event": round(b_uj / 1e6 / a.events, 12) if b_uj is not None else None,
            "aries_joules_per_event": round(a_uj / 1e6 / a.events, 12) if a_uj is not None else None,
            "measurement_available": b_uj is not None and a_uj is not None,
            "note": "Null means no supported readable telemetry; never interpret missing energy as zero."},
        "interpretation_limits": [
            "Synthetic event decisions only; no exchange feed, network, broker, order routing, fills, or P&L.",
            "Per-event software timing is not tick-to-trade latency and cannot establish HFT competitiveness.",
            "PRISE descriptors are additional features and deliberately do not alter the baseline action rule.",
            "Results apply only to this workload, machine, Python runtime, and run.",
            "Package energy telemetry is coarse and includes unrelated system activity; isolate hardware for procurement-grade power claims.",
            "This does not measure GPU energy or whole data-center PUE."
        ]
    }
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "baseline_events_per_second": baseline["events_per_second"],
        "aries_feature_events_per_second": aries["events_per_second"],
        "baseline_mean_event_ns": baseline["event_latency_ns"]["mean"],
        "aries_feature_mean_event_ns": aries["event_latency_ns"]["mean"],
        "action_counts_match": parity, "energy_measurement_available": report["energy"]["measurement_available"],
        "baseline_joules_per_event": report["energy"]["baseline_joules_per_event"],
        "aries_joules_per_event": report["energy"]["aries_joules_per_event"]}, indent=2))
    return 0 if parity else 2

if __name__ == "__main__":
    raise SystemExit(main())
