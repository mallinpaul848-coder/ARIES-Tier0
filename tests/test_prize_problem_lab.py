import unittest
from aries_math.prize_problem_lab import (
    sat_bruteforce, navier_stokes_sample_diagnostics,
    yang_mills_finite_spectrum_diagnostic, proof_obligation_template,
)


class TestPrizeProblemLab(unittest.TestCase):
    def test_sat_sat_unsat_and_empty_cases(self):
        self.assertTrue(sat_bruteforce([[1, -2], [2]])["satisfiable"])
        self.assertFalse(sat_bruteforce([[1], [-1]])["satisfiable"])
        self.assertTrue(sat_bruteforce([])["satisfiable"])
        self.assertFalse(sat_bruteforce([[]])["satisfiable"])

    def test_sat_rejects_invalid_and_over_limit(self):
        for formula in ([[0]], [[True]], [[25]]):
            with self.assertRaises(ValueError):
                sat_bruteforce(formula, max_variables=24)
        with self.assertRaises(ValueError):
            sat_bruteforce([], max_variables=-1)

    def test_sat_assignment_satisfies_formula(self):
        formula = [[1, -2], [2, 3], [-1, 3]]
        result = sat_bruteforce(formula)
        self.assertTrue(result["satisfiable"])
        assignment = {int(k): v for k, v in result["assignment"].items()}
        self.assertTrue(all(any(assignment[abs(x)] == (x > 0) for x in clause) for clause in formula))

    def test_navier_stokes_uniform_flow(self):
        u = [[1.0] * 3 for _ in range(3)]
        v = [[0.0] * 3 for _ in range(3)]
        result = navier_stokes_sample_diagnostics(u, v)
        self.assertEqual(result["max_abs_divergence"], 0.0)
        self.assertEqual(result["mean_squared_vorticity"], 0.0)
        self.assertAlmostEqual(result["mean_kinetic_energy_density"], 0.5)

    def test_navier_stokes_grid_validation(self):
        with self.assertRaises(ValueError):
            navier_stokes_sample_diagnostics([[1, 2], [3, 4]], [[0, 0], [0, 0]])
        with self.assertRaises(ValueError):
            navier_stokes_sample_diagnostics([[0]*3 for _ in range(3)], [[0]*3 for _ in range(3)], dx=0)

    def test_yang_mills_spectrum(self):
        result = yang_mills_finite_spectrum_diagnostic([0, 0, 0.25, 1])
        self.assertTrue(result["finite_sample_has_positive_gap"])
        self.assertEqual(result["lowest_positive_eigenvalue"], 0.25)
        self.assertFalse(yang_mills_finite_spectrum_diagnostic([0, -0.1, 1])["finite_sample_has_positive_gap"])
        with self.assertRaises(ValueError):
            yang_mills_finite_spectrum_diagnostic([])

    def test_proof_obligations_never_claim_solution(self):
        for key in ("P_VS_NP", "NAVIER_STOKES", "YANG_MILLS"):
            result = proof_obligation_template(key)
            self.assertEqual(result["status"], "open_research")
            self.assertFalse(result["claim_of_solution"])
            self.assertTrue(result["proof_obligations"])


if __name__ == "__main__":
    unittest.main()
