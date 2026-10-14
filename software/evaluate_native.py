#!/usr/bin/env python3
"""Evaluate the ARIES n-gram model on held-out text using stdlib only."""
import argparse
import json
import math
import time
from pathlib import Path
from native_runtime import NativeModel

def evaluate(model_path, test_path, report_path):
    model = NativeModel(model_path)
    text = Path(test_path).read_text(encoding="utf-8", errors="replace")
    if len(text) < model.order + 2:
        raise SystemExit("Held-out text is too short for evaluation.")
    # Conditional character cross-entropy from model's next-character counts.
    counts = model.counts
    nll = 0.0
    scored = 0
    misses = 0
    started = time.perf_counter()
    padded = ("\u0002" * model.order) + text + "\u0003"
    for i in range(model.order, len(padded)):
        context = padded[i-model.order:i]
        target = padded[i]
        counter = None
        for n in range(model.order, -1, -1):
            key = context[-n:] if n else ""
            counter = counts.get(key)
            if counter:
                break
        if not counter:
            misses += 1
            continue
        total = sum(counter.values())
        # Additive smoothing over observed local alphabet + target.
        vocab = max(1, len(model.vocab))
        prob = (counter.get(target, 0) + 0.1) / (total + 0.1 * vocab)
        nll -= math.log(prob)
        scored += 1
    elapsed = time.perf_counter() - started
    report = {
        "tool": "ARIES Native Held-out Evaluator 1.0",
        "model": str(model_path),
        "test_file": str(test_path),
        "test_characters": len(text),
        "scored_characters": scored,
        "unscored_contexts": misses,
        "mean_negative_log_likelihood_nats_per_char": round(nll / scored, 6) if scored else None,
        "perplexity_per_character": round(math.exp(min(50, nll / scored)), 6) if scored else None,
        "evaluation_seconds": round(elapsed, 6),
        "warning": "This is character-level n-gram perplexity, not MMLU/GSM8K/BBH or a public leaderboard score."
    }
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="aries-native-ngram.json")
    p.add_argument("--test", required=True, help="Held-out UTF-8 text not included in training")
    p.add_argument("--output", default="reports/native-evaluation.json")
    a = p.parse_args()
    evaluate(a.model, a.test, a.output)

if __name__ == "__main__":
    main()
