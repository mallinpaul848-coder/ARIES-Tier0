"""ARIES Launchpad: self-hosted dashboard and health probe for ARIES services."""
import json, os, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST=os.getenv("ARIES_LAUNCHPAD_HOST","0.0.0.0")
PORT=int(os.getenv("ARIES_LAUNCHPAD_PORT","8090"))
API=os.getenv("ARIES_API_BASE_URL","http://aries-api:8000").rstrip("/")
PUBLIC=os.getenv("ARIES_PUBLIC_API_URL","").rstrip("/")

def probe(path):
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(API+path,timeout=5) as r:
            raw=r.read(65536).decode("utf-8","replace")
            try: body=json.loads(raw)
            except ValueError: body={"text":raw[:300]}
            return {"path":path,"reachable":200<=r.status<300,"http_status":r.status,"latency_ms":round((time.perf_counter()-start)*1000,2),"body":body}
    except urllib.error.HTTPError as e:
        return {"path":path,"reachable":False,"http_status":e.code,"latency_ms":round((time.perf_counter()-start)*1000,2),"error":"upstream HTTP error"}
    except Exception as e:
        return {"path":path,"reachable":False,"latency_ms":round((time.perf_counter()-start)*1000,2),"error":type(e).__name__}

def status():
    checks=[probe(p) for p in ("/health","/","/diagnostics","/v1/models")]
    diag=next((x.get("body",{}) for x in checks if x["path"]=="/diagnostics"),{})
    models=next((x.get("body",{}) for x in checks if x["path"]=="/v1/models"),{})
    model=models.get("data",[]) if isinstance(models,dict) else []
    model_id=model[0].get("id","") if model else ""
    ready=bool(diag.get("inference_configured") and model_id and all(x["reachable"] for x in checks))
    return {"platform":"ARIES Launchpad","version":"0.1.0","mode":"self-hosted","public_api_url":PUBLIC or None,"services":[{"name":"ARIES API","status":"inference-ready" if ready else ("reachable" if checks[0]["reachable"] else "unreachable"),"inference_ready":ready,"model_id":model_id or None,"checks":checks}],"note":"This dashboard monitors services; it does not provision cloud servers or provide model weights."}

PAGE="""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ARIES Launchpad</title><style>
body{font:16px system-ui;max-width:1000px;margin:28px auto;padding:0 18px;background:#0a0c10;color:#e8edf5}h1{color:#00f0ff}.card{border:1px solid #293341;border-radius:14px;padding:18px;margin:18px 0;background:#121620}button{padding:10px 14px;border:0;border-radius:8px;background:#00f0ff;font-weight:bold}pre{white-space:pre-wrap;overflow-wrap:anywhere;color:#d6e2f0}.warn{color:#ffca70}.good{color:#66e3a1}
</style><h1>ARIES Launchpad</h1><p>Self-hosted ARIES service dashboard</p><button onclick="refresh()">Refresh status</button><section class="card"><h2 id="state" class="warn">Checking services...</h2><p id="note"></p></section><section class="card"><h2>Live diagnostics</h2><pre id="data">Loading...</pre></section><section class="card"><h2>Public endpoint</h2><p id="public">Not configured</p><p>This dashboard does not create cloud accounts, public HTTPS, or model weights. Configure those on infrastructure you control.</p></section><script>
async function refresh(){try{let r=await fetch('/api/status',{cache:'no-store'}),j=await r.json(),s=j.services[0];let el=document.getElementById('state');el.textContent=s.inference_ready?'INFERENCE READY':'API '+s.status.toUpperCase()+' — inference not verified';el.className=s.inference_ready?'good':'warn';document.getElementById('note').textContent=j.note;document.getElementById('data').textContent=JSON.stringify(j,null,2);document.getElementById('public').textContent=j.public_api_url||'Set ARIES_PUBLIC_API_URL to display the public API URL'}catch(e){document.getElementById('state').textContent='Status check failed';document.getElementById('data').textContent=String(e)}}refresh();
</script></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/health": self.json(200,{"status":"ok","service":"aries-launchpad"})
        elif self.path=="/api/status": self.json(200,status())
        elif self.path=="/":
            b=PAGE.encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(b)
        else: self.json(404,{"error":"not_found"})
    def json(self,code,data):
        b=json.dumps(data).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(b)
    def log_message(self,fmt,*args): print("aries-launchpad:",fmt%args)

if __name__=="__main__":
    print("ARIES Launchpad listening on %s:%s; API=%s"%(HOST,PORT,API))
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
