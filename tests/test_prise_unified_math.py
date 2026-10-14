import unittest

from aries_math.prise_unified import (
    ARIESExecutionEngine, DigitalRootSystem, EulerPoincareTopology,
    HelixoSpiralGeometry, PRISEProblem, SpectralHelmholtzHodge,
    ToroidalMatrixDynamics, exact_sat_bruteforce,
)

class TestARIESMath(unittest.TestCase):
    def test_digital_root(self):
        self.assertEqual(DigitalRootSystem.compute(0), 0)
        self.assertEqual(DigitalRootSystem.compute(18), 9)
        self.assertTrue(DigitalRootSystem.validate_triad(18))
        self.assertEqual(DigitalRootSystem.compute(-19), 1)

    def test_torus_geometry(self):
        torus = ToroidalMatrixDynamics(3, 1)
        self.assertAlmostEqual(torus.surface_area(), 12 * 3.141592653589793**2)
        self.assertEqual(len(torus.map_coordinates(0.2, 0.4)), 3)
        self.assertEqual(len(torus.rotated_coordinates(0.2, 0.4)), 3)

    def test_helixo_finite(self):
        coords = HelixoSpiralGeometry.generate_coordinates(2.5)
        self.assertEqual(len(coords), 3)
        self.assertTrue(all(abs(x) < 100 for x in coords))

    def test_topology(self):
        self.assertEqual(EulerPoincareTopology.compute_characteristic(16, 32, 16), 0)

    def test_finite_euler_product(self):
        value = EulerPoincareTopology.zeta_harmonic_scaling(2.0, [2, 3, 5, 7, 11])
        self.assertGreater(value, 1.0)

    def test_prise_score(self):
        p = PRISEProblem("test", 1, 0, 1, 0.5, 0.5)
        self.assertGreaterEqual(p.score(), 0.0)
        self.assertLessEqual(p.score(), 1.0)

    def test_sample_diagnostics(self):
        result = SpectralHelmholtzHodge.decompose_samples([1, 2, 3])
        self.assertEqual(result["centered"], [-1.0, 0.0, 1.0])
        self.assertEqual(len(result["first_difference"]), 3)

    def test_sat_sat_and_unsat(self):
        sat = exact_sat_bruteforce([[1, -2], [2]], 2)
        self.assertTrue(sat["satisfiable"])
        unsat = exact_sat_bruteforce([[1], [-1]], 1)
        self.assertFalse(unsat["satisfiable"])
        self.assertEqual(unsat["assignments_checked"], 2)

    def test_binary_analysis_does_not_claim_timing(self):
        result = ARIESExecutionEngine().analyze_binary_stream(b"ARIES")
        self.assertEqual(result["byte_count"], 5)
        self.assertEqual(result["latency_status"], "MEASURE_REQUIRED")

if __name__ == "__main__":
    unittest.main()
