"""Small, testable adapter from ARIES chat requests to the reasoning scaffold."""
from __future__ import annotations

from aries_math.reasoning_engine import decompose_question


def analyze_request(question: str) -> dict:
    """Return the deterministic question plan exposed by the API."""
    return decompose_question(question)


def build_reasoning_context(question: str) -> str:
    """Build concise instructions for a chat model; never fabricate evidence or conclusions."""
    plan = decompose_question(question)
    checks = "\n".join(f"- {item}" for item in plan["checks"])
    return (
        "ARIES reasoning checklist (process guidance, not evidence):\n"
        f"Task goal: {plan['goal']}\n"
        "Before answering, apply these checks where relevant:\n"
        f"{checks}\n"
        "Use only evidence actually available in the conversation or supplied sources. "
        "Do not claim these checks prove the answer is correct. If the task is simple, answer directly."
    )
