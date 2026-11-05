#!/usr/bin/env python3
"""Paired ARIES resource-efficiency proxy benchmark using Docker CPU accounting.

Runs the same image/workload twice on one host: baseline with FastPathEngine
disabled, then candidate enabled. Reports Docker CPU time, memory samples,
successful requests per CPU-second, and exact-answer rates. These are compute
resource proxies, not electrical energy or watts.
"""
from __future__ import annotations
import argparse, json, os, statistics, subprocess, sys, threading, time, urllib.request
from pathlib import Path

def docker(*args: str, capture: bool = True) -> str:
    p = subprocess.run(["docker", *args], text=True, capture_output=capture)
    if p.returncode:
        raise RuntimeError(f"docker {' '.join(args)} failed: {p.stderr[-1500:]}")
    return p.stdout.strip() if capture else ""

def wait_health(url: str, timeout: int) -> None:
    deadline=time.monotonic()+timeout
    last=""
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen(url+"/health",timeout=3) as r:
                if r.status==200: return
        except Exception as e: last=str(e)
        time.sleep(2)
    raise RuntimeError(f"Container health timeout: {last}")

def sample_stats(name: str, stop: threading.Event, rows: list) -> None:
    while not stop.is_set():
        try:
            out=docker("stats","--no-stream","--format","{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}",name)
            parts=out.split("|")
            if len(parts)==3:
                cpu=float(parts[0].strip().rstrip("%"))
                mem=float(parts[2].strip().rstrip("%"))
                rows.append({"elapsed_s":time.monotonic(),"cpu_percent":cpu,"memory_percent":mem,"memory_usage":parts[1].strip()})
        except Exception:
            pass
        stop.wait(0.5)

def parse_benchmark(path: Path) -> dict:
    data=json.loads(path.read_text())
    workloads=data.get("workloads",{})
    flat={}
    for workload, stages in workloads.items():
        flat[workload]={}
        for concurrency, result in stages.items():
            flat[workload][concurrency]={
                "requests":result.get("requests"),
                "successes":result.get("successes"),
                "failures":result.get("failures"),
                "exact_matches":result.get("exact_matches"),
                "exact_match_rate_percent":result.get("exact_match_rate_percent"),
                "throughput_successful_rps":result.get("throughput_successful_rps"),
                "latency_ms":result.get("latency_ms"),
            }
    return flat

