---
name: supabase-auth
description: "Supabase + local email/password + phone/SMS authentication for FastAPI apps — OAuth providers, JWT, redirect URLs, email signup/login, phone/SMS verification, login modal UI, password hashing, multi-mode auth coexistence, China network fallback."
version: 2.0.0
---

# Supabase Authentication 配置 + 本地邮箱登录 + 手机号/SMS 登录

> 多层认证架构：Google OAuth (Supabase) → Email/Password (本地) → Phone/SMS (本地) → 游客模式。
> 针对中国网络优化：无外部 CDN 依赖、动态导入、IP 地理定位自动切语言。

## 前置条件

### Supabase OAuth

需要 **Personal Access Token (PAT)**，在 https://supabase.com/dashboard/account/tokens 生成。

```bash
TOKEN="sbp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
PROJECT="your-project-ref"
```

### 本地邮箱/手机登录

- FastAPI + SQLAlchemy
- 前端纯 vanilla JS（无框架）
- Python 标准库 `hashlib`, `secrets`, `uuid`（零额外依赖）
- 短信 SMS：阿里云（可选）或 Console 模式（开发时用）

---

## 一、Supabase Management API

### 获取当前认证配置

```bash
curl -s "https://api.supabase.com/v1/projects/$PROJECT/config/auth" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 更新认证配置（PATCH）

```bash
curl -s -X PATCH "https://api.supabase.com/v1/projects/$PROJECT/config/auth" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"field_name": "value"}'
```

### 常用配置项

| 字段 | 类型 | 说明 |
|------|------|------|
| `site_url` | string | 站点根 URL，OAuth 回调的基础域 |
| `uri_allow_list` | **string（逗号分隔）** | 允许的重定向 URL。⚠️ 不是 JSON 数组！ |
| `external_google_enabled` | bool | Google 登录开关 |
| `external_google_client_id` | string | Google OAuth Client ID |
| `external_google_secret` | string | Google OAuth Client Secret |
| `disable_signup` | bool | 禁止新用户注册 |

### 配置示例：启用 Google OAuth

```bash
curl -s -X PATCH "https://api.supabase.com/v1/projects/$PROJECT/config/auth" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_url": "https://your-app.vercel.app",
    "uri_allow_list": "https://your-app.vercel.app/auth/callback,https://your-app.vercel.app",
    "external_google_enabled": true,
    "external_google_client_id": "your-client-id",
    "external_google_secret": "your-client-secret"
  }'
```

---

## 二、本地邮箱/密码登录

当 Supabase 不可达时（中国网络常见），用本地后端处理邮箱登录。

### 2.1 Password Hashing

```python
import hashlib
import secrets

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"

def _verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False
```

### 2.2 Database Model

```python
class EmailUser(Base):
    __tablename__ = "email_users"
    email: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=_uid)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
```

### 2.3 API Endpoints

```python
@app.post("/api/auth/email-signup")
def email_signup(body: EmailSignupIn):
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    db = SessionLocal()
    try:
        existing = db.query(EmailUser).filter(EmailUser.email == email).one_or_none()
        if existing:
            raise HTTPException(409, "Email already registered")
        user_id = str(uuid.uuid4())
        eu = EmailUser(email=email, user_id=user_id, password_hash=_hash_password(body.password), name=body.name)
        db.add(eu)
        db.add(User(id=f"email:{user_id}", profile={"email": email, "name": body.name or ""}))
        db.commit()
        return {"token": f"email:{user_id}", "user_id": f"email:{user_id}", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()

@app.post("/api/auth/email-login")
def email_login(body: EmailLoginIn):
    email = body.email.strip().lower()
    db = SessionLocal()
    try:
        eu = db.query(EmailUser).filter(EmailUser.email == email).one_or_none()
        if not eu or not _verify_password(body.password, eu.password_hash):
            raise HTTPException(401, "Invalid email or password")
        return {"token": f"email:{eu.user_id}", "user_id": f"email:{eu.user_id}", "email": email}
    finally:
        db.close()
```

### 2.4 Token Validation

```python
def _get_user_id(request, guest_id):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        # test: tokens are dev bypass (require AUTH_TEST_BYPASS)
        if token.startswith("test:"):
            if AUTH_TEST_BYPASS:
                return token.split(":", 1)[1], "user"
            raise HTTPException(401, "Invalid token")
        # email: and phone: tokens are real user auth
        if token.startswith("email:") or token.startswith("phone:"):
            return token.split(":", 1)[1], "user"
        # Verify Supabase JWT
        # ... existing JWT validation ...
```

---

## 三、手机号/SMS 登录（适用于国内用户）

### 3.1 数据库模型

```python
class PhoneVerification(Base):
    __tablename__ = "phone_verifications"
    phone: Mapped[str] = mapped_column(String, primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified: Mapped[bool] = mapped_column(default=False)

class PhoneUser(Base):
    __tablename__ = "phone_users"
    phone: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=_uid)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
```

### 3.2 SMS Provider Architecture

```python
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "console")
# Aliyun-specific env vars:
ALIYUN_SMS_ACCESS_KEY = os.getenv("ALIYUN_SMS_ACCESS_KEY", "")
ALIYUN_SMS_SECRET = os.getenv("ALIYUN_SMS_SECRET", "")
ALIYUN_SMS_SIGN_NAME = os.getenv("ALIYUN_SMS_SIGN_NAME", "VisePanda")
ALIYUN_SMS_TEMPLATE_CODE = os.getenv("ALIYUN_SMS_TEMPLATE_CODE", "")
```

**Console provider (default)**: just logs the code — use for development:
```
[SMS] Code for +8613800138000: 256265
```

**Aliyun provider**: uses HMAC-SHA1 signed GET request to `dysmsapi.aliyuncs.com`. See `references/aliyun-sms-integration.md` for full implementation.

### 3.3 API Endpoints

```python
@app.post("/api/auth/send-code")
def send_code(body: PhoneSendCodeIn):
    phone = body.phone.strip()
    code = str(random.randint(100000, 999999))
    expires_at = _now() + dt.timedelta(minutes=5)
    # Upsert PhoneVerification record
    db = SessionLocal()
    try:
        existing = db.query(PhoneVerification).filter(PhoneVerification.phone == phone).one_or_none()
        if existing:
            existing.code = code
            existing.expires_at = expires_at
            existing.verified = False
        else:
            db.add(PhoneVerification(phone=phone, code=code, expires_at=expires_at, verified=False))
        db.commit()
    finally:
        db.close()
    ok = _send_sms(phone, code)
    return {"ok": ok, "message": "Code sent" if ok else "SMS failed"}

