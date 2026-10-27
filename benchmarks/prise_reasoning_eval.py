#!/usr/bin/env python3
"""PRISE reasoning evaluation for ARIES. Project-owned diagnostic, not an official benchmark."""
import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CASES = [
    ("logic_01","deductive","All zargs are blue. Nimo is a zarg. Is Nimo blue? Answer yes or no.","yes"),
    ("logic_02","ordering","A is taller than B. B is taller than C. Who is shortest: A, B, or C? One letter.","C"),
    ("logic_03","calendar","If today is Tuesday, what day is two days after tomorrow? One weekday.","Friday"),
    ("logic_04","logic","If every flern is a miv and no miv is red, can a flern be red? Answer yes or no.","no"),
    ("math_01","arithmetic","What is 17 * 19? Number only.","323"),
    ("math_02","arithmetic","What is 144 / 12? Number only.","12"),
    ("math_03","arithmetic","What is 256 + 789? Number only.","1045"),
    ("math_04","arithmetic","What is 1000 - 367? Number only.","633"),
    ("math_05","arithmetic","A box has 4 rows of 7 items. How many items? Number only.","28"),
    ("instruction_01","instruction","Reply with exactly this token and nothing else: ARIES-OK","ARIES-OK"),
    ("instruction_02","instruction","Return exactly three items separated by commas: red, green, blue","red, green, blue"),
    ("instruction_03","instruction","Reply with the single lowercase word: verified","verified"),
    ("knowledge_01","knowledge","At standard atmospheric pressure, what is the chemical formula for water? Formula only.","H2O"),
    ("knowledge_02","knowledge","How many sides does a hexagon have? Number only.","6"),
    ("science_01","science","At ordinary Earth conditions, does liquid water freeze at about 0 degrees Celsius? Answer yes or no.","yes"),
    ("uncertainty_01","calibration","Can the digital root of an integer alone prove that the integer is prime? Answer yes or no.","no"),
    ("prise_01","prise","PRISE stands for Priority, Risk, Impact, Systemic, Emergent. Which dimension asks what could go wrong? One word.","Risk"),
    ("prise_02","prise","A proposed code change speeds up one test but breaks 3 existing tests. Should it be accepted as a verified improvement? Answer yes or no.","no"),
    ("reasoning_01","multi_step","A train travels 60 km in 1 hour at constant speed. How far in 3 hours? Number followed by km.","180 km"),
    ("reasoning_02","constraint","Return the smaller number: 81 or 18. Number only.","18"),
]

def norm(s):
    return " ".join(str(s).strip().lower().split()).strip(" .!\t\n")

def call(url, payload, key, timeout):
    data = json.dumps(payload).encode()
    headers = {"Content-Type":"application/json","Accept":"application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.status, json.loads(res.read().decode("utf-8", errors="replace"))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default=os.getenv("ARIES_BASE_URL","http://127.0.0.1:8000"))
    p.add_argument("--model", default=os.getenv("ARIES_MODEL_ID","auto"))
    p.add_argument("--api-key", default=os.getenv("ARIES_API_KEY",""))
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--output", default="reports/aries-prise-reasoning.json")
    args = p.parse_args()
    base = args.base_url.rstrip("/")
    api = base if base.endswith("/v1") else base + "/v1"
    report = {"suite":"ARIES PRISE Reasoning Matrix v1","suite_type":"project-owned diagnostic; not an official benchmark",
              "timestamp_utc":datetime.now(timezone.utc).isoformat(),"target":base,"requested_model":args.model,"results":[]}
    model = args.model
    try:
        req = urllib.request.Request(api+"/models", headers={"Authorization":"Bearer "+args.api_key} if args.api_key else {})
        with urllib.request.urlopen(req, timeout=args.timeout) as res:
            models = json.loads(res.read().decode())
        ids = [m.get("id") for m in models.get("data",[]) if m.get("id")]
        if model == "auto":
            if not ids: raise RuntimeError("No models advertised by /v1/models")
            model = ids[0]
        report["models"] = ids
    except Exception as e:
        report["models_error"] = type(e).__name__+": "+str(e)
        if model == "auto":
            model = ""
    report["selected_model"] = model
    for case_id, category, prompt, expected in CASES:
        row = {"id":case_id,"category":category,"expected":expected}
        start = time.perf_counter()
        try:
            if not model: raise RuntimeError("No model ID available; configure ARIES_MODEL_ID")
            status, data = call(api+"/chat/completions",
                {"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0,"max_tokens":64},
                args.api_key,args.timeout)
            choices = data.get("choices",[])
            answer = choices[0].get("message",{}).get("content","") if choices else ""
            row.update({"http_status":status,"actual":answer,"nonempty":bool(str(answer).strip()),
                        "passed_exact_match":norm(answer)==norm(expected)})
        except urllib.error.HTTPError as e:
            row.update({"http_status":e.code,"error":e.read().decode("utf-8",errors="replace")[:500]})
        except Exception as e:
            row["error"] = type(e).__name__+": "+str(e)
        row["latency_ms"] = round((time.perf_counter()-start)*1000,3)
        report["results"].append(row)
    done = [r for r in report["results"] if "passed_exact_match" in r]
    times = [r["latency_ms"] for r in report["results"]]
    cats = {}
    for r in report["results"]:
        c = cats.setdefault(r["category"],{"cases":0,"responses":0,"passed":0})
        c["cases"] += 1
        if "passed_exact_match" in r:
            c["responses"] += 1
            c["passed"] += int(r["passed_exact_match"])
    for c in cats.values():
        c["accuracy_percent"] = round(100*c["passed"]/c["responses"],2) if c["responses"] else None
    passed = sum(bool(r.get("passed_exact_match")) for r in report["results"])
    incomplete = len(CASES) - len(done)
    report["summary"] = {"cases":len(CASES),"responses":len(done),"incomplete_cases":incomplete,
        "exact_match_passes":passed,
        "accuracy_percent_of_completed_responses":round(100*passed/len(done),2) if done else None,
        "completion_rate_percent":round(100*len(done)/len(CASES),2),
        "all_case_pass_rate_percent":round(100*passed/len(CASES),2),
        "nonempty_responses":sum(bool(r.get("nonempty")) for r in done),
        "latency_min_ms":round(min(times),3) if times else None,"latency_mean_ms":round(statistics.mean(times),3) if times else None,
        "latency_p50_ms":round(sorted(times)[(len(times)-1)//2],3) if times else None,
        "latency_max_ms":round(max(times),3) if times else None,"category_metrics":cats,
        "warning":"Small authored diagnostic; exact-match score is not a general intelligence measure or third-party validation."}
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps(report["summary"],indent=2))
    if incomplete:
        raise SystemExit(f"FAIL: {incomplete}/{len(CASES)} cases did not return valid HTTP completions; inspect endpoint/model stalls.")
    if passed != len(CASES):
        raise SystemExit(f"FAIL: {len(CASES)-passed}/{len(CASES)} cases failed exact-match checks.")

if __name__=="__main__":
    main()
