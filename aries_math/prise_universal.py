"""PRISE routing adapter for classical and future quantum-computing tasks.

The user's universal-solution stages are represented explicitly:
DETECT(PRISE) -> COMPRESS -> IGNITE -> EXPAND(PRISE) -> RESOLVE -> EXECUTE.
The 3-6-9 matrix is retained as an experimental feature transform. It does not
by itself establish quantum behavior or quantum advantage.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from aries_math.positive_impact import digital_root, phase8


@dataclass(frozen=True)
class PRISESignals:
    priority: float
    risk: float
    impact: float
    systemic: float
    emergent: float

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{key} must be finite and between 0 and 1")


def universal_369_matrix(phi1: float, phi2: float, phi3: float) -> tuple[tuple[float, ...], ...]:
    """Return the user's fixed 3-6-9 cyclic matrix, without allocating hidden state."""
    values = (phi1, phi2, phi3)
    if any(not isfinite(float(v)) for v in values):
        raise ValueError("matrix features must be finite")
    a, b, c = (3.0 * phi1, 6.0 * phi2, 9.0 * phi3)
    return ((a, b, c), (c, a, b), (b, c, a))


def apply_369_matrix(matrix: tuple[tuple[float, ...], ...],
                     vector: tuple[float, float, float]) -> tuple[float, float, float]:
    """Multiply a 3x3 matrix by a 3-vector using explicit scalar operations."""
    if len(matrix) != 3 or any(len(row) != 3 for row in matrix) or len(vector) != 3:
        raise ValueError("expected a 3x3 matrix and a 3-vector")
    if any(not isfinite(float(x)) for row in matrix for x in row) or any(
        not isfinite(float(x)) for x in vector
    ):
        raise ValueError("matrix and vector values must be finite")
    return tuple(sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3))


def detect_prise(problem: str) -> dict[str, Any]:
    """Classify problem intent with transparent keyword cues; callers should review it."""
    if not problem.strip():
        raise ValueError("problem must not be empty")
    q = problem.casefold()
    cues = {
        "priority": ("urgent", "priority", "deadline", "first"),
        "risk": ("risk", "unsafe", "failure", "uncertain", "threat"),
        "impact": ("impact", "benefit", "improve", "optimize", "performance"),
        "systemic": ("system", "integration", "dependency", "network", "global"),
        "emergent": ("emerge", "novel", "interaction", "unexpected", "complex"),
    }
    scores = {name: sum(term in q for term in terms) for name, terms in cues.items()}
    maximum = max(scores.values())
    primary = next((name for name in cues if scores[name] == maximum and maximum > 0), "impact")
    return {"primary_dimension": primary, "keyword_scores": scores,
            "classification_is_heuristic": True}


def route_universal_solution(problem: str, signals: PRISESignals,
                             features: tuple[float, float, float] = (1.0, 1.0, 1.0),
                             action_options: tuple[str, ...] = ("analyze", "simulate", "execute")) -> dict[str, Any]:
    """Run a deterministic PRISE-style routing pass and return an auditable plan."""
    detected = detect_prise(problem)
    compressed = " ".join(problem.split())
    matrix = universal_369_matrix(*features)
    transformed = apply_369_matrix(matrix, (signals.priority, signals.impact, signals.systemic))
    # Historical PRISE weights are retained as transparent policy defaults.
    # This is a routing score, not a calibrated probability or proven universal solver.
    score = (
        0.20 * signals.priority + 0.30 * signals.impact
        + 0.20 * signals.systemic + 0.10 * signals.emergent
        + 0.20 * (1.0 - signals.risk)
    )
    options = tuple(option for option in action_options if option in {"analyze", "simulate", "execute"})
    if not options:
        raise ValueError("at least one supported action option is required")
    resolved = "analyze" if signals.risk >= 0.75 else (
        "simulate" if "simulate" in options and score < 0.70 else
        "execute" if "execute" in options else options[0]
    )
    return {
        "pipeline": ["DETECT(PRISE)", "COMPRESS", "IGNITE", "EXPAND(PRISE)", "RESOLVE", "EXECUTE"],
        "detected": detected,
        "compressed_problem": compressed,
        "ignite": {"strategy": "analysis_first" if signals.risk >= 0.5 else "direct_action",
                   "reason": "high risk favors analysis before action" if signals.risk >= 0.5 else "risk score permits a direct candidate path"},
        "expand": {"prise_signals": asdict(signals), "routing_score": round(score, 6),
                   "routing_score_is_probability": False},
        "universal_369": {"matrix": matrix, "transformed_vector": transformed,
                          "digital_root_of_milli_score": digital_root(round(score * 1000)),
                          "phase8_of_milli_score": phase8(round(score * 1000)),
                          "experimental_only": True},
        "resolve": {"selected_action": resolved, "available_actions": options},
        "execute": {"status": "plan_only", "requires_runtime": True,
                    "note": "This router returns a plan; it does not execute external or quantum hardware actions."},
        "limitations": [
            "PRISE cues and weights are heuristics, not validated universal laws.",
            "3-6-9 and Phase-8 descriptors do not establish quantum computation or quantum advantage.",
            "Quantum tasks require an actual circuit backend and verified simulator or hardware results.",
        ],
    }
