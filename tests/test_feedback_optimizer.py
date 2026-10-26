import unittest
from aries_math.feedback_optimizer import optimize_bounded

class FeedbackOptimizerTests(unittest.TestCase):
    def test_accepts_repeatable_improvement(self):
        best, report = optimize_bounded("base", ["slower", "faster"], lambda x: {"base":100.0,"slower":110.0,"faster":80.0}[x], trials_per_candidate=5)
        self.assertEqual(best, "faster")
        self.assertEqual(report.best_median, 80.0)
    def test_rejects_insufficient_gain(self):
        best, report = optimize_bounded("base", ["tiny"], lambda x: {"base":100.0,"tiny":99.0}[x], trials_per_candidate=3)
        self.assertEqual(best, "base")
        self.assertFalse(report.trials[0].accepted)
    def test_caps_candidates(self):
        seen=[]
        optimize_bounded("base", range(100), lambda x: seen.append(x) or 100.0, trials_per_candidate=3, max_candidates=2)
        self.assertEqual(len(seen), 9)
    def test_rejects_nan(self):
        with self.assertRaises(ValueError): optimize_bounded("base", [], lambda _: float("nan"), trials_per_candidate=3)
    def test_requires_repeated_measurements(self):
        with self.assertRaises(ValueError): optimize_bounded("base", [], lambda _: 1.0, trials_per_candidate=1)

if __name__ == "__main__": unittest.main()