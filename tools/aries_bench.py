#!/usr/bin/env python3
"""
ARIES Native Bench — dependency-free API smoke/latency/quality harness.

Uses only Python's standard library. This is an ARIES-authored diagnostic suite,
not an official MMLU/GSM8K/BBH score and not an independent model-quality certification.
"""
import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CASES = [
    {"id": "math_01", "category": "arithmetic", "prompt": "What is 17 * 19? Reply with the number only.", "expected": "323"},
    {"id": "math_02", "category": "arithmetic", "prompt": "What is 144 / 12? Reply with the number only.", "expected": "12"},
    {"id": "math_03", "category": "arithmetic", "prompt": "What is 256 + 789? Reply with the number only.", "expected": "1045"},
    {"id": "math_04", "category": "arithmetic", "prompt": "What is 1000 - 367? Reply with the number only.", "expected": "633"},
    {"id": "logic_01", "category": "reasoning", "prompt": "All zargs are blue. Nimo is a zarg. Is Nimo blue? Answer yes or no.", "expected": "yes"},
    {"id": "logic_02", "category": "reasoning", "prompt": "A is taller than B. B is taller than C. Who is shortest: A, B, or C? Reply with one letter.", "expected": "C"},
    {"id": "logic_03", "category": "reasoning", "prompt": "If today is Tuesday, what day is two days after tomorrow? Reply with the weekday.", "expected": "Friday"},
    {"id": "instruction_01", "category": "instruction", "prompt": "Reply with exactly this token and nothing else: ARIES-OK", "expected": "ARIES-OK"},
    {"id": "instruction_02", "category": "instruction", "prompt": "Return exactly three items separated by commas: red, green, blue", "expected": "red, green, blue"},
    {"id": "knowledge_01", "category": "knowledge", "prompt": "At standard atmospheric pressure, what is the chemical formula for water? Reply with the formula only.", "expected": "H2O"},
]

def normalize(text):
    return " ".join(str(text).strip().lower().split()).strip(" .!\t\n")

def request_json(url, payload=None, api_key=None, timeout=90):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return response.status, json.loads(raw) if raw else {}

def main():
    parser = argparse.ArgumentParser(description="Run ARIES native endpoint checks and small diagnostic benchmark.")
    parser.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "http://127.0.0.1:8000"), help="API base URL, e.g. https://service.example.com")
    parser.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "aries"), help="Model identifier accepted by the API")
    parser.add_argument("--api-key", default=os.getenv("ARIES_API_KEY", ""), help="Optional bearer token; prefer ARIES_API_KEY environment variable")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--output", default="aries-benchmark-results.json")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    api_root = base if base.endswith("/v1") else base + "/v1"
    report = {
        "suite": "ARIES Native Bench v1",
        "suite_type": "small diagnostic suite; not an official academic benchmark",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "requested_model": args.model,
        "results": [],
    }
    try:
        status, health = request_json(base + "/health", timeout=args.timeout)
        report["health"] = {"http_status": status, "response": health}
    except Exception as exc:
        report["health"] = {"error": type(exc).__name__ + ": " + str(exc)}
    try:
        status, models = request_json(api_root + "/models", api_key=args.api_key, timeout=args.timeout)
        report["models"] = {"http_status": status, "response": models}
    except Exception as exc:
        report["models"] = {"error": type(exc).__name__ + ": " + str(exc)}
    cases = CASES[:max(0, min(args.limit, len(CASES)))]
    latencies = []
    for case in cases:
        started = time.perf_counter()
        item = {"id": case["id"], "category": case["category"], "expected": case["expected"]}
        try:
            status, response = request_json(
                api_root + "/chat/completions",
                {"model": args.model, "messages": [{"role": "user", "content": case["prompt"]}],
                 "temperature": 0, "max_tokens": 64},
                args.api_key, args.timeout,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            latencies.append(elapsed_ms)
            choices = response.get("choices", [])
            actual = choices[0].get("message", {}).get("content", "") if choices else ""
            item.update({"http_status": status, "latency_ms": round(elapsed_ms, 3),
                         "actual": actual, "passed_exact_match": normalize(actual) == normalize(case["expected"])})
        except urllib.error.HTTPError as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            item.update({"http_status": exc.code, "latency_ms": round(elapsed_ms, 3),
                         "error": exc.read().decode("utf-8", errors="replace")[:1000]})
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            item.update({"latency_ms": round(elapsed_ms, 3), "error": type(exc).__name__ + ": " + str(exc)})
        report["results"].append(item)
        print(json.dumps(item, ensure_ascii=False))
    completed = [x for x in report["results"] if "passed_exact_match" in x]
    passes = sum(1 for x in completed if x["passed_exact_match"])
    nonempty = sum(1 for x in completed if str(x.get("actual", "")).strip())
    report["summary"] = {
        "cases_requested": len(cases),
        "cases_with_model_response": len(completed),
        "nonempty_responses": nonempty,
        "exact_match_passes": passes,
        "exact_match_accuracy_percent": round(100 * passes / len(completed), 2) if completed else None,
        "latency_samples": len(latencies),
        "latency_mean_ms": round(statistics.mean(latencies), 3) if latencies else None,
        "latency_median_ms": round(statistics.median(latencies), 3) if latencies else None,
        "latency_min_ms": round(min(latencies), 3) if latencies else None,
        "latency_max_ms": round(max(latencies), 3) if latencies else None,
        "warning": "Small authored diagnostic only. Results are not official MMLU, GSM8K, BBH, or leaderboard scores."
    }
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nSUMMARY")
    print(json.dumps(report["summary"], indent=2))
    print("Saved report:", args.output)
    if not completed:
        raise SystemExit("No valid model responses. Check endpoint configuration and credentials.")
    if nonempty == 0:
        raise SystemExit("Endpoint returned HTTP responses but every model completion was empty.")

if __name__ == "__main__":
    main()
