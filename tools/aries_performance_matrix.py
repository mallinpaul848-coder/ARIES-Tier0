#!/usr/bin/env python3
"""Repeatable ARIES API performance matrix using the existing authored smoke suite.

This measures end-to-end API latency and exact-match rate. It is not an official
model benchmark. Keep concurrency modest on shared/free hosting.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "tools" / "aries_bench.py"


def percentile(values, pct):
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * pct / 100
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo), 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"))
    parser.add_argument("--api-key", default=os.getenv("ARIES_API_KEY", ""))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 2, 4])
    parser.add_argument("--output", default="validation-results/performance-matrix.json")
    args = parser.parse_args()

    if args.rounds < 1 or args.rounds > 5:
        parser.error("--rounds must be between 1 and 5")
    if args.limit < 1 or args.limit > 10:
        parser.error("--limit must be between 1 and 10")
    if not args.concurrency or any(c < 1 or c > 4 for c in args.concurrency):
        parser.error("each --concurrency value must be between 1 and 4")

    outdir = Path(args.output).parent / (Path(args.output).stem + "-runs")
    outdir.mkdir(parents=True, exist_ok=True)
    report = {
        "suite": "ARIES repeatable API performance matrix",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": args.base_url.rstrip("/"),
        "model": args.model,
        "rounds": args.rounds,
        "cases_per_run": args.limit,
        "concurrency_levels": args.concurrency,
        "measurements": [],
        "scope": "Project-owned authored smoke test; not independent certification or an official leaderboard score.",
        "interpretation": [
            "Latency is end-to-end API latency measured from the runner and includes network/server overhead.",
            "Concurrency can change latency and throughput; compare only runs against the same target and setup.",
            "This suite does not measure model-only token generation speed unless the API exposes token usage and generation timing."
        ]
    }

    for concurrency in args.concurrency:
        for round_no in range(1, args.rounds + 1):
            output_file = outdir / f"c{concurrency}-round{round_no}.json"
            cmd = [
                sys.executable, str(BENCH),
                "--base-url", args.base_url,
                "--model", args.model,
                "--timeout", str(args.timeout),
                "--limit", str(args.limit),
                "--concurrency", str(concurrency),
                "--output", str(output_file),
            ]
            if args.api_key:
                cmd.extend(["--api-key", args.api_key])
            proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
            item = {
                "concurrency": concurrency,
                "round": round_no,
                "exit_code": proc.returncode,
                "report_path": str(output_file),
                "stderr_tail": proc.stderr[-1500:] if proc.stderr else ""
            }
            if output_file.exists():
                try:
                    child = json.loads(output_file.read_text(encoding="utf-8"))
                    item["summary"] = child.get("summary", {})
                    item["health"] = child.get("health", {})
                    item["models"] = child.get("models", {})
                except (ValueError, OSError) as exc:
                    item["report_parse_error"] = str(exc)
            report["measurements"].append(item)
            print(json.dumps(item, ensure_ascii=False), flush=True)

    summaries = [m.get("summary", {}) for m in report["measurements"]]
    latency = [
        result.get("latency_ms")
        for m in report["measurements"]
        for result in (json.loads(Path(m["report_path"]).read_text(encoding="utf-8")).get("results", [])
                       if Path(m["report_path"]).exists() else [])
        if isinstance(result.get("latency_ms"), (int, float))
    ]
    completed = sum(s.get("http_completion_responses", 0) or 0 for s in summaries)
    passed = sum(s.get("exact_match_passes", 0) or 0 for s in summaries)
    requested = args.limit * len(report["measurements"])
    report["aggregate"] = {
        "matrix_runs": len(report["measurements"]),
        "requests_requested": requested,
        "completion_responses": completed,
        "completion_response_rate_percent": round(100 * completed / requested, 2) if requested else None,
        "exact_match_passes": passed,
        "exact_match_accuracy_percent": round(100 * passed / completed, 2) if completed else None,
        "latency_samples": len(latency),
        "latency_min_ms": round(min(latency), 3) if latency else None,
        "latency_mean_ms": round(sum(latency) / len(latency), 3) if latency else None,
        "latency_p50_ms": percentile(latency, 50),
        "latency_p90_ms": percentile(latency, 90),
        "latency_p95_ms": percentile(latency, 95),
        "latency_p99_ms": percentile(latency, 99),
        "latency_max_ms": round(max(latency), 3) if latency else None,
        "failed_matrix_runs": sum(1 for m in report["measurements"] if m.get("exit_code") != 0)
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("MATRIX SUMMARY")
    print(json.dumps(report["aggregate"], indent=2))
    print("Saved report:", output)
    if completed == 0:
        raise SystemExit("FAIL: no completion responses; inspect endpoint and per-run reports.")


if __name__ == "__main__":
    main()
