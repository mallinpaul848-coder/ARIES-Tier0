import itertools

import pytest

from aries_math.continuation_states import (
    ORAccumulator,
    ParityAccumulator,
    analyze_continuation_matrix,
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
