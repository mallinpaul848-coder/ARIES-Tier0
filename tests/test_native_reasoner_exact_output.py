"""Regression tests for deterministic exact-output prompt handling."""

from software.native_reasoner import solve


def test_exact_output_with_colon():
    assert solve("Reply with exactly: ARIES live check") == "ARIES live check"


def test_exact_output_without_colon():
    assert solve("Reply with exactly ARIES live check") == "ARIES live check"


def test_exact_output_and_nothing_else():
    assert solve("Reply with exactly: READY and nothing else") == "READY"


def test_basic_arithmetic_still_works():
    assert solve("What is 17 times 19?") == "323"
