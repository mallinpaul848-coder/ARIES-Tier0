import pytest

from aries_math.mallin_universal import audit_sat_projection, q369_projection


def test_q369_projection_is_deterministic_and_exposes_residues():
    projection = q369_projection([[1, -2], [2]], 2)
    assert projection["q3"] == {"variables": 2, "clauses": 2, "literals": 0, "positive_literals": 2}
    assert projection["q6"]["literals"] == 3
    assert projection["q9"]["literals"] == 3


def test_audit_finds_opposite_sat_labels_with_same_projection():
    sat = {"variable_count": 2, "clauses": [[1, 2], [1, 2], [-1, -2], [-1, -2]]}
    unsat = {"variable_count": 2, "clauses": [[1, 2], [-1, 2], [1, -2], [-1, -2]]}
    result = audit_sat_projection([sat, unsat])
    assert result["formulas_checked"] == 2
    assert result["projection_collisions"] == 1
    assert result["sat_preserving_on_test_set"] is False
    assert result["proof_of_p_equals_np"] is False
    pair = result["counterexamples"][0]
    assert pair["satisfiable_formula"]["index"] != pair["unsatisfiable_formula"]["index"]


def test_audit_does_not_claim_proof_when_no_collision_found():
    result = audit_sat_projection([
        {"variable_count": 1, "clauses": [[1]]},
        {"variable_count": 1, "clauses": [[-1]]},
    ])
    assert result["projection_collisions"] == 0
    assert result["proof_status"] == "finite_empirical_audit_only"
    assert result["proof_of_p_equals_np"] is False


def test_audit_rejects_oversized_formula():
    with pytest.raises(ValueError):
        audit_sat_projection([{"variable_count": 21, "clauses": []}])


def test_audit_rejects_bad_literals():
    with pytest.raises(ValueError):
        audit_sat_projection([{"variable_count": 1, "clauses": [[2]]}])
