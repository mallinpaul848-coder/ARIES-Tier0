#!/usr/bin/env python3
"""Download a small public GGUF instruct model for ARIES local inference."""
from pathlib import Path
from urllib.request import Request, urlopen
import os
import sys

URL = os.getenv(
    "ARIES_GGUF_URL",
    "https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
)
DEST = Path(os.getenv("ARIES_GGUF_MODEL_PATH", "models/aries-model.gguf"))


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and DEST.stat().st_size > 10_000_000:
        print(f"Model already exists: {DEST} ({DEST.stat().st_size:,} bytes)")
        return
    print("Downloading the default small Qwen2.5 0.5B instruct GGUF model.")
    print("This is a third-party open model used as a starting point, not ARIES-trained weights.")
    print(f"Destination: {DEST}")
    request = Request(URL, headers={"User-Agent": "ARIES-Local-Inference/1.0"})
    temp = DEST.with_suffix(DEST.suffix + ".part")
    try:
        with urlopen(request, timeout=60) as response, temp.open("wb") as output:
            total_header = response.headers.get("Content-Length")
            total = int(total_header) if total_header and total_header.isdigit() else None
            copied = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                copied += len(chunk)
                if total:
                    print(f"\r{copied:,} / {total:,} bytes ({copied / total:.1%})", end="", flush=True)
        if copied < 10_000_000:
            raise RuntimeError(f"Downloaded file is unexpectedly small ({copied:,} bytes).")
        temp.replace(DEST)
        print(f"\nModel saved to {DEST} ({copied:,} bytes).")
        print("Review the model card and license before redistributing the weights.")
    except Exception as exc:
        temp.unlink(missing_ok=True)
        print(f"Download failed: {exc}", file=sys.stderr)
        print("You can set ARIES_GGUF_URL to another compatible GGUF model URL.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
