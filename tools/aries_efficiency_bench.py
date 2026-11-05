#!/usr/bin/env python3
"""ARIES controlled latency/energy comparison harness.

Run on the host that executes both services. RAPL measures this host only.
This is a project-owned diagnostic, not an HFT certification or an independent benchmark.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import platform
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

CASES = {
    "hft": [
        ("add_1", "What is 2 + 2? Reply with the number only.", "4"),
        ("multiply_1", "What is 17 times 19? Reply with the number only.", "323"),
        ("subtract_1", "What is 1000 minus 37? Reply with the number only.", "963"),
        ("multiply_2", "What is 12 times 12? Reply with the number only.", "144"),
    ],
    "datacenter": [
        ("add_1", "What is 2 + 2? Reply with the number only.", "4"),
        ("multiply_1", "What is 17 times 19? Reply with the number only.", "323"),
        ("subtract_1", "What is 1000 minus 37? Reply with the number only.", "963"),
        ("multiply_2", "What is 12 times 12? Reply with the number only.", "144"),
        ("divide_1", "What is 144 divided by 12? Reply with the number only.", "12"),
        ("percent_1", "What is 15 percent of 200? Reply with the number only.", "30"),
    ],
}

def percentile(values, pct):
    if not values:
        return None
    vals = sorted(values)
    pos = (len(vals) - 1) * pct / 100
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    return round(vals[lo] + (vals[hi] - vals[lo]) * (pos - lo), 4)

def normalize(value):
    return " ".join(str(value).strip().lower().split()).strip(" .!?\t\r\n")

def rapl_domains():
    root = Path("/sys/class/powercap")
    found = []
    if not root.exists():
        return found
    for energy_file in root.glob("**/energy_uj"):
        domain = energy_file.parent
        try:
            name = (domain / "name").read_text().strip()
            maximum = int((domain / "max_energy_range_uj").read_text().strip())
            found.append({"name": name, "energy": energy_file, "maximum": maximum})
        except (OSError, ValueError):
            continue
    return found

def read_energy(domains):
    readings = {}
    for item in domains:
        try:
            readings[item["name"]] = int(item["energy"].read_text().strip())
        except (OSError, ValueError):
            readings[item["name"]] = None
    return readings

def energy_delta(before, after, domains):
    result = {}
    for item in domains:
        name = item["name"]
        a, b = before.get(name), after.get(name)
        if a is None or b is None:
            result[name] = None
            continue
        delta = b - a
        if delta < 0:
            delta += item["maximum"]
        result[name] = round(delta / 1_000_000, 6)
    return result

def is_loopback(url):
    host = urllib.parse.urlparse(url).hostname or ""
    return host in {"127.0.0.1", "::1", "localhost"}

def post_chat(base_url, prompt, timeout):
    root = base_url.rstrip("/")
    if not root.endswith("/v1"):
        root += "/v1"
    payload = {
        "model": "auto",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 32,
    }
    req = urllib.request.Request(
        root + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    started = time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = response.status
        obj = json.loads(raw)
        choices = obj.get("choices", [])
        answer = choices[0].get("message", {}).get("content", "") if choices else ""
        return {
            "latency_ms": (time.perf_counter_ns() - started) / 1e6,
            "status": status,
            "answer": answer,
            "error": None,
        }
    except urllib.error.HTTPError as exc:
        return {
            "latency_ms": (time.perf_counter_ns() - started) / 1e6,
            "status": exc.code,
            "answer": "",
            "error": exc.read().decode("utf-8", errors="replace")[:500],
        }
    except Exception as exc:
        return {
            "latency_ms": (time.perf_counter_ns() - started) / 1e6,
            "status": None,
            "answer": "",
            "error": type(exc).__name__ + ": " + str(exc),
        }

def run_phase(label, url, cases, requests_count, concurrency, timeout, warmup):
    tasks = [cases[i % len(cases)] for i in range(requests_count)]
    started_wall = time.perf_counter()
    started_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    if concurrency == 1:
        results = [post_chat(url, case[1], timeout) for case in tasks]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(post_chat, url, case[1], timeout) for case in tasks]
            results = [future.result() for future in futures]
    elapsed = time.perf_counter() - started_wall
    ended_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    latencies = [r["latency_ms"] for r in results]
    successful = [r for r in results if r["status"] == 200 and r["answer"].strip()]
    exact = sum(
        normalize(r["answer"]) == normalize(tasks[i][2])
        for i, r in enumerate(results)
        if r["status"] == 200 and r["answer"].strip()
    )
    return {
        "label": label,
        "target": url,
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "requests": requests_count,
        "warmup_requests": warmup,
        "concurrency": concurrency,
        "wall_seconds": round(elapsed, 6),
        "throughput_successful_requests_per_second": round(len(successful) / elapsed, 4) if elapsed else None,
        "http_200_nonempty": len(successful),
        "errors_or_empty": requests_count - len(successful),
        "exact_match_count": exact,
        "exact_match_rate_percent": round(100 * exact / requests_count, 3) if requests_count else None,
        "latency_ms": {
            "min": round(min(latencies), 4) if latencies else None,
            "mean": round(statistics.mean(latencies), 4) if latencies else None,
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
            "p99_9": percentile(latencies, 99.9),
            "max": round(max(latencies), 4) if latencies else None,
        },
        "raw_requests": results,
    }

def main():
    parser = argparse.ArgumentParser(description="Compare ARIES latency and host energy against a same-host baseline.")
    parser.add_argument("--candidate-url", required=True, help="ARIES candidate base URL, e.g. http://127.0.0.1:10000")
    parser.add_argument("--baseline-url", help="Unoptimized baseline service URL on the same host")
    parser.add_argument("--profile", choices=sorted(CASES), default="datacenter")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--output", default="aries-efficiency-evidence.json")
    parser.add_argument("--no-rapl", action="store_true", help="Do not read Linux powercap energy counters")
    args = parser.parse_args()
    if args.requests < 1 or args.warmup < 0 or not 1 <= args.concurrency <= 64:
        parser.error("requests must be >=1, warmup >=0, concurrency 1..64")
    if args.baseline_url and args.baseline_url.rstrip("/") == args.candidate_url.rstrip("/"):
        parser.error("baseline and candidate URLs must differ")
    domains = [] if args.no_rapl else rapl_domains()
    energy_scope = "server_host_rapl" if domains and is_loopback(args.candidate_url) and (not args.baseline_url or is_loopback(args.baseline_url)) else "unavailable_or_not_server_local"
    if domains and energy_scope != "server_host_rapl":
        domains = []
    cases = CASES[args.profile]
    report = {
        "suite": "ARIES controlled efficiency diagnostic v1",
        "classification": "project-owned diagnostic; not HFT certification or independent benchmark",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "profile": args.profile,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "method": {
            "requests": args.requests,
            "warmup": args.warmup,
            "concurrency": args.concurrency,
            "timeout_seconds": args.timeout,
            "case_ids": [case[0] for case in cases],
            "energy_scope": energy_scope,
            "energy_domains": [d["name"] for d in domains],
            "warning": "RAPL values cover this host's supported package/DRAM domains only, not wall power or remote servers. No RAPL means energy is unavailable, not zero.",
        },
        "phases": [],
    }
    targets = []
    if args.baseline_url:
        targets.append(("baseline", args.baseline_url))
    targets.append(("candidate", args.candidate_url))
    # Warm both endpoints before the measured interval; randomize order to reduce fixed-order drift bias.
    for label, url in targets:
        for i in range(args.warmup):
            post_chat(url, cases[i % len(cases)][1], args.timeout)
    import random
    random.shuffle(targets)
    for label, url in targets:
        before = read_energy(domains)
        phase = run_phase(label, url, cases, args.requests, args.concurrency, args.timeout, 0)
        phase["warmup_requests"] = args.warmup
        after = read_energy(domains)
        phase["rapl_energy_joules"] = energy_delta(before, after, domains) if domains else None
        phase["energy_joules_per_successful_request"] = {}
        if domains and phase["http_200_nonempty"]:
            phase["energy_joules_per_successful_request"] = {
                name: round(joules / phase["http_200_nonempty"], 9) if joules is not None else None
                for name, joules in phase["rapl_energy_joules"].items()
            }
        report["phases"].append(phase)
    if args.baseline_url:
        base = next(p for p in report["phases"] if p["label"] == "baseline")
        cand = next(p for p in report["phases"] if p["label"] == "candidate")
        report["comparison"] = {
            "baseline_label": base["label"],
            "candidate_label": cand["label"],
            "same_request_count": base["requests"] == cand["requests"],
            "latency_p50_change_percent": (
                round(100 * (cand["latency_ms"]["p50"] - base["latency_ms"]["p50"]) / base["latency_ms"]["p50"], 3)
                if base["latency_ms"]["p50"] else None
            ),
            "latency_p99_change_percent": (
                round(100 * (cand["latency_ms"]["p99"] - base["latency_ms"]["p99"]) / base["latency_ms"]["p99"], 3)
                if base["latency_ms"]["p99"] else None
            ),
            "energy_per_successful_request_change_percent": {
                name: round(100 * (cand["energy_joules_per_successful_request"].get(name) - base["energy_joules_per_successful_request"].get(name)) / base["energy_joules_per_successful_request"][name], 3)
                for name in base["energy_joules_per_successful_request"]
                if base["energy_joules_per_successful_request"].get(name) not in (None, 0)
                and cand["energy_joules_per_successful_request"].get(name) is not None
            },
            "claim_gate": "Only comparable same-host runs with equal successful work and measured energy can support an energy-savings claim. Negative change means candidate used less energy; positive means more.",
        }
    report["claim_status"] = {
        "energy_savings_proven": False,
        "reason": "This file is a measurement harness. A result must be generated on the target host with a valid baseline, candidate, and supported energy meter/counter.",
        "scope_limit": "Default prompts exercise deterministic arithmetic/task routing only. They do not establish savings for general LLM inference, exchange-grade HFT, or an entire data center.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "phases"}, indent=2))
    for phase in report["phases"]:
        print(json.dumps({k: v for k, v in phase.items() if k != "raw_requests"}, indent=2))
    print("Saved raw evidence:", output)

if __name__ == "__main__":
    main()
