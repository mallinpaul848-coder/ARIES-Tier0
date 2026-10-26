#!/usr/bin/env python3
"""Measure latency and availability over cumulative multi-turn chat sequences.

This is an end-to-end API stress/latency diagnostic, not a general reasoning score.
"""
import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

def percentile(values, pct):
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * pct / 100
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo), 3)

def request_json(url, payload, api_key, timeout):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return response.status, json.loads(raw) if raw else {}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL", "http://127.0.0.1:8000"))
    p.add_argument("--model", default=os.getenv("ARIES_MODEL_ID", "auto"))
    p.add_argument("--api-key", default=os.getenv("ARIES_API_KEY", ""))
    p.add_argument("--timeout", type=int, default=15)
    p.add_argument("--turns", type=int, nargs="+", default=[5, 10, 20])
    p.add_argument("--output", default="validation-results/multi-turn-chat.json")
    args = p.parse_args()
    if any(n < 2 or n > 20 for n in args.turns):
        p.error("each turn count must be between 2 and 20")

    base = args.base_url.rstrip("/")
    api_root = base if base.endswith("/v1") else base + "/v1"
    report = {
        "suite": "ARIES cumulative multi-turn latency diagnostic",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": base,
        "requested_model": args.model,
        "turn_counts": args.turns,
        "scope": "Project-owned API diagnostic; not independent certification or a broad reasoning benchmark.",
        "sequences": []
    }
    try:
        req = urllib.request.Request(api_root + "/models", headers={"Accept":"application/json"})
        if args.api_key:
            req.add_header("Authorization", "Bearer " + args.api_key)
        with urllib.request.urlopen(req, timeout=args.timeout) as response:
            models = json.loads(response.read().decode("utf-8"))
        entries = models.get("data", []) if isinstance(models, dict) else []
        advertised = entries[0].get("id") if entries else None
        model = advertised if args.model == "auto" and advertised else args.model
        report["advertised_model_ids"] = [x.get("id") for x in entries if isinstance(x, dict)]
        report["selected_model"] = model
    except Exception as exc:
        report["model_discovery_error"] = type(exc).__name__ + ": " + str(exc)
        model = args.model

    all_latencies = []
    total_turns = 0
    nonempty = 0
    failures = 0
    abort_reason = None
    for turn_count in args.turns:
        messages = [{"role":"system","content":"You are in a multi-turn continuity and latency diagnostic. Answer briefly and accurately. Retain prior conversation context."}]
        turn_results = []
        for turn in range(1, turn_count + 1):
            if turn == 1:
                prompt = "For this test, remember this reference pair: MALLIN-ORBIT-731 maps to violet. Reply with only: stored."
            elif turn == turn_count:
                prompt = "What value maps to MALLIN-ORBIT-731? Reply with the value only."
            elif turn % 4 == 0:
                prompt = "Briefly summarize the reference pair stored earlier, without inventing any new pair."
            else:
                prompt = "Acknowledge this as continuation turn " + str(turn) + ". Keep the earlier reference pair available."
            messages.append({"role":"user","content":prompt})
            started = time.perf_counter()
            item = {"turn":turn, "messages_in_context":len(messages), "prompt_chars":len(prompt)}
            try:
                status, payload = request_json(
                    api_root + "/chat/completions",
                    {"model":model,"messages":messages,"temperature":0,"max_tokens":16},
                    args.api_key,args.timeout
                )
                elapsed = (time.perf_counter()-started)*1000
                choices = payload.get("choices", []) if isinstance(payload, dict) else []
                answer = choices[0].get("message",{}).get("content","") if choices else ""
                item.update({"http_status":status,"latency_ms":round(elapsed,3),"response_chars":len(answer),"nonempty":bool(str(answer).strip())})
                if answer:
                    messages.append({"role":"assistant","content":str(answer)})
                    nonempty += 1
                else:
                    failures += 1
                all_latencies.append(elapsed)
            except Exception as exc:
                elapsed = (time.perf_counter()-started)*1000
                item.update({"latency_ms":round(elapsed,3),"error":type(exc).__name__ + ": " + str(exc),"nonempty":False})
                failures += 1
                all_latencies.append(elapsed)
            turn_results.append(item)
            total_turns += 1
            if "error" in item:
                abort_reason = item["error"]
                print(json.dumps({"benchmark_aborted_early": True, "reason": abort_reason, "turn": turn}), flush=True)
                break
        vals = [x["latency_ms"] for x in turn_results if isinstance(x.get("latency_ms"),(int,float))]
        seq = {
            "requested_turns":turn_count,
            "completed_http_turns":sum(1 for x in turn_results if x.get("http_status")==200),
            "nonempty_responses":sum(1 for x in turn_results if x.get("nonempty")),
            "latency_min_ms":round(min(vals),3) if vals else None,
            "latency_mean_ms":round(statistics.mean(vals),3) if vals else None,
            "latency_p50_ms":percentile(vals,50),
            "latency_p95_ms":percentile(vals,95),
            "latency_max_ms":round(max(vals),3) if vals else None,
            "turns":turn_results
        }
        report["sequences"].append(seq)
        print(json.dumps({"sequence_turns":turn_count, **{k:v for k,v in seq.items() if k!="turns"}}), flush=True)
        if abort_reason:
            break

    report["aggregate"] = {
        "aborted_early": bool(abort_reason),
        "abort_reason": abort_reason,
        "requested_turns":total_turns,
        "nonempty_responses":nonempty,
        "nonempty_response_rate_percent":round(100*nonempty/total_turns,2) if total_turns else None,
        "failed_or_empty_turns":failures,
        "latency_samples":len(all_latencies),
        "latency_min_ms":round(min(all_latencies),3) if all_latencies else None,
        "latency_mean_ms":round(statistics.mean(all_latencies),3) if all_latencies else None,
        "latency_p50_ms":percentile(all_latencies,50),
        "latency_p95_ms":percentile(all_latencies,95),
        "latency_p99_ms":percentile(all_latencies,99),
        "latency_max_ms":round(max(all_latencies),3) if all_latencies else None
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("MULTI-TURN SUMMARY")
    print(json.dumps(report["aggregate"],indent=2))
    print("Saved report:",out)
    if total_turns == 0 or failures == total_turns:
        raise SystemExit("FAIL: no successful nonempty turns; inspect endpoint and report.")

if __name__ == "__main__":
    main()
