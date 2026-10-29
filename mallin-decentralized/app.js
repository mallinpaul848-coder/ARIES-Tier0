const $ = (id) => document.getElementById(id);
const messages = $("messages"), form = $("chatForm"), promptBox = $("prompt");
const loadModelBtn = $("loadModelBtn"), modelStatus = $("modelStatus");
const modelProgress = $("modelProgress"), modelSelect = $("localModel");
const WEBLLM_URL = "https://esm.sh/@mlc-ai/web-llm@0.2.86";
let engine = null, modelLoading = false, loadedModelId = "";
let conversation = [];

function status(text, connected=false) {
  $("statusText").textContent = text;
  $("statusDot").classList.toggle("connected", connected);
  $("engineLabel").textContent = connected ? "Local model ready · " + loadedModelId : text;
  $("chatMode").textContent = connected ? "Browser AI is ready" : "Browser inference not loaded";
}
function addMessage(text, role) {
  const node=document.createElement("div");
  node.className="message "+role;
  const who=document.createElement("div");
  who.className="who";
  who.textContent=role==="user"?"YOU":"ARIES";
  const p=document.createElement("p");
  p.textContent=text;
  node.append(who,p);
  messages.append(node);
  messages.scrollTop=messages.scrollHeight;
  return p;
}
function localReply(q) {
  const s=q.trim();
  const m=s.match(/^(?:calculate\s+)?(-?\d+(?:\.\d+)?)\s*([+*/x×-])\s*(-?\d+(?:\.\d+)?)\s*\??$/i);
  if(m){
    const a=Number(m[1]), b=Number(m[3]), op=m[2].toLowerCase();
    if(op==="/"&&b===0)return "Division by zero is undefined.";
    const n=op==="+"?a+b:op==="-"?a-b:(op==="*"||op==="x"||op==="×")?a*b:a/b;
    return "Local calculator result: "+n+". Load the browser AI model for general language-model responses.";
  }
  if(/what can you do|offline/i.test(s))return "I can handle basic arithmetic and show this interface offline. Load the browser AI model to enable genuine language-model responses on this device.";
  if(/hello|^hi\b|hey/i.test(s))return "Hello! I am MALLIN's ARIES chat interface. Load the browser AI model below to start local language-model inference.";
  return "The language model is not loaded yet. Select “Load browser AI model” below. The first download can be large and requires WebGPU.";
}
async function loadLocalModel() {
  if(engine) return true;
  if(modelLoading) {
    // If a user submits a prompt while the load button is working, wait for that same load.
    while(modelLoading) await new Promise(resolve => setTimeout(resolve, 150));
    return Boolean(engine);
  }
  if(!window.isSecureContext){
    modelStatus.textContent="A secure HTTPS page is required to use WebGPU. Open the permanent website through an HTTPS origin.";
    return false;
  }
  if(!("gpu" in navigator)){
    modelStatus.textContent="This browser does not expose WebGPU. Try a current Chrome or Edge browser on compatible hardware. No hosted inference fallback is configured.";
    status("WebGPU unavailable",false);
    return false;
  }
  modelLoading=true;
  loadModelBtn.disabled=true;
  const modelId=modelSelect.value;
  modelProgress.hidden=false;
  modelProgress.value=0;
  modelStatus.textContent="Loading browser inference engine…";
  status("Preparing local model…",false);
  try {
    // WebLLM executes inference in the visitor's browser. No AI inference API is called.
    // Runtime and model artifacts are downloaded on first use from their published repositories.
    const webllm = await import(WEBLLM_URL);
    if(typeof webllm.CreateMLCEngine!=="function")throw new Error("The browser runtime did not expose CreateMLCEngine.");
    engine = await webllm.CreateMLCEngine(modelId,{
      initProgressCallback:(progress)=>{
        const pct=typeof progress?.progress==="number"?Math.max(0,Math.min(100,Math.round(progress.progress*100))):0;
        modelProgress.value=pct;
        modelStatus.textContent=typeof progress?.text==="string"?progress.text:"Downloading model files…";
        status("Loading model "+pct+"%",false);
      }
    });
    loadedModelId=modelId;
    conversation=[];
    modelStatus.textContent="Ready. Inference runs locally in this browser. Prompts are not sent to an AI inference API.";
    status("Local model ready",true);
    loadModelBtn.textContent="Model loaded";
    modelSelect.disabled=true;
    modelProgress.value=100;
    modelProgress.hidden=true;
    // Keep the chat transcript focused on the user's conversation; readiness is shown in model status.
  } catch(error) {
    engine=null;
    loadedModelId="";
    modelStatus.textContent="Could not load the local model: "+(error?.message||String(error))+". Check WebGPU support, GPU memory, first-download connectivity, and browser console. No hosted inference fallback was used.";
    status("Local model failed to load",false);
    loadModelBtn.disabled=false;
  } finally {
    modelLoading=false;
  }
}
async function answerWithModel(q) {
  const messagesForModel=[
    {role:"system",content:"You are ARIES AI, the assistant inside the MALLIN Platform. Be helpful, accurate, and clear. Do not claim certification, capabilities, access, or benchmark scores unless supported by the conversation. If uncertain, say so."},
    ...conversation,
    {role:"user",content:q}
  ];
  const response=await engine.chat.completions.create({
    messages:messagesForModel,
    temperature:0.7,
    max_tokens:320
  });
  const answer=response?.choices?.[0]?.message?.content;
  if(typeof answer!=="string"||!answer.trim())throw new Error("The model returned an empty answer.");
  conversation.push({role:"user",content:q},{role:"assistant",content:answer.trim()});
  if(conversation.length>20)conversation=conversation.slice(-20);
  return answer.trim();
}
form.addEventListener("submit",async e=>{
  e.preventDefault();
  const q=promptBox.value.trim();
  if(!q)return;
  addMessage(q,"user");
  promptBox.value="";
  const answerNode=addMessage(engine?"Generating locally…":"Starting browser AI…","assistant");
  try {
    const calc=/^(?:calculate\\s+)?(-?\\d+(?:\\.\\d+)?)\\s*([+*/x×-])\\s*(-?\\d+(?:\\.\\d+)?)\\s*\\??$/i.test(q);
    if(!engine && !calc) {
      answerNode.textContent="Loading the selected language model for your first answer. This can take several minutes and download hundreds of megabytes…";
      const ready=await loadLocalModel();
      if(!ready) {
        answerNode.textContent=modelStatus.textContent || "Browser-local language model could not start.";
        return;
      }
    }
    answerNode.textContent=engine?await answerWithModel(q):localReply(q);
  } catch(error) {
    answerNode.textContent="Local inference error: "+(error?.message||String(error))+". The model did not provide an answer; check model status and retry.";
  }
});
$("clearBtn").addEventListener("click",()=>{
  messages.replaceChildren();
  conversation=[];
  addMessage("Chat cleared. The loaded model remains available in this tab.","assistant");
});
document.querySelectorAll("[data-prompt]").forEach(button=>button.addEventListener("click",()=>{
  promptBox.value=button.dataset.prompt;
  form.requestSubmit();
}));
loadModelBtn.addEventListener("click",loadLocalModel);
modelProgress.hidden=true;
status(navigator.onLine?"Ready · local model not loaded":"Offline · model not loaded",false);
window.addEventListener("online",()=>{if(!engine&&!modelLoading)status("Online · local model not loaded",false);});
window.addEventListener("offline",()=>{if(!engine&&!modelLoading)status("Offline · local model not loaded",false);});
if("serviceWorker" in navigator && location.protocol!=="file:"){
  navigator.serviceWorker.register("./sw.js").catch(()=>{});
}
