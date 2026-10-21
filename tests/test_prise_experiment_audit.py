import unittest

from aries_math.prise_experiment_audit import (
    create_experiment_receipt, summarize_timings,
)


class TestPriseExperimentAudit(unittest.TestCase):
    def test_receipt_is_stable_and_binds_inputs_and_outputs(self):
        first = create_experiment_receipt(
            "P_VS_NP", "bounded_sat", {"cnf": [[1], [-2]]},
            {"satisfiable": True}, 0.1, ["finite test"],
        )
        same = create_experiment_receipt(
            "P_VS_NP", "bounded_sat", {"cnf": [[1], [-2]]},
            {"satisfiable": True}, 99.0, ["finite test"],
        )
        changed = create_experiment_receipt(
            "P_VS_NP", "bounded_sat", {"cnf": [[1], [-2]]},
            {"satisfiable": False}, 0.1, ["finite test"],
        )
        self.assertEqual(first["sha256"], same["sha256"])
        self.assertNotEqual(first["sha256"], changed["sha256"])
        self.assertFalse(first["mathematical_proof"])

    def test_receipt_rejects_non_finite_json_and_bad_timing(self):
        with self.assertRaises(ValueError):
            create_experiment_receipt("x", "y", {"x": float("nan")}, {}, 0.1)
        with self.assertRaises(ValueError):
            create_experiment_receipt("x", "y", {}, {}, -1)

    def test_timing_summary_uses_measured_samples(self):
        result = summarize_timings([0.4, 0.1, 0.3, 0.2])
        self.assertEqual(result["sample_count"], 4)
        self.assertEqual(result["min_seconds"], 0.1)
        self.assertEqual(result["median_seconds"], 0.25)
        self.assertEqual(result["p95_seconds"], 0.4)
        self.assertFalse(result["mathematical_proof"])

    def test_timing_summary_rejects_empty_and_invalid(self):
        with self.assertRaises(ValueError):
            summarize_timings([])
        with self.assertRaises(ValueError):
            summarize_timings([0.1, float("inf")])


if __name__ == "__main__":
    unittest.main()
