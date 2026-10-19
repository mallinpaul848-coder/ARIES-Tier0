"""Regression tests for the ARIES SAT graph-spectral lab; stdlib unittest only."""
import math
import unittest

from aries_sat_lab import (
    auc,
    graph_spectral_features,
    interaction_matrices,
    jacobi_eigenvalues,
    rename_variables,
)


class GraphSpectralLabTests(unittest.TestCase):
    def test_renaming_invariance(self):
        formula = [[1, -2, 3], [-1, 2], [2, 3]]
        renamed = rename_variables(formula, {1: 19, 2: 7, 3: 42})
        a = graph_spectral_features(formula)
        b = graph_spectral_features(renamed)
        for key in ("algebraic_connectivity", "spectral_radius",
                    "signed_laplacian_min_eigenvalue"):
            self.assertTrue(math.isclose(a[key], b[key], rel_tol=1e-9, abs_tol=1e-9), key)

    def test_known_eigenvalues(self):
        self.assertEqual(jacobi_eigenvalues([[2.0, 0.0], [0.0, 3.0]]), [2.0, 3.0])
        got = jacobi_eigenvalues([[2.0, 1.0], [1.0, 2.0]])
        self.assertTrue(math.isclose(got[0], 1.0, abs_tol=1e-10))
        self.assertTrue(math.isclose(got[1], 3.0, abs_tol=1e-10))

    def test_disconnected_graph_connectivity_is_zero(self):
        features = graph_spectral_features([[1, 2], [3, 4]])
        self.assertAlmostEqual(features["algebraic_connectivity"], 0.0, places=9)

    def test_empty_formula(self):
        self.assertEqual(graph_spectral_features([])["variables"], 0)
        self.assertEqual(graph_spectral_features([[]])["edges"], 0)

    def test_auc_perfect_and_ties(self):
        self.assertEqual(auc([0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8]), 1.0)
        self.assertEqual(auc([0, 1], [0.5, 0.5]), 0.5)

    def test_invalid_literal_and_mapping(self):
        with self.assertRaises(ValueError):
            interaction_matrices([[0, 1]])
        with self.assertRaises(ValueError):
            rename_variables([[1, 2]], {1: 3, 2: 3})

    def test_literal_order_does_not_change_unsigned_graph(self):
        a = graph_spectral_features([[1, -2, 3], [4, -1]])
        b = graph_spectral_features([[3, 1, -2], [-1, 4]])
        self.assertAlmostEqual(a["algebraic_connectivity"], b["algebraic_connectivity"], places=9)
        self.assertAlmostEqual(a["spectral_radius"], b["spectral_radius"], places=9)


if __name__ == "__main__":
    unittest.main()
