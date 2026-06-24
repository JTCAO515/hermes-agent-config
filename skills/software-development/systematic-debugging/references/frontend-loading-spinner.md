# Frontend: Page Stuck at Loading Spinner

## Symptom

Page renders HTML with a visible loading spinner/title, but the content never loads.
The spinner keeps spinning indefinitely. No user-visible error is shown.
The page appears "broken" or "blank except for header/footer."

## Diagnostic Primer: Bypassing the Service Worker

**Before you start the deep dive below**, if the site has a Service Worker registered,
your first step should be to check whether the JS executes AT ALL by bypassing the SW:

```js
// Run this in browser_console (browser tool's expression field)
// This directly fetches and evals app.js, bypassing any SW cache
fetch('/app.js?_=' + Date.now()).then(function(r) {
  return r.text();
}).then(function(code) {
  console.log('FETCHED:', code.length, 'bytes');
  try {
    eval(code);
    console.log('EVAL OK — app.js is valid, SW is the blocker');
  } catch(e) {
    console.error('EVAL ERROR — real JS bug:', e.message, e.stack);
  }
}).catch(function(e) {
  console.error('FETCH FAILED — network issue');
});
```

- **FETCHED + EVAL OK** → The JS file itself is fine. The problem is the **Service Worker** serving a stale cached version. Go straight to §2.
- **EVAL ERROR** → Real JS syntax error. Go to §1.
- **FETCH FAILED** → Network/server issue.

## Common Root Causes (in order to check)

### 1. JavaScript SyntaxError — script doesn't execute at all

**Most common cause.** The entire `<script src="/app.js">` fails to parse,
so nothing runs — not even the loading spinner control logic.

**Check:**
```bash
node --check web/app.js
```

**Typical findings:**
- **Duplicate `const`/`let` declarations** in global scope
  (`SyntaxError: Identifier 'X' has already been declared`)
- **Truncated/corrupted lines** — literal `...[truncated]` in the file from
  a previous copy/paste that went wrong. **Always run `grep -c 'truncated' app.js`
  to check for literal truncation markers in the source.**
- **Spread operator used in non-ES6 context**
- **Missing closing braces** or mismatched parentheses

**Fix:** Remove the duplicate/corrupted section. Re-run `node --check` to verify.

### 2. Service Worker serves cached (broken) version

**Even after fixing the JS file, the browser may keep showing the old behavior**
because a Service Worker is serving a cached copy of the broken app.js.

**Check:**
```js
// In browser console or via browser_console tool
navigator.serviceWorker.getRegistrations().then(rs => rs.length)
caches.keys().then(keys => console.log(keys))
```

**Root cause:** SW uses cache-first strategy for static assets:
```js
e.respondWith(
  caches.match(e.request).then((hit) => hit || fetch(e.request))
);
```

The browser only re-fetches the SW script when `sw.js` content *changes*.
Fixing `app.js` alone does NOT trigger SW re-installation.

**Fix — bump the SW cache version:**
```diff
- const CACHE = "wc26-v1";
+ const CACHE = "wc26-v2";
```

This triggers the SW `install` event → `caches.open(CACHE).then(cache => cache.addAll(ASSETS))`
→ fetches fresh `app.js` → `self.skipWaiting()` activates the new SW immediately.

**⚠️ CRITICAL: Deploy order matters.** The SW re-registration trap:
1. ❌ **Wrong order**: Clear caches → unregister SW → reload. The page re-registers the old SW immediately from the still-deployed `sw.js`, restoring the broken cache.
2. ✅ **Correct order**: (a) Deploy the fixed `app.js` AND the SW version bump (`wc26-v1` → `wc26-v2`) in a single git commit → push → wait for Vercel deploy. (b) THEN clear caches + unregister SW in browser. (c) Reload — the page now fetches the fresh SW (v2) which installs and caches the fixed app.js.

**Verification after fix — clear old caches from browser:**
```js
// Run AFTER the SW update is deployed
(async function() {
  // Clear ALL caches
  var keys = await caches.keys();
  await Promise.all(keys.map(k => caches.delete(k)));
  // Unregister ALL SWs
  var regs = await navigator.serviceWorker.getRegistrations();
  await Promise.all(regs.map(r => r.unregister()));
  // Reload completely fresh
  window.location.href = '/?_=' + Date.now();
})();
```

**Alternative: Use the `fetch('/app.js') + eval()` primer** (described above) to
verify the app.js file is valid BEFORE going through the SW cache-busting process.

### 3. API endpoint hangs or errors

The `loadAll()` / `init()` function calls multiple APIs via `Promise.all()`.
If one endpoint hangs or returns an error, the entire promise chain fails.

**Check from terminal (not browser — bypasses SW cache):**
```bash
for ep in "api/wc/standings" "api/wc/predict" "api/wc/knockout" "api/wc/summary"; do
  time curl -s -w " HTTP:%{http_code} Size:%{size_download}\\n" "https://example.com/$ep" | tail -1
done
```

**Look for:**
- HTTP 500 errors
- Timeouts (>10s) that cause `Promise.all` to never resolve
- Query parameters that cause CPU-heavy computation

**Fix:** Add `.catch()` fallbacks for non-critical endpoints, or add timeouts
to `fetchJSON()`.

### 4. JavaScript runtime error in template literal rendering

**Symptom:** Script executes, data loads, but a specific tab/section is empty.
The error fires asynchronously inside a `.map().join('')` chain and gets
swallowed by a parent `catch` block or the Promise microtask queue.

**Detection:**
```js
// Override onerror to catch all errors
window.onerror = (msg, url, line, col, err) => {
  console.error('GLOBAL ERROR:', msg, url, line, col, err?.stack);
  return true;
};
```

Then check the browser console after reloading.

**Common pattern:** A function called inside a template literal (`${gs(value)}`)
was never defined (`ReferenceError: gs is not defined`). The `.map().join('')`
breaks silently because JS doesn't throw synchronously for undefined references
inside template literals called from async context.

## Diagnostic Flowchart

```
Page loads → title visible → spinner spinning forever
                      ↓
         Is HTTP status 200? ──NO──→ Server/deployment issue
                      ↓ YES
     Run fetch('/app.js') + eval() primer
      (bypasses SW, tests raw JS validity)
                      ↓
        EVAL ERROR ──────→ node --check app.js
        (real JS bug)         ↓
                        SyntaxError? → fix source, re-deploy
                      ↓
        EVAL OK ────────→ Check SW registrations
        (JS is valid,             ↓
         SW is blocker)     SW present? ──YES──→ Bump cache version
                                                   → Deploy SW + JS together
                                                   → Clear browser caches
                                                   → Reload
                                   ↓ NO/after fix
                         Check API endpoints from terminal
                                   ↓
                     Any endpoint 500/timeout? ──YES──→ Add error handling
                                   ↓ NO
                         Page should render now
```

## Minimizing SW-Induced Pain

- **Always update sw.js when changing static assets** — even if unmodified,
  change a comment or version string so the browser detects a new SW.
- **For urgent fixes where users already have the broken SW:**
  1. Fix the JS file
  2. Bump SW cache version
  3. Deploy both at the same commit
  4. Wait for deploy to complete
  5. THEN clear browser caches + unregister SW + reload
- **Permanent solution:** Add a cache-busting hash to the app.js URL in
  index.html: `<script src="/app.js?v={{BUILD_HASH}}"></script>`
- **Diagnostic shortcut:** When you see a site that loads HTML but the JS
  doesn't execute, the `fetch('/app.js') + eval()` trick tells you in 5 seconds
  whether it's a real JS bug or a SW caching issue — skip the guesswork.