def run_variant(label: str, image: str, disable_fast_path: bool, args, workdir: Path) -> dict:
    name="aries-resource-"+label
    port=args.port
    try:
        docker("rm","-f",name)
    except Exception:
        pass
    envflag="1" if disable_fast_path else "0"
    docker("run","-d","--rm","--name",name,"--cpus",str(args.cpus),"--memory",args.memory,
           "-e",f"ARIES_DISABLE_FAST_PATH={envflag}","-p",f"{port}:10000",image)
    url=f"http://127.0.0.1:{port}"
    rows=[]; stop=threading.Event()
    sampler=threading.Thread(target=sample_stats,args=(name,stop,rows),daemon=True)
    try:
        wait_health(url,args.health_timeout)
        sampler.start()
        report=workdir/f"{label}-http-report.json"
        env=os.environ.copy(); env["ARIES_BASE_URL"]=url
        subprocess.run([sys.executable,"tools/aries_native_http_bench.py",
                        "--requests",str(args.requests),"--concurrency",args.concurrency,
                        "--output",str(report)],check=True,env=env)
        time.sleep(1)
        stop.set(); sampler.join(timeout=3)
        stats=docker("inspect","--format","{{.State.Pid}}",name)
        # Docker CLI reports cumulative container CPU time in nanoseconds.
        raw=docker("inspect","--format","{{json .}}",name)
        inspect=json.loads(raw)
        cpu_ns=inspect.get("HostConfig",{}).get("NanoCpus")
        stats_text=docker("stats","--no-stream","--format","{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}",name)
        cpu_samples=[x["cpu_percent"] for x in rows]
        mem_samples=[x["memory_percent"] for x in rows]
        return {"variant":label,"fast_path_disabled":disable_fast_path,"image":image,
                "container_cpu_quota_nano_cpus":cpu_ns,
                "docker_stats_samples":len(rows),
                "cpu_percent_mean_sampled":round(statistics.mean(cpu_samples),3) if cpu_samples else None,
                "cpu_percent_peak_sampled":round(max(cpu_samples),3) if cpu_samples else None,
                "memory_percent_mean_sampled":round(statistics.mean(mem_samples),3) if mem_samples else None,
                "memory_percent_peak_sampled":round(max(mem_samples),3) if mem_samples else None,
                "final_docker_stats":stats_text,
                "workloads":parse_benchmark(report),
                "raw_http_report":str(report)}
    finally:
        stop.set()
        if sampler.is_alive(): sampler.join(timeout=2)
        try: docker("rm","-f",name)
        except Exception: pass

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--image",required=True)
    p.add_argument("--requests",type=int,default=300)
    p.add_argument("--concurrency",default="1,4,8")
    p.add_argument("--cpus",type=float,default=2.0)
    p.add_argument("--memory",default="512m")
    p.add_argument("--health-timeout",type=int,default=180)
    p.add_argument("--port",type=int,default=18080)
    p.add_argument("--output",default="reports/aries-resource-efficiency-proxy.json")
    a=p.parse_args()
    if not 100<=a.requests<=5000: p.error("--requests must be 100..5000")
    workdir=Path(a.output).parent; workdir.mkdir(parents=True,exist_ok=True)
    image_id=docker("image","inspect","--format","{{.Id}}",a.image)
    baseline=run_variant("baseline",a.image,True,a,workdir)
    candidate=run_variant("candidate",a.image,False,a,workdir)
    comparisons={}
    for workload, stages in baseline["workloads"].items():
        comparisons[workload]={}
        for concurrency,b in stages.items():
            c=candidate["workloads"].get(workload,{}).get(concurrency,{})
            b_rps=b.get("throughput_successful_rps"); c_rps=c.get("throughput_successful_rps")
            comparisons[workload][concurrency]={
                "baseline_successes":b.get("successes"),"candidate_successes":c.get("successes"),
                "baseline_exact_matches":b.get("exact_matches"),"candidate_exact_matches":c.get("exact_matches"),
                "throughput_change_percent":round(100*(c_rps-b_rps)/b_rps,3) if b_rps and c_rps is not None else None,
                "baseline_p50_ms":b.get("latency_ms",{}).get("p50"),
                "candidate_p50_ms":c.get("latency_ms",{}).get("p50"),
                "baseline_p95_ms":b.get("latency_ms",{}).get("p95"),
                "candidate_p95_ms":c.get("latency_ms",{}).get("p95")}
    report={"suite":"ARIES paired Docker CPU/resource proxy comparison",
            "classification":"CPU/memory utilization proxy only; NOT electrical energy measurement",
            "image":a.image,"image_id":image_id,"requests_per_deterministic_workload":a.requests,
            "concurrency":a.concurrency.split(","),"cpu_limit":a.cpus,"memory_limit":a.memory,
            "method":"Same Docker image and host; FastPathEngine disabled for baseline and enabled for candidate; variants run sequentially with identical workload; Docker stats sampled every 0.5s.",
            "baseline":baseline,"candidate":candidate,"comparison":comparisons,
            "limitations":["Docker CPU percentage and memory usage are compute-resource proxies, not joules or watts.",
                           "Sequential runs can be affected by host thermal/frequency drift and shared-runner noise.",
                           "The native HTTP suite includes cache-hit, unique arithmetic, and general model chat as separate workloads.",
                           "No exchange network, NIC, production co-location, or external power-meter measurement."]}
    Path(a.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
