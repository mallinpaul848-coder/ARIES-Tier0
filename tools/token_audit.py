#!/usr/bin/env python3
"""Audit a local text corpus for ARIES pretraining readiness.

Counts tokenizer tokens actually present in readable files. It does NOT train a
model, download a dataset, or claim that a target token budget has been processed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".jsonl", ".json", ".csv", ".html", ".xml"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="Directory containing licensed text files")
    parser.add_argument("--tokenizer", required=True, help="Hugging Face tokenizer ID or local path")
    parser.add_argument("--target-tokens", type=int, default=1_000_000_000_000)
    parser.add_argument("--output", default="reports/token-audit.json")
    parser.add_argument("--max-files", type=int, default=0, help="Optional limit for smoke tests; 0 means all")
    args = parser.parse_args()
    if args.target_tokens < 1:
        parser.error("--target-tokens must be positive")

    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("ERROR: install dependencies with: python -m pip install transformers")
        return 2

    root = Path(args.corpus).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: corpus directory does not exist: {root}")
        return 2

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, use_fast=True)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES)
    if args.max_files:
        files = files[:args.max_files]

    started = time.perf_counter()
    token_count = 0
    bytes_read = 0
    file_records = []
    corpus_hash = hashlib.sha256()
    failures = []

    for path in files:
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="replace")
            count = len(tokenizer.encode(text, add_special_tokens=False))
            token_count += count
            bytes_read += len(raw)
            digest = hashlib.sha256(raw).hexdigest()
            corpus_hash.update(path.relative_to(root).as_posix().encode("utf-8"))
            corpus_hash.update(bytes.fromhex(digest))
            file_records.append({"path": path.relative_to(root).as_posix(),
                                 "bytes": len(raw), "tokens": count, "sha256": digest})
        except Exception as exc:
            failures.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})

    elapsed = time.perf_counter() - started
    report = {
        "status": "AUDIT_COMPLETE" if not failures else "AUDIT_INCOMPLETE",
        "tokenizer": args.tokenizer,
        "corpus_directory": str(root),
        "files_discovered": len(files),
        "files_counted": len(file_records),
        "files_failed": len(failures),
        "bytes_counted": bytes_read,
        "actual_tokens_in_corpus": token_count,
        "target_tokens": args.target_tokens,
        "token_budget_coverage_percent": round(100 * token_count / args.target_tokens, 12),
        "additional_tokens_needed_to_reach_target": max(0, args.target_tokens - token_count),
        "corpus_manifest_sha256": corpus_hash.hexdigest(),
        "audit_seconds": round(elapsed, 3),
        "warning": "Corpus token count is not tokens trained. Training progress must be logged separately from completed optimizer steps and checkpoint metadata.",
        "files": file_records,
        "failures": failures,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"files", "failures"}}, indent=2))
    print(f"Report written to {output}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
