# Full-Stack Local Dev Reference

> Absorbed from `vercel-fullstack-local-dev` (archived). Covers __API_BASE__ injection, Supabase debugging, VisePanda architecture, and all full-stack-local-dev pitfalls.

## 1. `__API_BASE__` Injection Pattern

### Problem
Production: `fetch("/api/public-config")` → Vercel rewrite → backend
Local dev: `fetch("/api/public-config")` → `localhost:5173/api/public-config` → **404**

### Solution

**Frontend app.js:**
```js
export function apiUrl(path) {
  if (window.__API_BASE__) return `${window.__API_BASE__}${path}`;
  return `/api${path}`;  // production
}
```

**HTML injection (conditioned):**
```html
<script>
  if (location.hostname === "localhost" || location.hostname === "127.0.0.1")
    window.__API_BASE__ = "http://localhost:8000";
</script>
```

**⚠️ CRITICAL:** Never hardcode `__API_BASE__` without hostname check — production users will try to connect to their own localhost:8000 and all API calls fail.

### ⚠️ async loading race condition

Even with correct conditionalization, `fetchPublicConfig()` may not complete before `getSupabase()` runs. Fix with pre-fetch + Promise:

```html
<script>
  let _resolveConfig;
  window.__SUPABASE_CONFIG__ = { supabase_url: "", supabase_anon_key: "" };
  window.__CONFIG_READY__ = new Promise(r => { _resolveConfig = r; });
  (async () => {
    try { /* fetch config */ } catch (_) {}
    _resolveConfig();
  })();
</script>
```

Then in app.js: `if (window.__CONFIG_READY__) await window.__CONFIG_READY__;`

## 2. Alternative Architecture: Server-Rendered HTML

When the `__API_BASE__` pattern accumulates 4+ layers of patches, switch to FastAPI server-side rendering:

```bash
pip install fastapi uvicorn
```

**Structure:**
```
project/
├── api/
│   ├── main.py      # FastAPI + HTML f-string templates
│   └── index.py     # Vercel entry (from main import app)
├── static/          # JS/CSS files (zero f-string escaping)
├── requirements.txt
├── vercel.json      # { "rewrites": [{ "source": "/(.*)", "destination": "/api/index.py" }] }
└── .python-version  # 3.12
```

**Key advantages:**
- No `__API_BASE__` concept — doesn't exist
- No `/api/public-config` fetch — config in HTML
- No module loading race condition
- Single vercel.json rewrite rule

### Supabase config server-side injection
```python
def _supabase_js() -> str:
    return f"""<script>
const SUPABASE_URL = "{SUPABASE_URL}";
const SUPABASE_KEY = "{SUPABASE_ANON_KEY}";
</script>"""
```

### i18n via data-i18n + JS DOM walk
- Static i18n.js with EN/ZH dictionaries
- Elements tagged with `data-i18n="keyName"` 
- Server renders English, JS walks DOM on language switch

### PWA support
- `static/manifest.json`, `static/sw.js`, `static/pwa.js`
- SW registration must be in separate `.js` file — f-string `{}` in SW code causes Python NameError

### JS f-string escaping split threshold
- When main.py exceeds 600 lines
- When single JS change needs 3+ tries due to f-string escaping
- When `patch` tool repeatedly reports `Escape-drift detected`
- Solution: extract JS to `static/` directory, mount with `app.mount("/static", StaticFiles(directory="static"))`

## 3. "Supabase 未配置" Deep Debug

Layered debugging for the most common VisePanda online bug:

**Layer 1 — API reachable?**
```bash
curl https://domain/api/health          # must 200
curl https://domain/api/public-config   # must return supabase_url + anon_key
```

**Layer 2 — __API_BASE__ leak?** Search all HTML files for `__API_BASE` — ensure conditional.

**Layer 3 — Async race?** Pre-fetch config with Promise sync (see section 1 above).

**Layer 4 — OAuth callback URL?** Supabase Dashboard → Authentication → URL Configuration.

## 4. VisePanda Project Reference

- v1 (old): `~projects/china-travel-agent/` — GitHub `JTCAO515/VisePanda-New`
- v2 (new): `~projects/vise-panda-2/` — single-file, server-rendered HTML
- Model: GLM 5.1 (`https://open.bigmodel.cn/api/paas/v4`)
- Supabase: `jdlinmdhmulozrjeseyc.supabase.co`
- SSH key: `~/.ssh/vise_github`, configured in `~/.ssh/config`

### Backend routers
| Router | File | Endpoints |
|--------|------|-----------|
| planner_router | `backend/app/routers/planner.py` | PUT/GET /trips/{id}/itinerary, GET /shared/{token} |
| stream_router | `backend/app/routers/stream.py` | POST /chat/stream SSE |
| user_center_router | `backend/app/routers/user_center.py` | GET /user/profile, CRUD /user/documents |

### Environment variable fallback (for migration from Vite/Next)
```python
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
```

### Python import pattern for all routers
```python
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth import get_principal
from app.db import get_db
```

## 5. Complex f-string Replacement via Python Script

When `patch` tool fails due to escape-drift (multi-level f-strings with JS `{{}}`), write a temp Python script:

```python
# write_file /tmp/fix_N.py, then python3 /tmp/fix_N.py
f = open('api/main.py', 'r').read()
f = f.replace('old text', 'new text')
open('api/main.py', 'w').write(f)
```

## 6. Git Push in China

- **SSH (recommended):** Port 22 usually unblocked. Configure `~/.ssh/config` with `github.com` + IdentityFile.
- **HTTPS + Token:** `GIT_SSL_NO_VERIFY=1 git push` — ~40% success rate.
- **Retry loop:** `for i in 1..5; do git push && break; sleep 30; done`

## 7. Vercel CLI Deployment

```bash
# Install
npm i -g vercel

# Auth with token (NOT vercel login --token)
vercel link --project <name> --yes --token <token>
vercel deploy --prod --yes --no-color --token <token>
vercel env add KEY production --token <token>
```

**⚠️ China servers cannot curl Vercel sites (IP blocked).** Verify via:
1. `vercel logs` for runtime errors
2. User tests in browser
3. Build logs for import/dependency issues

## 8. Deployment Checklist

1. `GET /api/health` → 200
2. `GET /api/public-config` → 200 with supabase_url + anon_key
3. No red requests in Network panel
4. Sign in with Google doesn't show "Supabase 未配置"
5. Supabase Dashboard → URL Configuration correct

## 9. When to Rewrite Instead of Patch

**Triggers** (any one):
- Same category bug fixed 3+ rounds without root cause
- Architecture defect unfixable via local changes (e.g., `__API_BASE__` scattered across 4+ files)
- Async loading chain fragile enough to need Promise sync/retry/prefetch
- User explicitly says "rewrite the whole project"

**Rewrite flow:**
1. Generate `SPEC.md` with user journeys, tech stack, API endpoints, DB schema, all pitfalls
2. Choose simpler architecture — prefer server-rendered over separated SPA
3. Implement from scratch, don't reference old code
