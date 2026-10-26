import unittest

from aries_math.performance_matrix import (
    percentile, summarize_latencies_ms, timed_call, choose_path, platform_readiness,
)


class PerformanceMatrixTests(unittest.TestCase):
    def test_percentile_interpolation(self):
        self.assertAlmostEqual(percentile([10, 20, 30, 40], 50), 25)
        self.assertAlmostEqual(percentile([10, 20, 30, 40], 95), 38.5)

    def test_summary_includes_tail_latency(self):
        s = summarize_latencies_ms([1, 2, 3, 4, 100])
        self.assertEqual(s.samples, 5)
        self.assertEqual(s.min_ms, 1)
        self.assertEqual(s.max_ms, 100)
        self.assertGreaterEqual(s.p99_ms, s.p50_ms)

    def test_bad_samples_rejected(self):
        for samples in ([], [-1], [float("nan")], [float("inf")]):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                summarize_latencies_ms(samples)

    def test_timed_call_returns_result_and_duration(self):
        result, elapsed = timed_call(lambda x: x + 1, 4)
        self.assertEqual(result, 5)
        self.assertGreaterEqual(elapsed, 0)

    def test_candidate_must_be_correct_and_within_budget(self):
        self.assertTrue(choose_path(baseline_ms=100, candidate_ms=95,
                                    baseline_correct=True, candidate_correct=True)["accepted"])
        self.assertFalse(choose_path(baseline_ms=100, candidate_ms=95,
                                     baseline_correct=True, candidate_correct=False)["accepted"])
        self.assertFalse(choose_path(baseline_ms=100, candidate_ms=110,
                                     baseline_correct=True, candidate_correct=True)["accepted"])

    def test_platform_readiness_requires_all_components(self):
        self.assertTrue(platform_readiness({"api":{"passed":True}, "learning":{"passed":True}},
                                           ("api", "learning"))["ready"])
        report = platform_readiness({"api":{"passed":True}}, ("api", "learning"))
        self.assertFalse(report["ready"])
        self.assertEqual(report["missing"], ["learning"])


if __name__ == "__main__":
    unittest.main()
