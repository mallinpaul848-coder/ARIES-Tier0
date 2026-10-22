import json, os, re, statistics, time, urllib.request, urllib.error
from datetime import datetime, timezone
MODEL_ID=os.getenv("HF_MODEL_ID","Qwen/Qwen2.5-0.5B-Instruct")
URL=os.getenv("ARIES_BASE_URL","https://aries-tier0-api-6qjh.onrender.com").rstrip("/")
MODEL=os.getenv("ARIES_MODEL_ID","aries-native-ngram")
ROUNDS=int(os.getenv("ROUNDS","2")); TIMEOUT=int(os.getenv("REQUEST_TIMEOUT","90"))
CASES=[
("arithmetic","Compute 17 * 19. Return the numeric answer.",["323"]),
("arithmetic","Compute 144 / 12. Return the numeric answer.",["12"]),
("instruction","Reply with exactly: ARIES-OK",["aries-ok"]),
("knowledge","What is the capital of France?",["paris"]),
("reasoning","If all glips are blins and all blins are red, are all glips red? Answer yes or no.",["yes"]),
("logic","A is taller than B. B is taller than C. Who is shortest?",["c"]),
("arithmetic","What is 81 divided by 9?",["9"]),
("instruction","List exactly three items separated by commas: red, green, blue.",["red","green","blue"])]
def norm(s): return re.sub(r"\\s+"," ",s.casefold()).strip()
def pct(a,p):
 if not a:return None
 a=sorted(a); x=(len(a)-1)*p/100; i=int(x); j=min(i+1,len(a)-1)
 return a[i]+(a[j]-a[i])*(x-i)
def summarize(name,model,rows,wall):
 lat=[r["latency_ms"] for r in rows]; ok=sum(bool(r["text"].strip()) and not r["error"] for r in rows)
 return {"target":name,"model":model,"requests":len(rows),"successful_nonempty":ok,"failures_or_empty":len(rows)-ok,
 "correct_smoke_cases":sum(r["correct"] for r in rows),"smoke_accuracy":sum(r["correct"] for r in rows)/len(rows),
 "wall_time_seconds":wall,"requests_per_second":len(rows)/wall if wall else None,
 "latency_ms":{"mean":statistics.fmean(lat),"p50":pct(lat,50),"p95":pct(lat,95),"p99":pct(lat,99),"max":max(lat)},"results":rows}
def api(prompt):
 t=time.perf_counter(); key=os.getenv("ARIES_API_KEY")
 body=json.dumps({"model":MODEL,"messages":[{"role":"user","content":prompt}],"temperature":0,"max_tokens":96}).encode()
 h={"Content-Type":"application/json"}
 if key:h["Authorization"]="Bearer "+key
 try:
  req=urllib.request.Request(URL+"/v1/chat/completions",data=body,headers=h,method="POST")
  with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
   d=json.loads(r.read()); c=(d.get("choices") or [{}])[0].get("message",{}).get("content","")
   if isinstance(c,list):c=" ".join(str(v.get("text","")) for v in c if isinstance(v,dict))
   return {"status":r.status,"latency_ms":(time.perf_counter()-t)*1000,"text":str(c),"error":None}
 except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,OSError) as e:
  return {"status":getattr(e,"code",None),"latency_ms":(time.perf_counter()-t)*1000,"text":"","error":type(e).__name__+": "+str(e)[:240]}
def main():
 import torch
 from transformers import AutoModelForCausalLM,AutoTokenizer
 print("Loading independent public model:",MODEL_ID,flush=True); t=time.perf_counter()
 tok=AutoTokenizer.from_pretrained(MODEL_ID)
 model=AutoModelForCausalLM.from_pretrained(MODEL_ID,torch_dtype=torch.float32,low_cpu_mem_usage=True); model.eval()
 load=time.perf_counter()-t
 report={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"method":"same eight prompts, sequential local CPU inference versus public ARIES API",
 "independent_model":{"id":MODEL_ID,"source":"Hugging Face public model repository","license":"Apache-2.0 per model card","load_time_seconds":load,"device":"CPU"},
 "note":"Small project-authored smoke test, not independent certification or a general intelligence ranking. ARIES timing includes network/server effects; local timing does not.",
 "rounds":ROUNDS,"cases_per_round":len(CASES),"targets":[]}
 local=[]; t0=time.perf_counter()
 for ri in range(ROUNDS):
  for cat,prompt,expected in CASES:
   t=time.perf_counter()
   try:
    inp=tok.apply_chat_template([{"role":"user","content":prompt}],add_generation_prompt=True,return_tensors="pt")
    with torch.inference_mode(): out=model.generate(inp,max_new_tokens=64,do_sample=False,pad_token_id=tok.eos_token_id)
    txt=tok.decode(out[0][inp.shape[-1]:],skip_special_tokens=True); err=None; status=200
   except Exception as e: txt=""; err=type(e).__name__+": "+str(e)[:240]; status=None
   local.append({"target":"qwen-local","round":ri+1,"category":cat,"prompt":prompt,"status":status,"latency_ms":(time.perf_counter()-t)*1000,"text":txt,"error":err,"correct":bool(norm(txt)) and all(x in norm(txt) for x in expected)})
 report["targets"].append(summarize("qwen-local",MODEL_ID,local,time.perf_counter()-t0))
 remote=[]; t0=time.perf_counter()
 for ri in range(ROUNDS):
  for cat,prompt,expected in CASES:
   r=api(prompt); r.update({"target":"aries-public-api","round":ri+1,"category":cat,"prompt":prompt,"correct":bool(norm(r["text"])) and all(x in norm(r["text"]) for x in expected)})
   remote.append(r); print("ARIES",ri+1,cat,r["status"],round(r["latency_ms"],1),"ms",flush=True)
 report["targets"].append(summarize("aries-public-api",MODEL,remote,time.perf_counter()-t0))
 os.makedirs("reports",exist_ok=True)
 with open("reports/aries-public-model-validation.json","w",encoding="utf-8") as f:json.dump(report,f,indent=2,ensure_ascii=False)
 for r in report["targets"]:
  l=r["latency_ms"]; print(f'SUMMARY {r["target"]}: success={r["successful_nonempty"]}/{r["requests"]} correct={r["correct_smoke_cases"]}/{r["requests"]} P50={l["p50"]:.1f}ms P95={l["p95"]:.1f}ms P99={l["p99"]:.1f}ms RPS={r["requests_per_second"]:.3f}',flush=True)
if __name__=="__main__":main()
