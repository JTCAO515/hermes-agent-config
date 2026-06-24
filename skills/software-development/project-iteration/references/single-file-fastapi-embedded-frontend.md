# Single-File FastAPI + Embedded Frontend (Vercel Serverless)

> Architecture pattern where CSS, HTML templates, and JS are all embedded as Python strings in one `api/index.py`. Common for Vercel-deployed projects where the entire app must be one file.

## Pattern Overview

```
api/index.py  ← 1678+ lines, contains:
  • FastAPI app def + routes
  • CSS variable (multi-line `"""` string)
  • HTML templates (f-strings with `{CSS}` injection)
  • SQLAlchemy models
  • Inline utility functions
```

## Key Rules

### CSS Variable
```python
CSS = """  # NOT an f-string — plain multi-line string
/* CSS here — no {{ }} escaping needed */
:root { --bg0: #05070b; }
"""
```

### HTML Templates (f-strings)
```python
def page_landing() -> str:
    return f"""<!doctype html>
<style>{CSS}</style>     ← CSS var injected here (not escaped)
<script>
if (x) {{ ... }}        ← JS { } MUST be doubled as {{ }}
</script>
"""
```

### JS Files (separate files in static/)
```javascript
// static/landing.js — standalone, no escaping issues
window.__SUPABASE_CONFIG__ = {...};
```

## Vercel Serverless Gotchas

### ⚠️ Module Name Conflict with Python stdlib

**Symptom:** Creating a file named `calendar.py` causes `ImportError: cannot import name 'timegm' from 'calendar'` or cascade failures on unrelated imports like `http.cookiejar` → `from calendar import timegm`.

**Cause:** Your `calendar.py` shadows Python's builtin `calendar` module. Other stdlib modules that import `calendar` get YOUR file instead.

**Fix:** Rename to something that doesn't conflict:
- `calendar.py` → `ics_export.py` (our fix) or `ical_gen.py`
- `email.py` → `mail_helper.py`
- `path.py` → `path_utils.py`

**Check before creating:** `python -c "import <name>"` if it returns without error, the name is taken.

**Second-order effect:** Even if YOUR code doesn't import stdlib `calendar`, other modules you import (like `httpx`, `http.cookiejar`) might. So the error appears in seemingly unrelated places.

### Module Imports Break
**Symptom:** `from fx import convert` works in local `python -c` test, returns 500 on Vercel.

**Cause:** Vercel Python serverless runtime resolves `api/` directory imports differently than local Python.

**Fix options (in priority order):**
1. **Inline** — copy the function logic directly into the route handler (proven fix)
2. **Use absolute path** — `sys.path.insert(0, os.path.dirname(__file__))` then `from fx import convert`
3. **Avoid new .py files** — keep everything in `index.py` for Vercel

### Async/Sync Route Mixing
```python
# ❌ Synchronous route calling async method
@app.get("/api/route")
def handler(request: Request):
    body = await request.json()  # TypeError: can't await in sync func

# ✅ Fix: make route async
@app.get("/api/route")
async def handler(request: Request):
    body = await request.json()
```

For routes that don't need `request.json()`, use a Pydantic model:
```python
class MyBody(BaseModel):
    data: str

@app.post("/api/route")
def handler(body: MyBody):   # sync is fine
    return {"ok": body.data}
```

### Multiple Path Parameters
```python
# Works on Vercel:
@app.get("/api/fx/{amount}/{from_curr}/{to_curr}")
# But test immediately after deployment — Vercel middleware can interfere
```

## i18n Sync Rules (Embedded HTML + Translation File)

The app uses a dual i18n system:
- **Server-rendered HTML** in `api/index.py` (Python f-strings with `data-i18n` attributes)
- **Client-side translations** in `static/i18n.js` (JS object keyed by `LANG`)

### Key Names Must Match

When you change a `data-i18n` key in the HTML template, you MUST:
1. Update the same key in `I18N.en`
2. Update the same key in `I18N.zh`
3. grep for any other references to the old key name

**Example mistake:** Changed `data-i18n="heroSubCN"` → `data-i18n="heroSub"` in `page_landing()` but forgot to update `i18n.js` → Chinese mode shows English text for that element.

### English-Native Landing Page Pattern

When the audience is international, server-rendered HTML uses English. Chinese becomes a switch-to option via `data-i18n`.

**Checklist (11 items):**
1. [ ] **Logo** — remove Chinese subtitle (`.name-ch` or inline `<span>`)
2. [ ] **Font** — Latin-first: `'Inter','Noto Sans SC'` not `'Noto Sans SC',...`
3. [ ] **Hero** — compelling English tagline, no Chinese decorative text
4. [ ] **Input placeholder** — English examples (`Beijing 5 days, food + history...`)
5. [ ] **City chips** — English names (`Beijing` not `北京`)
6. [ ] **Hot routes** — English names, understandable descriptions
7. [ ] **Category nav** — English labels (`Food / History / Nature / Cities`)
8. [ ] **Cards** — English titles, English POI names
9. [ ] **Footer** — English
10. [ ] **Button** — action-oriented English (`Plan My Trip`)
11. [ ] **grep all pages** — `熊猫行` may appear in 4+ page headers

## Multi-Page Branding Updates

When removing a Chinese subtitle from the logo, `熊猫行` may appear in multiple places:
- `page_landing()` header
- `page_trips()` header  
- `page_chat()` header
- `page_profile()` header
- CSS rule `.name-ch` (may become dead code, remove)

**Fix:** `grep -r "熊猫行" api/ static/` to find every occurrence, then patch each individually with enough surrounding context to make `old_string` unique. Using `replace_all=True` is risky because occurrences are structurally different (some have trailing elements, some don't).

## Theme Toggle Pattern (Vanilla JS)

### Data-theme Architecture
```css
:root { /* dark theme */ }
[data-theme="light"] { ... }
[data-theme="hongjin"] { ... }
[data-theme="mogreen"] { ... }
[data-theme="qinghua"] { ... }
```

### Toggle Function
```javascript
function toggleTheme() {
  var themes = ['dark', 'light', 'hongjin', 'mogreen', 'qinghua'];
  var cur = document.documentElement.getAttribute('data-theme') || 'dark';
  var next = themes[(themes.indexOf(cur) + 1) % themes.length];
  if (next === 'light') document.body.classList.add('light');
  else document.body.classList.remove('light');
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('vp_theme', next);
}
// Restore on page load
(function() {
  var saved = localStorage.getItem('vp_theme');
  if (saved && saved !== 'dark') {
    if (saved === 'light') document.body.classList.add('light');
    document.documentElement.setAttribute('data-theme', saved);
  }
})();
```

**Important:** `toggleTheme()` must be defined in EVERY JS file loaded by pages that have the theme toggle button (landing.js, chat.js), because the function is called inline via `onclick`.

## Deployment Verification for This Architecture

```bash
# 1. Python import check (catches Column import, syntax errors)
python -c "import sys; sys.path.insert(0,'api'); from index import app; print('OK')"

# 2. Data file syntax check (catches missing commas in dicts)
python -m py_compile data/knowledge/*.py

# 3. Route tests
curl -sL https://site.com/api/fx/100/USD/CNY
curl -sL https://site.com/api/weather/Beijing
```

If a route returns `{"error":"Currency conversion failed"}` even after inlining, check:
- Is the environment variable set in Vercel Dashboard?
- Is the function using `from module import X`? → inline instead
- Does the function use `httpx` with `async` on Vercel? → use sync `httpx.Client` instead
