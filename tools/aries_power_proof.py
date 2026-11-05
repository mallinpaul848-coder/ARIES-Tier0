#!/usr/bin/env python3
"""Paired same-host ARIES energy comparison. No energy claim without a meter."""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, json, platform, re, statistics, time
from pathlib import Path
from urllib.parse import urlparse
import urllib.request, urllib.error

CASES = [
    ("2+2", "What is 2 + 2? Reply with the number only.", "4"),
    ("17x19", "What is 17 times 19? Reply with the number only.", "323"),
    ("1000-37", "What is 1000 minus 37? Reply with the number only.", "963"),
    ("12x12", "What is 12 times 12? Reply with the number only.", "144"),
    ("144/12", "What is 144 divided by 12? Reply with the number only.", "12"),
    ("15pct200", "What is 15 percent of 200? Reply with the number only.", "30"),
]
ROOT = Path("/sys/class/powercap")

def host_metadata():
    info={"platform":platform.platform(),"processor":platform.processor(),
          "cpu_count":__import__("os").cpu_count(),"python":platform.python_version(),
          "kernel":platform.release(),"cpu_model":None,"cpu_governor":None}
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                info["cpu_model"]=line.split(":",1)[1].strip()
                break
    except OSError:
        pass
    try:
        info["cpu_governor"]=Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read_text().strip()
    except OSError:
        pass
    return info


def domains():
    found=[]
    if ROOT.exists():
        for f in ROOT.glob("**/energy_uj"):
            try:
                found.append({"name":(f.parent/"name").read_text().strip(),
                              "path":str(f),"max":int((f.parent/"max_energy_range_uj").read_text())})
            except (OSError,ValueError): pass
    return found

def read_energy(ds):
    out={}
    for d in ds:
        try: out[d["name"]]=int(Path(d["path"]).read_text())
        except (OSError,ValueError): out[d["name"]]=None
    return out

def delta(a,b,ds):
    out={}
    for d in ds:
        x,y=a.get(d["name"]),b.get(d["name"])
        if x is None or y is None: out[d["name"]]=None
        else:
            z=y-x
            if z<0: z+=d["max"]
            out[d["name"]]=z/1e6
    return out

def subtract_idle(gross, idle):
    """Return idle-adjusted joules by domain; preserve negative noise values."""
    if gross is None or idle is None:
        return None
    return {key: (gross.get(key) - idle.get(key)) if gross.get(key) is not None
            and idle.get(key) is not None else None for key in gross}


def measure_idle(ds, seconds):
    """Measure host/service idle energy over a duration matching an active phase."""
    before = read_energy(ds)
    start = time.perf_counter()
    time.sleep(max(0.0, seconds))
    elapsed = time.perf_counter() - start
    after = read_energy(ds)
    return delta(before, after, ds), elapsed


def exact_numeric_answer(answer, expected):
    # Accept a short explanatory wrapper, but require exactly the expected numeric result.
    tokens = re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])", str(answer))
    return tokens == [str(expected)]

def call(url,prompt,expected,timeout):
    base=url.rstrip("/")
    if not base.endswith("/v1"): base+="/v1"
    body=json.dumps({"model":"auto","messages":[{"role":"user","content":prompt}],
                     "temperature":0,"max_tokens":32}).encode()
    req=urllib.request.Request(base+"/chat/completions",data=body,
        headers={"Content-Type":"application/json"},method="POST")
    t=time.perf_counter_ns()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            obj=json.loads(r.read())
            choices=obj.get("choices") or []
            answer=choices[0].get("message",{}).get("content","") if choices else ""
            return {"ok":r.status==200 and bool(str(answer).strip()),
                    "exact":exact_numeric_answer(answer, expected),"status":r.status,
                    "latency_ms":(time.perf_counter_ns()-t)/1e6,"answer":str(answer)[:200],"error":None}
    except Exception as e:
        return {"ok":False,"exact":False,"status":None,
                "latency_ms":(time.perf_counter_ns()-t)/1e6,"answer":"",
                "error":type(e).__name__+": "+str(e)[:200]}

