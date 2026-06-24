# Password Reset Flow (Email-Less Token Pattern)

> For MVP / early-stage products where email sending infrastructure is not yet set up.

## Architecture

```
┌─────────┐  1. Enter email    ┌──────────┐
│  User   │ ──────────────────→│  /forgot  │
│  Modal  │←──────────────────│  API     │
│         │  2. Return token   └──────────┘
│         │   (in API response)     │
│         │                    Generate token
│         │                    Store in password_reset_tokens table
│         │                    1-hour expiry
│         │
│         │  3. Enter token    ┌──────────┐
│         │     + new password →│  /reset  │
│         │←──────────────────│  API     │
│         │  4. "Success"     └──────────┘
└─────────┘                    Validate token
                               Update password
                               Mark token used
```

## Database Table

```sql
CREATE TABLE password_reset_tokens (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    expires_at  TEXT NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_reset_token ON password_reset_tokens(token);
```

## Backend API: Forgot Password

```python
def handle_forgot_password(environ, start_response):
    data = _read_post(environ)
    email = data["email"].strip().lower()
    user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    
    # Always return same response to prevent email enumeration
    response = {"message": "If this email exists, a reset code has been generated."}
    
    if user:
        user_id = user["id"]
        # Invalidate old unused tokens for this user
        conn.execute("UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0", (user_id,))
        
        token = uuid.uuid4().hex[:32]
        expires = (datetime.utcnow() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO password_reset_tokens (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
                     (token_id, user_id, token, expires))
        
        # ⚠️ Only for MVP: return token in response (no email infra)
        # In production, send this via email instead
        response["reset_token"] = token
```

## Backend API: Reset Password

```python
def handle_reset_password(environ, start_response):
    data = _read_post(environ)
    token = data["token"].strip()
    password = data["password"]
    
    row = conn.execute(
        "SELECT id, user_id, expires_at FROM password_reset_tokens WHERE token = ? AND used = 0",
        (token,)
    ).fetchone()
    
    # Validate expiry
    expires = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.utcnow() > expires:
        return {"error": "Reset token has expired"}
    
    # Update password + mark token used
    conn.execute("UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
                 (new_hash, row["user_id"]))
    conn.execute("UPDATE password_reset_tokens SET used = 1 WHERE id = ?", (row["id"],))
```

## Frontend UX (Three Screens)

1. **Login screen** → "Forgot password?" link
2. **Enter email** → call `/forgot-password` → auto-advance to step 3
3. **Enter token + new password + confirm** → call `/reset-password` → success → redirect to login

## Production Upgrade Path

| MVP (email-less) | Production |
|-----------------|------------|
| Return token in API response | Send token via SMTP email |
| Auto-fill token in frontend | User copies token from email |
| Same UI flow | Same UI flow, just token entry is manual |

## Pitfalls

- **Email enumeration**: Always return the same response whether the email exists or not
- **Token reuse**: Mark tokens as `used=1` after successful reset AND when generating a new token
- **Expiry**: 1 hour is standard; longer windows increase security risk
- **Rate limiting**: Consider checking IP-based rate limits on `/forgot-password` to prevent abuse
- **Password validation**: Minimum length (4+ chars) on both client and server

## When to Use This Pattern

- MVP / prototype with no email infrastructure
- Admin can manually give reset codes to users
- Internal tools where all users have direct access to support
- Temporary measure before SMTP integration
