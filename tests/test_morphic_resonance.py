import unittest

from research.morphic_resonance import exact_binomial_test


class ExactBinomialTest(unittest.TestCase):
    def test_balanced_result_does_not_reject_chance(self):
        result = exact_binomial_test(5, 10)
        self.assertEqual(result["observed_rate"], 0.5)
        self.assertAlmostEqual(result["two_sided_exact_p_value"], 1.0)

    def test_extreme_result_is_unusual_under_chance_null(self):
        result = exact_binomial_test(10, 10)
        self.assertAlmostEqual(result["two_sided_exact_p_value"], 2 / 1024)
        self.assertIn("cannot establish morphic resonance", result["claim_limit"])

    def test_invalid_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            exact_binomial_test(11, 10)
        with self.assertRaises(ValueError):
            exact_binomial_test(0, 0)


if __name__ == "__main__":
    unittest.main()
