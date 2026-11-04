"""Mallin–PRISE request features for the ARIES Gateway X fast path.

This module turns the user's mathematical highlights into deterministic,
bounded request metadata. The features are advisory only: they never decide
whether an answer is true, never replace the exact task router, and never
collapse distinct prompts into the same cache key.
"""
from __future__ import annotations

from hashlib import sha256
import string
import time
from typing import Any

from .prise_research_engine import DigitalRootSystem, PRISEProfile, helixo_features, phase8


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def analyze_gateway_request(prompt: str) -> dict[str, Any]:
    """Compute an auditable Mallin–PRISE profile in linear time and O(n) auxiliary space, where n is prompt length."""
    started_ns = time.perf_counter_ns()
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    normalized = " ".join(prompt.strip().split())
    lower = normalized.casefold()
    words = normalized.split()
    encoded = normalized.encode("utf-8")
    byte_count = len(encoded)
    char_sum = sum(encoded)
    digit_count = sum(ch.isdigit() for ch in normalized)
    punctuation_count = sum(ch in string.punctuation for ch in normalized)

    # PRISE dimensions are transparent keyword heuristics, not probabilities.
    priority = 1.0 if _contains_any(lower, ("urgent", "priority", "deadline", "asap")) else 0.25
    risk = 1.0 if _contains_any(lower, (
        "medical", "diagnosis", "legal", "financial", "password", "credential",
        "security", "production", "delete", "safety", "unsafe",
    )) else 0.20
    impact = 1.0 if _contains_any(lower, (
        "performance", "latency", "optimize", "improve", "benchmark", "upgrade",
    )) else 0.40
    systemic = 1.0 if _contains_any(lower, (
        "integrate", "integration", "architecture", "dependency", "gateway", "system",
    )) else 0.20
    emergent = 1.0 if _contains_any(lower, (
        "research", "derive", "proof", "novel", "complex", "step by step",
    )) else 0.20
    profile = PRISEProfile(
        priority=priority, risk=risk, impact=impact,
        systemic=systemic, emergent=emergent,
    )

    # 3–6–9 and Phase-8 are deterministic descriptors, not correctness tests.
    root = DigitalRootSystem.compute(char_sum)
    phase = phase8(float(len(words)), float((digit_count + punctuation_count) % 8))
    helixo = helixo_features((
        float(byte_count), float(len(words)), float(digit_count),
        float(punctuation_count),
    ))
    risk_review = risk >= 1.0
    needs_scaffold = (
        risk_review
        or len(normalized) > 280
        or _contains_any(lower, (
            "prise", "mallin", "proof", "derive", "analyze", "analyse",
            "compare", "evaluate", "research", "step by step",
        ))
    )
    if risk_review:
        route_hint = "review_first"
    elif needs_scaffold:
        route_hint = "reasoning_scaffold_candidate"
    else:
        route_hint = "fast_path_candidate"

    elapsed_ns = max(0, time.perf_counter_ns() - started_ns)
    return {
        "version": "1.0.0",
        "fingerprint_sha256": sha256(encoded).hexdigest(),
        "fingerprint_scope": "exact whitespace-normalized UTF-8 prompt; case preserved",
        "input": {
            "byte_count": byte_count,
            "word_count": len(words),
            "digit_count": digit_count,
            "punctuation_count": punctuation_count,
        },
        "harmonic": {
            "byte_sum_digital_root": root,
            "is_3_6_9_node": root in (3, 6, 9),
            "phase8": phase,
            "helixo": helixo,
            "interpretation": "descriptive routing features only; not an answer-quality score",
        },
        "prise": {
            "profile": {
                "priority": priority, "risk": risk, "impact": impact,
                "systemic": systemic, "emergent": emergent,
            },
            "score": profile.score(),
            "score_is_probability": False,
            "classification_is_heuristic": True,
        },
        "routing": {
            "hint": route_hint,
            "reasoning_scaffold_recommended": needs_scaffold,
            "high_risk_review_flag": risk_review,
            "hint_is_advisory": True,
        },
        "elapsed_ns": elapsed_ns,
    }



def benchmark_gateway_profile(prompts: list[str], repeats: int = 5) -> dict[str, Any]:
    """Measure profiling overhead only; does not measure model inference latency.

    Each prompt is analyzed repeatedly. The report includes raw samples and
    robust percentiles so callers can compare this feature cost against a
    separately measured baseline on the same machine.
    """
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    if not prompts:
        raise ValueError("prompts must not be empty")
    # One unrecorded pass reduces first-call/import/cache effects in the samples.
    for prompt in prompts:
        analyze_gateway_request(prompt)
    samples: list[int] = []
    for _ in range(repeats):
        for prompt in prompts:
            started = time.perf_counter_ns()
            analyze_gateway_request(prompt)
            # Measure the complete function call, including hashing and result construction.
            samples.append(max(0, time.perf_counter_ns() - started))
    ordered = sorted(samples)

    def percentile(p: float) -> float:
        pos = (len(ordered) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        frac = pos - lo
        return ordered[lo] * (1.0 - frac) + ordered[hi] * frac

    return {
        "benchmark": "mallin_prise_gateway_profile_only",
        "scope": "complete profile function call including normalization, feature calculation, hashing, and result construction; excludes HTTP, queueing, model prefill, and generation",
        "prompt_count": len(prompts),
        "repeats": repeats,
        "warmup_passes": 1,
        "sample_count": len(samples),
        "latency_ns": {
            "min": min(samples),
            "mean": sum(samples) / len(samples),
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
            "max": max(samples),
        },
        "samples_ns": samples,
    }
