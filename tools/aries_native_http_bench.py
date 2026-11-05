#!/usr/bin/env python3
"""Bounded HTTP benchmark for the actual ARIES public-native Docker gateway.

Separates deterministic fast-path cache hits, unique arithmetic fast-path
requests, and general local-model inference. CI loopback measurements are not
production HFT or energy evidence.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import platform
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.getenv("ARIES_BASE_URL", "http://127.0.0.1:18080").rstrip("/")
OUT = Path(os.getenv("ARIES_NATIVE_HTTP_REPORT", "reports/aries-native-http-latency.json"))
STAGES = [1, 4, 8, 16]
TIMEOUT = 90


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * p + 0.999999)))
    return round(ordered[index], 3)


def call_chat(prompt: str, model: str, max_tokens: int) -> dict:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + "/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read()
            elapsed = (time.perf_counter_ns() - started) / 1e6
            body = json.loads(raw.decode("utf-8"))
            choices = body.get("choices")
            answer = ""
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                message = choices[0].get("message", {})
                if isinstance(message, dict):
                    answer = message.get("content", "")
            return {
                "ok": response.status == 200 and isinstance(answer, str) and bool(answer.strip()),
                "status": response.status,
                "latency_ms": elapsed,
                "answer": answer,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code,
                "latency_ms": (time.perf_counter_ns() - started) / 1e6,
                "answer": "", "error": str(exc)[:300]}
    except Exception as exc:
        return {"ok": False, "status": None,
                "latency_ms": (time.perf_counter_ns() - started) / 1e6,
                "answer": "", "error": f"{type(exc).__name__}: {exc}"[:300]}


def summarize(results: list[dict], concurrency: int, wall_seconds: float, expected: list[str] | None = None) -> dict:
    latencies = [r["latency_ms"] for r in results]
    return {
        "concurrency": concurrency,
        "requests": len(results),
        "successes": sum(bool(r["ok"]) for r in results),
        "failures": sum(not r["ok"] for r in results),
        "throughput_successful_rps": round(sum(bool(r["ok"]) for r in results) / wall_seconds, 3)
            if wall_seconds else None,
        "latency_ms": {
            "min": round(min(latencies), 3) if latencies else None,
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "p50": percentile(latencies, .50),
            "p95": percentile(latencies, .95),
            "p99": percentile(latencies, .99),
            "p99_9": percentile(latencies, .999),
            "max": round(max(latencies), 3) if latencies else None,
        },
        "exact_matches": sum(" ".join(str(r["answer"]).strip().lower().split()).strip(" .!?") == " ".join(x.strip().lower().split()).strip(" .!?" ) for r, x in zip(results, expected)) if expected else None,
        "exact_match_rate_percent": round(100 * sum(" ".join(str(r["answer"]).strip().lower().split()).strip(" .!?") == " ".join(x.strip().lower().split()).strip(" .!?" ) for r, x in zip(results, expected)) / len(expected), 2) if expected else None,
        "error_samples": [r["error"] for r in results if r.get("error")][:5],\n        "raw_requests": [{"ok": r["ok"], "status": r["status"], "latency_ms": round(r["latency_ms"], 3), "answer": str(r["answer"])[:300], "error": r["error"]} for r in results],
    }


def run_stage(prompts: list[str], model: str, concurrency: int, max_tokens: int, expected: list[str] | None = None) -> dict:
    # Warm-up is intentionally outside the measured batch.
    warm = call_chat(prompts[0], model, max_tokens)
    if not warm["ok"]:
        raise RuntimeError(f"Warm-up failed for {model}: {warm}")
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda p: call_chat(p, model, max_tokens), prompts))
    elapsed = time.perf_counter() - started
    return summarize(results, concurrency, elapsed, expected)


def main() -> int:
    os.makedirs(OUT.parent, exist_ok=True)
    with urllib.request.urlopen(BASE_URL + "/v1/models", timeout=15) as response:
        models = json.loads(response.read().decode("utf-8"))
    model_rows = models.get("data", [])
    if not model_rows:
        raise SystemExit("No model returned by /v1/models")
    model = model_rows[0]["id"]

    workloads = {}
    for concurrency in STAGES:
        # Same prompt each time exercises the repeated-prompt cache-hit route.
        repeated = ["What is 17 times 19?"] * 100
        # Distinct arithmetic inputs force cache misses; the native reasoner is
        # expected to answer simple multiplication exactly.
        unique = [f"What is {31 + i} times 7? Reply with the number only." for i in range(100)]
        unique_expected = [str((31 + i) * 7) for i in range(100)]
        # General questions intentionally route through local model generation.
        general = [
            f"Explain in one short sentence why reliable software gateways matter, variation {i}."
            for i in range(12)
        ]
        workloads.setdefault("repeated_deterministic_prompt", {})[str(concurrency)] = run_stage(
            repeated, model, concurrency, 16, ["323"] * len(repeated))
        workloads.setdefault("unique_deterministic_prompts", {})[str(concurrency)] = run_stage(
            unique, model, concurrency, 16, unique_expected)
        workloads.setdefault("general_local_model_chat", {})[str(concurrency)] = run_stage(
            general, model, concurrency, 24)

    report = {
        "suite": "ARIES current public-native gateway HTTP benchmark",
        "classification": "CI loopback diagnostic; not production HFT qualification or energy measurement",
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "base_url": BASE_URL,
            "model_id": model,
            "concurrency_stages": STAGES,
            "timeout_seconds": TIMEOUT,
        },
        "workloads": workloads,
        "limitations": [
            "Runs against the Docker gateway on a GitHub-hosted runner over loopback.",
            "The local model is SmolLM2-135M; results are not representative of larger production models.",
            "No NIC, exchange network, production co-location, CPU energy, DRAM energy, or wall-power measurement.",
            "Concurrent model requests may serialize in the model wrapper; results expose that behavior but do not imply linear scaling.",
            "CI runner hardware and scheduling vary; compare repeated runs on matched hardware before claiming a regression or gain.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2) + "
", encoding="utf-8")
    print(json.dumps(report, indent=2))
    failures = [
        (workload, stage, result["failures"])
        for workload, stages in workloads.items()
        for stage, result in stages.items()
        if result["failures"]
    ]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