@app.post("/api/auth/phone-login")
def phone_login(body: PhoneLoginIn):
    phone = body.phone.strip()
    code = body.code.strip()
    pu_user_id = None
    db = SessionLocal()
    try:
        record = db.query(PhoneVerification).filter(
            PhoneVerification.phone == phone,
            PhoneVerification.verified == False
        ).one_or_none()
        if not record:
            raise HTTPException(401, "No verification code found")
        if record.expires_at.replace(tzinfo=dt.timezone.utc) < _now():  # ⚠️ timezone fix
            db.delete(record)
            db.commit()
            raise HTTPException(401, "Code expired")
        if record.code != code:
            raise HTTPException(401, "Invalid code")
        record.verified = True  # One-time use
        # Create or get user
        pu = db.query(PhoneUser).filter(PhoneUser.phone == phone).one_or_none()
        if not pu:
            pu = PhoneUser(phone=phone, user_id=_uid())
            db.add(pu)
            db.add(User(id=f"phone:{pu.user_id}", profile={"phone": phone}))
        db.commit()
        pu_user_id = pu.user_id
    finally:
        db.close()
    return {"token": f"phone:{pu_user_id}", "user_id": f"phone:{pu_user_id}", "phone": phone}
```

### 3.4 Frontend Phone Tab

Login modal third tab. Flow: 选择国家代码 → 输入手机号 → 点击"发送验证码" → 60s 倒计时 → 输入验证码 → 登录。

Key UI elements:
- `<select id="phoneCountryCode">` — 默认 +86，支持 +1/+852/+853/+886/+81/+82/+65
- `<input id="phoneInput" type="tel">` — 手机号输入
- `<button id="phoneSendCodeBtn">` — 发送验证码按钮（带倒计时）
- `<input id="phoneCodeInput" type="text" inputmode="numeric">` — 6位验证码
- `<button id="phoneLoginBtn">` — 登录按钮

---

## 四、Token 格式约定

| Token 前缀 | 来源 | 校验方式 | AUTH_TEST_BYPASS 要求 |
|-----------|------|---------|----------------------|
| `test:` | 游客/匿名 | 本地 token | 需要 |
| `email:` | 邮箱登录 | 本地 token | 不需要（真实用户） |
| `phone:` | 手机登录 | 本地 token | 不需要（真实用户） |
| (RS256 JWT) | Supabase OAuth | Supabase JWKS | 不需要 |

---

## 五、Auth 架构：4-Tier

```
┌──────────────────────────────────────────────────┐
│  Tier 1: Google OAuth (Supabase)  ← 国际用户      │
│     ↓ 如果 Supabase 不可达                           │
│  Tier 2: Email/Password (本地)  ← 国内用户          │
│     ↓ 如果用户不想注册邮箱                            │
│  Tier 3: Phone/SMS (本地)  ← 国内用户首选           │
│     ↓ 如果用户不想登录                                │
│  Tier 4: 游客模式 (匿名 token)  ← 零摩擦体验         │
└──────────────────────────────────────────────────┘
```

Tiers are additive: users can start as guest, then upgrade via email/phone/Google later. Backend accepts any token format.

---

## 六、中国网络优化

### 6.1 移除 esm.sh CDN 依赖

❌ 不要这样（中国网络 esm.sh 超时）：
```html
<script src="https://esm.sh/@supabase/supabase-js@2"></script>
```

✅ 改为按需动态导入：
```javascript
// landing.js / chat.js — 只在用户点击 Google 登录时才加载
async function doGoogleLogin() {
    try {
        const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
        sb = createClient(config.url, config.key);
        await sb.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: ... }});
    } catch(e) {
        // Supabase unavailable — fall through to local auth
        initDirectAuth();
        location.href = '/chat';
    }
}
```

影响范围：
- Landing 页: 移除 `<script>` 标签，Google 登录用 `import()` 按需加载
- Chat 页: 同上 + 如果 `sb` 不可用，跳过 Supabase session 获取，直接走 local token
- Auth callback 页: 保留 CDN 标签（OAuth 回跳时网络必定可用）

### 6.2 IP 地理定位自动切中文

**后端** (`GET /api/locale`):
```python
@app.get("/api/locale")
def get_locale(request: Request):
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip or ip in ("127.0.0.1",) or ip.startswith(("10.", "192.168.")):
        return {"locale": None}
    try:
        r = httpx.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=3)
        if r.json().get("countryCode") == "CN":
            return {"locale": "zh"}
    except Exception:
        pass
    return {"locale": None}
