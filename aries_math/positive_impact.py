"""Deterministic positive-impact scoring for ARIES/MALLIN.

This is a transparent prioritization heuristic, not a proof of truth or a substitute
for safety review. Core scoring uses explicit impact/risk inputs. Digital-root and
Phase-8 signals are optional experimental metadata and never change the core score.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class ImpactInputs:
    """All scalar inputs are normalized to [0, 1]. Higher risk means more risk."""
    priority: float
    benefit: float
    risk: float
    systemic_effect: float
    emergence: float
    confidence: float = 1.0
    reversibility: float = 0.5


def _unit(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1")
    return value


def digital_root(n: int) -> int:
    """Return the base-10 digital root; zero maps to zero."""
    n = abs(int(n))
    return 0 if n == 0 else 1 + (n - 1) % 9


def phase8(value: int) -> int:
    """Map an integer onto the eight-phase ring [0, 7]. Experimental descriptor."""
    return int(value) % 8


def score_positive_impact(inputs: ImpactInputs) -> dict[str, Any]:
    """Score an option using transparent PRISE-inspired weighted components.

    benefit_score rewards benefit, priority, systemic effect and emergence.
    risk-adjusted value discounts benefit by risk, uncertainty and irreversibility.
    Weights are explicit policy defaults, not empirically established constants.
    """
    p = _unit("priority", inputs.priority)
    b = _unit("benefit", inputs.benefit)
    r = _unit("risk", inputs.risk)
    s = _unit("systemic_effect", inputs.systemic_effect)
    e = _unit("emergence", inputs.emergence)
    c = _unit("confidence", inputs.confidence)
    rev = _unit("reversibility", inputs.reversibility)

    upside = 0.35 * b + 0.20 * p + 0.20 * s + 0.10 * e + 0.15 * c
    risk_penalty = 0.60 * r + 0.25 * (1.0 - c) + 0.15 * (1.0 - rev)
    net = max(0.0, min(1.0, upside * (1.0 - risk_penalty)))

    return {
        "method": "PRISE-positive-impact-v1",
        "score": round(net, 6),
        "upside": round(upside, 6),
        "risk_penalty": round(risk_penalty, 6),
        "decision_band": (
            "high-priority-review" if net >= 0.70 else
            "consider" if net >= 0.40 else
            "defer-or-revise"
        ),
        "components": {
            "priority": p, "benefit": b, "risk": r,
            "systemic_effect": s, "emergence": e,
            "confidence": c, "reversibility": rev,
        },
        "experimental_signals": {
            "digital_root_score_milli": digital_root(round(net * 1000)),
            "phase8_score_milli": phase8(round(net * 1000)),
            "used_in_core_score": False,
        },
        "limitations": [
            "Heuristic ranking only; inputs and weights require domain validation.",
            "Not a causal model, safety certification, or proof of mathematical novelty.",
            "Review high-risk, low-confidence, irreversible actions separately.",
        ],
    }


def rank_positive_impact(options: list[tuple[str, ImpactInputs]]) -> list[dict[str, Any]]:
    """Return options sorted by score descending, preserving input order on ties."""
    ranked = []
    for index, (name, inputs) in enumerate(options):
        if not str(name).strip():
            raise ValueError("option name must not be empty")
        ranked.append({"name": str(name), **score_positive_impact(inputs), "_index": index})
    ranked.sort(key=lambda item: (-item["score"], item["_index"]))
    for item in ranked:
        item.pop("_index")
    return ranked
