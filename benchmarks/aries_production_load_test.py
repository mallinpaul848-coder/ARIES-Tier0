#!/usr/bin/env python3
"""Bounded, non-destructive ARIES public API load test.

This is a capacity smoke test, not a substitute for a controlled independent
benchmark. It sends only GET /health and POST /v1/chat/completions requests.
"""
from __future__ import annotations
import concurrent.futures
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ.get("ARIES_PUBLIC_BASE_URL", "https://aries-tier0-api-6qjh.onrender.com").rstrip("/")
REPORT_PATH = Path(os.environ.get("ARIES_LOAD_REPORT", "aries-production-load-report.json"))
REQUESTS_PER_STAGE = int(os.environ.get("ARIES_REQUESTS_PER_STAGE", "20"))
STAGES = [int(x) for x in os.environ.get("ARIES_CONCURRENCY_STAGES", "1,5,10,20").split(",")]
TIMEOUT_SECONDS = 45

def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"User-Agent": "ARIES-Production-Readiness-Test/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
            elapsed = (time.perf_counter() - start) * 1000
            parsed = None
            if body:
                try:
                    parsed = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
            return {"ok": 200 <= response.status < 300, "status": response.status,
                    "latency_ms": round(elapsed, 3), "body": parsed,
                    "error": None if 200 <= response.status < 300 else "non-2xx status"}
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        try:
            body = e.read(1000).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return {"ok": False, "status": e.code, "latency_ms": round(elapsed, 3),
                "body": None, "error": body or str(e)}
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return {"ok": False, "status": None, "latency_ms": round(elapsed, 3),
                "body": None, "error": f"{type(e).__name__}: {e}"}

def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    idx = max(0, min(len(vals)-1, int((len(vals)-1) * p + 0.999999)))
    return round(vals[idx], 3)

def summarize(results: list[dict], concurrency: int) -> dict:
    latencies = [r["latency_ms"] for r in results]
    successes = sum(bool(r["ok"]) and isinstance(r.get("body"), dict)
                    and isinstance(r["body"].get("choices"), list)
                    and len(r["body"]["choices"]) > 0 for r in results)
    started = min((r.get("_start", 0) for r in results), default=0)
    finished = max((r.get("_end", 0) for r in results), default=0)
    wall_seconds = max(0.001, finished - started)
    return {
        "concurrency": concurrency, "requests": len(results),
        "successful_chat_responses": successes,
        "http_or_transport_failures": sum(not r["ok"] for r in results),
        "invalid_chat_payloads": sum(not (isinstance(r.get("body"), dict)
            and isinstance(r["body"].get("choices"), list)
            and len(r["body"]["choices"]) > 0) for r in results if r["ok"]),
        "success_rate_pct": round(100 * successes / len(results), 2) if results else 0,
        "throughput_requests_per_second": round(len(results) / wall_seconds, 3),
        "latency_ms": {
            "min": round(min(latencies), 3) if latencies else None,
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "p50": percentile(latencies, .50), "p95": percentile(latencies, .95),
            "p99": percentile(latencies, .99),
            "max": round(max(latencies), 3) if latencies else None,
        },
        "duration_seconds": round(wall_seconds, 3),
        "errors_sample": [r["error"] for r in results if r.get("error")][:5],
    }

def run_one(index: int, concurrency: int) -> dict:
    result = request("POST", "/v1/chat/completions", {
        "model": "aries-native-ngram",
        "messages": [{"role": "user", "content": f"Load-test request {index}. Reply briefly with a useful response."}],
        "max_tokens": 24, "temperature": 0
    })
    result["_start"] = time.monotonic()
    result["_end"] = result["_start"]
    return result

def main() -> int:
    if REQUESTS_PER_STAGE < 1 or REQUESTS_PER_STAGE > 100:
        print("ARIES_REQUESTS_PER_STAGE must be 1..100", file=sys.stderr)
        return 2
    if not STAGES or any(n < 1 or n > 20 for n in STAGES):
        print("Concurrency stages must be between 1 and 20", file=sys.stderr)
        return 2
    report = {
        "title": "ARIES bounded production API load test",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL, "methodology": {
            "requests_per_stage": REQUESTS_PER_STAGE, "concurrency_stages": STAGES,
            "max_concurrency": max(STAGES), "timeout_seconds": TIMEOUT_SECONDS,
            "endpoints": ["GET /health", "POST /v1/chat/completions"],
            "note": "GitHub-hosted runner test; not an independent laboratory certification. Bounded to avoid stressing a free/shared service."
        },
        "health_check": request("GET", "/health"),
        "stages": [],
    }
    if not report["health_check"]["ok"]:
        print("Health check failed; recording result and stopping load stage.", file=sys.stderr)
        report["overall_pass"] = False
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    all_pass = True
    for concurrency in STAGES:
        stage_results: list[dict] = []
        wall_start = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(run_one, i, concurrency)
                       for i in range(REQUESTS_PER_STAGE)]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                result["_start"] = wall_start
                result["_end"] = time.monotonic()
                stage_results.append(result)
        summary = summarize(stage_results, concurrency)
        report["stages"].append(summary)
        print(json.dumps(summary), flush=True)
        if summary["success_rate_pct"] < 99:
            all_pass = False
    report["overall_pass"] = all_pass
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    print(f"OVERALL_PASS={all_pass}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