```

**前端**（内联在 HTML head 中）:
```javascript
if (!localStorage.getItem('vp_lang')) {
    fetch('/api/locale').then(r => r.json()).then(d => {
        if (d.locale === 'zh') { localStorage.setItem('vp_lang', 'zh'); location.reload(); }
    }).catch(() => {});
}
```

同时配合 `navigator.language` 检测（`i18n.js` 中已有）：
```javascript
if (!localStorage.getItem('vp_lang')) {
    if (navigator.language.startsWith('zh')) {
        setLang('zh');
    }
}
```

---

## 七、前端登录弹窗

### 7.1 Login Modal (3 tab)

```html
<div id="loginModalOverlay">
  <div class="login-modal-content">
    <!-- Tab bar: Google | 邮箱 | 手机 -->
    <!-- Google tab: "Continue with Google" 按钮 -->
    <!-- Email tab: 邮箱 + 密码输入 + 登录/注册切换 -->
    <!-- Phone tab: 国家代码 + 手机号 + 验证码 + 60s 倒计时 -->
    <!-- Guest: "继续游客模式" (always visible) -->
  </div>
</div>
```

See `references/visepanda-auth-setup.md` for the full VisePanda implementation.

### 7.2 动画 CSS

```css
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes scaleIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
```

---

## 陷阱

### `uri_allow_list` 必须是字符串

```json
// ❌
"uri_allow_list": ["https://...", "https://..."]
// ✅
"uri_allow_list": "https://.../auth/callback,https://..."
```

### SQLite 时区问题

`DateTime(timezone=True)` 在 SQLite 中存储时不带时区，读回时是 offset-naive datetime。需要 `.replace(tzinfo=dt.timezone.utc)` 后再比较：

```python
# ❌ TypeError: can't compare offset-naive and offset-aware
if record.expires_at < _now():

# ✅
if record.expires_at.replace(tzinfo=dt.timezone.utc) < _now():
```

### AUTH_TEST_BYPASS 判等

```python
# ❌ 只接受 "1"
os.getenv("AUTH_TEST_BYPASS", "0") == "1"
# ✅ 接受 "1", "true", "yes"
os.getenv("AUTH_TEST_BYPASS", "0").lower() in ("1", "true", "yes")
```

### 避免 DB session 重复 close

```python
# ❌ except 和 finally 都 close — 双重 close 会报错
try:
    ...
except HTTPException:
    db.close()
    raise
finally:
    db.close()

# ✅ 只用一个 finally
try:
    ...
finally:
    db.close()
```

### 密码最小长度

建议后端校验 ≥ 6 字符，前端也做相同校验。

### f-string 中嵌入 JS

当 Python f-string 包含 JS `{}` 时，需要用 `{{}}` 双花括号转义：

```python
# ❌ SyntaxError
f"...<script>if(x){{y()}}</script>..."
# ✅ 用 {{ }} 包裹每个 JS 块
f"...<script>if(x){{y()}}</script>..."
```

---

## 相关资源

- `references/visepanda-auth-setup.md` — VisePanda 项目完整 auth 配置记录
- `references/aliyun-sms-integration.md` — 阿里云短信 API 完整集成代码
- Supabase Management API: https://supabase.com/docs/reference/api
- ip-api.com: https://ip-api.com/docs/api:json
