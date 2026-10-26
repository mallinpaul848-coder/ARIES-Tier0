"""Deterministic benchmark suite for ARIES reasoning and answer-quality baselines.

The suite intentionally measures exact-match task accuracy and categorizes tests.
It is not a substitute for MMLU, GSM8K, BBH, human evaluation, or independent validation.
"""
from __future__ import annotations

import json
import re
import statistics
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Case:
    case_id: str
    category: str
    prompt: str
    expected: str


CASES = (
    Case("math_add", "mathematics", "What is 17 + 19? Give the number only.", "36"),
    Case("math_multiply", "mathematics", "What is 12 * 13? Give the number only.", "156"),
    Case("math_fraction", "mathematics", "What is 3/4 as a decimal? Give the number only.", "0.75"),
    Case("logic_order", "logic", "A is taller than B. B is taller than C. Who is shortest? Answer with one letter.", "C"),
    Case("logic_implication", "logic", "If all zargs are blue and Mira is a zarg, what color is Mira? One word.", "blue"),
    Case("instruction_format", "instruction_following", "Reply with exactly: ARIES READY", "ARIES READY"),
    Case("instruction_list", "instruction_following", "Return exactly three words: red green blue", "red green blue"),
    Case("knowledge_planet", "basic_knowledge", "Which planet is known as the Red Planet? One word.", "Mars"),
    Case("knowledge_water", "basic_knowledge", "At standard sea-level pressure, water freezes at what Celsius temperature? Number only.", "0"),
    Case("coding_python", "coding", "In Python, what keyword defines a function? One word.", "def"),
    Case("safety_uncertainty", "calibration", "Does this prompt provide enough information to know the user's age? Answer yes or no: 'Tell me a joke.'", "no"),
    Case("reasoning_evidence", "evidence_awareness", "Can a source-free claim be called independently verified solely because it sounds plausible? Answer yes or no.", "no"),
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def score_answer(expected: str, actual: str) -> bool:
    return normalize(expected) == normalize(actual)


def run_benchmark(answer_fn: Callable[[str], str], *, backend_name: str = "unspecified") -> dict:
    results = []
    for case in CASES:
        start = time.perf_counter_ns()
        error = None
        try:
            actual = answer_fn(case.prompt)
            if not isinstance(actual, str):
                actual = str(actual)
        except Exception as exc:  # benchmark records errors instead of hiding them
            actual = ""
            error = type(exc).__name__ + ": " + str(exc)
        elapsed_ns = max(1, time.perf_counter_ns() - start)
        results.append({
            **asdict(case),
            "actual": actual,
            "correct": score_answer(case.expected, actual),
            "latency_ms": elapsed_ns / 1_000_000,
            "error": error,
        })
    latencies = [row["latency_ms"] for row in results]
    categories = {}
    for row in results:
        group = categories.setdefault(row["category"], {"total": 0, "correct": 0})
        group["total"] += 1
        group["correct"] += int(row["correct"])
    for group in categories.values():
        group["accuracy"] = group["correct"] / group["total"] if group["total"] else 0.0
    ordered = sorted(latencies)
    def percentile(p: float) -> float:
        if not ordered:
            return 0.0
        pos = (len(ordered) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
    correct = sum(row["correct"] for row in results)
    return {
        "benchmark": "aries_reasoning_quality_smoke_v1",
        "backend": backend_name,
        "case_count": len(results),
        "correct_count": correct,
        "exact_match_accuracy": correct / len(results) if results else 0.0,
        "category_accuracy": categories,
        "latency_ms": {
            "min": min(latencies, default=0.0),
            "mean": statistics.mean(latencies) if latencies else 0.0,
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "max": max(latencies, default=0.0),
        },
        "cases": results,
        "limitations": [
            "Small deterministic smoke benchmark; not a standard academic benchmark.",
            "Exact-match scoring can mark semantically correct answers wrong.",
            "A high score does not prove broad intelligence or self-awareness.",
            "Compare backends only when prompts, hardware, settings, and conditions match.",
        ],
    }


def write_report(report: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
