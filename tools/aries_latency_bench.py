#!/usr/bin/env python3
"""Benchmark ARIES deterministic routing in the current process.

This reports measured elapsed nanoseconds per call on the current machine. It
does not measure public network latency, full language-model quality, CPU cycles,
or certify sub-nanosecond execution. A timing unit is not the same thing as clock
resolution.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from software.latency_engine import FastPathEngine
from software.native_reasoner import solve


def run_benchmark(name, fn, iterations, prompt_factory):
    # Warm up interpreter, imports, and code paths before the timed section.
    for i in range(min(500, max(20, iterations // 10))):
        fn(prompt_factory(i))
    started = time.perf_counter_ns()
    for i in range(iterations):
        fn(prompt_factory(i + 100_000))
    elapsed = time.perf_counter_ns() - started
    return {
        "name": name,
        "iterations": iterations,
        "total_elapsed_ns": elapsed,
        "mean_ns_per_call": round(elapsed / iterations, 2),
        "calls_per_second": round(iterations * 1_000_000_000 / elapsed, 2) if elapsed else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--output", default="aries-latency-benchmark.json")
    parser.add_argument("--cache-size", type=int, default=50_000)
    args = parser.parse_args()
    if args.iterations < 100 or args.iterations > 2_000_000:
        parser.error("--iterations must be between 100 and 2000000")
    if args.cache_size < 0:
        parser.error("--cache-size must be non-negative")

    # Vary arithmetic operands to avoid accidentally timing a pre-warmed repeated result.
    direct = lambda prompt: solve(prompt)
    uncached_engine = FastPathEngine(solve, max_entries=0)
    cold_engine = FastPathEngine(solve, max_entries=max(args.cache_size, args.iterations + 1000))
    hot_engine = FastPathEngine(solve, max_entries=1)
    hot_prompt = "What is 17 * 19? Reply with the number only."
    hot_engine.solve(hot_prompt)

    results = [
        run_benchmark(
            "direct_deterministic_reasoner_no_memoization",
            direct, args.iterations,
            lambda i: f"What is {i % 900000 + 101} + 7? Reply with the number only.",
        ),
        run_benchmark(
            "fast_path_cache_disabled",
            uncached_engine.solve, args.iterations,
            lambda i: f"What is {i % 900000 + 101} + 7? Reply with the number only.",
        ),
        run_benchmark(
            "fast_path_unique_prompt_cache_miss",
            cold_engine.solve, args.iterations,
            lambda i: f"What is {i % 900000 + 101} + 7? Reply with the number only.",
        ),
        run_benchmark(
            "fast_path_repeated_prompt_cache_hit",
            hot_engine.solve, args.iterations,
            lambda _i: hot_prompt,
        ),
    ]
    clock = time.get_clock_info("perf_counter")
    report = {
        "project": "ARIES Tier0",
        "benchmark_type": "local in-process deterministic fast-path microbenchmark",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "machine": platform.machine(),
            "processor_label": platform.processor() or "not reported by operating system",
            "logical_cpu_count": __import__("os").cpu_count(),
            "timer": clock.implementation,
            "timer_nominal_resolution_ns": max(1, round(clock.resolution * 1_000_000_000)),
            "timer_monotonic": clock.monotonic,
        },
        "results": results,
        "cache_stats": {
            "uncached": uncached_engine.snapshot(),
            "unique_prompt": cold_engine.snapshot(),
            "repeated_prompt": hot_engine.snapshot(),
        },
        "sub_nanosecond_latency_verified": False,
        "interpretation": (
            "Results are specific to this machine, Python build, OS, and run. "
            "The repeated-prompt case measures cache lookup plus Python overhead, not AI model inference. "
            "These measurements do not demonstrate sub-nanosecond execution."
        ),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved report to {output.resolve()}")


if __name__ == "__main__":
    main()
