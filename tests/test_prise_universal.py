import unittest

from aries_math.prise_universal import (
    PRISESignals, apply_369_matrix, detect_prise, route_universal_solution,
    universal_369_matrix,
)


class UniversalPRISETests(unittest.TestCase):
    def test_cyclic_matrix_matches_defined_pattern(self):
        self.assertEqual(
            universal_369_matrix(1, 2, 3),
            ((3.0, 12.0, 27.0), (27.0, 3.0, 12.0), (12.0, 27.0, 3.0)),
        )

    def test_matrix_transform(self):
        self.assertEqual(
            apply_369_matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)), (2, 3, 4)),
            (2, 3, 4),
        )

    def test_detect_and_route_high_risk_to_analysis(self):
        detected = detect_prise("Urgent risky system integration failure")
        self.assertIn(detected["primary_dimension"], detected["keyword_scores"])
        result = route_universal_solution(
            "Urgent risky system integration failure",
            PRISESignals(.9, .9, .7, .8, .6),
        )
        self.assertEqual(result["resolve"]["selected_action"], "analyze")
        self.assertEqual(result["execute"]["status"], "plan_only")
        self.assertEqual(result["pipeline"][0], "DETECT(PRISE)")

    def test_lower_risk_can_choose_simulation(self):
        result = route_universal_solution(
            "Optimize the simulation performance",
            PRISESignals(.5, .2, .8, .5, .4),
        )
        self.assertEqual(result["resolve"]["selected_action"], "simulate")

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            PRISESignals(.5, 2.0, .5, .5, .5)
        with self.assertRaises(ValueError):
            universal_369_matrix(float("inf"), 1, 1)
        with self.assertRaises(ValueError):
            route_universal_solution("", PRISESignals(.5, .5, .5, .5, .5))


if __name__ == "__main__":
    unittest.main()
