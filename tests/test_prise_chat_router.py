import json
import unittest

from aries_math.chat_router import route_math_prompt


class TestChatMathRouter(unittest.TestCase):
    def test_digital_root_routes(self):
        result = route_math_prompt("What is the digital root of 18?")
        self.assertEqual(result["route"], "digital_root_369")
        payload = json.loads(result["answer"])
        self.assertEqual(payload["digital_root"], 9)
        self.assertTrue(payload["is_3_6_9"])

    def test_phase8_routes(self):
        result = route_math_prompt("Phase-8 vector 3,4")
        self.assertEqual(result["route"], "phase8_vector")
        self.assertEqual(json.loads(result["answer"])["magnitude"], 5.0)

    def test_sat_routes_and_discloses_limit(self):
        result = route_math_prompt('SAT JSON: {"clauses":[[1,-2],[2]],"variable_count":2}')
        self.assertEqual(result["route"], "exact_sat_bruteforce")
        payload = json.loads(result["answer"])
        self.assertTrue(payload["satisfiable"])
        self.assertIn("not a P-vs-NP proof", payload["notice"])

    def test_prise_score_routes(self):
        result = route_math_prompt(
            "PRISE score priority=0.8 risk=0.5 impact=0.9 systemic=0.6 emergent=0.4"
        )
        self.assertEqual(result["route"], "prise_scoring")
        self.assertGreater(json.loads(result["answer"])["score"], 0)

    def test_mallin_prise_research_routes_named_millennium_problem(self):
        result = route_math_prompt("Analyze P vs NP using Mallin PRISE and 3-6-9 logic.")
        self.assertEqual(result["route"], "mallin_prise_research")
        payload = json.loads(result["answer"])
        self.assertEqual(payload["problem"], "P_VS_NP")
        self.assertFalse(payload["proof_claim"])
        self.assertEqual(payload["evidence_status"], "exploratory_only")

    def test_mallin_prise_routes_other_prize_problems(self):
        for prompt, expected in (
            ("Analyze the Riemann Hypothesis using Mallin PRISE", "RIEMANN_HYPOTHESIS"),
            ("Research Navier-Stokes with Mallin", "NAVIER_STOKES"),
            ("Analyze Yang-Mills using PRISE", "YANG_MILLS"),
            ("Analyze Hodge conjecture with Mallin", "HODGE_CONJECTURE"),
            ("Analyze Birch Swinnerton Dyer with Mallin", "BIRCH_SWINNERTON_DYER"),
        ):
            with self.subTest(prompt=prompt):
                result = route_math_prompt(prompt)
                self.assertEqual(result["route"], "mallin_prise_research")
                self.assertEqual(json.loads(result["answer"])["problem"], expected)

    def test_unmatched_prompt_falls_through(self):
        self.assertIsNone(route_math_prompt("Tell me a joke."))


if __name__ == "__main__":
    unittest.main()
