import unittest

from aries_math.positive_impact import (
    ImpactInputs, digital_root, phase8, rank_positive_impact, score_positive_impact,
)


class PositiveImpactTests(unittest.TestCase):
    def test_digital_root_and_phase8_boundaries(self):
        self.assertEqual(digital_root(0), 0)
        self.assertEqual(digital_root(999), 9)
        self.assertEqual(digital_root(-18), 9)
        self.assertEqual(phase8(8), 0)
        self.assertEqual(phase8(-1), 7)

    def test_output_is_bounded_and_transparent(self):
        result = score_positive_impact(ImpactInputs(.8, .9, .1, .7, .5, .9, .8))
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 1)
        self.assertEqual(result["method"], "PRISE-positive-impact-v1")
        self.assertFalse(result["experimental_signals"]["used_in_core_score"])

    def test_higher_risk_does_not_improve_score(self):
        base = dict(priority=.8, benefit=.9, systemic_effect=.7, emergence=.5,
                    confidence=.9, reversibility=.8)
        low = score_positive_impact(ImpactInputs(risk=.1, **base))["score"]
        high = score_positive_impact(ImpactInputs(risk=.9, **base))["score"]
        self.assertGreater(low, high)

    def test_uncertainty_and_irreversibility_are_penalized(self):
        base = dict(priority=.8, benefit=.9, risk=.2, systemic_effect=.7, emergence=.5)
        confident = score_positive_impact(ImpactInputs(**base, confidence=.95, reversibility=.9))["score"]
        uncertain = score_positive_impact(ImpactInputs(**base, confidence=.3, reversibility=.2))["score"]
        self.assertGreater(confident, uncertain)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            score_positive_impact(ImpactInputs(1.2, .5, .2, .5, .5))

    def test_ranked_descending_and_stable(self):
        items = [
            ("low", ImpactInputs(.2, .2, .8, .2, .1)),
            ("high", ImpactInputs(.9, .9, .1, .9, .8)),
            ("tie-a", ImpactInputs(.5, .5, .5, .5, .5)),
            ("tie-b", ImpactInputs(.5, .5, .5, .5, .5)),
        ]
        ranked = rank_positive_impact(items)
        self.assertEqual(ranked[0]["name"], "high")
        self.assertEqual(ranked[-1]["name"], "low")
        self.assertLessEqual(ranked[2]["score"], ranked[1]["score"])
        self.assertEqual(
            [x["name"] for x in ranked if x["name"].startswith("tie-")],
            ["tie-a", "tie-b"],
        )


if __name__ == "__main__":
    unittest.main()
