#!/usr/bin/env python3
"""In-process ARIES fast-path microbenchmark.

Compares the deterministic solver with FastPathEngine cold and warm-cache paths.
This isolates routing/cache overhead; it is NOT an HTTP gateway, HFT, model,
or energy benchmark. Run on the same host/build when comparing revisions.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))
from native_reasoner import solve
from latency_engine import FastPathEngine

CASES = [
    ("What is 2 + 2?", "4"),
    ("What is 17 times 19?", "323"),
    ("What is 1000 minus 37?", "963"),
    ("What is 144 divided by 12?", "12"),
]

def pct(values, p):
    ordered = sorted(values)
    if not ordered:
        return None
    idx = min(len(ordered)-1, max(0, int((len(ordered)-1)*p/100 + 0.5)))
    return ordered[idx]

def summarize(samples):
    return {
        "samples": len(samples),
        "min_ns": min(samples) if samples else None,
        "mean_ns": round(statistics.mean(samples), 2) if samples else None,
        "p50_ns": pct(samples, 50),
        "p95_ns": pct(samples, 95),
        "p99_ns": pct(samples, 99),
        "max_ns": max(samples) if samples else None,
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iterations", type=int, default=50000)
    ap.add_argument("--warmup", type=int, default=2000)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--output", default="aries-fastpath-microbench.json")
    args = ap.parse_args()
    if args.iterations < 1 or args.warmup < 0 or not 1 <= args.concurrency <= 64:
        ap.error("iterations >= 1, warmup >= 0, concurrency 1..64 required")

    engine = FastPathEngine(solve, max_entries=128)
    prompts = [CASES[i % len(CASES)][0] for i in range(args.iterations)]
    expected = {prompt: answer for prompt, answer in CASES}

    # Warm interpreter and solver separately; exclude warm-up from reported samples.
    for i in range(args.warmup):
        prompt = CASES[i % len(CASES)][0]
        solve(prompt)
        engine.solve_with_metadata(prompt)

    direct, cold, warm = [], [], []
    cold_engine = FastPathEngine(solve, max_entries=0)
    warm_engine = FastPathEngine(solve, max_entries=128)
    for prompt, answer in CASES:
        got, hit, _ = warm_engine.solve_with_metadata(prompt)
        if got != answer or hit:
            raise SystemExit("FAIL: cache priming correctness/invariant check failed")
    # Run sequential latency samples to avoid mixing scheduler contention into
    # the per-call latency distribution. Concurrency is a separate throughput test.
    for prompt in prompts:
        t = time.perf_counter_ns(); got = solve(prompt); direct.append(time.perf_counter_ns()-t)
        if got != expected[prompt]:
            raise SystemExit("FAIL: direct solver returned an unexpected answer")
        t = time.perf_counter_ns(); got, hit, _ = cold_engine.solve_with_metadata(prompt); cold.append(time.perf_counter_ns()-t)
        if got != expected[prompt] or hit:
            raise SystemExit("FAIL: uncached path correctness/cache invariant failed")
        t = time.perf_counter_ns(); got, hit, _ = warm_engine.solve_with_metadata(prompt); warm.append(time.perf_counter_ns()-t)
        if got != expected[prompt] or not hit:
            raise SystemExit("FAIL: warm cache correctness/cache-hit invariant failed")

    concurrent_engine = FastPathEngine(solve, max_entries=128)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        answers = list(pool.map(concurrent_engine.solve, prompts))
    concurrent_seconds = time.perf_counter() - start
    if answers != [expected[p] for p in prompts]:
        raise SystemExit("FAIL: concurrent correctness check failed")

    report = {
        "suite": "ARIES fast-path in-process microbenchmark v1",
        "classification": "component diagnostic; not end-to-end gateway or HFT qualification",
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "processor": platform.processor(), "python": platform.python_version()},
        "configuration": vars(args),
        "correctness": {"cases": len(prompts), "all_exact": True,
                        "concurrent_all_exact": True},
        "latency": {"direct_solver": summarize(direct),
                    "cache_disabled_engine": summarize(cold),
                    "warm_cache_engine": summarize(warm)},
        "concurrency": {"workers": args.concurrency, "requests": len(prompts),
                        "wall_seconds": round(concurrent_seconds, 6),
                        "completed_per_second": round(len(prompts)/concurrent_seconds, 2)
                        if concurrent_seconds else None,
                        "cache": concurrent_engine.snapshot()},
        "interpretation": (
            "Compare these component timings only on the same host and Python build. "
            "Warm-cache results apply only to repeated identical prompts. HTTP, JSON, "
            "thread scheduling, model inference, CPU energy, and network costs are excluded."
        ),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Saved:", out)

if __name__ == "__main__":
    main()
