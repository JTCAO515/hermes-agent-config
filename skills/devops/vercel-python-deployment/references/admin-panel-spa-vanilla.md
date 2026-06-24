# Admin Panel SPA (Vanilla JS + Python WSGI on Vercel)

> 在 Python WSGI Vercel 项目上构建独立管理后台 SPA 的完整模式。

## 适用场景

- 项目已有用户系统（注册/登录/Chat 等）
- 需要 Dashboard 统计、用户管理、对话/内容审查后台
- 无前端框架，纯 vanilla JS
- 部署在 Vercel Python WSGI

## 架构

```
/admin → Vercel → WSGI app() → 显式路由 → web/admin.html (SPA)
                                   ↓
POST /api/auth/login          → 获取 JWT token
GET  /api/admin/stats         → Dashboard 统计
GET  /api/admin/users         → 用户列表（搜索/筛选/分页）
GET  /api/admin/users/:id     → 用户详情
PATCH /api/admin/users/:id    → 更新用户角色/状态
GET  /api/admin/users/:id/chat → 用户对话列表
GET  /api/admin/chat/:id      → 对话详情（全部消息）
```

## 文件结构

```js
web/
  index.html     // 原有前端（用户端）
  admin.html     // 管理后台 SPA（嵌入式 CSS + JS，单文件）
api/
  index.py       // WSGI handler + 路由
  auth.py        // 认证 + 管理 API
```

## 关键实现模式

### 1. `/admin` 路由（不要依赖自动静态文件）

```python
# ⚠️ _serve_static 不会自动补 .html 后缀
# /admin 路径只会搜索 web/admin（文文件），不会搜 web/admin.html
# 必须显式路由：
if path in ("/admin", "/admin/") and method == "GET":
    return _serve_static(start_response, "admin.html")
```

### 2. 复用用户端 Auth Token

```javascript
// admin.html — 复用已有的 vp_token，同时隔离为 vp_admin_token
var _token = localStorage.getItem('vp_admin_token') || localStorage.getItem('vp_token');
// 登录后专门存 admin token，不干扰用户端登录
localStorage.setItem('vp_admin_token', _token);
```

### 3. 角色中间件（后端）

```python
# 管理 API 需要 ops/admin 角色
check = require_role("ops", "admin")
user = check(environ, start_response)
if user is None:
    return []  # 401 Unauthorized
```

### 4. 种子管理员（数据库初始化）

```python
# init_db() 末尾
admin_email = os.environ.get("ADMIN_EMAIL", "admin@go2china.space")
admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
if existing is None:
    pw_hash, salt = _hash_password(admin_password)
    conn.execute("INSERT INTO users (...) VALUES (..., 'admin', 'active')", ...)
```

### 5. 用户列表查询参数（WSGI Handler）

```python
def handle_admin_users(environ, start_response):
    params = parse_qs(environ.get("QUERY_STRING", ""))
    search = (params.get("search", [""])[0] or "").strip()
    role_filter = params.get("role", [""])[0] or ""
    page = int(params.get("page", ["1"])[0])
    limit = int(params.get("limit", ["50"])[0])
    offset = (page - 1) * limit

    # 动态 WHERE 子句（防 SQL 注入：参数化查询）
    where, bind = [], []
    if search:
        where.append("(email LIKE ? OR display_name LIKE ?)")
        bind.extend([f"%{search}%", f"%{search}%"])
    where_clause = " AND ".join(where) if where else "1=1"
    rows = conn.execute(f"SELECT ... WHERE {where_clause} LIMIT ? OFFSET ?", bind + [limit, offset])
```

## 用户端补充功能

### 聊天查看器（用户端 Chat Viewer）

用户可以在 My Chats modal 中点进对话查看完整消息。模式：

```javascript
// app.js — VP.auth.loadChat()
loadChat: function(convId) {
  fetch('/api/auth/chat/' + convId, {
    headers: {'Authorization': 'Bearer ' + _authToken}
  }).then(function(r){ return r.json(); }).then(function(data){
    // 渲染 messages[].role, .content
    // role=user → 蓝色 accent, role=assistant → 金色 accent
  });
}
```

后端 API（user-facing，按用户 ID 过滤防止越权）：

