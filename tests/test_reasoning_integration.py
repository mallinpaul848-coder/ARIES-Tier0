import unittest

from aries_math.reasoning_integration import analyze_request, build_reasoning_context


class ReasoningIntegrationTests(unittest.TestCase):
    def test_api_adapter_returns_question_analysis(self):
        result = analyze_request("Why is this test failing?")
        self.assertIn("plausible explanations", result["goal"])
        self.assertTrue(result["checks"])

    def test_context_is_grounded_and_concise(self):
        context = build_reasoning_context("How do I implement a regression test?")
        self.assertIn("ordered, testable plan", context)
        self.assertIn("Do not claim these checks prove", context)
        self.assertIn("available in the conversation", context)

    def test_empty_question_rejected(self):
        with self.assertRaises(ValueError):
            analyze_request("  ")


if __name__ == "__main__":
    unittest.main()
