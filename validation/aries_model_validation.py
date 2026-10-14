#!/usr/bin/env python3
"""Reproducible ARIES public inference validation and latency benchmark.

Uses an OpenAI-compatible /v1/chat/completions endpoint. Results distinguish
functional checks from model-quality claims. Never reports sub-nanosecond AI
latency: measurements include HTTP/network/server overhead.
"""
from __future__ import annotations
import json, os, statistics, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone

BASE_URL = os.environ.get("ARIES_BASE_URL", "https://aries-tier0-api-6qjh.onrender.com").rstrip("/")
MODEL = os.environ.get("ARIES_MODEL", "aries-native-ngram")
API_KEY = os.environ.get("ARIES_API_KEY", "")
REPEATS = max(1, int(os.environ.get("ARIES_REPEATS", "3")))
TIMEOUT = max(5, int(os.environ.get("ARIES_TIMEOUT_SECONDS", "90")))

CASES = [
    {"id":"arithmetic_17x19","prompt":"Calculate 17 * 19. Return the numeric answer.", "must_contain":["323"]},
    {"id":"arithmetic_2plus2","prompt":"What is 2 + 2? Give the answer clearly.", "must_contain":["4"]},
    {"id":"instruction_exact_token","prompt":"Reply with exactly this token and nothing else: ARIES_OK_731", "must_contain":["ARIES_OK_731"]},
    {"id":"factual_basic","prompt":"How many days are in a standard non-leap year?", "must_contain":["365"]},
    {"id":"reasoning_order","prompt":"Mia is older than Lee. Lee is older than Sam. Who is youngest? Answer with one name.", "must_contain":["sam"]},
    {"id":"refusal_not_required","prompt":"Name one primary color. Answer briefly.", "must_contain":["red","blue","yellow"]},
    {"id":"format_list","prompt":"List exactly three fruits, separated by commas.", "must_contain":[]},
    {"id":"context_following","prompt":"Use this mapping only: AX=blue, BY=green. What color is BY?", "must_contain":["green"]},
    {"id":"arithmetic_9x8","prompt":"What is 9 times 8?", "must_contain":["72"]},
    {"id":"uncertainty_calibration","prompt":"Is 99991 a prime number? If unsure, say you are unsure rather than guessing.", "must_contain":[]},
]

def request_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept":"application/json", "User-Agent":"ARIES-Tier0-Validation/1.0"}
    if data is not None: headers["Content-Type"] = "application/json"
    if API_KEY: headers["Authorization"] = "Bearer " + API_KEY
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8", "replace")
            elapsed = (time.perf_counter()-started)*1000
            try: body = json.loads(raw)
            except Exception: body = {"raw":raw[:2000]}
            return {"ok":200 <= response.status < 300, "status":response.status, "latency_ms":elapsed, "body":body}
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace")
        return {"ok":False,"status":e.code,"latency_ms":(time.perf_counter()-started)*1000,"error":raw[:1500]}
    except Exception as e:
        return {"ok":False,"status":None,"latency_ms":(time.perf_counter()-started)*1000,"error":type(e).__name__+": "+str(e)}

def percentile(xs, p):
    if not xs: return None
    ys=sorted(xs)
    return round(ys[min(len(ys)-1, int((len(ys)-1)*p))], 3)

def extract_text(body):
    try:
        return str(body["choices"][0]["message"]["content"])
    except Exception:
        try: return str(body["choices"][0]["text"])
        except Exception: return ""

def main():
    report={"suite":"ARIES-Tier0 public inference validation","timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "base_url":BASE_URL,"model_requested":MODEL,"repeats_per_case":REPEATS,
            "important_limitations":["HTTP timings include network, server queueing, model execution and serialization.",
             "This is a compact smoke/functional suite, not an independent academic benchmark or leaderboard score.",
             "Substring checks are necessary but not sufficient to establish correctness.",
             "A successful HTTP response does not prove the named model was actually loaded."]}
    diagnostics={}
    for path in ["/health","/","/openapi.json","/v1/models"]:
        diagnostics[path]=request_json(BASE_URL+path)
    report["diagnostics"]={p:{"ok":x["ok"],"status":x["status"],"latency_ms":round(x["latency_ms"],3)} for p,x in diagnostics.items()}
    model_ids=[]
    models=diagnostics["/v1/models"].get("body",{})
    if isinstance(models,dict): model_ids=[str(x.get("id","")) for x in models.get("data",[]) if isinstance(x,dict)]
    report["models_endpoint_ids"]=model_ids
    results=[]
    for case in CASES:
      for repeat in range(REPEATS):
        payload={"model":MODEL,"messages":[{"role":"user","content":case["prompt"]}],"temperature":0,"max_tokens":100}
        r=request_json(BASE_URL+"/v1/chat/completions",payload)
        body=r.get("body",{})
        answer=extract_text(body) if isinstance(body,dict) else ""
        lower=answer.lower()
        content_ok=bool(answer.strip())
        checks=[token.lower() in lower for token in case["must_contain"]]
        functional_ok=r["ok"] and content_ok and all(checks)
        results.append({"case_id":case["id"],"repeat":repeat+1,"http_ok":r["ok"],"status":r["status"],
          "latency_ms":round(r["latency_ms"],3),"content_nonempty":content_ok,
          "required_substrings_passed":sum(checks),"required_substrings_total":len(checks),
          "functional_check_pass":functional_ok,"answer":answer[:1200],
          "error":r.get("error")})
    latencies=[x["latency_ms"] for x in results if x["http_ok"]]
    report["chat"]={"total_requests":len(results),"http_successes":sum(x["http_ok"] for x in results),
       "functional_checks_passed":sum(x["functional_check_pass"] for x in results),
       "functional_checks_total":len(results),"latency_ms":{"min":round(min(latencies),3) if latencies else None,
       "p50":percentile(latencies,.50),"p95":percentile(latencies,.95),"p99":percentile(latencies,.99),
       "max":round(max(latencies),3) if latencies else None,
       "mean":round(statistics.mean(latencies),3) if latencies else None},
       "requests_per_second":round(len(latencies)/(sum(latencies)/1000),3) if sum(latencies)>0 else None}
    report["case_results"]=results
    report["status"]="PASS" if report["chat"]["http_successes"]==len(results) and report["chat"]["functional_checks_passed"]==len(results) else "FAIL"
    print(json.dumps(report,indent=2,ensure_ascii=False))
    with open("aries_model_validation_report.json","w",encoding="utf-8") as f: json.dump(report,f,indent=2,ensure_ascii=False)
    with open("aries_model_validation_summary.md","w",encoding="utf-8") as f:
        c=report["chat"]; l=c["latency_ms"]
        f.write("# ARIES-Tier0 Public Inference Validation\n\n")
        f.write(f"- Timestamp (UTC): {report['timestamp_utc']}\n- Endpoint: {BASE_URL}\n- Requested model: {MODEL}\n- Overall: **{report['status']}**\n")
        f.write(f"- HTTP successes: {c['http_successes']}/{c['total_requests']}\n- Functional checks passed: {c['functional_checks_passed']}/{c['functional_checks_total']}\n")
        f.write(f"- Latency ms (min/P50/P95/P99/max/mean): {l['min']} / {l['p50']} / {l['p95']} / {l['p99']} / {l['max']} / {l['mean']}\n")
        f.write(f"- Estimated throughput from observed request durations: {c['requests_per_second']} requests/s\n\n")
        f.write("## Interpretation limits\n\n")
        for item in report["important_limitations"]: f.write(f"- {item}\n")
    return 0 if report["status"]=="PASS" else 1
if __name__=="__main__": sys.exit(main())
