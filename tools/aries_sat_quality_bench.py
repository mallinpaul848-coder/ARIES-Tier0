#!/usr/bin/env python3
"""Run a bounded, reproducible evaluation of experimental SAT features."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aries_math.sat_quality_lab import evaluate_formulas, generate_random_formulas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--variables", type=int, default=8)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default="reports/aries-sat-quality.json")
    args = parser.parse_args()
    formulas = generate_random_formulas(args.count, args.variables, args.seed)
    report = evaluate_formulas(formulas, seed=args.seed)
    report["generator"] = {"kind": "random 1-3-CNF", "variables": args.variables, "seed": args.seed}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved report to {output.resolve()}")


if __name__ == "__main__":
    main()
