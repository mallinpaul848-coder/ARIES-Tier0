"""Smoke tests for the ARIES streaming causal trainer."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "training" / "aries_trillion_token_trainer.py"


class AriesStreamingTrainerTests(unittest.TestCase):
    def test_help_and_argument_validation(self):
        help_result = subprocess.run(
            [sys.executable, str(TRAINER), "--help"],
            cwd=ROOT, text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--target-training-tokens", help_result.stdout)
        self.assertIn("--resume-from-checkpoint", help_result.stdout)

        missing_corpus = subprocess.run(
            [sys.executable, str(TRAINER), "--corpus", str(ROOT / "no-such-corpus.txt")],
            cwd=ROOT, text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(missing_corpus.returncode, 2)
        self.assertIn("corpus file not found", missing_corpus.stderr)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "PyTorch is needed for the training smoke test")
    def test_training_counts_only_real_batch_targets_and_resumes(self):
        with tempfile.TemporaryDirectory(prefix="aries-trainer-test-") as temp:
            temp_dir = Path(temp)
            corpus = temp_dir / "licensed-smoke-corpus.txt"
            # Repeated valid UTF-8 text gives the byte tokenizer enough stream blocks.
            corpus.write_text(("ARIES trains on actual corpus bytes, not randomly sampled fake targets.\\n" * 250),
                              encoding="utf-8")
            output_dir = temp_dir / "output"

            def run(steps: int, resume: bool = False):
                cmd = [
                    sys.executable, str(TRAINER),
                    "--corpus", str(corpus),
                    "--tokenizer", "byte",
                    "--output-dir", str(output_dir),
                    "--target-training-tokens", "4096",
                    "--max-steps", str(steps),
                    "--checkpoint-every-steps", "1",
                    "--batch-size", "2",
                    "--seq-len", "16",
                    "--d-model", "32",
                    "--layers", "1",
                    "--heads", "4",
                    "--no-amp",
                ]
                if resume:
                    cmd.extend(["--resume-from-checkpoint", "latest"])
                result = subprocess.run(
                    cmd, cwd=ROOT, text=True, capture_output=True, timeout=120,
                )
                self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
                return json.loads((output_dir / "training_evidence.json").read_text(encoding="utf-8"))

            first = run(2)
            self.assertEqual(first["status"], "PARTIAL_TARGET_NOT_REACHED")
            self.assertEqual(first["tokens_seen_this_run"], 2 * 2 * 16 * 2 // 2)
            self.assertEqual(first["optimizer_steps_this_run"], 2)
            self.assertEqual(first["tokens_seen_cumulative"], 64)
            self.assertTrue((output_dir / "checkpoint.pt").is_file())
            self.assertEqual(len(first["corpus_sha256"]), 64)
            self.assertGreater(first["checkpoint_sha256"] and len(first["checkpoint_sha256"]), 0)

            second = run(1, resume=True)
            self.assertEqual(second["optimizer_steps_cumulative"], 3)
            self.assertEqual(second["optimizer_steps_this_run"], 1)
            self.assertEqual(second["tokens_seen_cumulative"], 96)
            self.assertEqual(second["tokens_seen_this_run"], 32)
            self.assertEqual(second["status"], "PARTIAL_TARGET_NOT_REACHED")


if __name__ == "__main__":
    unittest.main()
