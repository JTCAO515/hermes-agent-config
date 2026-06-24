# Google OAuth with GIS + stdlib-only Python WSGI on Vercel

> Reference for integrating Google Identity Services (GIS) sign-in with a Python WSGI backend on Vercel Serverless, using zero external pip dependencies.

## Architecture

```
Frontend (GIS library)          Backend (Python stdlib only)
┌──────────────────────┐        ┌───────────────────────────┐
│ Google Sign-In btn   │        │ POST /api/auth/google/login│
│ → Google popup       │───────→│ receives credential (JWT)  │
│ → receives credential│        │ verifies via               │
│ → POST to backend    │        │   tokeninfo endpoint       │
└──────────────────────┘        │   (urllib.request)         │
                                │ creates/logs in user       │
                                │ returns our JWT token      │
                                └───────────────────────────┘
```

## Backend Implementation

### Load GIS library in HTML

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

### Render Google Sign-In button

```html
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID"
     data-context="signin"
     data-ux_mode="popup"
     data-callback="handleGoogleCredential"
     data-auto_prompt="false">
</div>
<div class="g_id_signin"
     data-type="standard"
     data-shape="rectangular"
     data-theme="outline"
     data-text="signin_with"
     data-size="large">
</div>
```

### GIS callback (frontend JS)

```javascript
window.handleGoogleCredential = function(response) {
  if (response && response.credential) {
    fetch('/api/auth/google/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({credential: response.credential})
    }).then(r => r.json()).then(data => {
      localStorage.setItem('vp_token', data.token);
      _updateAuthUI();
    });
  }
};
```

### Backend verification (stdlib only)

```python
def handle_google_login(environ, start_response):
    import urllib.request, json
    data = json.loads(environ["wsgi.input"].read(
        int(environ.get("CONTENT_LENGTH", 0))))
    credential = data.get("credential", "")

    if not credential:
        return _json_error(start_response, "Google credential required")
    if not GOOGLE_CLIENT_ID:
        return _json_error(start_response, "Google login not configured", "503")

    try:
        url = GOOGLE_TOKENINFO_URL + urllib.request.quote(credential, safe='')
        req = urllib.request.Request(url, headers={"User-Agent": "App/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode())

        if payload.get("aud") != GOOGLE_CLIENT_ID:
            return _json_error(start_response, "Token audience mismatch", "401")

        google_id, email, name = payload["sub"], payload["email"].lower(), \
            payload.get("name", "") or payload["email"].split("@")[0]
    except urllib.error.HTTPError as e:
        return _json_error(start_response, f"Google verification failed: {e.code}", "401")
    except Exception as e:
        return _json_error(start_response, f"Error: {str(e)[:100]}", "401")

    # Find or create user in SQLite, generate session token...
```

## Required Env Vars

Set in Vercel Dashboard → Project Settings → Environment Variables:

- `GOOGLE_CLIENT_ID` — OAuth 2.0 Web Client ID from Google Cloud Console

No other env vars needed. The tokeninfo endpoint is public.

## Key Points

- **No pip deps**: Uses `urllib.request` to call Google's `tokeninfo` endpoint directly
- **Audience check**: `payload["aud"] == GOOGLE_CLIENT_ID` prevents token reuse from other apps
- **User linking**: If email exists (from password registration), update `google_id` instead of creating duplicate
- **Authorized JavaScript Origins** (Google Cloud Console): Add `https://yourdomain.com`. DO NOT configure redirect URIs (popup flow doesn't need them)

## User Schema (with Google ID)

```sql
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    salt        TEXT NOT NULL DEFAULT '',
    display_name TEXT NOT NULL DEFAULT '',
    role        TEXT NOT NULL DEFAULT 'user',
    status      TEXT NOT NULL DEFAULT 'active',
    google_id   TEXT DEFAULT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Migration: Adding google_id to Existing Tables

```python
# ALTER TABLE before CREATE INDEX (index will fail if column doesn't exist)
for col, typ in [("google_id", "TEXT DEFAULT NULL"),
                 ("display_name", "TEXT NOT NULL DEFAULT ''"),
                 ("status", "TEXT NOT NULL DEFAULT 'active'")]:
    try:
        conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    except sqlite3.OperationalError:
        pass

# Partial index after columns exist
conn.execute(
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google "
    "ON users(google_id) WHERE google_id IS NOT NULL"
)
```

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `CREATE INDEX` before `ALTER TABLE` | `no such column: google_id` | ALTER TABLE first, CREATE INDEX second (separate `execute()` calls) |
| GIS `async defer` not set | Google button shows but click does nothing | Ensure `async defer` on GIS script tag |
| `urllib.error.HTTPError` not caught | 500 error | Wrap tokeninfo in `try/except urllib.error.HTTPError` |
| Tokeninfo timeout on cold start | 504 | Vercel cold start + network call = ~2-3s total; set client-side timeout > 10s |
| Wrong `aud` check | 401 "Token audience mismatch" | The `aud` field = your Client ID; common copy-paste mistake |
