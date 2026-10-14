#!/usr/bin/env python3
"""Safe entry point for ARIES public model packaging.

This deliberately delegates to publish_robust.py, which validates and packages
the EXISTING trained checkpoint. It does not create or upload random GPT-2
weights. HF_TOKEN is read only from the runtime environment, never source code.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    target = Path(__file__).resolve().with_name("publish_robust.py")
    if not target.is_file():
        print(f"ERROR: required publisher not found: {target}", file=sys.stderr)
        return 2
    command = [sys.executable, str(target), *sys.argv[1:]]
    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
