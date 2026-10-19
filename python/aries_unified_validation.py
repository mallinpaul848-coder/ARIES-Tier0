"""Unified ARIES API validation harness.

This tests the current FastAPI prototype honestly. The current endpoint is a
template response, not a connected language model; results must not be described
as LLM inference speed or an intelligence score.
Run from the repository root:
    python -m pip install -r requirements.txt
    PYTHONPATH=. python python/aries_unified_validation.py
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
from python.aries_smart_answering import app


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


def run(samples: int = 50) -> dict:
    client = TestClient(app)
    report: dict = {
        "suite": "ARIES unified API validation",
        "python_version": sys.version.split()[0],
        "sample_count": samples,
        "scope": "in-process FastAPI template endpoint; not LLM inference",
        "checks": {},
    }

    response = client.get("/health")
    assert response.status_code == 200, f"/health returned {response.status_code}"
    assert response.json().get("status") == "ok"
    report["checks"]["health"] = "PASS"

    response = client.post("/v1/aries/query", json={"query": ""})
    assert response.status_code == 422, f"empty query returned {response.status_code}"
    report["checks"]["input_validation"] = "PASS"

    latencies: list[float] = []
    for i in range(samples):
        started = time.perf_counter()
        response = client.post(
            "/v1/aries/query",
            json={"query": f"validation sample {i}: what is 17 times 19?"},
        )
        latencies.append((time.perf_counter() - started) * 1000)
        assert response.status_code == 200, f"sample {i} returned {response.status_code}"
        body = response.json()
        assert body.get("status") == "OK"
        metrics = body.get("execution_metrics", {})
        assert metrics.get("llm_invoked") is False, "LLM invocation was misreported"
        assert metrics.get("cpp_core_invoked") is False, "C++ invocation was misreported"

    report["checks"]["query_requests"] = "PASS"
    report["checks"]["backend_disclosure"] = "PASS"
    report["latency_ms"] = {
        "min": round(min(latencies), 3),
        "mean": round(statistics.mean(latencies), 3),
        "median": round(statistics.median(latencies), 3),
        "p95": round(percentile(latencies, 95), 3),
        "max": round(max(latencies), 3),
    }
    report["approx_in_process_requests_per_second"] = round(
        1000 / statistics.mean(latencies), 2
    )
    report["limitations"] = [
        "Does not test a trained language model or generated tokens.",
        "Does not measure internet or deployed-server latency.",
        "Does not establish general intelligence or consciousness.",
        "Does not solve P versus NP or any named open mathematical problem.",
    ]
    return report


if __name__ == "__main__":
    result = run()
    rendered = json.dumps(result, indent=2)
    print(rendered)
    Path("aries-unified-validation-report.json").write_text(rendered + "\n", encoding="utf-8")
