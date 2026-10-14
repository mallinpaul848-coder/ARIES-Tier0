#!/usr/bin/env python3
"""ARIES training/export/Hub-publish orchestrator.

This calls the repository's real corpus-trained GPT-2-style trainer. It does not
pretend randomly initialized weights are a trained ARIES model. A licensed corpus
of sufficient size and HF_TOKEN with write permission are required for publishing.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=os.getenv("CORPUS_PATH", "data/training.txt"))
    parser.add_argument("--repo-id", default=os.getenv("HF_TARGET_REPO", "PaulMallin/aries-core-v1"))
    parser.add_argument("--output-dir", default="artifacts/aries-core-v1")
    parser.add_argument("--steps", type=int, default=int(os.getenv("TRAINING_STEPS", "1000")))
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*", args.repo_id):
        parser.error("--repo-id must be a valid namespace/name identifier")
    if args.steps < 1 or args.steps > 100000:
        parser.error("--steps must be between 1 and 100000")

    corpus = Path(args.corpus)
    if not corpus.is_file():
        print(
            f"ERROR: training corpus not found: {corpus}. Add a UTF-8 dataset you own "
            "or are licensed to use; the demo deployment corpus is intentionally not "
            "substituted for a real training dataset.",
            file=sys.stderr,
        )
        return 2
    corpus_text = corpus.read_text(encoding="utf-8-sig").strip()
    if len(corpus_text) < 100_000:
        print(
            f"ERROR: corpus contains {len(corpus_text):,} characters; at least 100,000 "
            "are required by the repository training safeguards. Use a larger, diverse, "
            "licensed corpus.",
            file=sys.stderr,
        )
        return 2
    if not os.getenv("HF_TOKEN"):
        print(
            "ERROR: HF_TOKEN is missing. Add a Hugging Face write token under GitHub "
            "Settings > Secrets and variables > Actions. Never paste it into source code.",
            file=sys.stderr,
        )
        return 2

    cmd = [
        sys.executable, "software/train_and_publish_aries_lm.py",
        "--corpus", str(corpus),
        "--repo-id", args.repo_id,
        "--output-dir", args.output_dir,
        "--steps", str(args.steps),
        "--model-name", "ARIES Experimental Causal LM",
        "--license", "other",
    ]
    if args.private:
        cmd.append("--private")

    print(f"Starting real corpus-based ARIES training: corpus={corpus}, steps={args.steps}, target={args.repo_id}", flush=True)
    result = subprocess.run(cmd, check=False)
    if result.returncode:
        return result.returncode

    output = Path(args.output_dir)
    required = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json", "README.md"]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        print(f"ERROR: expected exported files are missing: {missing}", file=sys.stderr)
        return 3
    print("PASS: trained model artifacts exist; training script completed local reload checks and Hub upload.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
