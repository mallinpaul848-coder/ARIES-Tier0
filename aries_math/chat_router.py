"""Deterministic chat routing for ARIES mathematical tools.

These are explicit, bounded tools, not a claim that experimental features improve
all tasks or solve P vs NP. Returns None when a prompt does not match a supported
command so normal inference can continue.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .prise_unified import (
    ARIESExecutionEngine,
    PRISEProblem,
    exact_sat_bruteforce,
)
from .prise_research_engine import DigitalRootSystem as ResearchDigitalRoot, phase8, vortex369, helixo_features
from .prise_research_engine import ARIESPRISEResearchEngine, PRIZE_PROBLEM_ROUTES

_BINARY_ENGINE = ARIESExecutionEngine()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def route_math_prompt(prompt: str) -> dict[str, str] | None:
    """Route supported explicit math prompts; otherwise return None."""
    text = str(prompt).strip()
    lower = text.lower()

    # Explicit Mallin research request for a named Millennium Prize problem.
    if any(term in lower for term in (
        "mallin", "prise", "analyze", "analyse", "proof obligation", "research route"
    )):
        aliases = {
            "P_VS_NP": ("p vs np", "p versus np", "p-vs-np", "sat complexity"),
            "RIEMANN_HYPOTHESIS": ("riemann hypothesis", "riemann"),
            "NAVIER_STOKES": ("navier-stokes", "navier stokes"),
            "YANG_MILLS": ("yang-mills", "yang mills"),
            "HODGE_CONJECTURE": ("hodge conjecture",),
            "BIRCH_SWINNERTON_DYER": (
                "birch-swinderton-dyer", "birch and swinnerton-dyer",
                "birch swinnerton dyer", "bsd conjecture",
            ),
        }
        selected = next(
            (key for key, names in aliases.items() if any(name in lower for name in names)),
            None,
        )
        if selected:
            values_match = re.search(
                r"\b(?:values|series|samples)\s*[:=]\s*(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+)",
                lower,
            )
            values = [float(part.strip()) for part in values_match.group(1).split(",")] if values_match else []
            result = ARIESPRISEResearchEngine().analyze(selected, values)
            return {"route": "mallin_prise_research", "answer": _json(result)}

    # Exact digital-root arithmetic.
    match = re.search(r"\b(?:digital\s+root|digitalroot)\s+(?:of\s+)?(-?\d+)\b", lower)
    if match:
        n = int(match.group(1))
        return {
            "route": "digital_root_369",
            "answer": _json({"input": n, **ResearchDigitalRoot.triad(n),
                             "is_3_6_9": (n != 0 and abs(n) % 3 == 0)}),
        }

    # Phase-8 vector descriptor.
    match = re.search(r"\bphase\s*[- ]?8\s*(?:for|of|vector)?\s*[:=(]?\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)", lower)
    if match:
        result = phase8(float(match.group(1)), float(match.group(2)))
        return {"route": "phase8_vector", "answer": _json(result)}

    # Vortex cycle descriptor.
    match = re.search(r"\bvortex(?:\s*369)?\s+(?:of\s+)?(-?\d+)\b", lower)
    if match:
        n = int(match.group(1))
        return {"route": "vortex369", "answer": _json({"input": n, "cycle_value": vortex369(n),
                                                            "cycle": [1, 2, 4, 8, 7, 5]})}

    # Helixo features for a comma-separated numeric series.
    match = re.search(r"\bhelixo\s+(?:features?\s+)?(?:of\s+)?[:=]?\s*(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+)", lower)
    if match:
        values = [float(part.strip()) for part in match.group(1).split(",")]
        return {"route": "helixo_features", "answer": _json(helixo_features(values))}

    # Analyze a quoted/text payload as UTF-8 bytes; this is a descriptor, not
    # a disassembler or security scanner for executable binaries.
    match = re.search(r"\b(?:analyze|analyse)\s+binary\s+(?:payload|text|stream)\s*[:=]\s*(.+)", text, re.I | re.S)
    if match:
        result = _BINARY_ENGINE.analyze_binary_stream(match.group(1).encode("utf-8"))
        return {"route": "binary_feature_analysis", "answer": _json(result)}

    # Explicit SAT JSON command, e.g. "SAT JSON: {\"clauses\":[[1,-2],[2]],\"variable_count\":2}"
    match = re.search(r"\bsat\s+json\s*:\s*(\{.*\})\s*$", text, re.I | re.S)
    if match:
        payload = json.loads(match.group(1))
        clauses, variable_count = payload.get("clauses"), payload.get("variable_count")
        if not isinstance(clauses, list) or not isinstance(variable_count, int) or isinstance(variable_count, bool):
            return {"route": "exact_sat_bruteforce", "answer": "Invalid SAT JSON: provide clauses as a list and variable_count as an integer."}
        result = exact_sat_bruteforce(clauses, variable_count)
        result["notice"] = "Bounded exhaustive SAT baseline; exponential worst-case runtime; not a P-vs-NP proof."
        return {"route": "exact_sat_bruteforce", "answer": _json(result)}

    # PRISE weighted score from explicit key=value fields.
    if "prise score" in lower:
        values: dict[str, float] = {}
        for key in ("priority", "risk", "impact", "systemic", "emergent"):
            found = re.search(rf"\b{key}\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)\b", lower)
            if found:
                values[key] = float(found.group(1))
        if len(values) == 5:
            problem = PRISEProblem(
                name="Chat-request PRISE analysis",
                priority=values["priority"], risk=values["risk"],
                impact=values["impact"], systemic=values["systemic"],
                emergent=values["emergent"],
            )
            return {"route": "prise_scoring", "answer": _json(problem.to_dict())}

    return None
