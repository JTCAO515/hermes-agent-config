# Android Auth Flow — Email + Password

> Pattern from vp-hermes v1.1.0 (2026-06-17). User requested email-only login + admin panel for user management.

## Architecture

```
App Launch
  └─ SplashScreen (800ms) → check SharedPreferences for token
       ├─ Token found → verifyToken() via API
       │    ├─ Valid → MainApp (4 tabs)
       │    └─ Invalid → logout() → AuthScreen
       └─ No token → AuthScreen
            ├─ Login (email + password) → token → saveToken() → MainApp
            └─ Register → Login → MainApp
```

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Token storage | SharedPreferences | Zero deps, < 20 LOC, fits MVP |
| HTTP client | OkHttp (shared from network module) | Already in project, no new deps |
| JSON parser | `org.json` (Android stdlib) | Gson is in `core:network` module, NOT transitively available in `app` module |
| Password flow | email + password, not magic link | Simpler backend (no SMTP), user asked directly |
| Admin detection | First registered user = admin | No separate admin registration flow needed |
| Auth gate | State enum: SPLASH → AUTH → MAIN | Clean Compose `AnimatedContent` transition |

## API Contract

```json
POST /api/auth/register  → {"email":"a@b.com","password":"123456"} → 201 {"user":{...}}
POST /api/auth/login     → {"email":"a@b.com","password":"123456"} → 200 {"token":"...","user":{...}}
GET  /api/auth/me        → Authorization: Bearer <token>           → 200 {"user":{...}}
```

## Repository Pattern

```kotlin
class AuthRepository(private val context: Context) {
    private val prefs = context.getSharedPreferences("vp_auth", Context.MODE_PRIVATE)

    fun saveToken(token: String) { prefs.edit().putString("auth_token", token).apply() }
    fun getToken(): String? = prefs.getString("auth_token", null)
    fun isLoggedIn(): Boolean = getToken() != null
    fun logout() { prefs.edit().clear().apply() }

    suspend fun login(email: String, password: String): Result<String>
    suspend fun register(email: String, password: String): Result<String>
    suspend fun verifyToken(token: String): Result<String>

    companion object {
        fun parseToken(json: String): String?  // JSONObject(json).optString("token")
        fun parseUser(json: String): AuthUser? // JSONObject(json).getJSONObject("user")
    }
}
```

## Common Pitfalls

### ❌ Gson not available in app module

**Symptom:** `AuthRepository.kt:5 Unresolved reference: gson` even though `core:network` module uses Gson.

**Root cause:** Maven dependencies are NOT transitively available across multi-module projects unless explicitly declared as `api` (vs `implementation`). `core:network` declares Gson as `implementation`, so it's only available within that module.

**Fix:** Use `org.json.JSONObject` (Android stdlib) instead of Gson. No dependency needed:

```kotlin
import org.json.JSONObject

// Parse response
val obj = JSONObject(responseBody)
val token = obj.optString("token", "")
val email = obj.getJSONObject("user").optString("email", "")
```

### ❌ Token persistence across app restarts

Always check `isLoggedIn()` + `verifyToken()` on app launch. Don't assume a saved token is still valid — it could have expired on the server side.

### ❌ Login/Register race condition

Don't save token before the API call completes. Wait for the full response, call `parseToken()`, then `saveToken()`. If the API call fails (network, wrong password), the old token (if any) should remain in SharedPreferences.

### ❌ Activity lifecycle + Compose navigation

The auth gate is in `App.kt` (a `@Composable` function, not a NavHost destination). Use `AnimatedContent(targetState = currentScreen)` for the SPLASH → AUTH → MAIN transition. This avoids NavHost complexity for the simple 3-state flow.

## File Structure

```
app/src/main/java/com/visepanda/hermes/
├── data/
│   └── AuthRepository.kt     # Token storage + API calls
├── ui/auth/
│   └── LoginScreen.kt        # Login + Register screen, AuthMode enum
├── App.kt                    # SplashScreen + auth gate + MainApp
```

## Backend (Python, stdlib-only)

The companion backend module (`api/auth.py`) uses:
- `sqlite3` — user database
- `hashlib.sha256(password + salt)` — password hashing
- `uuid.uuid4().hex` — token generation (64 hex chars)
- Token expires in 7 days (`datetime('now', '+604800 seconds')`)
- First user auto-assigned `role = "admin"`
- CORS headers for cross-origin admin panel access

See the separate `references/python-auth-backend-pattern.md` for backend auth module details.
