#!/usr/bin/env python3
"""Validate a pinned Hugging Face model revision before leaderboard evaluation."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".pt", ".pth")
TOKENIZER_FILES = {
    "tokenizer.json", "tokenizer.model", "spiece.model", "vocab.json",
    "vocab.txt", "merges.txt", "tokenizer_config.json"
}

class PreflightError(RuntimeError):
    pass

def fetch_json(url: str, token: str = "") -> dict:
    headers = {"Accept": "application/json", "User-Agent": "ARIES-Leaderboard-Preflight/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read(8_000_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise PreflightError(
                f"Hugging Face returned HTTP {exc.code}; verify model visibility, model ID, and access permission."
            ) from None
        raise PreflightError(f"Hugging Face metadata request failed with HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError):
        raise PreflightError("Could not retrieve valid Hugging Face model metadata.") from None
    if not isinstance(payload, dict):
        raise PreflightError("Hugging Face returned an unexpected metadata format.")
    return payload

def validate_model(model_id: str, revision: str, token: str = "") -> dict:
    if not model_id or "/" not in model_id or model_id.startswith("/") or model_id.endswith("/"):
        raise PreflightError("Model ID must use owner/repository form, for example organization/model.")
    if not SHA_RE.fullmatch(revision):
        raise PreflightError("Revision must be a full 40-character immutable commit SHA.")
    url = "https://huggingface.co/api/models/" + model_id + "/revision/" + revision
    model = fetch_json(url, token)
    resolved = model.get("sha")
    if not isinstance(resolved, str) or resolved.lower() != revision.lower():
        raise PreflightError("Requested revision did not resolve to the exact pinned commit SHA.")
    siblings = model.get("siblings")
    if not isinstance(siblings, list):
        raise PreflightError("Model metadata did not provide a repository file list.")
    files = {
        item.get("rfilename") for item in siblings
        if isinstance(item, dict) and isinstance(item.get("rfilename"), str)
    }
    if "config.json" not in files:
        raise PreflightError("Model repository is missing config.json.")
    weights = sorted(name for name in files if name.endswith(WEIGHT_SUFFIXES))
    if not weights:
        raise PreflightError("No model weight files (.safetensors, .bin, .pt, or .pth) found; this Transformers evaluation path does not accept GGUF-only or API-only repositories.")
    if not files.intersection(TOKENIZER_FILES):
        raise PreflightError("No recognized tokenizer files found in the pinned model repository.")
    card = model.get("cardData") or {}
    return {
        "status": "passed",
        "model_id": model_id,
        "revision": resolved,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "private": bool(model.get("private", False)),
        "library_name": model.get("library_name"),
        "pipeline_tag": model.get("pipeline_tag"),
        "weight_files": weights,
        "tokenizer_files": sorted(files.intersection(TOKENIZER_FILES)),
        "model_card_license": card.get("license"),
        "file_count": len(files),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", default="reports/leaderboard/preflight.json")
    args = parser.parse_args()
    try:
        report = validate_model(args.model_id, args.revision, os.getenv("HF_TOKEN", "").strip())
    except PreflightError as exc:
        report = {
            "status": "failed", "model_id": args.model_id,
            "revision": args.revision, "error": str(exc),
            "created_at_utc": datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(report, indent=2))
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 1
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
