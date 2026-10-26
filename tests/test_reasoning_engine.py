import unittest

from aries_math.reasoning_engine import (
    Evidence, Hypothesis, build_reasoning_report, decompose_question,
    evaluate_hypotheses, find_conflicts,
)


class ReasoningEngineTests(unittest.TestCase):
    def test_question_decomposition(self):
        result = decompose_question("Why did latency increase?")
        self.assertIn("plausible explanations", result["goal"])
        self.assertTrue(result["subquestions"])

    def test_hypothesis_ranking_uses_evidence(self):
        ranked = evaluate_hypotheses(
            [Hypothesis("cache", .4), Hypothesis("network", .4)],
            [Evidence("cache hit rate fell", "cache", .9),
             Evidence("network stable", "cache", .5)],
        )
        self.assertEqual(ranked[0]["hypothesis"], "cache")
        self.assertFalse(ranked[0]["score_is_probability"])

    def test_unknown_evidence_target_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_hypotheses([Hypothesis("A")], [Evidence("fact", "B")])

    def test_duplicate_hypotheses_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_hypotheses([Hypothesis("A"), Hypothesis("A")], [])

    def test_explicit_negation_conflict(self):
        conflicts = find_conflicts(["API is ready", "not API is ready"])
        self.assertEqual(len(conflicts), 1)

    def test_report_flags_uncertainty_and_conflicts(self):
        report = build_reasoning_report(
            "Which option should we choose?",
            [Hypothesis("A"), Hypothesis("B")],
            [Evidence("test passed", "A", .8)],
            ["service is live", "not service is live"],
        )
        self.assertEqual(report["engine"], "ARIES-Evidence-Reasoning-Scaffold-v1")
        self.assertTrue(report["conflicts"])
        self.assertIn("Resolve conflicting facts", report["next_step"])

    def test_empty_question_rejected(self):
        with self.assertRaises(ValueError):
            decompose_question("  ")


if __name__ == "__main__":
    unittest.main()
