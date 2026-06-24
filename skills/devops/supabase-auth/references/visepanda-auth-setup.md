# VisePanda Auth 配置记录 (v2)

## 项目信息

- **Repo**: JTCAO515/vise-panda-2
- **部署**: Vercel → https://vise-panda-2.vercel.app
- **目标域名**: go2china.space (被 5 个旧 Vercel 项目占用，需手动解除)
- **数据库**: SQLite → `/tmp/data.sqlite3` (Vercel 可写路径)
- **LLM**: GLM 5.1 (ZhipuAI, `open.bigmodel.cn/api/paas/v4`)

## Auth 架构：4-Tier

Google OAuth (Supabase) → Email/Password (本地) → Phone/SMS (本地) → 游客模式

## Supabase 配置

**项目 ID**: `jdlinmdhmulozrjeseyc` (ap-southeast-1)
**PAT**: `YOUR_SUPABASE_SERVICE_ROLE_KEY` (find in Supabase Dashboard → Settings → API → `service_role` key)
**Site URL**: `https://vise-panda-2.vercel.app`
**重定向白名单**: `https://vise-panda-2.vercel.app/auth/callback,https://vise-panda-2.vercel.app`

**Google OAuth 凭据**:
- Client ID: `717391693553-g7dejd5nfoq76sqcs8h22a7fh3pjel57.apps.googleusercontent.com`
- Secret: `1954f769041553a906f3c4c25944fdb83a1fcd91e45b33331023c9b562314a4f`

## 本地 Email/Password Auth

**后端文件**: `api/index.py`

Token 格式: `email:{user_id}`。密码用 SHA-256 + salt, 格式 `salt:hash`。

**Endpoints**:
- `POST /api/auth/email-signup` — 注册
- `POST /api/auth/email-login` — 登录

**Model**: `EmailUser` (email PK, user_id UUID, password_hash, name, created_at)

## 手机号/SMS Auth (v2)

**后端文件**: `api/index.py` (同上)

Token 格式: `phone:{user_id}`。

**Endpoints**:
- `POST /api/auth/send-code` — 发送 6 位验证码（5 分钟有效）
- `POST /api/auth/phone-login` — 验证码登录/注册

**Models**: `PhoneVerification` (phone PK, code, expires_at, verified) — `PhoneUser` (phone PK, user_id, name)

**SMS 提供商**: 环境变量 `SMS_PROVIDER` — `"console"`(默认,打印到日志) 或 `"aliyun"`(阿里云)

**阿里云短信配置**:
- `ALIYUN_SMS_ACCESS_KEY` / `ALIYUN_SMS_SECRET` — RAM 用户 AccessKey
- `ALIYUN_SMS_SIGN_NAME` — 短信签名
- `ALIYUN_SMS_TEMPLATE_CODE` — 短信模板 ID

## 游客 Fallback

- localStorage: `vp_token`, `vp_user_id`, `vp_email`, `vp_phone`
- Token 格式: `test:{uuid}` / `email:{uuid}` / `phone:{uuid}`
- 环境变量: `AUTH_TEST_BYPASS=true` (Vercel), 判等用 `.lower() in ("1","true","yes")`

## Token 兼容性

| Token 前缀 | 条件 |
|-----------|------|
| `test:` | 需要 `AUTH_TEST_BYPASS=true` |
| `email:` | 真实用户，不需要 bypass |
| `phone:` | 真实用户，不需要 bypass |
| RS256 JWT | Supabase OAuth，不需要 bypass |

## 前端文件

| 文件 | 职责 |
|------|------|
| `static/landing.js` | 登录弹窗 (Google/Email/Guest 三种模式) |
| `static/auth.js` | `/auth/callback` — Supabase OAuth 回调 |
| `static/chat.js` | API 请求携带 token |
| `static/i18n.js` | 中英文翻译 (含登录弹窗字符串) |

## 关键逻辑位置

- `api/index.py:40` — AUTH_TEST_BYPASS 判等
- `api/index.py:123-146` — _get_user_id() 本地 token + Supabase JWT 验证
- `api/index.py:73-87` — 密码哈希函数
- `api/index.py:530-600` — email-signup / email-login 端点
- `static/landing.js` — 登录弹窗核心逻辑

## Supabase 配置

**项目 ID**: `jdlinmdhmulozrjeseyc`（VisePanda New, ap-southeast-1）  
**Site URL**: `https://vise-panda-2.vercel.app`  
**重定向白名单**: `https://vise-panda-2.vercel.app/auth/callback,https://vise-panda-2.vercel.app`

**Google OAuth 凭据**:
- Client ID: `717391693553-g7dejd5nfoq76sqcs8h22a7fh3pjel57.apps.googleusercontent.com`
- Secret: `1954f769041553a906f3c4c25944fdb83a1fcd91e45b33331023c9b562314a4f`

**状态**: Google 已启用，Site URL + 重定向白名单已正确配置（原先是 go2china.space 域名被占用导致的 404）。

## 本地 Auth Fallback

当 Supabase 不可达时（中国网络等），自动降级为本地 auth：

1. 前端生成 `user_{uuid}` 存入 `localStorage.vp_user_id`
2. 生成 `test:{user_id}` token 存入 `localStorage.vp_token`
3. 后端 `AUTH_TEST_BYPASS=true` 环境变量 + 代码：`token.startswith("test:")`
4. 所有请求携带 `Authorization: Bearer test:{user_id}`

**关键代码** (`api/index.py:40`):
```python
AUTH_TEST_BYPASS = os.getenv("AUTH_TEST_BYPASS", "0").lower() in ("1", "true", "yes")
```
注意 Vercel 环境变量值设为 `"true"`，所以判等不能用 `== "1"`。

## 前端文件

- `static/landing.js` — `signIn()`, `signOut()`, `initDirectAuth()`, `updateAuthUI()`
- `static/auth.js` — `/auth/callback` 页面处理 Supabase OAuth 回调 + 本地 fallback
- `static/chat.js` — API 请求时优先读 `localStorage.vp_token`，其次 Supabase session
