"""Composable performance policy and measurement helpers for ARIES/MALLIN.

This module is intentionally domain-neutral: optional platform subsystems may
propose work, but only measured latency, correctness, and resource budgets decide
whether a path is enabled. It does not implement or expose proprietary math.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Iterable, TypeVar
import math

T = TypeVar("T")


@dataclass(frozen=True)
class LatencySummary:
    samples: int
    min_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("latency samples cannot be empty")
    if not 0 <= p <= 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * p / 100
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def summarize_latencies_ms(values: Iterable[float]) -> LatencySummary:
    samples = [float(x) for x in values]
    if not samples or any(not math.isfinite(x) or x < 0 for x in samples):
        raise ValueError("provide one or more finite, non-negative latency samples")
    return LatencySummary(
        samples=len(samples),
        min_ms=round(min(samples), 3),
        mean_ms=round(sum(samples) / len(samples), 3),
        p50_ms=round(percentile(samples, 50), 3),
        p95_ms=round(percentile(samples, 95), 3),
        p99_ms=round(percentile(samples, 99), 3),
        max_ms=round(max(samples), 3),
    )


def timed_call(fn: Callable[..., T], *args, **kwargs) -> tuple[T, float]:
    """Return (result, elapsed milliseconds); exceptions propagate unchanged."""
    started = perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (perf_counter() - started) * 1000.0
    return result, elapsed_ms


def choose_path(
    *,
    baseline_ms: float,
    candidate_ms: float,
    baseline_correct: bool,
    candidate_correct: bool,
    max_regression_pct: float = 2.0,
) -> dict:
    """Promote only correct candidates; enforce latency budget against a correct baseline."""
    numbers = (baseline_ms, candidate_ms, max_regression_pct)
    if any(not math.isfinite(float(x)) for x in numbers):
        raise ValueError("latency and budget values must be finite")
    if baseline_ms < 0 or candidate_ms < 0 or max_regression_pct < 0:
        raise ValueError("latency and regression budget cannot be negative")

    allowed_ms = baseline_ms * (1.0 + max_regression_pct / 100.0)
    if not candidate_correct:
        accepted, reason = False, "candidate_incorrect"
    elif not baseline_correct:
        accepted, reason = True, "candidate_correct_baseline_incorrect"
    elif candidate_ms <= allowed_ms:
        accepted, reason = True, "correct_and_within_latency_budget"
    else:
        accepted, reason = False, "latency_budget_exceeded"

    if baseline_ms == 0:
        improvement_pct = 0.0 if candidate_ms == 0 else -100.0
    else:
        improvement_pct = (baseline_ms - candidate_ms) / baseline_ms * 100.0
    return {
        "accepted": accepted,
        "reason": reason,
        "baseline_correct": bool(baseline_correct),
        "candidate_correct": bool(candidate_correct),
        "baseline_ms": round(baseline_ms, 3),
        "candidate_ms": round(candidate_ms, 3),
        "allowed_ms": round(allowed_ms, 3),
        "latency_change_pct": round(improvement_pct, 3),
    }


def platform_readiness(results: dict[str, dict], required: tuple[str, ...]) -> dict:
    """Summarize independent subsystem checks without assuming every module helps."""
    missing = [name for name in required if name not in results]
    failed = [name for name in required if name in results and not results[name].get("passed", False)]
    return {
        "ready": not missing and not failed,
        "required_subsystems": list(required),
        "missing": missing,
        "failed": failed,
        "results": results,
    }
