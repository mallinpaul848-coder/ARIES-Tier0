"""Tests for deterministic experiment runner and tool dispatch."""
import unittest

from aries_sat_experiment_runner import (
    dispatch,
    exact_model_count,
    legacy_encoding_features,
    run_experiment,
    self_test,
)


class ExperimentRunnerTests(unittest.TestCase):
    def test_exact_model_count(self):
        self.assertEqual(exact_model_count([[1], [-1]]), 0)
        self.assertEqual(exact_model_count([[1]]), 2)

    def test_feature_dispatch(self):
        result = dispatch("features", formula=[[1, -2], [2, 3]])
        self.assertIn("graph", result)
        self.assertIn("legacy_encoding", result)
        self.assertIn("baseline", result)

    def test_unknown_tool(self):
        with self.assertRaises(ValueError):
            dispatch("not-a-tool")

    def test_deterministic_fingerprint(self):
        a = run_experiment(n_variables=4, instances=4, seed=11, clause_ratio=2.0)
        b = run_experiment(n_variables=4, instances=4, seed=11, clause_ratio=2.0)
        self.assertEqual(a["fingerprint_sha256"], b["fingerprint_sha256"])

    def test_renaming_checks_count(self):
        result = run_experiment(n_variables=4, instances=4, seed=9, clause_ratio=2.0)
        self.assertEqual(result["renaming_invariance_checks"], 4)

    def test_proposal_features_are_explicitly_heuristic(self):
        features = legacy_encoding_features([[1, -2, 3]])
        self.assertEqual(set(features), {"digital_root_369", "vortex_cycle",
            "vortex_circulation", "phase8_projection", "harmonic_energy_369"})

    def test_self_test(self):
        self.assertEqual(self_test()["status"], "passed")


if __name__ == "__main__":
    unittest.main()
