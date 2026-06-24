---
name: vp-hermes
description: VP-Hermes project family topology — Web (travel chat SPA) vs APK (admin React SPA), which repo/domain/Vercel project to work on, and deployment chains.
version: 1.0.0
---

# VP-Hermes Project Family

Two separate repos, two separate Vercel deployments, two different domains. **Never confuse them.**

## Project Topology

| Attribute | VP-Hermes-Web | VP-Hermes-APK |
|-----------|---------------|---------------|
| **Purpose** | Travel chat SPA (English-native for foreign tourists) | Android app + Admin React SPA |
| **GitHub** | `JTCAO515/VP-Hermes-Web` | `JTCAO515/vp-hermes-APK` |
| **Vercel** | `vise-panda-2` | *(separate)* |
| **Domain** | `www.go2china.space` | `hermesapp.go2china.space` |
| **Local path** | `~/projects/VP-Hermes-Web/` | `~/projects/VP-Hermes-APK/` |
| **Stack** | Python WSGI (`api/index.py`) + vanilla JS (`web/`) | React Vite SPA (`admin/`) + Android native |
| **vercel.json** | Routes all to `api/index.py` (Python) | Routes `/api/*` to backend `:8001`, else React SPA |

## Deployment Chains

### VP-Hermes-Web (main chat app)
```
GitHub JTCAO515/VP-Hermes-Web → Vercel vise-panda-2 → www.go2china.space
```

### VP-Hermes-APK (admin panel)
```
GitHub JTCAO515/vp-hermes-APK → Vercel (unknown project name) → hermesapp.go2china.space
```

## Which Project to Work On

| If user says... | Work on... |
|----------------|-----------|
| "vp-hermes", "旅行", "travel chat", "VisePanda" | **VP-Hermes-Web** (`~/projects/VP-Hermes-Web/`) |
| "admin", "登录", "管理后台", "用户管理" | **VP-Hermes-APK** (`~/projects/VP-Hermes-APK/admin/`) |
| "apk", "android", "打包" | **VP-Hermes-APK** Android part |

## Related Project Families

- `vp-codex` — Sister project family: VP-Codex-Web (AI-first China travel SPA at `codex.go2china.space`) and VP-Codex-APK (native Android port). Different repos, different domain, different workflow (Codex implements, I QA/report).

## Common Pitfalls

### ❌ Confusing VP-Hermes projects
When user asks for a UI change, ask yourself: *"Is this the travel chat page (Web) or the admin panel (APK)?"*
- Travel chat page = `www.go2china.space` = Web project
- Admin login/panel = `hermesapp.go2china.space` = APK project

### ❌ Working on wrong Vercel domain
- `www.go2china.space` → Web project (vise-panda-2). Push to VP-Hermes-Web repo.
- `hermesapp.go2china.space` → APK project. Push to vp-hermes-APK repo.

### ✅ Auth button visibility bug (Web)
If user says "login button not showing on page", check `web/app.js`:
```javascript
// ❌ Bug: _updateAuthUI() only called when token exists
if (token) {
  fetch('/api/me').then(user => { _updateAuthUI(); });
}
// No else branch → button never shown for unauthenticated users

// ✅ Fix: call unconditionally
if (token) { ... } else { _updateAuthUI(); }
```

### ✅ Version sync (Web)
The frontend overrides the HTML version with the response from `/api/health`. If versions don't match:
1. Update version in `web/index.html` (HTML fallback)
2. Update version in `api/index.py` (`/api/health` endpoint returns `"version": "X.Y.Z"`)
3. Both must match

## English-Native Requirement
All UI text, AI responses, and tool descriptions must be in English. Chinese is only allowed as:
- **Proper nouns in parentheses**: `Forbidden City (故宫)`, `Peking Duck (北京烤鸭)`, `Alipay (支付宝)`
- User input (user is free to type any language)
