#!/usr/bin/env python3
"""ARIES Native Bench: API availability, latency, throughput and authored QA diagnostics.

Standard-library only. This is a small project-owned smoke suite, not an official
academic benchmark or independent certification.
"""
import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

CASES = [
    {"id":"math_01","category":"arithmetic","prompt":"What is 17 * 19? Reply with the number only.","expected":"323"},
    {"id":"math_02","category":"arithmetic","prompt":"What is 144 / 12? Reply with the number only.","expected":"12"},
    {"id":"math_03","category":"arithmetic","prompt":"What is 256 + 789? Reply with the number only.","expected":"1045"},
    {"id":"math_04","category":"arithmetic","prompt":"What is 1000 - 367? Reply with the number only.","expected":"633"},
    {"id":"logic_01","category":"reasoning","prompt":"All zargs are blue. Nimo is a zarg. Is Nimo blue? Answer yes or no.","expected":"yes"},
    {"id":"logic_02","category":"reasoning","prompt":"A is taller than B. B is taller than C. Who is shortest: A, B, or C? Reply with one letter.","expected":"C"},
    {"id":"logic_03","category":"reasoning","prompt":"If today is Tuesday, what day is two days after tomorrow? Reply with the weekday.","expected":"Friday"},
    {"id":"instruction_01","category":"instruction","prompt":"Reply with exactly this token and nothing else: ARIES-OK","expected":"ARIES-OK"},
    {"id":"instruction_02","category":"instruction","prompt":"Return exactly three items separated by commas: red, green, blue","expected":"red, green, blue"},
    {"id":"knowledge_01","category":"knowledge","prompt":"At standard atmospheric pressure, what is the chemical formula for water? Reply with the formula only.","expected":"H2O"},
]

def normalize(value):
    return " ".join(str(value).strip().lower().split()).strip(" .!\\t\\n")

