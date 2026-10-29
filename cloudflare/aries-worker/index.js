const MODEL = "@cf/meta/llama-3.2-3b-instruct";
const ALLOWED_ORIGINS = new Set([
  "https://aries-ai-mallin-chat.vercel.app",
  "https://aries-ai-mallin-chat-mallinpaul848-4176.vercel.app"
]);

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.has(origin) ? origin : "https://aries-ai-mallin-chat.vercel.app";
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
    "X-Content-Type-Options": "nosniff"
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders(origin) }
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (url.pathname === "/health" && request.method === "GET") {
      return json({ status: "ok", service: "ARIES AI hosted inference", model: MODEL }, 200, origin);
    }
    if (url.pathname !== "/v1/chat/completions" || request.method !== "POST") {
      return json({ error: { message: "Not found" } }, 404, origin);
    }
    if (origin && !ALLOWED_ORIGINS.has(origin)) {
      return json({ error: { message: "Origin not allowed" } }, 403, origin);
    }
    const declaredLength = Number(request.headers.get("Content-Length") || "0");
    if (declaredLength > 100000) {
      return json({ error: { message: "Request is too large (100 KB maximum)." } }, 413, origin);
    }
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: { message: "Expected a JSON request body." } }, 400, origin);
    }
    if (!Array.isArray(body.messages) || body.messages.length < 1 || body.messages.length > 64) {
      return json({ error: { message: "messages must contain 1 to 64 items." } }, 400, origin);
    }
    const messages = body.messages.filter(m =>
      m && ["system", "user", "assistant"].includes(m.role) &&
      typeof m.content === "string" && m.content.length > 0
    ).map(m => ({ role: m.role, content: m.content.slice(0, 12000) }));
    if (!messages.some(m => m.role === "user")) {
      return json({ error: { message: "At least one user message is required." } }, 400, origin);
    }
    const max_tokens = Math.max(1, Math.min(Number(body.max_tokens) || 384, 512));
    const temperature = Math.max(0, Math.min(Number(body.temperature ?? 0.6), 1.5));
    try {
      const result = await env.AI.run(MODEL, { messages, max_tokens, temperature });
      const content = typeof result?.response === "string"
        ? result.response
        : typeof result?.output_text === "string" ? result.output_text : "";
      if (!content.trim()) {
        return json({ error: { message: "Hosted model returned an empty response. Please retry." } }, 502, origin);
      }
      return json({
        id: "aries-" + crypto.randomUUID(),
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: MODEL,
        choices: [{ index: 0, message: { role: "assistant", content }, finish_reason: "stop" }]
      }, 200, origin);
    } catch (error) {
      return json({ error: { message: "Hosted inference failed or the free daily allowance is exhausted.", type: "inference_error" } }, 503, origin);
    }
  }
};
