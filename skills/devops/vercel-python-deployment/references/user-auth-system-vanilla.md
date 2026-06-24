# User Auth System on Vercel Python (Vanilla JS + WSGI)

> Full user auth system built on Vercel Python (stdlib only) + vanilla JS SPA. Covers: email register/login, password reset, user settings, chat viewer, admin panel, role-based access, UX polish patterns.

## Architecture

```
Vercel (api/index.py — WSGI) ← all requests
    ├── /api/auth/register       ← POST: create user
    ├── /api/auth/login          ← POST: authenticate, return JWT-like token
    ├── /api/auth/me             ← GET: current user info
    ├── /api/auth/chat-history   ← GET: user's conversation list
    ├── /api/auth/chat/:id       ← GET: full conversation messages
    ├── /api/auth/chat/save      ← POST: save conversation
    ├── /api/auth/forgot-password ← POST: generate reset token
    ├── /api/auth/reset-password  ← POST: use token to set new password
    ├── /api/auth/update-profile  ← POST: change display_name, password
    ├── /api/admin/stats          ← GET: dashboard stats (ops/admin)
    ├── /api/admin/users          ← GET: user list with search/filter/page
    ├── /api/admin/users/:id      ← GET/PATCH/DELETE: user detail
    ├── /api/admin/users/:id/chat ← GET: user's conversations
    ├── /api/admin/chat/:id       ← GET: conversation messages
    ├── /admin                    ← GET: admin SPA (mapped explicitly)
    └── /**
```

## Key Patterns

### 1. SQLite on Vercel (/tmp detection)

```python
import os
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
DATA_DIR = THIS_DIR.parent / "data"
_DEFAULT_DB = str(Path("/tmp/users.db") if os.environ.get("VERCEL") else DATA_DIR / "users.db")
DB_PATH = Path(os.environ.get("AUTH_DB_PATH", _DEFAULT_DB))
```

### 2. Token-based session (no JWT library)

```python
import uuid

def _generate_token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex  # 64 hex chars

def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = uuid.uuid4().hex[:16]
    h = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return h, salt
```

### 3. Role-based middleware

```python
def require_role(*roles):
    """Returns a middleware checker. Usage: check = require_role('admin')"""
    def _check(environ, start_response):
        token = _extract_token(environ)
        user = _get_user_from_token(token)
        if not user:
            _json_error(start_response, "Authentication required", "401 Unauthorized")
            return None
        if user["role"] not in roles:
            _json_error(start_response, "Insufficient permissions", "403 Forbidden")
            return None
        return user
    return _check
```

Usage in routing:
```python
check = require_role("ops", "admin")
user = check(environ, start_response)
if user is None:
    return []  # middleware already wrote the response
```

### 4. Password Reset Flow (Token-based, no email required)

**Backend:** Generate a UUID token, store in `password_reset_tokens` table with 1h expiry. Return the token in the API response (in production, email it).

```python
# Table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TEXT NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
)

# Forgot: generate token (1h expiry)
token = uuid.uuid4().hex[:32]
expires = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

# Reset: validate token, check expiry, update password, mark used
```

**Frontend:** Three-step form flow:
1. Login form → "Forgot password?" link
2. Step 1: Enter email → API call → receive reset code
3. Step 2: Enter reset code + new password + confirm → API call → redirect to login

### 5. Admin SPA (Vanilla JS)

Standalone HTML page at `/admin` with its own auth check. Must be explicitly mapped in the WSGI router because `_serve_static` doesn't add `.html` extension:

```python
# In app():
if path in ("/admin", "/admin/") and method == "GET":
    return _serve_static(start_response, "admin.html")  # explicit file name
```

Admin panel structure:
- Dashboard tab: stats (users, conversations, roles breakdown)
- Users tab: search+filter+paginated list, click for detail/edit
- Chat Logs tab: browse all user conversations, click to view messages

### 6. User Settings (Update Profile)

