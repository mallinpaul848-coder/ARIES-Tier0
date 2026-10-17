import pytest

from api.main import execute_aries_operation


def test_digital_root_handles_positive_negative_and_zero():
    assert execute_aries_operation("digital_root", {"n": 12345}) == 6
    assert execute_aries_operation("digital_root", {"n": -12345}) == 6
    assert execute_aries_operation("digital_root", {"n": 0}) == 0


def test_gcd_and_lcm():
    assert execute_aries_operation("gcd", {"values": [24, 36, 60]}) == 12
    assert execute_aries_operation("lcm", {"values": [4, 6, 10]}) == 60


def test_prime_check():
    assert execute_aries_operation("is_prime", {"n": 97}) is True
    assert execute_aries_operation("is_prime", {"n": 1}) is False


def test_dot_product_and_matrix_multiply():
    assert execute_aries_operation("dot_product", {"left": [1, 2, 3], "right": [4, 5, 6]}) == 32
    assert execute_aries_operation(
        "matrix_multiply",
        {"left": [[1, 2], [3, 4]], "right": [[5, 6], [7, 8]]},
    ) == [[19, 22], [43, 50]]


def test_invalid_operation_is_rejected():
    with pytest.raises(ValueError, match="Unsupported operation"):
        execute_aries_operation("run_shell", {})


def test_mismatched_dot_product_lengths_are_rejected():
    with pytest.raises(ValueError, match="equal lengths"):
        execute_aries_operation("dot_product", {"left": [1, 2], "right": [3]})
