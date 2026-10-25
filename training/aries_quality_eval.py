#!/usr/bin/env python3
"""Evaluate an ARIES trainer checkpoint on a separate held-out text corpus.

Reports held-out next-token loss, perplexity, and token accuracy. These are
language-model diagnostics, not proof of reasoning ability or general intelligence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="checkpoint.pt from aries_trillion_token_trainer.py")
    parser.add_argument("--validation-corpus", required=True, help="Separate, licensed UTF-8 validation corpus")
    parser.add_argument("--tokenizer", default="", help="Override checkpoint tokenizer only if intentionally compatible")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-batches", type=int, default=100, help="Maximum validation batches; 0 means all")
    parser.add_argument("--output", default="artifacts/aries-quality-evaluation.json")
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    corpus_path = Path(args.validation_corpus)
    if not checkpoint_path.is_file() or not corpus_path.is_file() or corpus_path.stat().st_size == 0:
        parser.error("checkpoint and a non-empty validation corpus must exist")
    if args.batch_size < 1 or args.max_batches < 0:
        parser.error("batch-size must be >= 1 and max-batches must be >= 0")

    try:
        import torch
        import torch.nn.functional as F
        from torch.utils.data import DataLoader
    except ImportError:
        print("ERROR: install PyTorch before evaluating.", file=sys.stderr)
        return 2

    if args.max_batches == 0:
        max_batches = None
    else:
        max_batches = args.max_batches

    trainer_path = Path(__file__).with_name("aries_trillion_token_trainer.py")
    spec = importlib.util.spec_from_file_location("aries_trainer_module", trainer_path)
    if spec is None or spec.loader is None:
        print("ERROR: could not load ARIES trainer implementation.", file=sys.stderr)
        return 2
    trainer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = trainer
    spec.loader.exec_module(trainer)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    try:
        state = torch.load(checkpoint_path, map_location=device, weights_only=False)
        if state.get("format") != "aries-streaming-causal-lm-v1":
            raise ValueError("unsupported checkpoint format")
        config = state["model_config"]
        tokenizer_mode = args.tokenizer or (
            "byte" if config["tokenizer"] == "utf8_byte_ids_plus_eol_v1"
            else "hf:" + config["tokenizer"]
        )
        tokenizer, vocab_size, eos_id, tokenizer_label = trainer.load_tokenizer(tokenizer_mode)
        if vocab_size != int(config["vocab_size"]):
            raise ValueError(f"vocab mismatch: checkpoint={config['vocab_size']} tokenizer={vocab_size}")
        model = trainer.build_model(
            torch, torch.nn, F, vocab_size, int(config["d_model"]), int(config["layers"]),
            int(config["heads"]), int(config["seq_len"]), float(config["dropout"]),
        ).to(device)
        model.load_state_dict(state["model_state_dict"])
    except Exception as exc:
        print(f"ERROR: checkpoint/model loading failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    training_hash = state.get("corpus_sha256")
    validation_hash = sha256_file(corpus_path)
    if training_hash and training_hash == validation_hash:
        print("ERROR: validation corpus hash matches training corpus; use a distinct held-out file.", file=sys.stderr)
        return 2

    dataset = trainer.build_dataset(
        torch, corpus_path, tokenizer, tokenizer_mode, eos_id, int(config["seq_len"]), 0, 1
    )
    loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=0)
    model.eval()
    token_loss_sum = 0.0
    correct_tokens = 0
    total_tokens = 0
    batches = 0
    started = time.perf_counter()
    with torch.inference_mode():
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            logits = model(inputs)
            loss_sum = F.cross_entropy(
                logits.reshape(-1, vocab_size), targets.reshape(-1), reduction="sum"
            )
            predictions = logits.argmax(dim=-1)
            token_loss_sum += float(loss_sum.item())
            correct_tokens += int((predictions == targets).sum().item())
            total_tokens += int(targets.numel())
            batches += 1
            if max_batches is not None and batches >= max_batches:
                break

    if total_tokens == 0:
        print("ERROR: validation corpus yielded no full token blocks; add text or reduce sequence length.", file=sys.stderr)
        return 2

    elapsed = max(time.perf_counter() - started, 1e-9)
    mean_loss = token_loss_sum / total_tokens
    evidence = {
        "format": "aries-heldout-quality-evaluation-v1",
        "status": "PASS",
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "checkpoint_global_step": int(state.get("global_step", 0)),
        "checkpoint_training_tokens_seen": int(state.get("tokens_seen", 0)),
        "training_corpus_sha256": training_hash,
        "validation_corpus_sha256": validation_hash,
        "validation_corpus_bytes": corpus_path.stat().st_size,
        "tokenizer": tokenizer_label,
        "device": str(device),
        "validation_batches": batches,
        "validation_tokens": total_tokens,
        "mean_next_token_cross_entropy": round(mean_loss, 8),
        "perplexity": round(math.exp(min(mean_loss, 80.0)), 8),
        "next_token_accuracy": round(correct_tokens / total_tokens, 8),
        "correct_next_token_predictions": correct_tokens,
        "elapsed_seconds": round(elapsed, 6),
        "validation_tokens_per_second": round(total_tokens / elapsed, 3),
        "interpretation": "Held-out next-token metrics only; not a reasoning benchmark, human preference study, or independent certification.",
    }
    atomic_json(Path(args.output), evidence)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
