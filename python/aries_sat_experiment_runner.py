"""ARIES/MALLIN deterministic SAT experiment runner.

Standard-library-only orchestration around aries_sat_lab.py. Generates seeded
random 3-SAT instances, computes exact labels by exhaustive enumeration, scores
baseline and feature heuristics, checks variable-renaming invariance, and emits
a stable SHA-256 result fingerprint. Exact enumeration is exponential and is
intended only for small instances. This is research tooling, not a P-vs-NP proof.

Run from this directory:
  python aries_sat_experiment_runner.py --variables 8 --instances 30 --seed 7
  python aries_sat_experiment_runner.py --self-test
  python aries_sat_experiment_runner.py --tool graph --formula '[[1,-2],[2,3]]'
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import statistics
from typing import Any, Sequence

from aries_sat_lab import graph_spectral_features, rename_variables, validate_cnf, auc


def evaluate_cnf(cnf: Sequence[Sequence[int]], assignment: dict[int, bool]) -> bool:
    """Evaluate a CNF formula under a complete or partial assignment."""
    for clause in cnf:
        if not any(assignment.get(abs(lit), False) == (lit > 0) for lit in clause):
            return False
    return True


def exact_model_count(cnf: Sequence[Sequence[int]], n_variables: int | None = None) -> int:
    """Return exact #SAT by exhaustive assignment enumeration."""
    formula = validate_cnf(cnf)
    used = {abs(lit) for clause in formula for lit in clause}
    n = max(used, default=0) if n_variables is None else n_variables
    if n < max(used, default=0) or n < 0:
        raise ValueError("n_variables must include every variable in the formula.")
    if n > 24:
        raise ValueError("Exact enumeration is limited to 24 variables by this safety guard.")
    count = 0
    for bits in itertools.product((False, True), repeat=n):
        assignment = {i + 1: bits[i] for i in range(n)}
        if evaluate_cnf(formula, assignment):
            count += 1
    return count


def random_3sat(n_variables: int, n_clauses: int, rng: random.Random) -> list[list[int]]:
    """Generate a seeded random 3-CNF formula with three distinct variables per clause."""
    if n_variables < 3:
        raise ValueError("3-SAT generation requires at least 3 variables.")
    if n_clauses < 0:
        raise ValueError("n_clauses must be nonnegative.")
    formula: list[list[int]] = []
    for _ in range(n_clauses):
        chosen = rng.sample(range(1, n_variables + 1), 3)
        clause = [v if rng.getrandbits(1) else -v for v in chosen]
        formula.append(clause)
    return formula


def baseline_score(cnf: Sequence[Sequence[int]]) -> float:
    """Simple variable-occurrence balance baseline; heuristic only."""
    positive: dict[int, int] = {}
    negative: dict[int, int] = {}
    for clause in cnf:
        for lit in clause:
            target = positive if lit > 0 else negative
            v = abs(lit)
            target[v] = target.get(v, 0) + 1
    vars_seen = set(positive) | set(negative)
    if not vars_seen:
        return 0.0
    # Higher means more positive/negative occurrence imbalance, not a SAT proof.
    return sum(abs(positive.get(v, 0) - negative.get(v, 0)) for v in vars_seen) / len(vars_seen)


def legacy_encoding_features(cnf: Sequence[Sequence[int]]) -> dict[str, float]:
    """Illustrative, explicitly encoding-dependent features from the proposal.

    These deterministic summaries are not claimed to be canonical invariants.
    They are included so the runner can compare them with invariant graph features.
    """
    formula = validate_cnf(cnf)
    literals = [lit for clause in formula for lit in clause]
    if not literals:
        return {"digital_root_369": 0.0, "vortex_cycle": 0.0,
                "vortex_circulation": 0.0, "phase8_projection": 0.0,
                "harmonic_energy_369": 0.0}
    signed_sum = sum(literals)
    root_input = sum(abs(x) for x in literals)
    digital_root = 0 if root_input == 0 else 1 + (root_input - 1) % 9
    phases = [((abs(lit) - 1) % 8) + 1 for lit in literals]
    phase_projection = sum(math.cos(2 * math.pi * p / 8) for p in phases) / len(phases)
    vortex = sum((1 if lit > 0 else -1) * ((abs(lit) % 3) + 1) for lit in literals)
    harmonics = sum(math.cos(2 * math.pi * abs(lit) / 3) for lit in literals) / len(literals)
    return {
        "digital_root_369": float(digital_root),
        "vortex_cycle": float(sum(phases) % 8),
        "vortex_circulation": float(vortex),
        "phase8_projection": float(phase_projection),
        "harmonic_energy_369": float(harmonics + (signed_sum / len(literals)) * 0.0),
    }


def rename_with_random_bijection(cnf: Sequence[Sequence[int]], rng: random.Random) -> list[list[int]]:
    used = sorted({abs(lit) for clause in cnf for lit in clause})
    targets = list(range(1001, 1001 + len(used)))
    rng.shuffle(targets)
    return rename_variables(cnf, dict(zip(used, targets)))


