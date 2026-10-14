#!/usr/bin/env python3
"""Validate and publish an EXISTING trained ARIES checkpoint.

This script intentionally does not instantiate a new randomly initialized model.
It loads the checkpoint from ARIES_MODEL_DIR, validates its Transformers interfaces,
exports only model/config/tokenizer files to a clean staging directory, and uploads
that allowlisted directory. Raw source code and training corpora are never copied.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ALLOWED_FILES = {
    "config.json",
    "generation_config.json",
    "model.safetensors",
    "model.safetensors.index.json",
    "pytorch_model.bin",
    "pytorch_model.bin.index.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.json",
    "merges.txt",
    "vocab.txt",
    "added_tokens.json",
    "README.md",
}
ALLOWED_PREFIXES = ("model-", "pytorch_model-", "tokenizer-")


def main() -> int:
    source = Path(os.getenv("ARIES_MODEL_DIR", "published/aries-core-v1")).resolve()
    repo_id = os.getenv("HF_TARGET_REPO", "PaulMallin/aries-core-v1").strip()
    token = os.getenv("HF_TOKEN", "").strip()

    if not repo_id or repo_id.count("/") != 1:
        print("ERROR: HF_TARGET_REPO must be namespace/name.", file=sys.stderr)
        return 2
    if not source.is_dir():
        print(f"ERROR: checkpoint directory does not exist: {source}", file=sys.stderr)
        return 2
    if not (source / "config.json").is_file():
        print("ERROR: source checkpoint is missing config.json.", file=sys.stderr)
        return 2

    try:
        from huggingface_hub import HfApi, create_repo
        from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        print(f"ERROR: missing dependency: {exc}. Install transformers, torch, safetensors, and huggingface_hub.", file=sys.stderr)
        return 2

    print(f"[1/4] Loading existing checkpoint: {source}", flush=True)
    try:
        config = AutoConfig.from_pretrained(source, local_files_only=True, trust_remote_code=False)
        tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(
            source, local_files_only=True, trust_remote_code=False, use_safetensors=True
        )
        model.eval()
        test = tokenizer("ARIES checkpoint validation.", return_tensors="pt")
        import torch
        with torch.inference_mode():
            generated = model.generate(**test, max_new_tokens=4, do_sample=False)
        decoded = tokenizer.decode(generated[0], skip_special_tokens=True)
        if not decoded.strip():
            raise RuntimeError("generation produced empty decoded text")
    except Exception as exc:
        print(f"ERROR: local checkpoint load/generation validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    print(f"[2/4] Validated architecture={config.model_type}; parameters={sum(p.numel() for p in model.parameters()):,}; smoke output={decoded!r}", flush=True)
    with tempfile.TemporaryDirectory(prefix="aries-public-export-") as tmp:
        stage = Path(tmp) / "export"
        stage.mkdir()
        # Re-serialize the loaded trained checkpoint, not a new random model.
        model.save_pretrained(stage, safe_serialization=True)
        tokenizer.save_pretrained(stage)
        readme_source = source / "README.md"
        if readme_source.is_file():
            shutil.copyfile(readme_source, stage / "README.md")
        else:
            (stage / "README.md").write_text(
                "---\nlanguage:\n- en\nlibrary_name: transformers\nlicense: other\ntags:\n- aries\n---\n\n"
                "# ARIES experimental checkpoint\n\n"
                "Experimental model checkpoint. Review the repository's training-data provenance, "
                "limitations, and evaluation reports before relying on this model. No official leaderboard "
                "rank or independent quality certification is claimed.\n",
                encoding="utf-8",
            )

        unexpected = [p.name for p in stage.iterdir() if p.is_file() and p.name not in ALLOWED_FILES and not p.name.startswith(ALLOWED_PREFIXES)]
        if unexpected:
            print(f"ERROR: refusing export with unexpected files: {unexpected}", file=sys.stderr)
            return 4
        required = ("config.json", "model.safetensors", "tokenizer_config.json")
        missing = [name for name in required if not (stage / name).is_file()]
        if missing:
            print(f"ERROR: staged export is missing required files: {missing}", file=sys.stderr)
            return 4

        if "--validate-only" in sys.argv[1:]:
            print("[3/4] VALIDATION PASSED: existing checkpoint loaded, generation succeeded, and allowlisted export files are staged.", flush=True)
            print("No upload was attempted because --validate-only was selected.", flush=True)
            return 0

        if not token:
            print("[3/4] Local checkpoint validation and allowlisted export passed.", flush=True)
            print("BLOCKED: HF_TOKEN is missing, so no Hugging Face upload was attempted. Add it as a GitHub Actions repository secret; never paste it into source code or chat.", file=sys.stderr)
            return 6

        print(f"[3/4] Creating/confirming public model repository: {repo_id}", flush=True)
        try:
            api = HfApi(token=token)
            create_repo(repo_id=repo_id, repo_type="model", private=False, exist_ok=True, token=token)
            print("[4/4] Uploading allowlisted serialized model files only.", flush=True)
            api.upload_folder(
                folder_path=str(stage),
                repo_id=repo_id,
                repo_type="model",
                token=token,
                allow_patterns=sorted(ALLOWED_FILES | {p.name for p in stage.iterdir() if p.is_file() and p.name.startswith(ALLOWED_PREFIXES)}),
                commit_message="Publish validated ARIES experimental checkpoint",
            )
            info = api.model_info(repo_id, token=token)
            print(f"SUCCESS: uploaded and verified model repository https://huggingface.co/{info.id}", flush=True)
            print("LIMIT: successful upload verifies repository access and files, not leaderboard eligibility or model quality.", flush=True)
        except Exception as exc:
            print(f"ERROR: Hugging Face publish/verification failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
