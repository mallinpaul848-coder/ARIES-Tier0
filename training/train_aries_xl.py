#!/usr/bin/env python3
"""Launch ARIES XL (~1B parameters) using the repository's existing trainer.

Default is a 3-step smoke run. Use --full only with a licensed corpus and
adequate GPU memory. This launcher does not claim training has completed.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "training" / "aries_trillion_token_trainer.py"
CONFIG = ROOT / "training" / "aries_xl_config.json"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, help="UTF-8 text file you own or are licensed to use")
    p.add_argument("--output-dir", default="artifacts/aries-xl-1b")
    p.add_argument("--tokenizer", default="byte", help="byte (offline) or hf:NAME")
    p.add_argument("--target-training-tokens", type=int, default=1_000_000_000)
    p.add_argument("--max-steps", type=int, default=3, help="Smoke-run default; 0 runs to token target")
    p.add_argument("--full", action="store_true", help="Run until the target token-exposure count")
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--seq-len", type=int, default=1024)
    p.add_argument("--checkpoint-every-steps", type=int, default=100)
    p.add_argument("--resume-from-checkpoint", default="")
    p.add_argument("--no-amp", action="store_true")
    a = p.parse_args()
    corpus = Path(a.corpus).expanduser().resolve()
    if not corpus.is_file(): p.error(f"Corpus file not found: {corpus}")
    if corpus.stat().st_size == 0: p.error("Corpus file is empty.")
    if a.target_training_tokens <= 0: p.error("--target-training-tokens must be positive")
    if a.batch_size < 1 or a.seq_len < 8: p.error("batch-size must be >=1 and seq-len >=8")
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    cmd = [sys.executable, str(TRAINER), "--corpus", str(corpus),
      "--tokenizer", a.tokenizer, "--output-dir", a.output_dir,
      "--target-training-tokens", str(a.target_training_tokens),
      "--max-steps", "0" if a.full else str(a.max_steps),
      "--checkpoint-every-steps", str(a.checkpoint_every_steps),
      "--resume-from-checkpoint", a.resume_from_checkpoint,
      "--batch-size", str(a.batch_size), "--seq-len", str(a.seq_len),
      "--d-model", str(c["d_model"]), "--layers", str(c["layers"]),
      "--heads", str(c["heads"]), "--dropout", str(c["dropout"]),
      "--learning-rate", str(c["learning_rate"]), "--weight-decay", str(c["weight_decay"]),
      "--seed", str(c["seed"])]
    if a.no_amp: cmd.append("--no-amp")
    print(json.dumps({"model": c["model_name"], "approx_parameters": c["target_parameters_approx"],
      "d_model": c["d_model"], "layers": c["layers"], "heads": c["heads"],
      "seq_len": a.seq_len, "batch_size": a.batch_size, "tokenizer": a.tokenizer,
      "max_steps": 0 if a.full else a.max_steps, "target_token_exposures": a.target_training_tokens,
      "corpus_bytes": corpus.stat().st_size, "mode": "full training" if a.full else "smoke run"}, indent=2))
    print("Starting ARIES streaming trainer. Review logs for actual measurements.")
    return subprocess.call(cmd, cwd=ROOT)

if __name__ == "__main__":
    raise SystemExit(main())
