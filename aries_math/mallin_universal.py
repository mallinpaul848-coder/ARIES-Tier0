"""Mallin universal SAT-projection audit.

Implements the user's q3/q6/q9 projection idea as a falsifiable experiment:
compute modular features, compare them against exact SAT labels on bounded CNFs,
and return concrete collisions/counterexamples. A finite audit cannot prove P=NP.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

from .prise_unified import exact_sat_bruteforce


def _validate_cnf(clauses: Sequence[Sequence[int]], variable_count: int) -> list[list[int]]:
    if isinstance(variable_count, bool) or not isinstance(variable_count, int):
        raise ValueError("variable_count must be an integer")
    if variable_count < 0 or variable_count > 20:
        raise ValueError("variable_count must be between 0 and 20 for bounded exact auditing")
    if not isinstance(clauses, (list, tuple)) or len(clauses) > 2000:
        raise ValueError("clauses must be a list of at most 2000 clauses")
    normalized: list[list[int]] = []
    for ci, clause in enumerate(clauses):
        if not isinstance(clause, (list, tuple)) or len(clause) > 200:
            raise ValueError(f"clause {ci} must be a list of at most 200 literals")
        row = []
        for literal in clause:
            if isinstance(literal, bool) or not isinstance(literal, int):
                raise ValueError(f"clause {ci} contains a non-integer literal")
            if literal == 0 or abs(literal) > variable_count:
                raise ValueError(f"clause {ci} contains a literal outside 1..{variable_count}")
            row.append(literal)
        normalized.append(row)
    return normalized


def q369_projection(clauses: Sequence[Sequence[int]], variable_count: int) -> dict[str, Any]:
    """Return deterministic structural residues; not a SAT-preserving encoding."""
    cnf = _validate_cnf(clauses, variable_count)
    clause_count = len(cnf)
    literal_count = sum(map(len, cnf))
    positive = sum(lit > 0 for row in cnf for lit in row)
    negative = literal_count - positive
    clause_widths = [len(row) for row in cnf]
    # q3/q6/q9 are explicitly defined as structural modular projections.
    # The full residue tuple is retained so the feature is reproducible.
    return {
        "variable_count": variable_count,
        "clause_count": clause_count,
        "literal_count": literal_count,
        "positive_literal_count": positive,
        "negative_literal_count": negative,
        "q3": {
            "variables": variable_count % 3,
            "clauses": clause_count % 3,
            "literals": literal_count % 3,
            "positive_literals": positive % 3,
        },
        "q6": {
            "variables": variable_count % 6,
            "clauses": clause_count % 6,
            "literals": literal_count % 6,
            "positive_literals": positive % 6,
        },
        "q9": {
            "variables": variable_count % 9,
            "clauses": clause_count % 9,
            "literals": literal_count % 9,
            "positive_literals": positive % 9,
        },
        "clause_width_digital_roots": [
            0 if width == 0 else 1 + (width - 1) % 9 for width in clause_widths
        ],
    }


def audit_sat_projection(
    formulas: Sequence[dict[str, Any]], max_variables: int = 20
) -> dict[str, Any]:
    """Compare q3/q6/q9 signatures to exact SAT labels and return collisions."""
    if not isinstance(formulas, (list, tuple)) or len(formulas) > 500:
        raise ValueError("formulas must be a list of at most 500 CNF instances")
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    records: list[dict[str, Any]] = []
    for index, formula in enumerate(formulas):
        if not isinstance(formula, dict):
            raise ValueError(f"formula {index} must be an object")
        variable_count = formula.get("variable_count")
        if isinstance(variable_count, bool) or not isinstance(variable_count, int):
            raise ValueError(f"formula {index}: variable_count must be an integer")
        if variable_count > max_variables:
            raise ValueError(f"formula {index}: exceeds max_variables={max_variables}")
        cnf = _validate_cnf(formula.get("clauses"), variable_count)
        projection = q369_projection(cnf, variable_count)
        exact = exact_sat_bruteforce(cnf, variable_count, max_variables=max_variables)
        # A feature signature is deliberately compact: it is the candidate compression
        # under test, not a claim that the compression preserves satisfiability.
        signature_payload = {
            "q3": projection["q3"],
            "q6": projection["q6"],
            "q9": projection["q9"],
            "clause_width_digital_roots": projection["clause_width_digital_roots"],
        }
        import json
        signature = json.dumps(signature_payload, sort_keys=True, separators=(",", ":"))
        record = {
            "index": index,
            "signature": signature,
            "satisfiable": exact["satisfiable"],
            "assignments_checked": exact["assignments_checked"],
            "projection": projection,
            "clauses": cnf,
            "variable_count": variable_count,
        }
        records.append(record)
        buckets[signature].append(record)

    collisions = []
    for signature, group in buckets.items():
        sat = next((item for item in group if item["satisfiable"]), None)
        unsat = next((item for item in group if not item["satisfiable"]), None)
        if sat is not None and unsat is not None:
            collisions.append({
                "signature": signature,
                "satisfiable_formula": {
                    "index": sat["index"],
                    "variable_count": sat["variable_count"],
                    "clauses": sat["clauses"],
                },
                "unsatisfiable_formula": {
                    "index": unsat["index"],
                    "variable_count": unsat["variable_count"],
                    "clauses": unsat["clauses"],
                },
                "meaning": "Same q3/q6/q9 projection, opposite SAT labels: this projection is not SAT-preserving on this pair.",
            })

    return {
        "engine": "Mallin Universal SAT Projection Audit",
        "formulas_checked": len(records),
        "distinct_signatures": len(buckets),
        "projection_collisions": len(collisions),
        "sat_preserving_on_test_set": len(collisions) == 0 and len(records) > 0,
        "proof_of_p_equals_np": False,
        "proof_status": "finite_empirical_audit_only",
        "assignments_checked_total": sum(r["assignments_checked"] for r in records),
        "counterexamples": collisions,
        "records": [
            {k: v for k, v in record.items() if k not in {"clauses"}}
            for record in records
        ],
        "interpretation": (
            "No conflicting labels were found in this finite sample; this is not a proof."
            if records and not collisions
            else "Projection collisions are explicit counterexamples to this candidate compression."
            if collisions
            else "No formulas supplied; no conclusion can be drawn."
        ),
    }
