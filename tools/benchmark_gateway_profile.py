#!/usr/bin/env python3
"""Run the isolated Mallin–PRISE Gateway X profiling benchmark.

Examples:
  python tools/benchmark_gateway_profile.py --repeats 100
  python tools/benchmark_gateway_profile.py --prompts-file prompts.txt --repeats 50 --output report.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aries_math.gateway_optimizer import benchmark_gateway_profile


DEFAULT_PROMPTS = [
    "2 + 2",
    "Summarize this paragraph in one sentence.",
    "Optimize ARIES gateway latency and benchmark performance.",
    "Compare two approaches and explain the trade-offs.",
    "Research the PRISE framework and derive a proof outline.",
    "Review this production security configuration for risk.",
    "Write a Python function that validates structured input.",
    "Explain how a bounded queue prevents overload.",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--prompts-file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.prompts_file:
        prompts = [
            line.strip()
            for line in args.prompts_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    else:
        prompts = DEFAULT_PROMPTS

    report = benchmark_gateway_profile(prompts, repeats=args.repeats)
    report["environment"] = {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "note": "Record CPU model, OS version, power mode, and commit SHA alongside this report for comparisons.",
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