```python
# auth.py — GET /api/auth/chat/:id
def handle_chat_detail(environ, start_response, conv_id: str):
    user = require_role("user", "ops", "admin")(environ, start_response)
    conv = conn.execute(
        "SELECT ... FROM chat_conversations WHERE id = ? AND user_id = ?",
        (conv_id, user["id"])  # ⚠️ user_id 过滤，只能看自己的
    ).fetchone()
    messages = conn.execute(
        "SELECT role, content, created_at FROM chat_messages WHERE conversation_id = ? ORDER BY created_at",
        (conv_id,)
    ).fetchall()
```

HTML 结构（chats modal 内嵌 viewer，通过 `display:none`/`display:block` 切换）：

```html
<div id="chats-list" class="chats-list">...</div>
<div id="chat-viewer" class="chat-viewer">
  <div class="chat-viewer-back" onclick="VP.auth.backToChatList()">← Back</div>
  <div id="chat-viewer-title" class="chat-viewer-title">Chat</div>
  <div id="chat-messages" class="chat-messages"></div>
</div>
```

CSS 切换逻辑：
```css
.chat-viewer{display:none}
.chat-viewer.active{display:block}
```

### 用户设置（User Settings Modal）

用户菜单新增 Settings，点击弹出独立 modal，支持改 display_name 和 password。

**后端** — POST `/api/auth/update-profile`：

```python
def handle_update_profile(environ, start_response):
    user = require_role("user", "ops", "admin")(environ, start_response)
    data = _read_post(environ)
    updates = []
    if "display_name" in data and data["display_name"]:
        updates.append("display_name = ?")
    if "password" in data and data["password"]:
        pw_hash, salt = _hash_password(data["password"])
        updates.append("password_hash = ?")
        updates.append("salt = ?")
    conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
```

路由注册（放在 Chat routes 和 Admin routes 之间）：

```python
if path == "/api/auth/update-profile" and method == "POST":
    return handle_update_profile(environ, start_response)
```

**前端** — Settings modal 结构（与 auth modal 同模式）：

```html
<div id="settings-modal-overlay" class="modal-overlay auth-modal-overlay hidden">
  <div class="modal-panel settings-modal-panel">
    <input type="text" id="settings-name">
    <input type="password" id="settings-password">
    <input type="password" id="settings-password-confirm">
    <button onclick="VP.auth.saveSettings()">Save Changes</button>
  </div>
</div>
```

用户菜单添加入口（index.html）：

```html
<button onclick="VP.auth.showSettings()">⚙️ Settings</button>
```

## admin.html SPA 结构

| Section | 功能 | 后端 API |
|---------|------|----------|
| 登录页 (login-view) | 邮箱密码登录，检查 role=admin/ops | POST /api/auth/login |
| Dashboard | 4 个统计卡片 + 角色分布 | GET /api/admin/stats |
| Users 列表 | 搜索框 + 角色/状态下拉筛选 + 分页，可点击查看 | GET /api/admin/users?search=&role=&page= |
| 用户详情 | 字段展示 + 角色/状态下拉即时编辑 + 关联对话列表 | GET/PATCH /api/admin/users/:id, GET /api/admin/users/:id/chat |
| Chat Logs | 所有对话列表（跨用户聚合），搜索用户/标题 | GET /api/admin/users + GET /api/admin/users/:id/chat |
| 对话详情 | 消息全文阅读（msg-viewer） | GET /api/admin/chat/:id |

## 常见陷阱

| 陷阱 | 症状 | 修复 |
|------|------|------|
| `/admin` 404 | 文件存在但访问 404 | 添加显式路由，别依赖 `_serve_static` 自动补 `.html` |
| 登录后界面空 | login POST 返回 200，但页面空白 | 检查 admin.html 中 `_user = d.user` 而非 `d.user_id` |
| PATCH 返回 404 | 前端 PATCH `/api/admin/users/:id` 但后端路由不匹配 | WSGI handler 中检查 `startswith("/api/admin/users/") and method == "PATCH"` 顺序 — 要优先于 GET 单用户路由 |
| 搜索框无反应 | 输入文字没触发 API 调用 | query string 用 `encodeURIComponent` 编码，后端用 `parse_qs`（不要用 `urlparse`） |
| SQLite 写失败 | 权限错误 | Vercel Serverless 用 `/tmp/` 路径 |

## 相关技能

- `vercel-python-deployment` — Vercel Python 部署全流程
- `product-management` — 产品需求文档标准
