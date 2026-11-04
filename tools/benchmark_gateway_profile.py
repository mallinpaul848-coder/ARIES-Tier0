#!/usr/bin/env python3
"""Run paired Mallin–PRISE full-vs-route-only profiling benchmarks.

This measures the request profiler only. It excludes HTTP, queues, model
prefill, and token generation; it is not an end-to-end inference benchmark.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
import platform
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aries_math.gateway_optimizer import analyze_gateway_request


DEFAULT_PROMPTS = [
    "2 + 2",
    "Summarize this paragraph in one sentence.",
    "Optimize ARIES gateway latency and benchmark performance.",
    "Compare two approaches and explain the trade-offs.",
    "Research the PRISE framework and derive a proof outline.",
    "Review this production security configuration for risk.",
    "Write a Python function that validates structured input.",
    "Explain how a bounded queue prevents overload.",
]


def summarize(samples: list[int]) -> dict:
    ordered = sorted(samples)

    def percentile(p: float) -> float:
        pos = (len(ordered) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        fraction = pos - lo
        return ordered[lo] * (1.0 - fraction) + ordered[hi] * fraction

    return {
        "sample_count": len(samples),
        "min_ns": min(samples),
        "mean_ns": sum(samples) / len(samples),
        "p50_ns": percentile(0.50),
        "p95_ns": percentile(0.95),
        "p99_ns": percentile(0.99),
        "max_ns": max(samples),
    }


def paired_benchmark(prompts: list[str], repeats: int) -> dict:
    if repeats < 1:
        raise ValueError("--repeats must be >= 1")
    if not prompts:
        raise ValueError("prompt corpus must not be empty")

    # Warm both modes before recording.
    for prompt in prompts:
        analyze_gateway_request(prompt, include_diagnostics=True)
        analyze_gateway_request(prompt, include_diagnostics=False)

    full_samples: list[int] = []
    route_samples: list[int] = []
    # Alternate measurement order to reduce systematic order/thermal bias.
    for repeat in range(repeats):
        for prompt in prompts:
            modes = (True, False) if repeat % 2 == 0 else (False, True)
            for full_mode in modes:
                started = time.perf_counter_ns()
                analyze_gateway_request(prompt, include_diagnostics=full_mode)
                elapsed = max(0, time.perf_counter_ns() - started)
                (full_samples if full_mode else route_samples).append(elapsed)

    full = summarize(full_samples)
    route = summarize(route_samples)
    return {
        "benchmark": "mallin_prise_gateway_profile_paired_modes",
        "scope": (
            "complete analyze_gateway_request call; full mode includes harmonic "
            "descriptors and SHA-256; route-only omits non-routing diagnostics; "
            "both exclude HTTP, queueing, model prefill, and generation"
        ),
        "prompt_count": len(prompts),
        "repeats": repeats,
        "warmup_passes": 1,
        "full_diagnostics": full,
        "route_only": route,
        "p50_reduction_percent": round(
            100.0 * (full["p50_ns"] - route["p50_ns"]) / full["p50_ns"], 3
        ) if full["p50_ns"] else 0.0,
        "p95_reduction_percent": round(
            100.0 * (full["p95_ns"] - route["p95_ns"]) / full["p95_ns"], 3
        ) if full["p95_ns"] else 0.0,
        "samples_ns": {
            "full_diagnostics": full_samples,
            "route_only": route_samples,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--prompts-file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.prompts_file:
        prompts = [
            line.strip()
            for line in args.prompts_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    else:
        prompts = DEFAULT_PROMPTS

    report = paired_benchmark(prompts, args.repeats)
    corpus_bytes = json.dumps(
        prompts, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    report["prompt_corpus_sha256"] = sha256(corpus_bytes).hexdigest()
    report["environment"] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or os.environ.get(
            "PROCESSOR_IDENTIFIER", "unknown"
        ),
        "cpu_count": os.cpu_count(),
        "note": (
            "Record exact commit SHA and power/thermal conditions. "
            "Paired profiler timings are not end-to-end inference timings."
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
