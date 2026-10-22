#!/usr/bin/env python3
"""Repeatable model-agnostic smoke benchmark for authorized OpenAI-compatible APIs."""
from __future__ import annotations
import argparse
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

CASES = [
    ("arithmetic", "Compute 17 * 19. Return the numeric answer.", ["323"]),
    ("arithmetic", "Compute 144 / 12. Return the numeric answer.", ["12"]),
    ("instruction", "Reply with exactly: ARIES-OK", ["aries-ok"]),
    ("knowledge", "What is the capital of France?", ["paris"]),
    ("reasoning", "If all glips are blins and all blins are red, are all glips red? Answer yes or no.", ["yes"]),
    ("logic", "A is taller than B. B is taller than C. Who is shortest?", ["c"]),
    ("arithmetic", "What is 81 divided by 9?", ["9"]),
    ("instruction", "List exactly three items separated by commas: red, green, blue.", ["red", "green", "blue"]),
]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p / 100
    lo, hi = int(pos), min(int(pos) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def parse_target(value: str) -> tuple[str, str, str]:
    parts = value.split(",", 1)
    if len(parts) != 2 or "=" not in parts[0]:
        raise argparse.ArgumentTypeError("target format: NAME=BASE_URL,MODEL_ID")
    name, url = parts[0].split("=", 1)
    model = parts[1]
    if not name.strip() or not url.startswith(("http://", "https://")) or not model.strip():
        raise argparse.ArgumentTypeError("target needs a name, HTTP(S) base URL, and model ID")
    return name.strip(), url.rstrip("/"), model.strip()


def request_one(base_url: str, model: str, prompt: str, timeout: float, api_key: str | None) -> dict[str, Any]:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0, "max_tokens": 96}).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(base_url + "/v1/chat/completions", data=body, headers=headers, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            elapsed = (time.perf_counter() - started) * 1000
            data = json.loads(raw)
            choices = data.get("choices") or []
            message = choices[0].get("message", {}) if choices else {}
            content = message.get("content", "")
            if isinstance(content, list):
                content = " ".join(str(x.get("text", "")) for x in content if isinstance(x, dict))
            return {"status": resp.status, "latency_ms": elapsed, "text": str(content), "error": None}
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return {"status": None, "latency_ms": (time.perf_counter() - started) * 1000,
                "text": "", "error": type(exc).__name__ + ": " + str(exc)[:240]}


def run_target(name: str, url: str, model: str, rounds: int, timeout: float) -> dict[str, Any]:
    env_name = "ARIES_BENCH_KEY_" + re.sub(r"[^A-Za-z0-9]", "_", name).upper()
    key = os.environ.get(env_name)
    results = []
    wall_start = time.perf_counter()
    for round_index in range(rounds):
        for category, prompt, expected in CASES:
            result = request_one(url, model, prompt, timeout, key)
            normalized = normalize(result["text"])
            result.update({"target": name, "model": model, "round": round_index + 1,
                           "category": category, "prompt": prompt,
                           "correct": bool(normalized) and all(token in normalized for token in expected)})
            results.append(result)
    wall_seconds = time.perf_counter() - wall_start
    good = [r for r in results if r["status"] is not None and 200 <= r["status"] < 300 and r["text"].strip()]
    latencies = [r["latency_ms"] for r in results]
    return {
        "target": name, "base_url": url, "model": model, "api_key_configured": bool(key),
        "requests": len(results), "successful_nonempty": len(good),
        "failures_or_empty": len(results) - len(good),
        "correct_smoke_cases": sum(r["correct"] for r in results),
        "smoke_accuracy": sum(r["correct"] for r in results) / len(results) if results else 0,
        "wall_time_seconds": wall_seconds,
        "requests_per_second": len(results) / wall_seconds if wall_seconds else None,
        "latency_ms": {"mean": statistics.fmean(latencies) if latencies else None,
                       "p50": percentile(latencies, 50), "p95": percentile(latencies, 95),
                       "p99": percentile(latencies, 99), "max": max(latencies) if latencies else None},
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", type=parse_target, required=True,
                        help="NAME=BASE_URL,MODEL_ID; repeat for alternatives")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--output", default="reports/aries-alternative-comparison.json")
    args = parser.parse_args()
    if args.rounds < 1 or args.rounds > 100 or args.timeout <= 0:
        parser.error("--rounds must be 1..100 and --timeout must be positive")
    report = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
              "method": "sequential OpenAI-compatible API smoke comparison",
              "note": "Project-authored smoke set; not independent certification or a general intelligence ranking.",
              "rounds": args.rounds, "cases_per_round": len(CASES),
              "targets": [run_target(*target, args.rounds, args.timeout) for target in args.target]}
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    for target in report["targets"]:
        lat = target["latency_ms"]
        print(f"{target['target']}: success={target['successful_nonempty']}/{target['requests']} "
              f"smoke={target['correct_smoke_cases']}/{target['requests']} "
              f"P50={lat['p50']:.2f}ms P95={lat['p95']:.2f}ms P99={lat['p99']:.2f}ms "
              f"RPS={target['requests_per_second']:.2f}")
    print("Wrote", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
