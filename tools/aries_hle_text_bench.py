#!/usr/bin/env python3
"""Preliminary ARIES HLE text-only probe.

This is not the official HLE evaluation: it skips image-dependent items, uses a
deterministic sample, and reports strict normalized exact match without an LLM
judge. It deliberately stores aggregate metrics only, not questions or answers.
"""
import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

def normalize(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"^[\s\W]+|[\s\W]+$", "", value)
    return value

def request_json(url, payload, api_key, timeout):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return response.status, json.loads(raw) if raw else {}

def has_image(example):
    image = example.get("image")
    if image is not None:
        return True
    for key in ("image_url", "image_path", "figure", "diagram"):
        if example.get(key):
            return True
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "https://aries-tier0-api-6qjh.onrender.com"))
    parser.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"))
    parser.add_argument("--api-key", default=os.getenv("ARIES_API_KEY", ""))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--output", default="reports/aries-hle-text-probe.json")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 2500:
        parser.error("--limit must be between 1 and 2500")

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install requirements with: pip install datasets") from exc

    started = time.perf_counter()
    dataset = load_dataset("cais/hle", split="test")
    dataset_rows = len(dataset)
    selected = []
    skipped_images = 0
    for row in dataset:
        if has_image(row):
            skipped_images += 1
            continue
        question = str(row.get("question", "")).strip()
        answer = str(row.get("answer", "")).strip()
        if question and answer:
            selected.append({"question": question, "answer": answer, "subject": str(row.get("subject", "unknown"))})
        if len(selected) >= args.limit:
            break

    base = args.base_url.rstrip("/")
    api_root = base if base.endswith("/v1") else base + "/v1"
    model = args.model
    try:
        req = urllib.request.Request(api_root + "/models", headers={"Accept":"application/json"})
        with urllib.request.urlopen(req, timeout=args.timeout) as response:
            models = json.loads(response.read().decode("utf-8", errors="replace"))
        advertised = models.get("data", [])
        if model == "auto" and advertised:
            model = advertised[0].get("id", "auto")
    except Exception:
        pass

    category = {}
    outcomes = []
    latencies = []
    errors = 0
    for idx, item in enumerate(selected, 1):
        t0 = time.perf_counter()
        result = {"index": idx, "subject": item["subject"]}
        try:
            status, response = request_json(
                api_root + "/chat/completions",
                {"model": model, "messages":[{"role":"user","content":item["question"]}],
                 "temperature":0, "max_tokens":512},
                args.api_key, args.timeout)
            elapsed = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed)
            choices = response.get("choices", [])
            actual = choices[0].get("message", {}).get("content", "") if choices else ""
            passed = normalize(actual) == normalize(item["answer"])
            result.update({"status":status, "nonempty":bool(str(actual).strip()), "exact_match":passed})
            category.setdefault(item["subject"], {"total":0, "exact_match":0, "errors":0})
            category[item["subject"]]["total"] += 1
            category[item["subject"]]["exact_match"] += int(passed)
            outcomes.append(passed)
        except Exception as exc:
            errors += 1
            category.setdefault(item["subject"], {"total":0, "exact_match":0, "errors":0})
            category[item["subject"]]["total"] += 1
            category[item["subject"]]["errors"] += 1
            result.update({"error_type":type(exc).__name__})
        # Keep only aggregate information; no prompt, gold answer, or model response is persisted.
    sorted_latency = sorted(latencies)
    def pct(p):
        if not sorted_latency:
            return None
        pos = (len(sorted_latency)-1)*p/100
        lo = int(pos); hi = min(lo+1, len(sorted_latency)-1)
        return round(sorted_latency[lo]*(hi-pos)+sorted_latency[hi]*(pos-lo), 2)
    report = {
        "benchmark":"Humanity's Last Exam (HLE) — preliminary text-only probe",
        "official_score":False,
        "grading":"strict normalized exact match; no LLM judge",
        "sampling":"first eligible text-only questions in dataset order; not a random representative sample",
        "dataset":"cais/hle test split",
        "dataset_rows":dataset_rows,
        "requested_limit":args.limit,
        "evaluated":len(outcomes)+errors,
        "correct_exact_match":sum(outcomes),
        "exact_match_accuracy_percent":round(100*sum(outcomes)/len(outcomes),2) if outcomes else 0,
        "successful_nonempty_responses":sum(1 for _ in outcomes),
        "request_errors":errors,
        "image_dependent_rows_skipped_before_limit":skipped_images,
        "selected_model":model,
        "target":base,
        "latency_ms":{"mean":round(sum(latencies)/len(latencies),2) if latencies else None,
                      "p50":pct(50),"p95":pct(95),"p99":pct(99),"max":round(max(latencies),2) if latencies else None},
        "elapsed_seconds":round(time.perf_counter()-started,2),
        "subject_breakdown":category,
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "note":"Not comparable to official full-set or text-only leaderboard scores because this probe uses a limited non-random sample, excludes image-dependent items, and uses strict exact-match grading without the official evaluator."
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not outcomes and errors:
        raise SystemExit("No benchmark requests succeeded; see aggregate report.")

if __name__ == "__main__":
    main()
