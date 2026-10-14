#!/usr/bin/env python3
"""ARIES corpus preparation utility. Python standard library only."""
import argparse
import hashlib
import json
import re
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".rst", ".csv", ".jsonl"}

def normalize(text):
    text = text.replace("\ufeff", "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def prepare(source, output, report):
    src = Path(source)
    files = [src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES)
    if not files:
        raise SystemExit(f"No supported text files found under {src}")
    seen = set()
    blocks = []
    inputs = []
    chars_in = 0
    for path in files:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            inputs.append({"file": str(path), "error": str(exc)})
            continue
        chars_in += len(raw)
        cleaned = normalize(raw)
        digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
        duplicate = digest in seen
        seen.add(digest)
        inputs.append({"file": str(path), "characters": len(raw), "clean_characters": len(cleaned), "sha256": digest, "duplicate": duplicate})
        if cleaned and not duplicate:
            blocks.append(cleaned)
    corpus = "\n\n".join(blocks) + ("\n" if blocks else "")
    if len(corpus.strip()) < 100:
        raise SystemExit("Prepared corpus has fewer than 100 non-whitespace characters; add more text.")
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(corpus, encoding="utf-8")
    result = {
        "tool": "ARIES Native Corpus Prep 1.0",
        "source": str(src),
        "output": str(out),
        "files_seen": len(files),
        "unique_documents": len(blocks),
        "input_characters": chars_in,
        "output_characters": len(corpus),
        "sha256": hashlib.sha256(corpus.encode("utf-8")).hexdigest(),
        "files": inputs,
        "warning": "This tool normalizes and deduplicates text only. It does not verify factual accuracy, licensing, privacy, or data quality."
    }
    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "files"}, indent=2))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, help="A UTF-8 text file or directory")
    p.add_argument("--output", default="data/prepared.txt")
    p.add_argument("--report", default="reports/corpus-prep.json")
    a = p.parse_args()
    prepare(a.source, a.output, a.report)

if __name__ == "__main__":
    main()