```python
def handle_update_profile(environ, start_response):
    # Authentication + update display_name and/or password
    data = _read_post(environ)
    updates = []
    params = []
    
    if "display_name" in data and data["display_name"]:
        updates.append("display_name = ?")
        params.append(data["display_name"].strip())
    
    if "password" in data and data["password"]:
        pw_hash, salt = _hash_password(data["password"])
        updates.append("password_hash = ?")
        params.append(pw_hash)
        updates.append("salt = ?")
        params.append(salt)
    
    updates.append("updated_at = datetime('now')")
    params.append(user["id"])
    
    conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
```

### 7. Query String Parsing (WSGI Pitfall)

**⚠️ Critical:** `environ.get("QUERY_STRING")` returns raw `"key=value&..."` (no `?` prefix). DO NOT use `urlparse()`:

```python
# ❌ WRONG: qs will be empty
from urllib.parse import urlparse, parse_qs
qs = parse_qs(urlparse(environ.get("QUERY_STRING", "")).query)

# ✅ CORRECT: parse_qs handles raw query string directly
from urllib.parse import parse_qs
qs = parse_qs(environ.get("QUERY_STRING", ""))
```

### 8. Modal State Management (Vanilla JS)

Multiple auth states in one modal, shown/hidden by class:
```html
<div id="auth-login-form" class="auth-form">...</div>
<div id="auth-register-form" class="auth-form hidden">...</div>
<div id="auth-forgot-form" class="auth-form hidden">...</div>
<div id="auth-reset-form" class="auth-form hidden">...</div>
<div id="auth-success" class="auth-form hidden">...</div>
```

JS functions toggle visibility. Backtrack navigation: each form has a "← Back to Sign In" link.

### 9. Click-Outside-to-Close Dropdown

```javascript
toggleMenu: function() {
  var dd = document.getElementById('user-dropdown');
  dd.classList.toggle('hidden');
  if (!dd.classList.contains('hidden')) {
    setTimeout(function(){
      document.addEventListener('click', VP.auth._closeDropdownOutside);
    }, 0);
  }
},

_closeDropdownOutside: function(e) {
  var dd = document.getElementById('user-dropdown');
  var avatar = document.querySelector('.user-avatar');
  if (dd && !dd.contains(e.target) && avatar && !avatar.contains(e.target)) {
    dd.classList.add('hidden');
    document.removeEventListener('click', VP.auth._closeDropdownOutside);
  }
},
```

### 10. Enter Key Submission

Add `onkeydown` to input elements:
```html
<input type="password" id="login-password" 
       onkeydown="if(event.key==='Enter')VP.auth.login()">
```

## Database Schema

```sql
CREATE TABLE users (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL DEFAULT '',
    salt            TEXT NOT NULL DEFAULT '',
    display_name    TEXT NOT NULL DEFAULT '',
    role            TEXT NOT NULL DEFAULT 'user',       -- user | ops | admin
    status          TEXT NOT NULL DEFAULT 'active',     -- active | disabled | pending
    google_id       TEXT DEFAULT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE sessions (
    token       TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL
);

CREATE TABLE chat_conversations (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL DEFAULT '',
    message_count   INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE chat_messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,           -- user | assistant
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE password_reset_tokens (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TEXT NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Seed Admin User

Create on init (safe to run repeatedly):
```python
admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
existing = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
if existing is None:
    pw_hash, salt = _hash_password(admin_password)
    admin_id = uuid.uuid4().hex[:16]
    conn.execute(
        "INSERT INTO users (id, email, password_hash, salt, display_name, role, status) VALUES (?, ?, ?, ?, ?, 'admin', 'active')",
        (admin_id, admin_email, pw_hash, salt, "Admin")
    )
```

## UX Patterns Summary

| Pattern | Implementation |
|---------|---------------|
| Enter key submit | `onkeydown="if(event.key==='Enter')fn()"` on input |
| Click-outside close | Event listener on document, remove after close |
| Modal state machine | Multiple form divs, toggle hidden class |
| Chat viewer | Messages fetched async, displayed with role colors |
| Pagination | `page` + `limit` + `offset` query params, total count |
| Search debounce | `setTimeout` 300ms on input change |
| Avatar initials | First char of display_name or email |
