#!/usr/bin/env python3
"""ARIES endpoint evidence benchmark.

Standard-library only. Measures end-to-end HTTP completion latency, not model-only
compute time. Streaming TTFT/token throughput are deliberately not inferred from
non-streaming responses. This is a project diagnostic, not an official benchmark.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def percentile_nearest_rank(values: list[float], percentile: float) -> float | None:
    """Nearest-rank percentile: sorted[ceil(p*n)-1], with p in [0, 100]."""
    if not values:
        return None
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile / 100.0) * len(ordered)))
    return round(ordered[rank - 1], 3)


def git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True,
            text=True, timeout=2,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return os.getenv("GITHUB_SHA") or os.getenv("GIT_COMMIT") or None


def memory_total_bytes() -> int | None:
    try:
        with open("/proc/meminfo", encoding="ascii") as stream:
            for line in stream:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def http_json(url: str, payload: dict | None, timeout: float,
              api_key: str | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    request = urllib.request.Request(
        url, data=body, headers=headers, method="GET" if body is None else "POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        parsed = json.loads(raw) if raw else {}
        if not isinstance(parsed, dict):
            raise ValueError("API returned a non-object JSON response")
        return response.status, parsed


def timed_get(url: str, timeout: float, api_key: str | None) -> dict:
    started = time.perf_counter_ns()
    try:
        status, payload = http_json(url, None, timeout, api_key)
        return {"http_status": status,
                "latency_ms": round((time.perf_counter_ns() - started) / 1e6, 3),
                "response": payload}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code,
                "latency_ms": round((time.perf_counter_ns() - started) / 1e6, 3),
                "error": exc.read().decode("utf-8", errors="replace")[:1000]}
    except Exception as exc:  # retain failure evidence instead of dropping the sample
        return {"latency_ms": round((time.perf_counter_ns() - started) / 1e6, 3),
                "error": f"{type(exc).__name__}: {exc}"}


def run_request(index: int, api_url: str, model: str, prompt: str,
                max_tokens: int, timeout: float, api_key: str | None) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
    }
    started = time.perf_counter_ns()
    try:
        status, response = http_json(api_url, payload, timeout, api_key)
        elapsed = (time.perf_counter_ns() - started) / 1e6
        choices = response.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content") if isinstance(message, dict) else None
        usage = response.get("usage") or {}
        completion_tokens = usage.get("completion_tokens")
        return {
            "request_index": index, "http_status": status,
            "latency_ms": round(elapsed, 3),
            "success": status == 200 and isinstance(content, str) and bool(content.strip()),
            "response_chars": len(content) if isinstance(content, str) else None,
            "completion_tokens_reported_by_server": completion_tokens,
            "tokens_per_second_reported_usage": (
                round(completion_tokens / (elapsed / 1000), 3)
                if isinstance(completion_tokens, (int, float)) and elapsed > 0 else None
            ),
            "response_preview": content[:240] if isinstance(content, str) else None,
        }
    except urllib.error.HTTPError as exc:
        elapsed = (time.perf_counter_ns() - started) / 1e6
        return {"request_index": index, "http_status": exc.code,
                "latency_ms": round(elapsed, 3), "success": False,
                "error": exc.read().decode("utf-8", errors="replace")[:1000]}
    except Exception as exc:
        elapsed = (time.perf_counter_ns() - started) / 1e6
        return {"request_index": index, "latency_ms": round(elapsed, 3),
                "success": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "http://127.0.0.1:10000"))
    parser.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"))
    parser.add_argument("--requests", type=int, default=30)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--prompt", default="Explain what causes a rainbow in three concise sentences.")
    parser.add_argument("--output", default="reports/aries-endpoint-evidence.json")
    parser.add_argument("--api-key", default=os.getenv("ARIES_API_KEY"))
    args = parser.parse_args()
    if args.requests < 1 or args.requests > 10000:
        parser.error("--requests must be between 1 and 10000")
    if args.concurrency < 1 or args.concurrency > 32:
        parser.error("--concurrency must be between 1 and 32")
    if args.warmup < 0 or args.warmup > 100:
        parser.error("--warmup must be between 0 and 100")
    if args.max_tokens < 1 or args.max_tokens > 1024:
        parser.error("--max-tokens must be between 1 and 1024")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    base = args.base_url.rstrip("/")
    api_root = base if base.endswith("/v1") else base + "/v1"
    report = {
        "schema_version": "1.0",
        "suite": "ARIES Endpoint Evidence Benchmark",
        "suite_type": "project-owned diagnostic; not independent certification",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "target": base,
        "hardware_profile": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
            "logical_cpu_count": os.cpu_count(),
            "memory_total_bytes": memory_total_bytes(),
            "python_version": platform.python_version(),
        },
        "configuration": {
            "model_requested": args.model,
            "requests": args.requests,
            "concurrency": args.concurrency,
            "warmup_requests": args.warmup,
            "max_tokens": args.max_tokens,
            "timeout_seconds": args.timeout,
            "temperature": 0,
            "stream": False,
            "prompt": args.prompt,
        },
        "measurement_scope": {
            "latency": "Client-observed end-to-end HTTP round-trip, including network, queueing, server, and response transfer.",
            "ttft_ms": None,
            "ttft_note": "Not measured: this run uses non-streaming responses.",
            "model_only_compute_latency_ms": None,
            "tokens_per_second": None,
            "tokens_per_second_note": "Only reported if the API supplies completion_tokens; derived rate still includes full HTTP latency and is not isolated decode speed.",
            "energy_joules_per_request": None,
            "allocation_counts": None,
        },
    }

    report["health"] = timed_get(base + "/health", args.timeout, args.api_key)
    models_result = timed_get(api_root + "/models", args.timeout, args.api_key)
    report["models_endpoint"] = models_result
    model_data = (models_result.get("response") or {}).get("data", [])
    advertised_model = model_data[0].get("id") if model_data and isinstance(model_data[0], dict) else None
    model = advertised_model if args.model == "auto" else args.model
    report["selected_model"] = model

    if not model:
        report["fatal_error"] = "No model ID was supplied or advertised by /v1/models."
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2

    # Warm-up calls are recorded separately and excluded from latency statistics.
    report["warmup_results"] = [
        run_request(i + 1, api_root + "/chat/completions", model, args.prompt,
                    args.max_tokens, args.timeout, args.api_key)
        for i in range(args.warmup)
    ]

    started = time.perf_counter()
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(run_request, i + 1, api_root + "/chat/completions",
                            model, args.prompt, args.max_tokens, args.timeout, args.api_key)
            for i in range(args.requests)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    wall_seconds = time.perf_counter() - started
    results.sort(key=lambda item: item["request_index"])
    report["results"] = results

    successful = [item for item in results if item.get("success")]
    latencies = [item["latency_ms"] for item in results if "latency_ms" in item]
    success_latencies = [item["latency_ms"] for item in successful]
    usage_rates = [item["tokens_per_second_reported_usage"] for item in successful
                   if item.get("tokens_per_second_reported_usage") is not None]
    report["summary"] = {
        "requests_attempted": len(results),
        "successful_responses": len(successful),
        "failed_responses": len(results) - len(successful),
        "success_rate_percent": round(100 * len(successful) / len(results), 2),
        "wall_clock_seconds": round(wall_seconds, 3),
        "successful_requests_per_second": round(len(successful) / wall_seconds, 3) if wall_seconds else None,
        "latency_sample_count_all_http_attempts": len(latencies),
        "latency_all_attempts_ms": {
            "min": round(min(latencies), 3) if latencies else None,
            "mean": round(sum(latencies) / len(latencies), 3) if latencies else None,
            "p50_nearest_rank": percentile_nearest_rank(latencies, 50),
            "p95_nearest_rank": percentile_nearest_rank(latencies, 95),
            "p99_nearest_rank": percentile_nearest_rank(latencies, 99),
            "max": round(max(latencies), 3) if latencies else None,
        },
        "latency_successful_responses_ms": {
            "p50_nearest_rank": percentile_nearest_rank(success_latencies, 50),
            "p95_nearest_rank": percentile_nearest_rank(success_latencies, 95),
            "p99_nearest_rank": percentile_nearest_rank(success_latencies, 99),
        },
        "server_usage_derived_tokens_per_second_sample_count": len(usage_rates),
        "server_usage_derived_tokens_per_second_mean": (
            round(sum(usage_rates) / len(usage_rates), 3) if usage_rates else None
        ),
        "interpretation": "Small-sample percentiles are descriptive only. The nearest-rank P95/P99 may equal the maximum for small samples; increase request count and repeat runs for tail-latency claims.",
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved evidence report: {output}")
    return 0 if successful else 1


if __name__ == "__main__":
    sys.exit(main())
