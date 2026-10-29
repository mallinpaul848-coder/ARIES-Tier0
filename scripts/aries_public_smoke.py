#!/usr/bin/env python3
"""Black-box smoke tests for the public ARIES API.

Usage:
  python scripts/aries_public_smoke.py --base-url https://your-aries-host.example
  ARIES_BASE_URL=http://127.0.0.1:10000 python scripts/aries_public_smoke.py

Uses only the Python standard library. Reports measured request latency; it does not
claim independent certification or model-quality scores.
"""
import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request


def request_json(base_url, path, payload=None, timeout=45):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base_url.rstrip("/") + path, data=data, headers=headers)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    elapsed_ms = (time.perf_counter() - started) * 1000
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        body = {"raw": raw[:500].decode("utf-8", errors="replace")}
    return status, body, elapsed_ms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "http://127.0.0.1:10000"))
    parser.add_argument("--repeat", type=int, default=3, help="number of chat probes (1-20)")
    args = parser.parse_args()
    if not 1 <= args.repeat <= 20:
        parser.error("--repeat must be between 1 and 20")

    failures = []
    latencies = []
    print("ARIES public API smoke test")
    print("Base URL:", args.base_url.rstrip("/"))

    for path in ("/health", "/diagnostics", "/v1/models"):
        try:
            status, body, elapsed = request_json(args.base_url, path)
            ok = status == 200 and isinstance(body, dict)
            print(f"{'PASS' if ok else 'FAIL'} {path}: HTTP {status}, {elapsed:.1f} ms")
            if path == "/diagnostics" and isinstance(body, dict):
                print("  backend:", body.get("backend", "not reported"))
                print("  general_chat_ready:", body.get("general_chat_ready", "not reported"))
            if not ok:
                failures.append(f"{path} returned HTTP {status}")
        except Exception as exc:
            print(f"FAIL {path}: {type(exc).__name__}: {exc}")
            failures.append(f"{path} request failed")

    prompt = "Reply with a short greeting and state that you are ARIES AI."
    for index in range(args.repeat):
        try:
            status, body, elapsed = request_json(
                args.base_url,
                "/v1/chat/completions",
                {
                    "model": "aries-native-ngram",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 96,
                    "temperature": 0,
                },
            )
            choices = body.get("choices", []) if isinstance(body, dict) else []
            message = choices[0].get("message", {}) if choices else {}
            answer = message.get("content") if isinstance(message, dict) else None
            ok = status == 200 and isinstance(answer, str) and bool(answer.strip())
            print(f"{'PASS' if ok else 'FAIL'} chat probe {index + 1}: HTTP {status}, {elapsed:.1f} ms")
            if ok:
                latencies.append(elapsed)
                meta = body.get("aries_native", {})
                if index == 0 and isinstance(meta, dict):
                    print("  runtime:", meta.get("runtime", "not reported"))
                    print("  model_type:", meta.get("model_type", "not reported"))
            else:
                detail = body.get("detail") or body.get("error") or body
                print("  response:", str(detail)[:300])
                failures.append(f"chat probe {index + 1} returned no usable answer")
        except Exception as exc:
            print(f"FAIL chat probe {index + 1}: {type(exc).__name__}: {exc}")
            failures.append(f"chat probe {index + 1} request failed")

    if latencies:
        ordered = sorted(latencies)
        p95_index = max(0, min(len(ordered) - 1, int(0.95 * len(ordered) + 0.999) - 1))
        print(f"Chat latency ms: min={min(latencies):.1f}, mean={statistics.mean(latencies):.1f}, "
              f"p95={ordered[p95_index]:.1f} (n={len(latencies)}; includes network)")
    print(f"\nResult: {'PASS' if not failures else 'FAIL'} — "
          f"{args.repeat - len(latencies)} failed chat probe(s), {len(failures)} total failure(s).")
    print("These are smoke tests, not a third-party benchmark or certification.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
