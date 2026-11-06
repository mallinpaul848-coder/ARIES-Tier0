import unittest

from aries_math.prise_projection import (
    eliminate_affine_variables,
    project_affine_interface,
)


def parity(mask, assignment):
    return (mask & assignment).bit_count() & 1


class TestExactAffineProjection(unittest.TestCase):
    def test_projection_matches_exhaustive_quantification(self):
        # U0 xor U1 xor B0 = 1; U1 xor B1 = 0
        result = eliminate_affine_variables(
            a_u=[0b11, 0b10], a_b=[0b01, 0b10], rhs=[1, 0],
            n_u=2, n_b=2,
        )
        for boundary in range(4):
            brute = any(
                (parity(0b11, u) ^ parity(0b01, boundary)) == 1
                and (parity(0b10, u) ^ parity(0b10, boundary)) == 0
                for u in range(4)
            )
            self.assertEqual(result.accepts(boundary), brute)

    def test_inconsistent_constant_row_is_detected(self):
        result = eliminate_affine_variables(
            a_u=[0], a_b=[0], rhs=[1], n_u=1, n_b=2
        )
        self.assertTrue(result.inconsistent)
        self.assertFalse(any(result.accepts(b) for b in range(4)))

    def test_free_eliminated_variables_project_to_true(self):
        result = eliminate_affine_variables([], [], [], n_u=5, n_b=3)
        self.assertFalse(result.inconsistent)
        self.assertTrue(all(result.accepts(b) for b in range(8)))

    def test_duplicate_equations_reduce_exactly(self):
        result = eliminate_affine_variables(
            a_u=[1, 1], a_b=[1, 1], rhs=[0, 0], n_u=1, n_b=1
        )
        self.assertTrue(all(result.accepts(b) for b in range(2)))

    def test_interface_projection_matches_brute_force(self):
        # Output bits: s0=t0 xor t2, s1=t1 xor t2, s2=t0 xor t1.
        matrix = [0b101, 0b110, 0b011]
        offset = 0b100
        predicate = lambda value: value in (0b001, 0b111)
        result = project_affine_interface(matrix, offset, 3, predicate)
        brute = False
        for t in range(1 << 3):
            image = sum((parity(row, t) << r) for r, row in enumerate(matrix))
            brute = brute or predicate(offset ^ image)
        self.assertEqual(result.satisfiable, brute)
        self.assertEqual(result.rank, 2)
        self.assertEqual(result.enumerated, 4)

    def test_interface_rank_guard(self):
        with self.assertRaises(ValueError):
            project_affine_interface([0b01, 0b10], 0, 2, bool, max_rank=1)

    def test_zero_output_interface(self):
        result = project_affine_interface([], 0, 4, lambda _: True)
        self.assertTrue(result.satisfiable)
        self.assertEqual(result.rank, 0)
        self.assertEqual(result.enumerated, 1)


if __name__ == "__main__":
    unittest.main()
