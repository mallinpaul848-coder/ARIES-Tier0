const $ = (id) => document.getElementById(id);
const messages = $("messages"), form = $("chatForm"), promptBox = $("prompt");
const endpointBox = $("endpoint"), modelBox = $("model"), endpointResult = $("endpointResult");
const STORE_URL = "mallin.endpoint", STORE_MODEL = "mallin.model";
let endpoint = "", model = "";
try { endpoint = localStorage.getItem(STORE_URL) || ""; model = localStorage.getItem(STORE_MODEL) || ""; } catch {}
endpointBox.value = endpoint; modelBox.value = model;
function status(text, connected=false) { $("statusText").textContent=text; $("statusDot").classList.toggle("connected", connected); }
function addMessage(text, role) {
  const node=document.createElement("div"); node.className="message "+role;
  const who=document.createElement("div"); who.className="who"; who.textContent=role==="user"?"YOU":"ARIES";
  const p=document.createElement("p"); p.textContent=text; node.append(who,p); messages.append(node); messages.scrollTop=messages.scrollHeight;
}
function localReply(q) {
  const s=q.trim();
  const m=s.match(/^(?:calculate\s+)?(-?\d+(?:\.\d+)?)\s*([+*/x×-])\s*(-?\d+(?:\.\d+)?)\s*\??$/i);
  if(m){const a=Number(m[1]),b=Number(m[3]),op=m[2].toLowerCase(); if(op==="/"&&b===0)return "Division by zero is undefined."; const n=op==="+"?a+b:op==="-"?a-b:(op==="*"||op==="x"||op==="×")?a*b:a/b; return "Demo calculator result: "+n+". This is a local arithmetic test, not an AI-model response.";}
  if(/what can you do|offline/i.test(s))return "This prototype provides a chat interface, basic arithmetic, and status messages offline. It does not include model weights or a built-in language model.";
  if(/test api|endpoint|connection status|connected/i.test(s))return endpoint ? "An endpoint is configured in this browser. Use “Check connection” in settings to test it; configuration alone does not prove the model works." : "No model endpoint is configured. Open “Connect a model endpoint you control” below the chat.";
  if(/hello|^hi\b|hey/i.test(s))return "Hello! ARIES is currently in local demo mode. Connect a model you control for general-purpose answers.";
  return "I received your message, but this offline demo does not contain a full language model. Configure a compatible model endpoint you control to get genuine model-generated answers. I will not pretend a canned response is AI inference.";
}
async function callModel(q) {
  if(!endpoint) return localReply(q);
  const base=endpoint.replace(/\/+$/,"");
  const response=await fetch(base+"/chat/completions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:model||"default",messages:[{role:"user",content:q}],stream:false})});
  if(!response.ok) throw new Error("Endpoint returned HTTP "+response.status);
  const data=await response.json(); const answer=data?.choices?.[0]?.message?.content;
  if(typeof answer!=="string"||!answer.trim()) throw new Error("Response did not contain choices[0].message.content");
  return answer.trim();
}
form.addEventListener("submit",async e=>{e.preventDefault();const q=promptBox.value.trim();if(!q)return;addMessage(q,"user");promptBox.value="";const wait=document.createElement("div");wait.className="message assistant";wait.textContent="Thinking…";messages.append(wait);messages.scrollTop=messages.scrollHeight;
  try{const answer=await callModel(q);wait.remove();addMessage(answer,"assistant");}
  catch(err){wait.remove();addMessage("Could not get a model response: "+err.message+". Check the endpoint URL, CORS policy, and server status. No fallback answer was presented as model output.","assistant");}
});
$("clearBtn").addEventListener("click",()=>{messages.replaceChildren();});
document.querySelectorAll("[data-prompt]").forEach(b=>b.addEventListener("click",()=>{promptBox.value=b.dataset.prompt;form.requestSubmit();}));
$("saveEndpoint").addEventListener("click",()=>{endpoint=endpointBox.value.trim().replace(/\/+$/,"");model=modelBox.value.trim();try{localStorage.setItem(STORE_URL,endpoint);localStorage.setItem(STORE_MODEL,model);}catch{} $("engineLabel").textContent=endpoint?"Endpoint configured · not yet verified":"Local demo · no model connected";endpointResult.textContent=endpoint?"Saved in this browser. Configuration is not proof of a successful model response.":"Endpoint cleared; local demo mode is active.";status(endpoint?"Endpoint configured (untested)":"Local demo mode",false);});
$("testEndpoint").addEventListener("click",async()=>{endpoint=endpointBox.value.trim().replace(/\/+$/,"");if(!endpoint){endpointResult.textContent="Enter an endpoint URL first.";return;}endpointResult.textContent="Testing /models…";try{const r=await fetch(endpoint+"/models");if(!r.ok)throw new Error("HTTP "+r.status);const data=await r.json();endpointResult.textContent="Endpoint responded to /models. This does not yet verify chat completion.";status("Endpoint reachable",true);if(data.error)endpointResult.textContent+=" Server reported: "+data.error.message;}catch(err){endpointResult.textContent="Could not verify endpoint: "+err.message+". The server may block browser CORS requests.";status("Endpoint unverified",false);}});
if("serviceWorker" in navigator && location.protocol!=="file:"){navigator.serviceWorker.register("./sw.js").catch(()=>{});}
status(navigator.onLine?"Local demo ready · model not connected":"Offline · local demo",false);
window.addEventListener("online",()=>status(endpoint?"Endpoint configured (untested)":"Local demo ready · model not connected",false));
window.addEventListener("offline",()=>status("Offline · local demo",false));
