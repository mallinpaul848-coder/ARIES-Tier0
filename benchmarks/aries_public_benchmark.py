#!/usr/bin/env python3
"""Repeatable public ARIES API smoke/latency benchmark; stdlib only."""
import json, os, statistics, time, urllib.error, urllib.request
from datetime import datetime, timezone

BASE = os.getenv("ARIES_PUBLIC_BASE_URL", "https://aries-tier0-api-6qjh.onrender.com").rstrip("/")
OUT = os.getenv("ARIES_BENCHMARK_REPORT", "aries-public-benchmark.json")
PROMPTS = [
    "Reply with exactly ARIES-TEST-ONE.",
    "What is 17 multiplied by 19? Give only the number.",
    "In one sentence, explain what an API health check proves.",
]

def request(path, payload=None, timeout=75):
    url = BASE + path
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept":"application/json"}
    if data is not None: headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try: body = json.loads(raw)
            except ValueError: body = {"text": raw[:500]}
            return {"path":path,"http_status":r.status,"latency_ms":round((time.perf_counter()-started)*1000,2),"body":body}
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace")
        try: body=json.loads(raw)
        except ValueError: body={"text":raw[:500]}
        return {"path":path,"http_status":e.code,"latency_ms":round((time.perf_counter()-started)*1000,2),"body":body}
    except Exception as e:
        return {"path":path,"error":type(e).__name__+": "+str(e),"latency_ms":round((time.perf_counter()-started)*1000,2)}

def main():
    report={"target":BASE,"started_at":datetime.now(timezone.utc).isoformat(),"samples_requested":len(PROMPTS),"checks":[],"chat_samples":[]}
    for p in ("/health","/","/diagnostics","/v1/models"):
        report["checks"].append(request(p,timeout=75))
    diag=next((x.get("body",{}) for x in report["checks"] if x["path"]=="/diagnostics"),{})
    models=next((x.get("body",{}) for x in report["checks"] if x["path"]=="/v1/models"),{})
    model_id=""
    if isinstance(models,dict) and models.get("data"): model_id=models["data"][0].get("id","")
    report["model_id"]=model_id or None
    report["inference_configured"]=bool(isinstance(diag,dict) and diag.get("inference_configured") and model_id)
    if report["inference_configured"]:
        for prompt in PROMPTS:
            result=request("/v1/chat/completions",{"model":model_id,"messages":[{"role":"user","content":prompt}],"max_tokens":48,"temperature":0},timeout=90)
            body=result.get("body",{})
            choices=body.get("choices",[]) if isinstance(body,dict) else []
            answer=choices[0].get("message",{}).get("content","") if choices else ""
            sample={k:v for k,v in result.items() if k!="body"}
            sample["prompt"]=prompt
            sample["nonempty_response"]=bool(str(answer).strip())
            sample["answer_preview"]=str(answer)[:240]
            report["chat_samples"].append(sample)
    else:
        report["chat_samples_skipped_reason"]="Public endpoint diagnostics do not report a configured backend and model ID."
    latencies=[x["latency_ms"] for x in report["chat_samples"] if x.get("http_status")==200 and x.get("nonempty_response")]
    report["successful_chat_samples"]=len(latencies)
    report["latency_summary_ms"]={"min":min(latencies),"median":statistics.median(latencies),"max":max(latencies)} if latencies else None
    report["pass"]=len(latencies)==len(PROMPTS) and len(report["checks"])==4 and all(x.get("http_status")==200 for x in report["checks"])
    report["finished_at"]=datetime.now(timezone.utc).isoformat()
    with open(OUT,"w",encoding="utf-8") as f: json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))
    if not report["pass"]: raise SystemExit("FAIL: public inference did not pass every required HTTP and non-empty response check; see JSON report.")
    print("PASS: all public API checks and chat inference samples succeeded.")
if __name__=="__main__": main()
