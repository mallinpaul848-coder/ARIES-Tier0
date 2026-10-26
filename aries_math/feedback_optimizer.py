"""Bounded feedback optimization using measured objective values only.
Callers supply an evaluator and candidate generator; adoption requires repeated
measurements. This does not claim quantum advantage or automatic self-awareness.
"""
from dataclasses import dataclass
from math import isfinite
from statistics import median
from typing import Callable, Iterable, TypeVar
T = TypeVar("T")

@dataclass(frozen=True)
class Trial:
    candidate: str
    measurements: tuple[float, ...]
    median_score: float
    accepted: bool
    reason: str

@dataclass
class OptimizationReport:
    baseline_median: float
    best_median: float
    trials: list[Trial]
    best_candidate: str

def optimize_bounded(baseline: T, candidates: Iterable[T], evaluate: Callable[[T], float],
                     describe: Callable[[T], str] = lambda x: repr(x), *,
                     trials_per_candidate: int = 5, max_candidates: int = 20,
                     min_relative_improvement: float = 0.03,
                     lower_is_better: bool = True) -> tuple[T, OptimizationReport]:
    """Choose only candidates with a repeatable median improvement over current best."""
    if trials_per_candidate < 3:
        raise ValueError("use at least 3 repeated measurements")
    if max_candidates < 0 or not 0 <= min_relative_improvement < 1:
        raise ValueError("invalid optimization bounds")
    def measure(value: T) -> tuple[float, ...]:
        vals = tuple(float(evaluate(value)) for _ in range(trials_per_candidate))
        if not all(isfinite(v) and v >= 0 for v in vals):
            raise ValueError("evaluator must return finite, non-negative metrics")
        return vals
    base_vals = measure(baseline)
    base_score = median(base_vals)
    best, best_score = baseline, base_score
    history: list[Trial] = []
    for index, candidate in enumerate(candidates):
        if index >= max_candidates:
            break
        vals = measure(candidate)
        score = median(vals)
        improves = (score < best_score * (1 - min_relative_improvement)) if lower_is_better else (score > best_score * (1 + min_relative_improvement))
        accepted = bool(improves)
        reason = "accepted: repeated median meets improvement margin" if accepted else "rejected: insufficient measured improvement"
        history.append(Trial(describe(candidate), vals, score, accepted, reason))
        if accepted:
            best, best_score = candidate, score
    return best, OptimizationReport(base_score, best_score, history, describe(best))