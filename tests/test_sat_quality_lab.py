import pytest

from aries_math.sat_quality_lab import (
    exact_sat_label, evaluate_formulas, feature_signature, generate_random_formulas,
    validate_cnf,
)


def test_exact_sat_labels_known_instances():
    assert exact_sat_label([[1], [-1]], 1) is False
    assert exact_sat_label([[1, -2], [2]], 2) is True
    assert exact_sat_label([], 0) is True
    assert exact_sat_label([[]], 0) is False


def test_cnf_validation_rejects_invalid_literals():
    with pytest.raises(ValueError):
        validate_cnf([[0]], 1)
    with pytest.raises(ValueError):
        validate_cnf([[2]], 1)
    with pytest.raises(ValueError):
        validate_cnf([[True]], 1)


def test_feature_signature_is_deterministic_and_does_not_claim_truth():
    cnf = [[1, -2], [2]]
    assert feature_signature(cnf, 2) == feature_signature(cnf, 2)
    assert exact_sat_label(cnf, 2) is True


def test_generated_evaluation_is_reproducible_and_reports_baseline():
    formulas = generate_random_formulas(count=30, variable_count=5, seed=11)
    first = evaluate_formulas(formulas, seed=19)
    second = evaluate_formulas(formulas, seed=19)
    assert first == second
    assert first["formula_count"] == 30
    assert first["test_count"] > 0
    assert 0 <= first["test_accuracy_percent"] <= 100
    assert 0 <= first["majority_baseline_accuracy_percent"] <= 100
    assert "No P-vs-NP claim" in first["limitations"][-1]


def test_evaluator_requires_enough_formulas():
    with pytest.raises(ValueError):
        evaluate_formulas([{"clauses": [[1]], "variable_count": 1}] * 3)
