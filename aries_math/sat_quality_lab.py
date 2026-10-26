"""Reproducible finite-instance evaluation of experimental SAT features.

This lab tests whether modular/PRISE-inspired descriptors carry predictive signal
on bounded CNF samples. Exact labels are obtained by exhaustive enumeration, so
instances are intentionally small. Results are empirical and distribution-specific;
they are not a polynomial-time SAT algorithm or a P-vs-NP proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
import random
from typing import Any, Sequence

from .prise_research_engine import DigitalRootSystem, phase8, vortex369


def validate_cnf(clauses: Sequence[Sequence[int]], variable_count: int, max_variables: int = 16) -> list[list[int]]:
    if isinstance(variable_count, bool) or not isinstance(variable_count, int) or not 0 <= variable_count <= max_variables:
        raise ValueError(f"variable_count must be an integer from 0 to {max_variables}")
    if not isinstance(clauses, (list, tuple)):
        raise ValueError("clauses must be a list or tuple")
    result: list[list[int]] = []
    for clause in clauses:
        if not isinstance(clause, (list, tuple)):
            raise ValueError("each clause must be a list or tuple")
        normalized: list[int] = []
        for literal in clause:
            if isinstance(literal, bool) or not isinstance(literal, int) or literal == 0 or abs(literal) > variable_count:
                raise ValueError("literals must be non-zero integers within variable_count")
            normalized.append(literal)
        result.append(normalized)
    return result


def exact_sat_label(clauses: Sequence[Sequence[int]], variable_count: int, max_variables: int = 16) -> bool:
    """Return exact satisfiability by exhaustive enumeration; exponential in variables."""
    cnf = validate_cnf(clauses, variable_count, max_variables)
    for mask in range(1 << variable_count):
        if all(any(((mask >> (abs(lit) - 1)) & 1) == (lit > 0) for lit in clause) for clause in cnf):
            return True
    return False


def feature_signature(clauses: Sequence[Sequence[int]], variable_count: int) -> tuple[int, ...]:
    """A deliberately small, inspectable feature signature for collision analysis."""
    cnf = validate_cnf(clauses, variable_count)
    clause_count = len(cnf)
    literal_count = sum(map(len, cnf))
    positive = sum(lit > 0 for clause in cnf for lit in clause)
    negative = literal_count - positive
    max_width = max((len(c) for c in cnf), default=0)
    root = DigitalRootSystem.compute(clause_count * 31 + literal_count * 7 + positive * 3 + variable_count)
    vortex = vortex369(clause_count + literal_count + variable_count)
    direction = phase8(positive - negative, clause_count - variable_count)["phase"]
    # Include raw coarse structural counts as well as the experimental transforms.
    return (variable_count, clause_count, literal_count, positive, negative, max_width, root, vortex, -1 if direction is None else direction)


def _balanced_accuracy(y_true: list[bool], y_pred: list[bool]) -> float:
    recalls = []
    for label in (False, True):
        indexes = [i for i, value in enumerate(y_true) if value is label]
        if indexes:
            recalls.append(sum(y_pred[i] is label for i in indexes) / len(indexes))
    return sum(recalls) / len(recalls) if recalls else 0.0


def evaluate_formulas(formulas: Sequence[dict[str, Any]], seed: int = 7, train_fraction: float = 0.7) -> dict[str, Any]:
    """Evaluate a train-only signature lookup against a majority-class baseline."""
    if not 0.1 <= train_fraction <= 0.9:
        raise ValueError("train_fraction must be between 0.1 and 0.9")
    rows = []
    for item in formulas:
        cnf = validate_cnf(item.get("clauses"), item.get("variable_count"))
        n = item["variable_count"]
        rows.append({"signature": feature_signature(cnf, n), "label": exact_sat_label(cnf, n)})
    if len(rows) < 4:
        raise ValueError("at least four formulas are required")
    rng = random.Random(seed)
    order = list(range(len(rows)))
    rng.shuffle(order)
    split = min(len(rows) - 1, max(1, int(len(rows) * train_fraction)))
    train, test = [rows[i] for i in order[:split]], [rows[i] for i in order[split:]]
    counts: dict[tuple[int, ...], Counter] = defaultdict(Counter)
    for row in train:
        counts[row["signature"]][row["label"]] += 1
    train_labels = [r["label"] for r in train]
    majority = Counter(train_labels).most_common(1)[0][0]
    truth = [r["label"] for r in test]
    baseline = [majority] * len(test)
    predictions = [counts[sig].most_common(1)[0][0] if sig in counts else majority for sig in (r["signature"] for r in test)]
    correct_signature = sum(a == b for a, b in zip(truth, predictions))
    correct_baseline = sum(a == b for a, b in zip(truth, baseline))
    all_labels: dict[tuple[int, ...], set[bool]] = defaultdict(set)
    for row in rows:
        all_labels[row["signature"]].add(row["label"])
    conflicts = sum(len(labels) > 1 for labels in all_labels.values())
    canonical = json.dumps([{"signature": r["signature"], "label": r["label"]} for r in rows], sort_keys=True, separators=(",", ":"))
    return {
        "experiment": "bounded_sat_feature_quality",
        "seed": seed,
        "formula_count": len(rows),
        "train_count": len(train),
        "test_count": len(test),
        "signature_unique_count": len(all_labels),
        "signatures_with_both_sat_labels": conflicts,
        "signature_conflict_rate_percent": round(100 * conflicts / max(1, len(all_labels)), 3),
        "test_accuracy_percent": round(100 * correct_signature / len(test), 3),
        "majority_baseline_accuracy_percent": round(100 * correct_baseline / len(test), 3),
        "test_balanced_accuracy_percent": round(100 * _balanced_accuracy(truth, predictions), 3),
        "test_balanced_baseline_percent": round(100 * _balanced_accuracy(truth, baseline), 3),
        "fingerprint_sha256": sha256(canonical.encode()).hexdigest(),
        "limitations": [
            "Exhaustive labels are limited to small CNFs and scale exponentially.",
            "Metrics apply only to this generated/supplied distribution and split.",
            "A feature signature is not a SAT solver; conflicting signatures expose information loss.",
            "No P-vs-NP claim, generalization guarantee, or sub-nanosecond claim is made."
        ],
    }


def generate_random_formulas(count: int = 100, variable_count: int = 8, seed: int = 7) -> list[dict[str, Any]]:
    if isinstance(count, bool) or not isinstance(count, int) or count < 4 or count > 10000:
        raise ValueError("count must be an integer from 4 to 10000")
    if isinstance(variable_count, bool) or not isinstance(variable_count, int) or not 1 <= variable_count <= 16:
        raise ValueError("variable_count must be an integer from 1 to 16")
    rng = random.Random(seed)
    formulas = []
    for _ in range(count):
        clause_count = rng.randint(max(1, variable_count // 2), variable_count * 2)
        clauses = []
        for _ in range(clause_count):
            width = rng.randint(1, min(3, variable_count))
            variables = rng.sample(range(1, variable_count + 1), width)
            clauses.append([v if rng.getrandbits(1) else -v for v in variables])
        formulas.append({"clauses": clauses, "variable_count": variable_count})
    return formulas
