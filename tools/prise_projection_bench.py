#!/usr/bin/env python3
"""Reproducible microbenchmark for the exact PRISE affine projection primitives.

This measures Python implementation time for bounded affine workloads only.
It is not LLM inference latency, an end-to-end API benchmark, or evidence that
arbitrary 3-SAT is polynomial-time solvable.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from aries_math.prise_projection import (
    eliminate_affine_variables,
    project_affine_interface,
)


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * p / 100 + 0.5)))
    return round(ordered[index], 3)


def summarize(samples: list[float]) -> dict:
    return {
        "samples": len(samples),
        "min_us": round(min(samples), 3),
        "mean_us": round(statistics.mean(samples), 3),
        "p50_us": percentile(samples, 50),
        "p95_us": percentile(samples, 95),
        "max_us": round(max(samples), 3),
        "operations_per_second": round(1_000_000 / statistics.mean(samples), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--output", default="reports/prise-projection-benchmark.json")
    args = parser.parse_args()
    if args.iterations < 10:
        parser.error("--iterations must be at least 10")

    # Deterministic, fixed workload: 28 eliminated bits, 12 boundary bits.
    u_rows = [((i * 7919) ^ (i << 3) ^ 0x15555) & ((1 << 28) - 1) for i in range(36)]
    b_rows = [((i * 3571) ^ (i << 2) ^ 0x2A5) & ((1 << 12) - 1) for i in range(36)]
    rhs = [(i * 7 + 1) & 1 for i in range(36)]
    matrix = [0b101101, 0b110011, 0b011110, 0b111000, 0b000111, 0b100101]
    predicate = lambda value: (value.bit_count() % 3) == 1

    affine_samples: list[float] = []
    interface_samples: list[float] = []
    affine_checksum = 0
    interface_checksum = 0
    for _ in range(args.iterations):
        start = time.perf_counter_ns()
        projected = eliminate_affine_variables(u_rows, b_rows, rhs, 28, 12)
        affine_samples.append((time.perf_counter_ns() - start) / 1000)
        affine_checksum ^= len(projected.equations) + int(projected.inconsistent)

        start = time.perf_counter_ns()
        result = project_affine_interface(matrix, 0b101010, 6, predicate, max_rank=6)
        interface_samples.append((time.perf_counter_ns() - start) / 1000)
        interface_checksum ^= result.enumerated + int(result.satisfiable)

    report = {
        "suite": "ARIES PRISE exact affine projection microbenchmark",
        "suite_type": "project-owned microbenchmark; not an official benchmark",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "processor": platform.processor() or os.getenv("PROCESSOR_IDENTIFIER", "not reported"),
            "cpu_count": os.cpu_count(),
        },
        "workload": {
            "iterations": args.iterations,
            "affine_elimination": {"equations": 36, "eliminated_variables": 28, "boundary_variables": 12},
            "affine_interface": {"input_variables": 6, "output_bits": 6, "enumerated_rank_bound": 6},
        },
        "results": {
            "affine_elimination": summarize(affine_samples),
            "affine_interface_projection": summarize(interface_samples),
        },
        "checksums": {"affine": affine_checksum, "interface": interface_checksum},
        "interpretation": (
            "These timings characterize only the stated exact affine workloads. "
            "They do not measure generative inference, HFT performance, or general SAT."
        ),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved report: {output}")


if __name__ == "__main__":
    main()
