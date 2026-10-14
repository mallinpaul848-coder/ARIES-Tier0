#!/usr/bin/env python3
"""Package ARIES source, benchmark tools, and available checkpoint files.

Run from any directory:
  python tools/package_aries.py
  python tools/package_aries.py --output /path/to/aries_sub_nanosecond_model.zip

The archive includes repository files and published checkpoint assets while excluding
Git metadata, virtual environments, caches, common credential files, and the output ZIP.
A SHA-256 manifest is included for every archived file except the manifest itself.
This script does not claim any particular inference latency or leaderboard status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", "node_modules",
}
EXCLUDED_NAMES = {
    ".env", ".env.local", ".env.production", "secrets.json",
    "credentials.json", "id_rsa", "id_ed25519",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
MANIFEST_NAME = "EXPORT_MANIFEST.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_exclude(path: Path, output: Path) -> bool:
    try:
        if path.resolve() == output.resolve():
            return True
    except OSError:
        pass
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name.endswith((".pem", ".key")):
        return True
    if path.name.lower().startswith(("hf_token", "huggingface_token", "github_token")):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(ROOT / "aries_sub_nanosecond_model.zip"),
        help="Output ZIP path (default: repository root)",
    )
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or should_exclude(path, output):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == MANIFEST_NAME:
            continue
        files.append((rel, path))
    files.sort(key=lambda item: item[0].lower())

    entries = [
        {"path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for rel, path in files
    ]
    manifest = {
        "project": "ARIES Tier0",
        "archive": output.name,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "repository_root": ROOT.name,
        "file_count_excluding_manifest": len(entries),
        "sha256_algorithm": "SHA-256",
        "scope": "Source and available repository assets; not a latency certification or leaderboard submission.",
        "files": entries,
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for rel, path in files:
            archive.write(path, arcname=f"ARIES-Tier0/{rel}")
        archive.writestr(
            f"ARIES-Tier0/{MANIFEST_NAME}",
            json.dumps(manifest, indent=2) + "\n",
        )

    print(f"Archive: {output}")
    print(f"Files packaged (excluding manifest): {len(entries)}")
    print(f"Archive size: {output.stat().st_size} bytes")
    print(f"Manifest: ARIES-Tier0/{MANIFEST_NAME}")
    print("Note: inspect the archive for sensitive or licensed files before sharing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
