import unittest
from unittest.mock import patch

from tools.leaderboard_preflight import PreflightError, validate_model

SHA = "a" * 40

class LeaderboardPreflightTests(unittest.TestCase):
    def test_rejects_moving_revision_tags(self):
        with self.assertRaisesRegex(PreflightError, "40-character immutable"):
            validate_model("org/model", "main")

    def test_rejects_model_id_without_owner(self):
        with self.assertRaisesRegex(PreflightError, "owner/repository"):
            validate_model("model", SHA)

    @patch("tools.leaderboard_preflight.fetch_json")
    def test_requires_weights_and_tokenizer(self, fetch):
        fetch.return_value = {"sha": SHA, "siblings": [{"rfilename": "config.json"}]}
        with self.assertRaisesRegex(PreflightError, "No model weight files"):
            validate_model("org/model", SHA)

    @patch("tools.leaderboard_preflight.fetch_json")
    def test_accepts_pinned_transformers_model(self, fetch):
        fetch.return_value = {
            "sha": SHA,
            "siblings": [
                {"rfilename": "config.json"},
                {"rfilename": "model.safetensors"},
                {"rfilename": "tokenizer.json"},
            ],
            "private": False,
            "library_name": "transformers",
            "pipeline_tag": "text-generation",
            "cardData": {"license": "apache-2.0"},
        }
        result = validate_model("org/model", SHA)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["revision"], SHA)
        self.assertIn("model.safetensors", result["weight_files"])
        self.assertIn("tokenizer.json", result["tokenizer_files"])

if __name__ == "__main__":
    unittest.main()
