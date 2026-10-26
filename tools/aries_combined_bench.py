#!/usr/bin/env python3
"""Run one combined ARIES latency, throughput, and answer-quality matrix."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "https://aries-tier0-api-6qjh.onrender.com"))
    p.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"))
    p.add_argument("--timeout", type=int, default=75)
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--output", default="reports/aries-combined-performance.json")
    args = p.parse_args()
    if not 1 <= args.repeats <= 5:
        p.error("--repeats must be between 1 and 5")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    levels = [1, 2, 4, 8]
    runs = []
    for concurrency in levels:
        for repeat in range(1, args.repeats + 1):
            path = out.parent / f"aries-c{concurrency}-r{repeat}.json"
            cmd = [
                sys.executable, "tools/aries_bench.py",
                "--base-url", args.base_url, "--model", args.model,
                "--timeout", str(args.timeout), "--limit", "15",
                "--concurrency", str(concurrency), "--output", str(path),
            ]
            print(f"\n=== concurrency={concurrency}, repeat={repeat}/{args.repeats} ===", flush=True)
            proc = subprocess.run(cmd, text=True)
            row = {"concurrency": concurrency, "repeat": repeat, "exit_code": proc.returncode, "report_file": str(path)}
            if path.exists():
                try:
                    report = json.loads(path.read_text(encoding="utf-8"))
                    row["summary"] = report.get("summary", {})
                    row["health"] = report.get("health", {})
                    row["models"] = report.get("models", {})
                    row["selected_model"] = report.get("selected_model")
                except Exception as exc:
                    row["report_error"] = str(exc)
            runs.append(row)

    matrix = []
    for concurrency in levels:
        selected = [r for r in runs if r["concurrency"] == concurrency and r.get("summary")]
        def mean_of(key):
            vals = [r["summary"].get(key) for r in selected if isinstance(r["summary"].get(key), (int, float))]
            return round(sum(vals) / len(vals), 3) if vals else None
        matrix.append({
            "concurrency": concurrency,
            "repeats_with_reports": len(selected),
            "mean_latency_ms_across_repeats": mean_of("latency_mean_ms"),
            "mean_p50_ms_across_repeats": mean_of("latency_p50_ms"),
            "mean_p95_ms_across_repeats": mean_of("latency_p95_ms"),
            "mean_p99_ms_across_repeats": mean_of("latency_p99_ms"),
            "mean_max_latency_ms_across_repeats": mean_of("latency_max_ms"),
            "mean_requests_per_second_across_repeats": mean_of("completed_requests_per_second"),
            "total_requests": sum(r["summary"].get("cases_requested", 0) for r in selected),
            "successful_completion_responses": sum(r["summary"].get("http_completion_responses", 0) for r in selected),
            "exact_match_passes": sum(r["summary"].get("exact_match_passes", 0) for r in selected),
            "exact_match_accuracy_percent": (
                round(100 * sum(r["summary"].get("exact_match_passes", 0) for r in selected) /
                      sum(r["summary"].get("http_completion_responses", 0) for r in selected), 2)
                if sum(r["summary"].get("http_completion_responses", 0) for r in selected) else None
            ),
        })
    result = {
        "suite": "ARIES Combined Performance Matrix",
        "suite_type": "project-owned diagnostic; not independent certification",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": args.base_url,
        "requested_model": args.model,
        "repeats_per_concurrency": args.repeats,
        "concurrency_levels": levels,
        "matrix": matrix,
        "runs": runs,
        "interpretation": "Compare latency, throughput, request success, and exact-match accuracy at concurrency 1, 2, 4, and 8. Results can vary with hosting load and model warm-up; this is not an official academic benchmark.",
    }
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("\nCOMBINED MATRIX SUMMARY")
    print(json.dumps(matrix, indent=2))
    print(f"Saved combined report: {out}")
    if not any(r.get("summary", {}).get("http_completion_responses", 0) for r in runs):
        raise SystemExit("FAIL: no benchmark run returned valid completion responses.")

if __name__ == "__main__":
    main()
