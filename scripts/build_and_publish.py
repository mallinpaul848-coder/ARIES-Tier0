#!/usr/bin/env python3
"""ARIES training/export/Hub-publish orchestrator.

Trains from a corpus file, validates a local reload/generation, and publishes only
when HF_TOKEN is present. Without a token it still creates a verified local artifact;
that is not a Hugging Face publication or leaderboard submission.
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
        print(f"ERROR: training corpus not found: {corpus}.", file=sys.stderr)
        return 2
    corpus_text = corpus.read_text(encoding="utf-8-sig").strip()
    if len(corpus_text) < 100_000:
        print(f"ERROR: corpus contains {len(corpus_text):,} characters; at least 100,000 are required.", file=sys.stderr)
        return 2

    token = os.getenv("HF_TOKEN", "").strip()
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
    if not token:
        cmd.append("--skip-upload")
        print("HF_TOKEN is not configured: running local train/export/validation only; publishing will be skipped.", flush=True)

    print(f"Starting corpus-based ARIES training: corpus={corpus}, characters={len(corpus_text):,}, steps={args.steps}, target={args.repo_id}", flush=True)
    result = subprocess.run(cmd, check=False)
    if result.returncode:
        return result.returncode

    output = Path(args.output_dir)
    required = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json", "README.md"]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        print(f"ERROR: expected exported files are missing: {missing}", file=sys.stderr)
        return 3
    if token:
        print("PASS: model artifacts exist; local reload/generation validation passed and upload command completed.", flush=True)
    else:
        print("PASS: local model artifacts exist and reload/generation validation passed. NOT PUBLISHED: HF_TOKEN is missing.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
