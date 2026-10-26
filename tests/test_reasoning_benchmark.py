import unittest

from aries_math.reasoning_benchmark import CASES, normalize, run_benchmark, score_answer


class ReasoningBenchmarkTests(unittest.TestCase):
    def test_dataset_has_multiple_categories(self):
        self.assertGreaterEqual(len(CASES), 10)
        self.assertGreaterEqual(len({case.category for case in CASES}), 5)

    def test_normalization_and_exact_match(self):
        self.assertEqual(normalize("  ARIES   READY "), "aries ready")
        self.assertTrue(score_answer("ARIES READY", "aries   ready"))
        self.assertFalse(score_answer("36", "thirty-six"))

    def test_report_metrics_and_limitations(self):
        expected = {case.prompt: case.expected for case in CASES}
        report = run_benchmark(lambda prompt: expected[prompt], backend_name="test-perfect")
        self.assertEqual(report["case_count"], len(CASES))
        self.assertEqual(report["correct_count"], len(CASES))
        self.assertEqual(report["exact_match_accuracy"], 1.0)
        self.assertIn("p95", report["latency_ms"])
        self.assertTrue(report["limitations"])

    def test_errors_are_recorded(self):
        report = run_benchmark(lambda _: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertEqual(report["correct_count"], 0)
        self.assertIn("RuntimeError", report["cases"][0]["error"])


if __name__ == "__main__":
    unittest.main()