def run_experiment(n_variables: int = 8, instances: int = 30, seed: int = 7,
                   clause_ratio: float = 4.6) -> dict[str, Any]:
    """Run seeded exact-label experiments and return metrics plus fingerprint."""
    if n_variables < 3 or n_variables > 20:
        raise ValueError("n_variables must be between 3 and 20 for experiment runs.")
    if instances < 2:
        raise ValueError("instances must be at least 2.")
    if clause_ratio <= 0:
        raise ValueError("clause_ratio must be positive.")
    rng = random.Random(seed)
    n_clauses = max(1, round(clause_ratio * n_variables))
    rows: list[dict[str, Any]] = []
    rename_checks = 0
    for i in range(instances):
        formula = random_3sat(n_variables, n_clauses, rng)
        models = exact_model_count(formula, n_variables)
        label = int(models > 0)
        graph = graph_spectral_features(formula)
        legacy = legacy_encoding_features(formula)
        scores = {
            "baseline": baseline_score(formula),
            "algebraic_connectivity": float(graph["algebraic_connectivity"]),
            "spectral_radius": float(graph["spectral_radius"]),
            "signed_laplacian_min_eigenvalue": -float(graph["signed_laplacian_min_eigenvalue"]),
            **legacy,
        }
        renamed = rename_with_random_bijection(formula, rng)
        renamed_graph = graph_spectral_features(renamed)
        for key in ("algebraic_connectivity", "spectral_radius",
                    "signed_laplacian_min_eigenvalue"):
            if not math.isclose(float(graph[key]), float(renamed_graph[key]),
                                rel_tol=1e-8, abs_tol=1e-8):
                raise AssertionError(f"Renaming invariance failed for {key}, instance {i}")
        rename_checks += 1
        rows.append({"id": i, "label": label, "models": models, "scores": scores})
    labels = [r["label"] for r in rows]
    aucs: dict[str, float | None] = {}
    for name in rows[0]["scores"]:
        try:
            aucs[name] = round(auc(labels, [float(r["scores"][name]) for r in rows]), 6)
        except ValueError:
            aucs[name] = None
    canonical = json.dumps({"seed": seed, "n_variables": n_variables,
                            "n_clauses": n_clauses, "rows": rows, "auc": aucs},
                           sort_keys=True, separators=(",", ":"), allow_nan=False)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "status": "completed",
        "warning": "Empirical results only; exhaustive labels are exponential and do not prove or disprove P vs NP.",
        "parameters": {"variables": n_variables, "clauses_per_formula": n_clauses,
                       "instances": instances, "seed": seed, "clause_ratio": clause_ratio},
        "satisfiable_fraction": round(sum(labels) / len(labels), 6),
        "auc": aucs,
        "renaming_invariance_checks": rename_checks,
        "fingerprint_sha256": fingerprint,
        "rows": rows,
    }


def dispatch(tool: str, formula: Sequence[Sequence[int]] | None = None,
             **kwargs: Any) -> dict[str, Any]:
    """Small deterministic tool dispatcher suitable for CLI/chat integration."""
    if tool == "graph":
        if formula is None:
            raise ValueError("graph tool requires formula")
        return graph_spectral_features(formula)
    if tool == "features":
        if formula is None:
            raise ValueError("features tool requires formula")
        return {"graph": graph_spectral_features(formula),
                "legacy_encoding": legacy_encoding_features(formula),
                "baseline": baseline_score(formula)}
    if tool == "exact":
        if formula is None:
            raise ValueError("exact tool requires formula")
        count = exact_model_count(formula)
        return {"satisfiable": count > 0, "model_count": count}
    if tool == "experiment":
        return run_experiment(**kwargs)
    if tool == "self-test":
        return self_test()
    raise ValueError(f"Unknown tool: {tool}")


def self_test() -> dict[str, Any]:
    """Quick tests for exact labels, deterministic fingerprints, and invariance."""
    formula = [[1, -2], [2, 3]]
    assert exact_model_count(formula) > 0
    assert exact_model_count([[1], [-1]]) == 0
    first = run_experiment(n_variables=4, instances=4, seed=7, clause_ratio=2.0)
    second = run_experiment(n_variables=4, instances=4, seed=7, clause_ratio=2.0)
    assert first["fingerprint_sha256"] == second["fingerprint_sha256"]
    assert first["renaming_invariance_checks"] == 4
    return {"status": "passed", "checks": 4,
            "fingerprint_sha256": first["fingerprint_sha256"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variables", type=int, default=8)
    parser.add_argument("--instances", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--clause-ratio", type=float, default=4.6)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--tool", choices=("graph", "features", "exact", "experiment", "self-test"))
    parser.add_argument("--formula", help="JSON CNF, e.g. [[1,-2],[2,3]]")
    args = parser.parse_args()
    if args.self_test or args.tool == "self-test":
        print(json.dumps(self_test(), sort_keys=True, indent=2))
        return
    if args.tool in ("graph", "features", "exact"):
        if args.formula is None:
            parser.error("--formula is required for graph/features/exact tools")
        result = dispatch(args.tool, formula=json.loads(args.formula))
    else:
        result = run_experiment(args.variables, args.instances, args.seed, args.clause_ratio)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
