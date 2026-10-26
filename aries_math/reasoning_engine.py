"""Evidence-aware reasoning utilities for ARIES/MALLIN.

This module provides a deterministic reasoning scaffold: decompose a question,
track evidence and uncertainty, compare hypotheses, flag contradictions, and rank
next steps. It does not generate knowledge by itself and is not a substitute for an
LLM, validated domain model, or human review.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class Evidence:
    statement: str
    supports: str
    strength: float = 0.5
    source: str = "unspecified"

    def __post_init__(self) -> None:
        if not self.statement.strip() or not self.supports.strip():
            raise ValueError("statement and supports must be non-empty")
        if not 0.0 <= float(self.strength) <= 1.0:
            raise ValueError("strength must be between 0 and 1")


@dataclass(frozen=True)
class Hypothesis:
    name: str
    prior: float = 0.5

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("hypothesis name must be non-empty")
        if not 0.0 <= float(self.prior) <= 1.0:
            raise ValueError("prior must be between 0 and 1")


def decompose_question(question: str) -> dict:
    """Return a lightweight, explainable question-analysis scaffold."""
    q = " ".join(question.split())
    if not q:
        raise ValueError("question must not be empty")
    parts = [p.strip(" \t") for p in q.replace("?", ".").split(".") if p.strip()]
    lower = q.lower()
    goal = "explain or answer the question"
    if any(w in lower for w in ("should i", "should we", "best option", "which option")):
        goal = "compare options and recommend a justified next step"
    elif any(w in lower for w in ("why", "cause", "reason")):
        goal = "identify plausible explanations and distinguish evidence from speculation"
    elif any(w in lower for w in ("how", "steps", "implement", "build")):
        goal = "derive an ordered, testable plan"
    return {
        "question": q,
        "goal": goal,
        "subquestions": parts,
        "checks": [
            "identify known facts and missing information",
            "generate at least one alternative explanation where relevant",
            "check contradictions and assumptions",
            "state uncertainty and what evidence would change the conclusion",
        ],
    }


def evaluate_hypotheses(
    hypotheses: Iterable[Hypothesis], evidence: Iterable[Evidence]
) -> list[dict]:
    """Rank hypotheses with a transparent support-minus-counterevidence heuristic.

    Evidence.supports must equal a hypothesis name. Strengths for matching evidence
    add support; evidence that explicitly supports another listed hypothesis counts
    as counterevidence. This is a ranking aid, not Bayesian inference or probability.
    """
    hs = list(hypotheses)
    evs = list(evidence)
    if not hs:
        raise ValueError("at least one hypothesis is required")
    names = [h.name for h in hs]
    if len(set(names)) != len(names):
        raise ValueError("hypothesis names must be unique")
    unknown = sorted({e.supports for e in evs if e.supports not in names})
    if unknown:
        raise ValueError(f"evidence references unknown hypotheses: {unknown}")

    out = []
    for index, h in enumerate(hs):
        support = sum(e.strength for e in evs if e.supports == h.name)
        counter = sum(e.strength for e in evs if e.supports != h.name)
        raw = h.prior + support - counter
        score = max(0.0, min(1.0, raw / (1.0 + sum(e.strength for e in evs))))
        out.append({
            "hypothesis": h.name,
            "prior": round(h.prior, 4),
            "support_strength": round(support, 4),
            "counterevidence_strength": round(counter, 4),
            "heuristic_score": round(score, 4),
            "score_is_probability": False,
            "_index": index,
        })
    out.sort(key=lambda x: (-x["heuristic_score"], x["_index"]))
    for row in out:
        row.pop("_index")
    return out


def find_conflicts(facts: Iterable[str]) -> list[dict]:
    """Flag exact-text negation pairs such as 'X' and 'not X'.

    This conservative check is intentionally not a general natural-language
    contradiction detector; it avoids pretending semantic conflict detection is solved.
    """
    normalized = [" ".join(f.split()).strip() for f in facts if f.strip()]
    lowered = {f.lower(): f for f in normalized}
    conflicts = []
    seen = set()
    for fact in normalized:
        low = fact.lower()
        if low.startswith("not "):
            opposite = low[4:].strip()
        else:
            opposite = "not " + low
        if opposite in lowered:
            pair = tuple(sorted((low, opposite)))
            if pair not in seen:
                conflicts.append({"fact_a": lowered[pair[0]], "fact_b": lowered[pair[1]]})
                seen.add(pair)
    return conflicts


def build_reasoning_report(
    question: str,
    hypotheses: Iterable[Hypothesis] = (),
    evidence: Iterable[Evidence] = (),
    facts: Iterable[str] = (),
) -> dict:
    """Compose a compact report with explicit limitations and follow-up checks."""
    hs, evs, fs = list(hypotheses), list(evidence), list(facts)
    ranked = evaluate_hypotheses(hs, evs) if hs else []
    conflicts = find_conflicts(fs)
    return {
        "engine": "ARIES-Evidence-Reasoning-Scaffold-v1",
        "analysis": decompose_question(question),
        "hypotheses": ranked,
        "conflicts": conflicts,
        "evidence_count": len(evs),
        "known_limitations": [
            "Deterministic scaffold only; it does not independently verify source truth.",
            "Heuristic scores are not probabilities and must not be presented as certainty.",
            "Contradiction detection currently catches only simple explicit negation pairs.",
            "Health, legal, safety, and other high-stakes conclusions require qualified review.",
        ],
        "next_step": (
            "Resolve conflicting facts and gather stronger evidence."
            if conflicts else
            "Test the leading explanation against an alternative and seek disconfirming evidence."
        ),
    }
