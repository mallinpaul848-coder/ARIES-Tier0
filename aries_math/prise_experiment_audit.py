"""Reproducible experiment receipts for ARIES PRISE research.

Receipts make a finite run auditable; they do not certify a mathematical proof.
Only JSON-compatible inputs/results are accepted so the digest is stable.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Sequence


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("receipt values must be finite JSON-compatible data") from exc


def create_experiment_receipt(
    problem: str,
    method: str,
    input_data: Any,
    result_data: Any,
    elapsed_seconds: float,
    notes: Sequence[str] = (),
) -> Dict[str, Any]:
    """Create a deterministic SHA-256 receipt for one finite experiment.

    The digest binds the problem label, method, inputs, outputs and notes.
    Timing is reported as metadata but excluded from the digest so reruns of
    identical work can share an identity despite machine timing variation.
    """
    if not isinstance(problem, str) or not problem.strip():
        raise ValueError("problem must be a non-empty string")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    if isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, (int, float)):
        raise ValueError("elapsed_seconds must be a finite non-negative number")
    if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must be a finite non-negative number")
    if isinstance(notes, (str, bytes)):
        raise ValueError("notes must be a sequence of strings, not one string")
    note_list = list(notes)
    if any(not isinstance(note, str) for note in note_list):
        raise ValueError("each note must be a string")

    bound_payload = {
        "schema": "aries-prise-experiment-receipt-v1",
        "problem": problem.strip(),
        "method": method.strip(),
        "input": input_data,
        "result": result_data,
        "notes": note_list,
    }
    canonical = _canonical_json(bound_payload)
    return {
        **bound_payload,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "elapsed_seconds": float(elapsed_seconds),
        "evidence_class": "finite_experiment",
        "mathematical_proof": False,
        "warning": (
            "A matching digest supports integrity checking only; it does not "
            "establish correctness, generality, or a solution to an open problem."
        ),
    }


def summarize_timings(samples_seconds: Sequence[float]) -> Dict[str, Any]:
    """Summarize measured non-negative durations using nearest-rank percentiles."""
    samples = list(samples_seconds)
    if not samples:
        raise ValueError("at least one timing sample is required")
    if any(
        isinstance(x, bool) or not isinstance(x, (int, float))
        or not math.isfinite(x) or x < 0
        for x in samples
    ):
        raise ValueError("timing samples must be finite non-negative numbers")
    ordered = sorted(float(x) for x in samples)

    def nearest_rank(p: float) -> float:
        index = max(0, math.ceil(p * len(ordered)) - 1)
        return ordered[index]

    return {
        "sample_count": len(ordered),
        "min_seconds": ordered[0],
        "median_seconds": (
            ordered[len(ordered) // 2] if len(ordered) % 2
            else (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2
        ),
        "p95_seconds": nearest_rank(0.95),
        "p99_seconds": nearest_rank(0.99),
        "max_seconds": ordered[-1],
        "method": "nearest_rank_percentile",
        "evidence_class": "measured_samples",
        "mathematical_proof": False,
    }
