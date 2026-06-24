# SSE Streaming Timeout on Vercel Hobby (10s Limit)

> How to diagnose and fix intermittent "Connection error" in Vercel-deployed SSE streaming chat apps.

## Symptom

Chat works sometimes, but intermittently shows **"Connection error"** in the frontend — especially on first visit after idle. Backend curl tests pass (SSE returns fine), but the browser shows `AbortError` or `TypeError: Failed to fetch` in the catch block.

## Root Cause

**Vercel Hobby plan enforces a 10-second timeout** for serverless function execution. When:

1. The function is **cold-starting** (~3-5s overhead: Python runtime init + module imports)
2. Plus the **DeepSeek/LLM API response time** (~2-8s depending on query complexity)
3. Plus **SSE streaming overhead** (first byte latency + chunk processing)

...the total can easily exceed 10s → Vercel kills the function → the browser's `fetch()` throws a network error → the frontend catch block shows "Connection error".

This is **intermittent** because hot instances respond in ~1-2s, making it seem like it "sometimes works."

## Two Error Paths in the Frontend

Most SSE chat apps have two error paths. Distinguishing them is key to diagnosis:

| Error | Code Path | Meaning |
|-------|-----------|---------|
| "Sorry, I couldn't process that" | `if (!resp.ok)` | Server returned non-2xx (e.g., 503, 500) — the function ran but errored |
| **"Connection error"** | `catch (e) { if (e.name !== 'AbortError') ... }` | **Network error mid-stream** — the fetch/reader threw a network exception. This is the Vercel timeout signature |

## Diagnosis

### 1. Test backend independently (curl)

```bash
# Proper SSE test — send a chat message, expect streaming response
curl -s -L -X POST "https://your-domain.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"say hello"}],"city":"beijing"}' \
  --max-time 30
```

If this **always works**, the backend is fine — the issue is client-side or timeout related.

### 2. Test with timing

```bash
curl -s -L -X POST "https://your-domain.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"tell me a detailed story about Beijing"}],"city":"beijing"}' \
  --max-time 30 -o /dev/null -w "\nTime: %{time_total}s\n"
```

If this takes >8-9s, it's at risk of hitting the 10s limit on cold start.

### 3. Check for Service Worker caching

The SW intercepts API calls and can return stale 503 errors if the network fetch fails. Check `sw.js`:

```js
// Problematic pattern — SW returns 503 on ANY network failure
if (e.request.url.includes("/api/")) {
  e.respondWith(fetch(e.request).catch(() => new Response(
    JSON.stringify({ error: "offline" }),
    { status: 503, ... }
  )));
}
```

The SW's 503 response would trigger the `!resp.ok` path ("Sorry, I couldn't process that"), **not** the catch path ("Connection error"). If the user sees "Connection error," the SW likely isn't the cause — but force-redeploying clears both.

## Fixes

### Immediate: Retry Button (low effort, high impact)

Replace the generic "Connection error" message with a retry-capable one:

```js
// Before
addMessage('Connection error. Please try again.', 'bot');

// After — Retry button that resends the last user message
} else {
  removeMessage(typingId);
  const errMsg = document.createElement('div');
  errMsg.className = 'msg msg-bot';
  errMsg.innerHTML = `<div class="msg-avatar">🐼</div>
    <div class="msg-body">
      <div class="msg-sender">VisePanda</div>
      <div class="msg-text" style="color:#e74c3c">
        ⚠️ Connection error.
        <a href="#" onclick="...retry logic..."
           style="color:var(--accent);font-weight:600">Retry ↻</a>
      </div>
    </div>`;
  document.getElementById('chat-messages').appendChild(errMsg);
}
```

The retry logic: find the last user message in state, rebuild the fetch call, and re-send. The simplest approach: trigger an Enter keydown event on the chat input if the last message text is still available.

### Med-Term: Force Redeploy

A git push that triggers Vercel redeployment:

```bash
git commit --allow-empty -m "chore: force redeploy"
git push origin main
```

This clears:
- Cold-start containers
- Service Worker caches on next page load
- Any stale build artifacts

### Long-Term: Mitigation Options

| Approach | Effort | Effect |
|----------|--------|--------|
| Upgrade to Vercel Pro ($20/mo) → 300s timeout | Low | Eliminates timeout entirely |
| Add keep-warm cron (every 5 min) | Low | Reduces cold starts but doesn't fix China latency |
| Move LLM call to VPS (not Vercel) | Medium | Bypasses 10s limit entirely, but adds CORS complexity |
| Reduce system prompt size | Low | Shaves 1-2s off first-byte latency |
| Use streaming mode with early response | Medium | First byte arrives faster, may complete before timeout |

## Pattern Summary

```
User: "问答又掉了" / "connection error"
  ↓
Test curl POST /api/chat → ✅ Works
  ↓
Test timing → Response > 8s possible
  ↓
Diagnosis: Vercel Hobby 10s timeout on cold start
  ↓
Fix: Force redeploy + add Retry button to error message
  ↓
Long-term: Upgrade or move LLM call off Vercel
```
