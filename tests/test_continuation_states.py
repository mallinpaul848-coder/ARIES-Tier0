import itertools

import pytest

from aries_math.continuation_states import (
    ORAccumulator,
    ParityAccumulator,
    analyze_continuation_matrix,
    induced_width,
    solve_gf2,
    verify_signature_soundness,
)


def _parity_matrix(prefix_bits=2):
    prefixes = list(itertools.product((0, 1), repeat=prefix_bits))
    suffixes = (0, 1)
    return [
        [int((sum(prefix) + suffix) % 2 == 0) for suffix in suffixes]
        for prefix in prefixes
    ]


def _independent_clause_matrix(prefix_bits=2):
    prefixes = list(itertools.product((0, 1), repeat=prefix_bits))
    outside = list(itertools.product((0, 1), repeat=prefix_bits))
    return [
        [int(all(q or y for q, y in zip(prefix, assignment))) for assignment in outside]
        for prefix in prefixes
    ]


def test_parity_parent_has_two_exact_continuation_states():
    matrix = _parity_matrix()
    quotient = analyze_continuation_matrix(matrix)
    assert quotient.state_count == 2
    assert quotient.state_bits == 1
    assert quotient.prefix_to_state[0] == quotient.prefix_to_state[3]
    assert quotient.prefix_to_state[1] == quotient.prefix_to_state[2]


def test_independent_clause_parent_has_exponential_prefix_states():
    matrix = _independent_clause_matrix(prefix_bits=4)
    quotient = analyze_continuation_matrix(matrix)
    assert quotient.prefix_count == 16
    assert quotient.state_count == 16
    assert quotient.state_bits == 4


def test_parity_signature_is_sound_for_parity_matrix():
    prefixes = list(itertools.product((0, 1), repeat=2))
    signatures = [sum(prefix) % 2 for prefix in prefixes]
    result = verify_signature_soundness(_parity_matrix(), signatures)
    assert result["sound"] is True
    assert result["violation_count"] == 0


def test_parity_signature_is_unsound_for_independent_clauses():
    prefixes = list(itertools.product((0, 1), repeat=2))
    signatures = [sum(prefix) % 2 for prefix in prefixes]
    result = verify_signature_soundness(_independent_clause_matrix(), signatures)
    assert result["sound"] is False
    assert result["violation_count"] > 0


def test_parity_accumulator_matches_xor():
    accumulator = ParityAccumulator()
    states = [accumulator.update(bit) for bit in (1, 1, 0, 1)]
    assert states == [1, 0, 0, 1]


def test_or_accumulator_matches_or():
    accumulator = ORAccumulator()
    states = [accumulator.update(bit) for bit in (0, 0, 1, 0)]
    assert states == [0, 0, 1, 1]


@pytest.mark.parametrize("bad", [2, -1, 0.5, "1"])
def test_accumulators_reject_non_bits(bad):
    with pytest.raises(ValueError):
        ParityAccumulator().update(bad)


def test_matrix_validation_and_empty_suffix_domain():
    with pytest.raises(ValueError):
        analyze_continuation_matrix([])
    with pytest.raises(ValueError):
        analyze_continuation_matrix([[0, 1], [1]])
    with pytest.raises(ValueError):
        analyze_continuation_matrix([[0, 2]])
    quotient = analyze_continuation_matrix([[], []])
    assert quotient.state_count == 1
    assert quotient.suffix_count == 0



def _gf2_matvec(matrix, vector):
    return [sum(a * b for a, b in zip(row, vector)) % 2 for row in matrix]


def test_gf2_solver_returns_particular_solution_and_nullspace():
    matrix = [[1, 1, 0], [0, 1, 1]]
    rhs = [1, 0]
    result = solve_gf2(matrix, rhs)
    assert result["consistent"] is True
    assert result["rank"] == 2
    particular = result["particular_solution"]
    assert _gf2_matvec(matrix, particular) == rhs
    for basis_vector in result["nullspace_basis"]:
        assert _gf2_matvec(matrix, basis_vector) == [0, 0]


def test_gf2_solver_detects_inconsistency():
    result = solve_gf2([[1, 1], [1, 1]], [0, 1])
    assert result["consistent"] is False
    assert result["particular_solution"] is None


def test_gf2_solver_reports_free_dimension():
    result = solve_gf2([[1, 1, 1]], [1])
    assert result["free_variable_count"] == 2
    assert len(result["nullspace_basis"]) == 2


def test_induced_width_adds_fill_edges():
    # Path a-b-c has width 1 in order a,b,c; eliminating b first creates a-c.
    graph = {"a": ["b"], "b": ["a", "c"], "c": ["b"]}
    assert induced_width(graph, ["a", "b", "c"])["induced_width"] == 1
    assert induced_width(graph, ["b", "a", "c"])["induced_width"] == 2


def test_induced_width_requires_a_complete_order():
    with pytest.raises(ValueError):
        induced_width({"a": ["b"], "b": ["a"]}, ["a"])
