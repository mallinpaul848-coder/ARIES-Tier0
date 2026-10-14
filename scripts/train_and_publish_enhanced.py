#!/usr/bin/env python3
"""ARIES enhanced training wrapper with an explicit, auditable math curriculum.

This adds a small set of user-authored educational examples to a licensed base corpus,
then delegates training, safetensors export, local reload/generation validation, and
optional Hub upload to the repository's tested training pipeline.

Important: a short curriculum does not prove new mathematics or solve Millennium Prize
problems. Results depend on corpus quality, training budget, and independent evaluation.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MATH_CURRICULUM = [
    "ARIES educational note: modular digital-root arithmetic can be used as a feature "
    "for pattern exploration. For positive integer n, the digital root is 1 + ((n - 1) mod 9). "
    "This identity is arithmetic, not evidence of a new physical law.",
    "ARIES educational note: a vortex in fluid mechanics is studied using the governing "
    "equations, boundary conditions, regularity estimates, and reproducible numerical experiments. "
    "A proposed compression tensor is a hypothesis until mathematically defined and validated.",
    "ARIES educational note: a helical or spiral coordinate transform is a geometric representation. "
    "Its usefulness must be tested against a baseline and does not itself establish a topological invariant.",
    "ARIES educational note: the Riemann hypothesis concerns the nontrivial zeros of the analytic "
    "continuation of the Riemann zeta function. Harmonic visualizations are not a proof about its zeros.",
    "ARIES educational note: the Navier-Stokes existence and smoothness problem requires a rigorous "
    "proof under the exact problem statement; simulation results or vortex analogies alone are insufficient.",
    "ARIES educational note: any claim about P versus NP must use formal complexity definitions and a "
    "valid proof. Pattern detection or numerical experiments do not establish P != NP.",
    "ARIES educational note: report assumptions, definitions, derivation steps, counterexamples, and "
    "independent verification separately. Label conjectures as conjectures and established theorems as theorems.",
]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=os.getenv("CORPUS_PATH", "data/training.txt"))
    parser.add_argument("--repo-id", default=os.getenv("HF_TARGET_REPO", "PaulMallin/aries-core-v1"))
    parser.add_argument("--output-dir", default="artifacts/aries-core-v1")
    parser.add_argument("--steps", type=int, default=int(os.getenv("TRAINING_STEPS", "1000")))
    args = parser.parse_args()

    corpus = Path(args.corpus)
    if not corpus.is_file():
        print(f"ERROR: base corpus not found: {corpus}", file=sys.stderr)
        return 2
    base = corpus.read_text(encoding="utf-8-sig").strip()
    if len(base) < 100_000:
        print(f"ERROR: base corpus has only {len(base):,} characters; at least 100,000 are required.", file=sys.stderr)
        return 2

    # Keep the generated curriculum file out of the repository and model output folder.
    with tempfile.TemporaryDirectory(prefix="aries-math-curriculum-") as tmp:
        combined = Path(tmp) / "training_with_math_curriculum.txt"
        combined.write_text(base + "\n\n" + "\n\n".join(MATH_CURRICULUM) + "\n", encoding="utf-8")
        env = os.environ.copy()
        env["TRAINING_DATA_PROVENANCE"] = (
            f"Base corpus: {corpus.as_posix()} ({len(base):,} characters; verify its license and attribution). "
            f"Supplement: {len(MATH_CURRICULUM)} short ARIES-authored educational math notes. "
            "These notes are training examples, not proofs of Millennium Prize problems."
        )
        cmd = [
            sys.executable, "scripts/build_and_publish.py",
            "--corpus", str(combined),
            "--repo-id", args.repo_id,
            "--output-dir", args.output_dir,
            "--steps", str(args.steps),
        ]
        print(f"ARIES enhanced pipeline: base characters={len(base):,}; math curriculum entries={len(MATH_CURRICULUM)}; steps={args.steps}", flush=True)
        return subprocess.run(cmd, env=env, check=False).returncode

if __name__ == "__main__":
    raise SystemExit(main())