def run_phase(label,url,tasks,concurrency,timeout,ds):
    before=read_energy(ds); start=time.perf_counter(); wall0=dt.datetime.now(dt.timezone.utc).isoformat()
    def one(i):
        _,prompt,expected=tasks[i%len(tasks)]
        return call(url,prompt,expected,timeout)
    if concurrency==1: rows=[one(i) for i in range(len(tasks))]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            rows=list(ex.map(one,range(len(tasks))))
    seconds=time.perf_counter()-start; wall1=dt.datetime.now(dt.timezone.utc).isoformat()
    after=read_energy(ds); good=sum(x["ok"] for x in rows); exact=sum(x["exact"] for x in rows)
    lat=sorted(x["latency_ms"] for x in rows)
    def p(q): return round(lat[min(len(lat)-1,int((len(lat)-1)*q+0.5))],4) if lat else None
    joules=delta(before,after,ds) if ds else None
    idle_joules, idle_seconds = measure_idle(ds, seconds) if ds and seconds > 0 else (None, 0.0)
    net_joules = subtract_idle(joules, idle_joules)
    return {"label":label,"start_utc":wall0,"end_utc":wall1,"requests":len(rows),
      "successful":good,"exact_matches":exact,"exact_match_rate_pct":round(100*exact/len(rows),3),
      "errors":len(rows)-good,"wall_seconds":round(seconds,6),
      "throughput_successful_rps":round(good/seconds,4) if seconds else None,
      "latency_ms":{"p50":p(.5),"p95":p(.95),"p99":p(.99),"p99_9":p(.999),
                    "mean":round(statistics.mean(lat),4) if lat else None},
      "rapl_joules_gross":joules,
      "rapl_idle_baseline_joules":idle_joules,
      "idle_baseline_seconds":round(idle_seconds,6),
      "rapl_joules_idle_adjusted":net_joules,
      "gross_joules_per_success":{k:(round(v/good,9) if v is not None and good else None)
                                  for k,v in (joules or {}).items()},
      "idle_adjusted_joules_per_success":{k:(round(v/good,9) if v is not None and good else None)
                                          for k,v in (net_joules or {}).items()},
      "raw":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline-url",required=True); p.add_argument("--candidate-url",required=True)
    p.add_argument("--requests",type=int,default=600); p.add_argument("--repeats",type=int,default=6)
    p.add_argument("--concurrency",type=int,default=1); p.add_argument("--warmup",type=int,default=30)
    p.add_argument("--timeout",type=float,default=15); p.add_argument("--output",default="aries-power-proof.json")
    a=p.parse_args()
    if a.requests<60 or a.repeats<2 or not 1<=a.concurrency<=64 or a.warmup<0: p.error("requests>=60, repeats>=2, concurrency 1..64, warmup>=0 required")
    urls=[a.baseline_url,a.candidate_url]
    if urls[0].rstrip("/")==urls[1].rstrip("/"): p.error("baseline and candidate must differ")
    if any((urlparse(u).hostname or "") not in ("localhost","127.0.0.1","::1") for u in urls):
        p.error("Both endpoints must be loopback URLs so RAPL is measured on the service host")
    ds=domains()
    # Validate both endpoints, then warm both before any measured pair.
    for name,url in zip(("baseline","candidate"),urls):
        for i in range(a.warmup):
            c=CASES[i%len(CASES)]; r=call(url,c[1],c[2],a.timeout)
            if not r["ok"]: raise SystemExit(f"{name} warm-up request failed: {r}")
    phases=[]
    for rep in range(a.repeats):
        order=[("baseline",urls[0]),("candidate",urls[1])]
        if rep%2: order.reverse()
        for label,url in order:
            tasks=[CASES[i%len(CASES)] for i in range(a.requests)]
            phases.append(run_phase(label,url,tasks,a.concurrency,a.timeout,ds))
    aggregate={}
    for label in ("baseline","candidate"):
        ps=[x for x in phases if x["label"]==label]
        good=sum(x["successful"] for x in ps); exact=sum(x["exact_matches"] for x in ps)
        joules={}
        if ds:
            for d in ds:
                vals=[x["rapl_joules_gross"].get(d["name"]) for x in ps]
                joules[d["name"]]=round(sum(v for v in vals if v is not None),6) if all(v is not None for v in vals) else None
        idle_joules={}
        net_joules={}
        if ds:
            for d in ds:
                ivals=[x["rapl_idle_baseline_joules"].get(d["name"]) for x in ps]
                nvals=[x["rapl_joules_idle_adjusted"].get(d["name"]) for x in ps]
                idle_joules[d["name"]]=round(sum(v for v in ivals if v is not None),6) if all(v is not None for v in ivals) else None
                net_joules[d["name"]]=round(sum(v for v in nvals if v is not None),6) if all(v is not None for v in nvals) else None
        aggregate[label]={"phases":len(ps),"requests":sum(x["requests"] for x in ps),
          "successful":good,"exact_matches":exact,
          "exact_match_rate_pct":round(100*exact/sum(x["requests"] for x in ps),3),
          "rapl_joules_gross":joules,"rapl_idle_baseline_joules":idle_joules,
          "rapl_joules_idle_adjusted":net_joules,
          "gross_joules_per_success":{k:(round(v/good,9) if v is not None and good else None) for k,v in joules.items()},
          "idle_adjusted_joules_per_success":{k:(round(v/good,9) if v is not None and good else None) for k,v in net_joules.items()}}
    b,c=aggregate["baseline"],aggregate["candidate"]; changes={}
    for k,bv in b["idle_adjusted_joules_per_success"].items():
        cv=c["idle_adjusted_joules_per_success"].get(k)
        changes[k]=round(100*(cv-bv)/bv,3) if bv not in (None,0) and cv is not None and bv > 0 and cv > 0 else None
    same=(b["requests"]==c["requests"] and b["successful"]==c["successful"] and
          b["exact_matches"]==c["exact_matches"])
    measured=bool(ds) and all(v is not None for v in changes.values())
    savings=all(v<0 for v in changes.values()) if measured and changes else False
    report={"suite":"ARIES paired same-host power proof","created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "host":host_metadata(),
      "method":{"requests_per_phase":a.requests,"repeats_per_variant":a.repeats,
        "concurrency":a.concurrency,"warmup_per_endpoint":a.warmup,"alternating_order":True,
        "idle_adjustment":"For each active phase, measure a no-request idle window of equal wall duration immediately after it; report gross and idle-adjusted energy separately.",
        "energy_meter":"Linux powercap/RAPL" if ds else "UNAVAILABLE",
        "domains":[d["name"] for d in ds],"workload":"fixed six-case deterministic request mix",
        "limits":"Idle subtraction is a local adjacent-window estimate and can be affected by host drift; RAPL covers only reported CPU/package/DRAM domains, not whole-system wall power. Hosted/cloud remote targets prohibited."},
      "aggregate":aggregate,"energy_change_candidate_vs_baseline_pct":changes,
      "equal_work_gate_passed":same,"energy_savings_observed":bool(same and measured and savings),
      "claim_status":"All reported idle-adjusted RAPL domains decreased per exact successful request; repeat and independent wall-meter validation still required" if same and measured and savings
        else "NOT PROVEN: require RAPL readings, equal successful/exact work, positive idle-adjusted energy, and lower joules per successful request",
      "phases":phases}
    Path(a.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="phases"},indent=2))
    print("Raw paired evidence:",a.output)
    if not same: raise SystemExit("Unequal successful/exact work: reject energy claim")
    if not measured: raise SystemExit("No usable RAPL energy domains: energy savings not measurable here")
if __name__=="__main__": main()
