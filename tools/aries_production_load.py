#!/usr/bin/env python3
"""Capped, opt-in ARIES production endpoint load ramp.

This is a project-operated capacity diagnostic, not an independent certification.
Use only against an endpoint you own or have explicit permission to test.
"""
import argparse
import concurrent.futures
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def percentile(values, pct):
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * pct / 100
    lo, hi = int(pos), min(int(pos) + 1, len(values) - 1)
    return round(values[lo] * (1 - (pos - lo)) + values[hi] * (pos - lo), 3)


def request_json(url, payload=None, api_key="", timeout=30):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=body, headers=headers,
                                 method="GET" if body is None else "POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return resp.status, json.loads(raw) if raw else {}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", ""))
    p.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"))
    p.add_argument("--api-key", default=os.getenv("ARIES_API_KEY", ""))
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--requests-per-level", type=int, default=20)
    p.add_argument("--levels", default="1,4,8,16")
    p.add_argument("--output", default="reports/production-load.json")
    args = p.parse_args()
    if not args.base_url:
        p.error("--base-url or ARIES_BASE_URL is required")
    if not 1 <= args.requests_per_level <= 250:
        p.error("--requests-per-level must be 1..250 (safety cap)")
    try:
        levels = [int(v) for v in args.levels.split(",")]
    except ValueError:
        p.error("--levels must be comma-separated integers")
    if not levels or any(v < 1 or v > 16 for v in levels):
        p.error("each concurrency level must be 1..16")
    if args.timeout < 1 or args.timeout > 120:
        p.error("--timeout must be 1..120 seconds")

    base = args.base_url.rstrip("/")
    api_root = base if base.endswith("/v1") else base + "/v1"
    report = {
        "suite": "ARIES opt-in production endpoint load ramp",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": base,
        "requested_model": args.model,
        "configuration": {"requests_per_level": args.requests_per_level,
                          "concurrency_levels": levels, "timeout_seconds": args.timeout,
                          "maximum_total_requests": args.requests_per_level * len(levels)},
        "independent_third_party_validation": False,
        "results": [],
        "limitations": "Project-operated HTTP test. Measures endpoint response behavior, not isolated model tokens/sec, general intelligence, or third-party certification. Use only with authorization."
    }
    try:
        _, health = request_json(base + "/health", timeout=args.timeout, api_key=args.api_key)
        _, models = request_json(api_root + "/models", timeout=args.timeout, api_key=args.api_key)
    except Exception as exc:
        raise SystemExit(f"Preflight failed; no load was sent: {type(exc).__name__}: {exc}")
    available = models.get("data", []) if isinstance(models, dict) else []
    advertised = available[0].get("id") if available and isinstance(available[0], dict) else None
    model = advertised if args.model == "auto" and advertised else args.model
    report["preflight"] = {"health": health, "advertised_model_count": len(available),
                           "selected_model": model}

    def one_request(index, level):
        started = time.perf_counter()
        item = {"index": index}
        try:
            status, data = request_json(
                api_root + "/chat/completions",
                {"model": model, "messages": [{"role": "user", "content": "Reply with exactly OK."}],
                 "temperature": 0, "max_tokens": 8},
                api_key=args.api_key, timeout=args.timeout)
            choices = data.get("choices", []) if isinstance(data, dict) else []
            answer = choices[0].get("message", {}).get("content", "") if choices else ""
            nonempty = bool(str(answer).strip())
            exact_match = str(answer).strip() == "OK"
            item.update({"http_status": status,
                         "success": 200 <= status < 300 and nonempty,
                         "nonempty": nonempty,
                         "exact_match": exact_match})
            usage = data.get("usage", {}) if isinstance(data, dict) else {}
            item["completion_tokens"] = usage.get("completion_tokens")
        except urllib.error.HTTPError as exc:
            item.update({"http_status": exc.code, "success": False,
                         "error": exc.read().decode("utf-8", errors="replace")[:300]})
        except Exception as exc:
            item.update({"success": False, "error": type(exc).__name__ + ": " + str(exc)[:300]})
        item["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
        return item

    for level in levels:
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=level) as pool:
            items = list(pool.map(lambda i: one_request(i, level), range(args.requests_per_level)))
        elapsed = time.perf_counter() - start
        latencies = [x["latency_ms"] for x in items]
        successes = sum(bool(x.get("success")) for x in items)
        row = {
            "concurrency": level, "requests": len(items), "successes": successes,
            "failures": len(items) - successes,
            "success_rate_percent": round(100 * successes / len(items), 2) if items else None,
            "exact_match_count": sum(bool(x.get("exact_match")) for x in items),
            "exact_match_rate_percent": round(100 * sum(bool(x.get("exact_match")) for x in items) / len(items), 2) if items else None,
            "latency_min_ms": round(min(latencies), 3) if latencies else None,
            "latency_mean_ms": round(statistics.mean(latencies), 3) if latencies else None,
            "latency_p50_ms": percentile(latencies, 50),
            "latency_p95_ms": percentile(latencies, 95),
            "latency_p99_ms": percentile(latencies, 99),
            "latency_max_ms": round(max(latencies), 3) if latencies else None,
            "wall_clock_seconds": round(elapsed, 3),
            "requests_per_second": round(len(items) / elapsed, 3) if elapsed else None,
            "request_results": items
        }
        report["results"].append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "request_results"}))
        # Stop ramping if endpoint starts failing; avoid piling load onto an unhealthy service.
        if row["success_rate_percent"] < 95:
            report["stopped_early"] = True
            report["stop_reason"] = f"Success rate fell below 95% at concurrency {level}"
            break

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Saved:", output)
    if any(row["success_rate_percent"] < 95 for row in report["results"]):
        raise SystemExit("FAIL: at least one load level had less than 95% successful non-empty responses")


if __name__ == "__main__":
    main()
