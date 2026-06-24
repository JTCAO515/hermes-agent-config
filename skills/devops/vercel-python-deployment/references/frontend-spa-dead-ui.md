# Frontend: SPA Loads HTML But UI Components Are Dead

> Distinguish this from "loading spinner never resolves" (see `frontend-loading-spinner.md` in `systematic-debugging`) and "SSE streaming timeout" (see `sse-streaming-timeout-vercel.md`). This is a third distinct failure mode: **HTML renders, CSS applies partially, but JavaScript-powered UI (tabs, drawers, modals, images) never initializes.**

## Symptom

User says: *"包括抽屉，图片，tab都没加载出来"* / *"the drawers, images, tabs all didn't load"*

Page characteristics:
- HTML title/header/footer visible
- Some CSS styles applied (background, fonts)
- No loading spinner (because the SPA JS never ran to show one)
- Navigation buttons might be visible but don't respond to clicks
- Chat input empty and unresponsive
- ❌ No console errors in browser_devtools (because JS never even started)

## Three Most Common Root Causes

Check in order:

### 1. Blocking external script prevents `app.js` from loading

**Most common when the app uses CDN-hosted dependencies (Leaflet, Google Maps, etc.).**

The index.html loads an external script **synchronously** (neither `async` nor `defer`) **before** `/app.js`:

```html
<!-- ❌ CRITICAL: This blocks app.js -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin></script>
<script src="/app.js"></script>  <!-- never loads if unpkg is slow/blocked -->
```

If `unpkg.com` is unreachable from the user's network (common in China), the browser blocks on the Leaflet download. `/app.js` never even starts fetching. The entire SPA is dead.

**Diagnosis:**

```bash
# From a representative network, test all external resources independently
for url in "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" \
           "https://fonts.googleapis.com/css2?family=Inter:wght@400" \
           "https://accounts.google.com/gsi/client" \
           "https://your-domain.com/app.js"; do
  time curl -s -o /dev/null -w "$url → %{http_code} (%{time_total}s, %{size_download}B)\n" --max-time 15 "$url"
done
```

**Key pattern:** If CDN-1 (unpkg) is slow/blocked but CDN-2 (your-domain) is fast, the blocking script is the root cause. The user sees a broken page while you testing from a different network see everything working perfectly.

**Fixes (in order of preference):**

| Fix | Effort | Effect |
|-----|--------|--------|
| Add `async` to external scripts | Low | Non-blocking load, but execution order undefined |
| Add `defer` to external scripts | Low | Non-blocking load, execution after HTML parse, before DOMContentLoaded |
| Bundle all dependencies locally | Medium | No external dependency at all |
| Move external scripts below app.js | Low | app.js loads first, UI initializes immediately, Leaflet loads async |

**Best practice for VisePanda-style apps:** Move blocking scripts to bottom of `<body>` or add `defer`:

```html
<!-- Before (blocking): -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin></script>
<script src="/app.js"></script>

<!-- After (non-blocking): -->
<script src="/app.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin defer></script>
```

### 2. Domain redirect (bare → www) and browser cache inconsistency

**Common when Vercel project has a redirect configured: `go2china.space` → `www.go2china.space`**

```bash
# Test:
curl -sL -o /dev/null -w "%{http_code} → %{url_effective}\n" "https://go2china.space/"
# → 200 → https://www.go2china.space/  (followed redirect correctly)

curl -s -v "https://go2china.space/app.js" 2>&1 | grep -i location
# → 307 → https://www.go2china.space/app.js
```

**Problems this creates:**
- If the user previously visited `go2china.space` (bare domain), the browser may have cached resources for that origin
- Service Worker registered on the bare domain doesn't apply to `www` subdomain
- Some browsers/extensions/PWA installs cache the redirect itself, causing race conditions
- The 307 redirect is applied to EVERY resource (JS, CSS, images), not just the base URL — multiplying latency

**Diagnosis:**
```bash
# For each critical resource, check if bare domain redirects
for path in "/" "/app.js" "/app.css" "/manifest.json"; do
  r=$(curl -s -o /dev/null -w "%{http_code}" "https://go2china.space$path")
  w=$(curl -s -o /dev/null -w "%{http_code}" "https://www.go2china.space$path")
  echo "$path → bare:$r www:$w"
done
```

**Fixes:**
- **Short-term**: Tell user to visit `www.go2china.space` directly (skip the redirect)
- **Medium-term**: Configure the redirect at the application level (not Vercel project setting) so it returns HTML immediately with a meta-refresh or JS redirect, avoiding 307 on every asset
- **Alternative**: Use Vercel's redirect configuration but ensure it only applies to `/` and not sub-resources

### 3. JavaScript error on first execution (SyntaxError at parse time)

**Different from runtime errors — these prevent the entire script from executing.**

Causes:
- Accidental truncation: `...[truncated]` literal marker copied into the file
- Duplicate `const`/`let` in global scope
- Corrupted line during write_file → read_file round-trip (line number corruption)

**Check:**
```bash
node --check web/app.js
```

If this passes and the script is valid, the issue is not #3.

## Diagnostic Protocol (Full Flow)

When user says "page not loading fully" / "UI dead" / "all tabs missing":

```
Step 1: Test all resources independently
  ↓
Any resource HTTP non-200? → Fix static file serving
  ↓ All 200
Step 2: Check for 307 redirect on resources
  ↓
Redirect present? → Tell user to use www subdomain directly
  ↓ No redirect
Step 3: Check for blocking external scripts
  ↓
Scripts before app.js? → Move app.js above CDN scripts
  ↓ No blocking scripts
Step 4: Validate JS syntax
  ↓
node --check fails? → Fix SyntaxError
  ↓ Valid JS
Step 5: Test in browser with console logging
  ↓
Check if fetch('/app.js') + eval() works
  ↓
Report findings
```

## Comparison of Three Frongend Failure Modes

| Symptom | "Loading spinner" | "Connection error" | **"UI dead"** |
|---------|-------------------|--------------------|----------------|
| What user sees | Empty page with icon/title + animation | Chat breaks mid-conversation | HTML visible but buttons/tabs don't work |
| JS state | Executed, stuck at `Promise.all` | Executed fine, then fetch threw | **Never executed** |
| Typical cause | A hang in JS runtime (API timeout, template error) | Vercel 10s timeout on SSE streaming | **Blocking script or syntax error at parse time** |
| Diagnosis | Check `Promise.all` flow | Check SSE streaming timing | **Check external scripts before app.js, validate syntax** |
| Fix in this session | — | Force redeploy + Retry button | Move app.js above CDN scripts |

## Key Insight

When the user says "everything is broken" (tabs, drawers, images all missing), the most common cause is **a synchronous external script blocking app.js from loading** — not a bug in the app.js itself. The headless browser test (which has different network conditions) might show the page working fine, making the bug seem intermittent or user-specific. Always check the resource loading chain first.
