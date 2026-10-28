const CACHE = "mallin-shell-v2-local-model";
const ASSETS = ["./", "./index.html", "./styles.css", "./app.js", "./manifest.webmanifest"];
self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())));
self.addEventListener("activate", event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith("mallin-shell-") && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin) return;
  // Cache only the static application shell. Model packages, weights, and WebGPU libraries
  // are cached by the browser inference runtime; never store chat prompts in this service worker.
  if (!ASSETS.some(path => new URL(path, self.location.href).pathname === url.pathname)) return;
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (response.ok) { const copy=response.clone(); caches.open(CACHE).then(cache=>cache.put(event.request,copy)); }
    return response;
  }).catch(() => caches.match("./index.html"))));
});
