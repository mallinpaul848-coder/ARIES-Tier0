const DEFAULT_API = "https://aries-tier0-api-6qjh.onrender.com";
export default async function handler(req,res) {
  if(req.method!=="GET"){res.setHeader("Allow","GET");return res.status(405).json({error:"Method not allowed"});}
  const base=(process.env.ARIES_API_BASE_URL||DEFAULT_API).replace(/\/+$/,""), controller=new AbortController(), timer=setTimeout(()=>controller.abort(),12000);
  try {
    const rs=await Promise.all(["/health","/diagnostics","/v1/models"].map(p=>fetch(base+p,{cache:"no-store",signal:controller.signal})));
    const [health,diagnostics,models]=await Promise.all(rs.map(r=>r.json().catch(()=>({}))));
    const configured=diagnostics.inference_configured===true||models.inference_ready===true;
    res.setHeader("Cache-Control","no-store");
    return res.status(200).json({reachable:rs[0].ok,health,diagnostics,models,inferenceConfigured:configured,generalChatReady:configured&&Array.isArray(models.data)&&models.data.length>0,note:configured?"Backend configuration exists; send a real prompt to verify generation.":rs[0].ok?"API is reachable but a general language-model backend is not configured.":"ARIES API is unreachable."});
  } catch(e) { return res.status(e.name==="AbortError"?504:502).json({reachable:false,inferenceConfigured:false,generalChatReady:false,error:"Could not reach ARIES API"}); }
  finally {clearTimeout(timer);}
}