def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * pct / 100
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return round(ordered[low] * (1 - fraction) + ordered[high] * fraction, 3)

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
    parser = argparse.ArgumentParser(description="Measure ARIES endpoint readiness, latency, throughput and diagnostic QA.")
    parser.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"), help="Model ID or auto to select the first advertised model")
    parser.add_argument("--api-key", default=os.getenv("ARIES_API_KEY", ""))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--output", default="aries-benchmark-results.json")
    parser.add_argument("--limit", type=int, default=len(CASES))
    parser.add_argument("--concurrency", type=int, default=1, help="Parallel completion requests (1 is safest for CPU-only models)")
    args = parser.parse_args()
    if args.concurrency < 1 or args.concurrency > 16:
        parser.error("--concurrency must be between 1 and 16")
    base = args.base_url.rstrip("/")
    api_root = base if base.endswith("/v1") else base + "/v1"
    report = {
        "suite": "ARIES Native Bench v2",
        "suite_type": "project-owned diagnostic; not an official academic benchmark",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": base,
        "requested_model": args.model,
        "configuration": {"timeout_seconds": args.timeout, "concurrency": args.concurrency},
        "results": [],
    }
    try:
        started = time.perf_counter()
        status, health = request_json(base + "/health", api_key=args.api_key, timeout=args.timeout)
        report["health"] = {"http_status": status, "latency_ms": round((time.perf_counter()-started)*1000, 3), "response": health}
    except Exception as exc:
        report["health"] = {"error": type(exc).__name__ + ": " + str(exc)}
    try:
        started = time.perf_counter()
        status, models = request_json(api_root + "/models", api_key=args.api_key, timeout=args.timeout)
        report["models"] = {"http_status": status, "latency_ms": round((time.perf_counter()-started)*1000, 3), "response": models}
    except Exception as exc:
        models = {}
        report["models"] = {"error": type(exc).__name__ + ": " + str(exc)}
    available = models.get("data", []) if isinstance(models, dict) else []
    advertised = available[0].get("id") if available and isinstance(available[0], dict) else None
    model = advertised if args.model == "auto" and advertised else args.model
    report["selected_model"] = model
    cases = CASES[:max(0, min(args.limit, len(CASES)))]
    run_started = time.perf_counter()

    def run_case(case):
        started = time.perf_counter()
        item = {"id": case["id"], "category": case["category"], "expected": case["expected"]}
        try:
            status, response = request_json(
                api_root + "/chat/completions",
                {"model": model, "messages": [{"role":"user","content":case["prompt"]}],
                 "temperature": 0, "max_tokens": 64},
                args.api_key, args.timeout,
            )
            elapsed = (time.perf_counter()-started)*1000
            choices = response.get("choices", []) if isinstance(response, dict) else []
            actual = choices[0].get("message", {}).get("content", "") if choices else ""
            usage = response.get("usage", {}) if isinstance(response, dict) else {}
            item.update({"http_status":status, "latency_ms":round(elapsed,3), "actual":actual,
                         "nonempty":bool(str(actual).strip()),
                         "passed_exact_match":normalize(actual)==normalize(case["expected"]),
                         "prompt_tokens":usage.get("prompt_tokens"), "completion_tokens":usage.get("completion_tokens")})
        except urllib.error.HTTPError as exc:
            elapsed = (time.perf_counter()-started)*1000
            item.update({"http_status":exc.code,"latency_ms":round(elapsed,3),
                         "error":exc.read().decode("utf-8",errors="replace")[:1000]})
        except Exception as exc:
            elapsed = (time.perf_counter()-started)*1000
            item.update({"latency_ms":round(elapsed,3),"error":type(exc).__name__+": "+str(exc)})
        return item

    if args.concurrency == 1:
        report["results"] = [run_case(case) for case in cases]
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {pool.submit(run_case, case): case for case in cases}
            for future in as_completed(futures):
                report["results"].append(future.result())
        report["results"].sort(key=lambda item: next(i for i,c in enumerate(cases) if c["id"] == item["id"]))
    total_elapsed = time.perf_counter()-run_started
    for item in report["results"]:
        print(json.dumps(item, ensure_ascii=False))
    completed = [item for item in report["results"] if "passed_exact_match" in item]
    latencies = [item["latency_ms"] for item in report["results"] if "latency_ms" in item]
    passed = sum(bool(item.get("passed_exact_match")) for item in completed)
    nonempty = sum(bool(item.get("nonempty")) for item in completed)
    by_category = defaultdict(lambda: {"cases":0,"responses":0,"exact_match_passes":0,"accuracy_percent":None})
    for item in report["results"]:
        row = by_category[item["category"]]
        row["cases"] += 1
        if "passed_exact_match" in item:
            row["responses"] += 1
            row["exact_match_passes"] += int(bool(item["passed_exact_match"]))
    for row in by_category.values():
        row["accuracy_percent"] = round(100*row["exact_match_passes"]/row["responses"],2) if row["responses"] else None
    report["summary"] = {
        "cases_requested":len(cases),
        "http_completion_responses":len(completed),
        "request_success_rate_percent":round(100*len(completed)/len(cases),2) if cases else None,
        "nonempty_responses":nonempty,
        "exact_match_passes":passed,
        "exact_match_accuracy_percent":round(100*passed/len(completed),2) if completed else None,
        "category_metrics":dict(by_category),
        "latency_sample_count":len(latencies),
        "latency_min_ms":round(min(latencies),3) if latencies else None,
        "latency_mean_ms":round(statistics.mean(latencies),3) if latencies else None,
        "latency_p50_ms":percentile(latencies,50),
        "latency_p90_ms":percentile(latencies,90),
        "latency_p95_ms":percentile(latencies,95),
        "latency_p99_ms":percentile(latencies,99),
        "latency_max_ms":round(max(latencies),3) if latencies else None,
        "wall_clock_seconds":round(total_elapsed,3),
        "completed_requests_per_second":round(len(completed)/total_elapsed,3) if total_elapsed > 0 else None,
        "warning":"Small authored diagnostic only; not an official MMLU, GSM8K, BBH, or leaderboard score."
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\\n", encoding="utf-8")
    print("\\nPERFORMANCE SUMMARY")
    print(json.dumps(report["summary"], indent=2))
    print("Saved report:", output)
    if not completed:
        raise SystemExit("FAIL: no valid completion responses; inspect health/models errors and endpoint configuration.")
    if nonempty == 0:
        raise SystemExit("FAIL: endpoint returned completions but every answer was empty.")

if __name__ == "__main__":
    main()
