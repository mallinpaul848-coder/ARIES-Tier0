#!/usr/bin/env python3
"""Validate that a public Hugging Face repository can load as a causal LM.

Usage:
  python -m pip install -U transformers torch safetensors
  python benchmarks/verify_hf_model.py YOUR_HF_ORG/aries-v1
  python benchmarks/verify_hf_model.py YOUR_HF_ORG/aries-v1 --revision COMMIT_SHA

This verifies packaging/loading only. It does not certify benchmark quality or submit
the model to any leaderboard.
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_id", help="Public Hugging Face model repository, e.g. org/model")
    parser.add_argument("--revision", help="Optional immutable model commit SHA or revision")
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Allow custom repository code (not accepted by the Open LLM Leaderboard submission path)",
    )
    args = parser.parse_args()

    try:
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("ERROR: Missing dependencies. Run: python -m pip install -U transformers torch safetensors", file=sys.stderr)
        return 2

    load_args = {"revision": args.revision} if args.revision else {}
    if args.trust_remote_code:
        load_args["trust_remote_code"] = True

    try:
        print(f"Loading config: {args.repo_id}", flush=True)
        config = AutoConfig.from_pretrained(args.repo_id, **load_args)
        print(f"Loading tokenizer: {args.repo_id}", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(args.repo_id, **load_args)
        print(f"Loading causal-LM weights: {args.repo_id}", flush=True)
        model = AutoModelForCausalLM.from_pretrained(args.repo_id, **load_args)
        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        print("PASS: config, tokenizer, and causal-LM weights loaded.")
        print(f"repo_id={args.repo_id}")
        print(f"revision={args.revision or 'default branch (not pinned)'}")
        print(f"model_type={getattr(config, 'model_type', 'unknown')}")
        print(f"tokenizer_class={tokenizer.__class__.__name__}")
        print(f"model_class={model.__class__.__name__}")
        print(f"parameter_count={parameter_count}")
        print("NOTE: This is a packaging smoke test, not a benchmark result or leaderboard submission.")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Check that the repository is public, includes supported config/tokenizer/weights, and uses a stable Transformers architecture.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
