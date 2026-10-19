#!/usr/bin/env python3
"""ARIES/MALLIN gateway performance suite; reports measurements with explicit scope.

This measures deterministic Python arithmetic and in-process API overhead only.
It does not measure a trained language model, network latency, or AI quality.
"""
from __future__ import annotations
import concurrent.futures
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
from python.aries_smart_answering import app

ITERATIONS = int(os.getenv("ARIES_BENCH_ITERATIONS", "20000"))
API_SAMPLES = int(os.getenv("ARIES_BENCH_API_SAMPLES", "250"))


def percentile(values: list[float], p: float) -> float:
    vals = sorted(values)
    return vals[min(len(vals)-1, max(0, int((len(vals)-1)*p)))] if vals else 0.0


def summarize(values: list[float]) -> dict:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min_ns": round(min(values), 1),
        "median_ns": round(statistics.median(values), 1),
        "p95_ns": round(percentile(values, .95), 1),
        "p99_ns": round(percentile(values, .99), 1),
        "mean_ns": round(statistics.mean(values), 1),
        "max_ns": round(max(values), 1),
        "operations_per_second_approx": round(1e9 / statistics.mean(values), 2),
    }


def mallin_deterministic_ops(n: int) -> dict:
    # Small deterministic utilities only; these are not a proof engine.
    digital_root_samples = []
    phase8_samples = []
    checksum = 0
    for i in range(n):
        value = i + 1
        t = time.perf_counter_ns()
        digital_root = 0 if value == 0 else 1 + ((value - 1) % 9)
        digital_root_samples.append(time.perf_counter_ns() - t)
        t = time.perf_counter_ns()
        phase = value % 8
        phase8_samples.append(time.perf_counter_ns() - t)
        checksum += digital_root + phase
    return {
        "digital_root": summarize(digital_root_samples),
        "phase8_modulo": summarize(phase8_samples),
        "iterations": n,
        "checksum": checksum,
        "scope": "Python integer/modulo micro-operations; includes timer overhead",
    }


def api_benchmark(n: int) -> dict:
    client = TestClient(app)
    latencies = []
    successful = 0
    for i in range(n):
        started = time.perf_counter_ns()
        response = client.post("/v1/aries/query", json={"query": f"benchmark request {i}"})
        elapsed = time.perf_counter_ns() - started
        latencies.append(elapsed)
        if response.status_code == 200:
            body = response.json()
            metrics = body.get("execution_metrics", {})
            assert metrics.get("llm_invoked") is False
            assert metrics.get("cpp_core_invoked") is False
            successful += 1
    if successful != n:
        raise RuntimeError(f"API requests passed {successful}/{n}")
    return {
        "latency": summarize(latencies),
        "requests_per_second_approx": round(n / (sum(latencies) / 1e9), 2),
        "successful_requests": successful,
        "scope": "in-process FastAPI TestClient; excludes network/deployed server and LLM inference",
    }


def main() -> None:
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200 and health.json().get("status") == "ok"
    invalid = client.post("/v1/aries/query", json={"query": ""})
    assert invalid.status_code == 422

    # Warm-up before timing.
    for i in range(100):
        client.post("/v1/aries/query", json={"query": f"warmup {i}"})

    report = {
        "suite": "ARIES / MALLIN Gateway Full Performance Suite",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": os.getenv("GITHUB_SHA"),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count_logical": os.cpu_count(),
        "checks": {"health": "PASS", "empty_input_rejected": "PASS"},
        "mallin_deterministic_micro_ops": mallin_deterministic_ops(ITERATIONS),
        "api": api_benchmark(API_SAMPLES),
        "interpretation": {
            "sub_nanosecond_claim": "NOT ESTABLISHED",
            "llm_inference_tested": False,
            "tokens_per_second": None,
            "network_latency_tested": False,
            "general_intelligence_score": None,
            "consciousness_or_P_vs_NP_claim": "NOT TESTED",
            "limitations": [
                "Python timer and function-call overhead dominate tiny micro-operations.",
                "API timings are in-process and exclude HTTP network and hosted-server latency.",
                "The current endpoint is a deterministic template and does not invoke an LLM or C++ core.",
                "These metrics are engineering baselines, not AI quality scores or official leaderboard results.",
            ],
        },
    }
    out = Path(os.getenv("ARIES_PERF_REPORT", "aries-gateway-performance.json"))
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
