#!/usr/bin/env python3
"""Verify a public Hugging Face causal-LM repository can load and generate text.

Usage:
  python benchmarks/verify_hf_model.py YOUR_HF_ORG/aries-v1
  python benchmarks/verify_hf_model.py YOUR_HF_ORG/aries-v1 --revision MODEL_COMMIT_SHA

This is a packaging/generation smoke test only. It does not measure model quality or
submit the model to any leaderboard.
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_id", help="Public Hugging Face model repository, e.g. org/model")
    parser.add_argument("--revision", help="Optional immutable model commit SHA or revision")
    parser.add_argument("--max-new-tokens", type=int, default=16)
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Allow custom repository code (not accepted by the standard Open LLM Leaderboard path)",
    )
    args = parser.parse_args()
    if args.max_new_tokens < 1 or args.max_new_tokens > 128:
        parser.error("--max-new-tokens must be between 1 and 128")

    try:
        import torch
        from huggingface_hub import HfApi
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print(
            "ERROR: Missing dependencies. Run: python -m pip install -U transformers torch safetensors huggingface_hub",
            file=sys.stderr,
        )
        return 2

    load_args = {"revision": args.revision} if args.revision else {}
    if args.trust_remote_code:
        load_args["trust_remote_code"] = True

    try:
        info = HfApi().model_info(args.repo_id, revision=args.revision)
        if info.private:
            raise RuntimeError("Repository is private; public-download validation requires a public model repository.")
        resolved_revision = info.sha
        print(f"Public repository confirmed: https://huggingface.co/{args.repo_id}", flush=True)
        print(f"Resolved immutable revision: {resolved_revision}", flush=True)

        config = AutoConfig.from_pretrained(args.repo_id, **load_args)
        tokenizer = AutoTokenizer.from_pretrained(args.repo_id, **load_args)
        model = AutoModelForCausalLM.from_pretrained(args.repo_id, torch_dtype="auto", **load_args)
        model.eval()
        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        inputs = tokenizer("Verify ARIES model generation:", return_tensors="pt")
        inputs = {key: value.to(next(model.parameters()).device) for key, value in inputs.items()}
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        if generated.shape[1] <= inputs["input_ids"].shape[1]:
            raise RuntimeError("Model loaded but did not generate any new tokens.")
        decoded = tokenizer.decode(generated[0], skip_special_tokens=True)
        print("PASS: public config, tokenizer, and causal-LM weights loaded.")
        print("PASS: generated new tokens from the public repository.")
        print(f"repo_id={args.repo_id}")
        print(f"revision={resolved_revision}")
        print(f"model_type={getattr(config, 'model_type', 'unknown')}")
        print(f"tokenizer_class={tokenizer.__class__.__name__}")
        print(f"model_class={model.__class__.__name__}")
        print(f"parameter_count={parameter_count}")
        print(f"generated_text={decoded!r}")
        print("NOTE: Packaging/generation validation is not an independent benchmark or leaderboard submission.")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "Check that the repository is public, contains supported config/tokenizer/weights, "
            "and uses a stable Transformers architecture.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
