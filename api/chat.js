const DEFAULT_API = "https://aries-tier0-api-6qjh.onrender.com";
const WINDOW_MS = 60000, LIMIT = 20, buckets = new Map();
export default async function handler(req, res) {
  if (req.method !== "POST") { res.setHeader("Allow", "POST"); return res.status(405).json({error:{message:"Method not allowed"}}); }
  const ip = String(req.headers["x-forwarded-for"] || "unknown").split(",")[0].trim(), now = Date.now();
  const b = buckets.get(ip) || {start:now,count:0};
  if (now-b.start>WINDOW_MS) { b.start=now; b.count=0; }
  if (++b.count>LIMIT) return res.status(429).json({error:{message:"Rate limit reached; wait one minute and retry."}});
  buckets.set(ip,b);
  let body=req.body;
  if (typeof body==="string") { try { body=JSON.parse(body); } catch { return res.status(400).json({error:{message:"Invalid JSON"}}); } }
  if (!body || !Array.isArray(body.messages) || body.messages.length<1 || body.messages.length>80) return res.status(400).json({error:{message:"messages must contain 1–80 entries"}});
  const messages=body.messages.map(m=>({role:["system","user","assistant"].includes(m?.role)?m.role:"user",content:typeof m?.content==="string"?m.content.slice(0,24000):""})).filter(m=>m.content.trim());
  if (!messages.length) return res.status(400).json({error:{message:"No valid message content"}});
  const base=(process.env.ARIES_API_BASE_URL||DEFAULT_API).replace(/\/+$/,""), controller=new AbortController(), timer=setTimeout(()=>controller.abort(),100000);
  try {
    const upstream=await fetch(base+"/v1/chat/completions",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({model:body.model||"aries-native",messages,max_tokens:Number.isInteger(body.max_tokens)?Math.max(1,Math.min(body.max_tokens,2048)):700,temperature:Number.isFinite(body.temperature)?Math.max(0,Math.min(body.temperature,1.2)):.25}),signal:controller.signal});
    const result=await upstream.text(); res.setHeader("Cache-Control","no-store"); res.setHeader("X-Mallin-Proxy","aries-chat"); res.status(upstream.status); res.setHeader("Content-Type",upstream.headers.get("content-type")||"application/json"); return res.send(result);
  } catch(e) { return res.status(e.name==="AbortError"?504:502).json({error:{message:e.name==="AbortError"?"ARIES inference timed out":"ARIES inference backend is unreachable"}}); }
  finally { clearTimeout(timer); }
}