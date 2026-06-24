# PWA on Vercel Static Sites

> How to add Progressive Web App support to a Vercel-hosted static site served via a Python WSGI handler.

## Minimal Files

### 1. `web/manifest.json`

```json
{
  "name": "WC26 Edge Lab",
  "short_name": "WC26 Lab",
  "description": "2026 FIFA World Cup prediction lab",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#08090a",
  "theme_color": "#5e6ad2",
  "orientation": "any",
  "categories": ["sports", "utilities"],
  "icons": [
    { "src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable" }
  ]
}
```

### 2. `web/sw.js` — Service Worker

Cache-first for static assets, network-only for API calls:

```javascript
const CACHE = "wc26-v1";
const ASSETS = ["/", "/index.html", "/app.css", "/app.js", "/manifest.json", "/icon.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (e.request.url.includes("/api/")) {
    e.respondWith(fetch(e.request).catch(() => new Response(
      JSON.stringify({ error: "offline" }), { status: 503, headers: { "Content-Type": "application/json" } }
    )));
    return;
  }
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request)));
});
```

### 3. `web/icon.svg`

Simple SVG app icon (512x512, soccer ball + text).

### 4. HTML head additions

```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#5e6ad2">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
```

### 5. SW Registration (in app.js)

```javascript
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}
```

## Vercel-Specific Notes

- **SW must be served from root path** (`/sw.js`), not a subdirectory
- **manifest.json** must be served from root path (`/manifest.json`) — browsers only recognize manifests at the site root
- All PWA files live in `web/` and are served by the catch-all WSGI route `"/(.*)" → api/index.py`
- No extra Vercel config needed — the static file handler already serves them
- PNG icons are optional — SVG icons work on modern browsers (2025+) and scale infinitely
