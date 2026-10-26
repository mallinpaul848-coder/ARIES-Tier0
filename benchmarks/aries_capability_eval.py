#!/usr/bin/env python3
"""Repeatable ARIES capability smoke evaluation for an OpenAI-compatible chat API.

This is a project-authored diagnostic, not a standardized intelligence benchmark.
It measures observed API latency and narrow assertions; it does not certify broad
reasoning ability. Keep prompts and scoring rules identical when comparing models.
"""
from __future__ import annotations

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
    {"id": "arith_mul", "category": "arithmetic", "prompt": "Compute 17 * 19. Reply with only the number.", "expected_any": ["323"]},
    {"id": "arith_fraction", "category": "arithmetic", "prompt": "Compute 144 / 12. Reply with only the number.", "expected_any": ["12"]},
    {"id": "logic_chain", "category": "reasoning", "prompt": "All glips are blins. All blins are red. Are all glips red? Reply yes or no.", "expected_any": ["yes"]},
    {"id": "ordering", "category": "reasoning", "prompt": "A is taller than B. B is taller than C. Who is shortest? Reply with one letter.", "expected_any": ["c"]},
    {"id": "instruction_exact", "category": "instruction_following", "prompt": "Reply with exactly this text and nothing else: ARIES-OK", "expected_any": ["aries-ok"]},
    {"id": "instruction_list", "category": "instruction_following", "prompt": "Return exactly three colors, in this order, separated by commas: red, green, blue.", "expected_any": ["red, green, blue"]},
    {"id": "knowledge_water", "category": "knowledge", "prompt": "What is the chemical formula for water? Reply with the formula only.", "expected_any": ["h2o"]},
    {"id": "knowledge_capital", "category": "knowledge", "prompt": "What is the capital of France? Reply with the city only.", "expected_any": ["paris"]},
    {"id": "explanation", "category": "explanation", "prompt": "In one short sentence, explain why testing software with edge cases is useful.", "expected_any": ["edge", "case", "boundary", "failure"]},
    {"id": "uncertainty", "category": "calibration", "prompt": "What exact number will a fair six-sided die show on my next roll? Answer honestly.", "expected_any": ["cannot", "can't", "unknown", "predict", "random", "know"]},
]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * p / 100
    low = int(pos)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (pos - low)


def request(base_url: str, model: str, prompt: str, timeout: float, api_key: str | None) -> dict:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 128,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=body, headers=headers, method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read())
            choices = payload.get("choices") or []
            message = choices[0].get("message", {}) if choices else {}
            text = message.get("content", "")
            if isinstance(text, list):
                text = " ".join(str(part.get("text", "")) for part in text if isinstance(part, dict))
            return {"http_status": response.status, "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "text": str(text), "error": None}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        return {"http_status": status, "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "text": "", "error": f"{type(exc).__name__}: {str(exc)[:300]}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://aries-tier0-api-6qjh.onrender.com")
    parser.add_argument("--model", default="aries-local-smollm2-135m")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--output", default="reports/aries-capability-evaluation.json")
    args = parser.parse_args()
    if not args.base_url.startswith(("http://", "https://")):
        parser.error("--base-url must use HTTP or HTTPS")
    if args.timeout <= 0 or not 1 <= args.rounds <= 20:
        parser.error("--timeout must be positive and --rounds must be between 1 and 20")

    key = os.environ.get("ARIES_CAPABILITY_API_KEY")
    results = []
    started_all = time.perf_counter()
    for round_number in range(1, args.rounds + 1):
        for case in CASES:
            observed = request(args.base_url, args.model, case["prompt"], args.timeout, key)
            normalized = " ".join(observed["text"].casefold().split())
            expected = case["expected_any"]
            if case["id"] == "explanation":
                passed = bool(normalized) and any(token in normalized for token in expected)
            else:
                passed = bool(normalized) and any(token in normalized for token in expected)
            results.append({
                "id": case["id"], "category": case["category"], "round": round_number,
                "prompt": case["prompt"], "expected_any": expected,
                **observed, "nonempty": bool(normalized),
                "passed_narrow_assertion": bool(passed and observed["http_status"] and 200 <= observed["http_status"] < 300),
            })

    elapsed = time.perf_counter() - started_all
    latencies = [r["latency_ms"] for r in results]
    successful = [r for r in results if r["http_status"] is not None and 200 <= r["http_status"] < 300 and r["nonempty"]]
    categories = {}
    for category in sorted({r["category"] for r in results}):
        subset = [r for r in results if r["category"] == category]
        categories[category] = {
            "cases": len(subset),
            "successful_nonempty": sum(r["http_status"] is not None and 200 <= r["http_status"] < 300 and r["nonempty"] for r in subset),
            "passed_narrow_assertions": sum(r["passed_narrow_assertion"] for r in subset),
            "assertion_rate_percent": round(100 * sum(r["passed_narrow_assertion"] for r in subset) / len(subset), 2),
        }
    report = {
        "suite": "ARIES Capability Smoke Evaluation v1",
        "suite_type": "project-authored diagnostic; not standardized or independent certification",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": args.base_url, "model": args.model, "rounds": args.rounds,
        "case_count_per_round": len(CASES), "timeout_seconds": args.timeout,
        "summary": {
            "requests": len(results), "successful_nonempty": len(successful),
            "http_success_and_nonempty_percent": round(100 * len(successful) / len(results), 2),
            "narrow_assertion_passes": sum(r["passed_narrow_assertion"] for r in results),
            "narrow_assertion_rate_percent": round(100 * sum(r["passed_narrow_assertion"] for r in results) / len(results), 2),
            "latency_min_ms": round(min(latencies), 3) if latencies else None,
            "latency_mean_ms": round(statistics.fmean(latencies), 3) if latencies else None,
            "latency_p50_ms": round(percentile(latencies, 50), 3) if latencies else None,
            "latency_p95_ms": round(percentile(latencies, 95), 3) if latencies else None,
            "latency_p99_ms": round(percentile(latencies, 99), 3) if latencies else None,
            "latency_max_ms": round(max(latencies), 3) if latencies else None,
            "wall_clock_seconds": round(elapsed, 3),
            "completed_requests_per_second": round(len(results) / elapsed, 3) if elapsed else None,
            "category_metrics": categories,
        },
        "limitations": [
            "Small, project-authored smoke set; not MMLU, GSM8K, BBH, HumanEval, or an official leaderboard score.",
            "Keyword assertions can produce false positives and do not establish deep reasoning.",
            "Sequential API latency includes network and service effects; it is not pure model inference latency.",
            "Repeat with a larger recognized evaluator and independent review before making comparative capability claims.",
        ],
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
