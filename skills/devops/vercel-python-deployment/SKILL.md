---
name: vercel-python-deployment
description: 部署 Python 项目到 Vercel Serverless。含 FastAPI/WSGI/raw handler 三种模式、vercel.json 配置、FUNCTION_INVOCATION_FAILED 调试方法。
---

# Vercel Python 部署规范

> 本技能是 Vercel Python 生态的**统一入口**。涵盖：Python 项目部署到 Vercel Serverless、全栈本地开发、FUNCTION_INVOCATION_FAILED 调试、vercel.json 配置、Supabase 集成、前端 API 代理等问题。吸收了 `vercel-fullstack-local-dev`（已归档）。

## Section A — 纯后端 Python 部署

见下方 1-7 节（FastAPI/WSGI/handler 模式、requirements.txt 锁定、调试方法论）。

## Section B — 全栈本地开发（含前端 + API 代理）

> 吸收自 `vercel-fullstack-local-dev`（已归档）。当用户说\"本地跑不起来\"、\"前端调不到后端\"、\"/api 路由 404\" 时，优先查阅 `references/fullstack-local-dev.md`。

### 核心问题

生产环境：前端 `fetch("/api/xxx")` → Vercel rewrite → 后端处理
本地开发：前端 `fetch("/api/xxx")` → `localhost:5173/api/xxx` → **404**

### 解决模式：`__API_BASE__` 注入

```html
<!-- 仅在 localhost 时注入 -->
<script>
  if (location.hostname === "localhost" || location.hostname === "127.0.0.1")
    window.__API_BASE__ = "http://localhost:8000";
</script>
```

### 替代架构：后端渲染 HTML

当 `__API_BASE__` 模式出现 4+ 层补丁时，切换到 FastAPI 直接渲染 HTML（f-string 模板）。优势：
- 无 `__API_BASE__` 概念
- 无 vercel.json 繁重 rewrite 列表 — `"/(.*)" → "/api/index.py"` 一条搞定
- Supabase 配置在服务端注入，前端零异步获取
- 参考 `references/fullstack-local-dev.md` §"替代架构：后端渲染 HTML"

## Section D — 混合部署模式（静态前端 + VPS API 代理）

> **适用场景**：当应用需要在 Vercel 上展示前端界面，但后端需要持久化运行（文件系统写入、WebSocket、SQLite 等 Serverless 不支持的功能）时使用。前端静态文件部署到 Vercel，API 请求通过 vercel.json rewrites 反向代理到 VPS 后端。

Python stdlib 零依赖系统数据 API 模板 → `references/python-stdlib-system-api.md`。
Cloudflared Tunnel 备用方案（端口受限时使用）→ `references/cloudflared-tunnel.md`。

### 架构图

```
Browser → hermes.jtcao.space/ → Vercel Edge (CDN)
                │
                ├── / (index.html)          → 静态文件（Vercel 直接 serve）
                ├── /some-page              → 静态文件 / SPA 路由
                ├── /api/*                  → Vercel rewrite → VPS :8503 (Express/Node.js)
                └── /api/hermes/*           → Vercel rewrite → VPS :8504 (Python stdlib)

VPS (64.176.82.81) — PM2 持久化服务：
  ├── mission-control (:8503) — Node.js Express + WebSocket + 文件系统
  └── hermes-api (:8504) — Python HTTPServer (stdlib only)
```

### vercel.json 配置

```json
{
  "version": 2,
  "builds": [
    {
      "src": "**/*",
      "use": "@vercel/static"
    }
  ],
  "rewrites": [
    { "source": "/api/hermes/(.*)", "destination": "http://64.176.82.81:8504/api/hermes/$1" },
    { "source": "/api/(.*)", "destination": "http://64.176.82.81:8503/api/$1" },
    { "source": "/hermes", "destination": "/hermes.html" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### 优势

- **无 CORS 问题**：浏览器看所有请求都是同一域名（same-origin），rewrite 在 Vercel Edge 端透明完成
- **CDN 加速前端**：静态文件走 Vercel 全球 CDN
- **持久化后端**：VPS 上运行 Express/Python 等有状态服务，通过 PM2 管理
- **分层代理**：可以按路径将 API 请求分发到不同的 VPS 端口和服务

### 局限性

- WebSocket 不能通过 Vercel rewrites 代理（Vercel 不支持 WS 反向代理）
- VPS 需要公网 IP 且相关端口开放（Vultr 新加坡防火墙需开放指定端口）
- 前端 JS 中如果用 `new WebSocket()` 自动连 `wss://domain/ws`，会握手失败 — 要么 fallback 到轮询，要么直接连 VPS

### 部署流程

1. VPS 端：PM2 启动后端服务（见 `references/pm2-service-management.md`）
2. 前端端：`git push origin main` → Vercel 自动部署（GitHub 集成）
3. Vercel 配域名：Vercel Dashboard → Project → Domains → `yourdomain.com`
4. 验证：访问 `https://yourdomain.com/` 检查前端，检查 `/api/*` 是否成功代理

### 陷阱

| 陷阱 | 症状 | 修复 |
|------|------|------|
| Vercel rewrite 到的 VPS IP 写死 | VPS 换 IP 后全挂 | 用固定公网 IP（Vultr 支持 Reserved IP） |
| VPS 端口被防火墙拦截 | `/api/*` 返回 502 | Vultr 防火墙开对应端口，或用 cloudflared tunnel 做反向代理（见 `references/cloudflared-tunnel.md`） |
| 前端用了 WebSocket（new WebSocket） | WebSocket 连不上 | 前端 fallback 轮询，或前端直接连 `ws://VPS_IP:PORT`（但失去 same-origin 优势） |
| 本地开发时 API 请求被 proxy 指向线上 | 本地前端调线上 API | 只在 `vercel.json` 配线上 rewrite；本地用 `.env.development` 或 `window.API_BASE` 覆盖 |
| PDF/大文件混在静态目录中 | git push 超时（pack-objects 太慢） | 从 Vercel 部署目录移除大文件，用 `git rm` 后 commit + push |
| **`http_proxy` 环境变量干扰 localhost 测试** | 服务器设了 `http_proxy=http://127.0.0.1:10809` 做科学上网，导致 `curl http://localhost:3000` 走代理 → 503 Service Unavailable | 所有本地测试用 `curl --noproxy '*' http://localhost:PORT/...` 绕过。PM2 启动的服务不受影响。`git push` HTTPS 也可能受代理干扰 → 换 SSH push |

详细架构说明及各组件的具体配置 → `references/vercel-hybrid-deploy.md`

## Section C — 常见陷阱

| 陷阱 | 症状 | 修复 |
|------|------|------|
| __API_BASE__ 硬编码泄漏线上 | 线上 API 全挂 | 所有 HTML 的 `__API_BASE__` 必须加 hostname 条件判断 |
| SQLite 在 Vercel 只读文件系统 | 500 FUNCTION_INVOCATION_FAILED | **推荐方案**：代码自动检测 `VERCEL` 环境变量，自动切到 `/tmp/`：<br>```python<br>_DEFAULT_DB = str(Path("/tmp/users.db") if os.environ.get("VERCEL") else DATA_DIR / "users.db")<br>DB_PATH = Path(os.environ.get("AUTH_DB_PATH", _DEFAULT_DB))<br>```<br>**备选方案**：在 Vercel Dashboard 设置 `AUTH_DB_PATH=/tmp/users.db` 环境变量 |
| Vercel uv 构建器找不到依赖 | 构建日志无 manifest | 根目录放 `requirements.txt` + `.python-version` |
| 前端异步加载竞态 | "/api/public-config" 正常但弹"未配置" | 预取配置 + Promise 同步（见 ref） |
| commit author 不匹配 Vercel 账号 | Vercel 部署被拒绝：\n\"The commit author email is not a valid email address\" | 1. `git config user.email \"verified@email.com\"`\n2. `git commit --amend --author=\"Name <email>\" --no-edit`\n修复已有 commit 的 author\n3. `git push --force` 推送修复后的 commit |
| vercel domains rm 交互式阻塞 | 域名无法移除 | 登录 Vercel Dashboard 手动移除 |

详细内容及 VisePanda 项目参考 → `references/fullstack-local-dev.md`。

---

# Vercel Python 部署规范

## 适用场景

- Python Web 应用部署到 Vercel Serverless
- 排查 FUNCTION_INVOCATION_FAILED、404 路由错误、静态文件不生效

---

## 1. 项目结构与模式选择

三种模式从高到低优先级排列。优先用 FastAPI 双文件模式，只有它彻底失败时才降级。

### 降级路径

```
FastAPI 双文件 (GMA模式) → FastAPI 单文件 → WSGI app → 原始 handler
        1                       2              3             4
```

**2026-06 关键发现**：第 4 步（`handler(event, context)`）在较新 Vercel 上**已无法被静态扫描器识别**。即使 handler 清晰定义在行 48、文件仅 2 行，Vercel 依然报 \"Could not find a top-level handler\"。**遇到时直接跳到第 3 步（WSGI app）。WSGI 模式在 Vercel 上 100% 可靠。**

---

### 模式 1：FastAPI 双文件（优先使用）

```
project-root/
├── api/
│   ├── __init__.py          # 空文件
│   └── index.py             # 薄入口，仅 re-export
│   └── main.py              # 真正的 FastAPI 应用
├── your_package/            # Python 包在项目根目录（NOT src/）
├── requirements.txt
└── vercel.json
```

**api/index.py**:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from api.main import app
```

**api/main.py**:
```python
from fastapi import FastAPI, Response
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = ROOT / "web"

app = FastAPI(title="...", version="...")

@app.get("/")
async def index():
    return Response((WEB_ROOT / "index.html").read_bytes(), media_type="text/html")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

### 模式 2：FastAPI 单文件（备选）

当双文件 re-export 在 Vercel 不稳定时（所有端点 FUNCTION_INVOCATION_FAILED 且非依赖问题），合进一个文件：

```python
"""Self-contained FastAPI app."""
import sys
from pathlib import Path
from fastapi import FastAPI, Response

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from your_package import your_fn
WEB_ROOT = ROOT / "web"

app = FastAPI(...)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

### 模式 3：WSGI app（零依赖）

当 FastAPI/ASGI 在 Vercel 上反复失败时使用。详见第 5 节。

### 模式 4：原始 handler（最后一搏）

`handler(event, context)` 模式。Vercel 最新版本可能不支持，详见第 6 节。

---

## 2. vercel.json 配置

```json
{
  "builds": [{
    "src": "api/index.py",
    "use": "@vercel/python",
    "config": {
      "maxLambdaSize": "50mb",
      "runtime": "python3.11"
    }
  }],
  "routes": [
    { "src": "/(.*)", "dest": "api/index.py" }
  ]
}
```

**要点**：
- routes：**只用一个 `/(.*)`**，让应用内部处理路由
- maxLambdaSize：纯 FastAPI+Pydantic 建议 ≥50mb（15mb 边缘危险）
- runtime：指定 python3.11 或 python3.12

---

## 3. requirements.txt

- **纯标准库项目**（模式 3/4）：留空或注释
- **FastAPI 项目**：必须锁定版本

### ⚠️ 版本锁定策略

**关键教训**：`pydantic>=2.0.0` → pip 安装最新 pydantic-core（Rust 二进制）→ 如果其 glibc 要求高于 Lambda 的 2.26 → 运行时动态库加载失败 → FUNCTION_INVOCATION_FAILED。

**已知能用的版本**（2026-06 已验证）：
```
fastapi==0.115.6
pydantic==2.10.6
```

**原则**：
- 用 `==` 完全锁定版本
- 部署前在干净 venv 验证：`python3 -m venv /tmp/test && /tmp/test/bin/pip install -q -r requirements.txt`

---

## 4. 调试方法论

### 4.1 增量诊断链

遇到 FUNCTION_INVOCATION_FAILED 时，按此链条逐级收窄问题范围：

```
┌─ 本地能跑吗？
│  ├─ ❌ → 修本地代码
│  └─ ✅ → 看 Vercel Build Logs
│
├─ Build Logs 有错误？
│  ├─ ❌ pip install 失败 → 检查 requirements.txt / 版本兼容性
│  ├─ ❌ "Could not find handler" → 换模式（见 4.2）
│  └─ ✅ Build 成功但运行时报 → 检查 import 链路
│
├─ 2 行 WSGI 能跑吗？（见 4.3）
│  ├─ ❌ → 项目级配置问题（见 4.4）
│  └─ ✅ → 代码结构问题
│
└─ 用完整 WSGI 重写（见第 5 节）
```

### 4.2 "Could not find a top-level app/handler"

**2026-06 核心发现**：`handler(event, context)` 原始模式在较新 `@vercel/python` builder 中可能已被移除静态扫描支持。表现：

- handler 明确定义在第 48 行
- 文件仅 2 行，无外部 import
- Vercel 依然报 "Could not find a top-level handler"

**排查步骤**：
1. 换成 WSGI `def app(environ, start_response)` 测试
2. WSGI 成功后用完整 WSGI 实现
3. 如果 WSGI 也失败 → 项目级配置问题（见 4.4）

### 4.3 2 行 WSGI 测试（最小诊断）

```python
def app(environ, start_response):
    start_response("200 OK", [("Content-Type", "application/json")])
    return [b'{"status":"ok"}']
```

写入 `api/index.py`，push 部署后 curl。
- ✅ `{"status":"ok"}` → Vercel 基本 Python 正常，可以构建完整应用
- ❌ 仍报错 → 项目级配置问题（见 4.4）

### 4.4 项目级配置检查

如果 2 行 WSGI 也失败：

**Vercel Dashboard → Project Settings → General → Framework Preset**
- ✅ 必须是 **"Other"** 或 **"Python"**
- ❌ 如果设成 Next.js/React → 删项目重新 Import，选 "Other"

**构建缓存**：Dashboard → Deployments → ⋯ → "Clear Build Cache & Deploy"

### 4.5 git push HTTPS 超时

```bash
# 切换 SSH
git remote set-url origin git@github.com:user/repo.git
git push origin master
```

---

## 5. WSGI 应用模板（零依赖）

### 适用场景

- FastAPI/ASGI 在 Vercel 上反复失败
- 希望完全消除 pip 依赖
- Vercel 对 ASGI 检测不稳定

### 结构

```
project-root/
├── api/
│   ├── __init__.py          # 必须存在，空文件
│   └── index.py             # WSGI app + 全部逻辑
├── data/
├── configs/
└── web/
```

### 完整模板

```python
"""
WSGI application for Vercel — zero external dependencies.
"""
import json
from pathlib import Path
from datetime import datetime

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_DATA = str(_ROOT / "data" / "dataset.json")
_CONFIG = str(_ROOT / "configs" / "config.json")
_WEB = _ROOT / "web"

_CT = {".js": "application/javascript", ".css": "text/css", ".html": "text/html",
       ".json": "application/json", ".svg": "image/svg+xml"}


def _json(start, data, status="200 OK"):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    start(status, [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]


def _static(start, path):
    rel = "index.html" if path in ("", "/") else path.lstrip("/")
    fp = _WEB / rel
    if not fp.exists():
        return None
    b = fp.read_bytes()
    start("200 OK", [("Content-Type", _CT.get(fp.suffix, "application/octet-stream")),
                     ("Content-Length", str(len(b)))])
    return [b]


def _body(environ):
    length = int(environ.get("CONTENT_LENGTH", 0))
    if length <= 0:
        return {}
    return json.loads(environ["wsgi.input"].read(length))


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/health":
        return _json(start_response, {"status": "ok"})

    if path == "/api/config" and method == "GET":
        try:
            return _json(start_response, json.load(open(_CONFIG)))
        except Exception as e:
            return _json(start_response, {"error": str(e)}, "500 Internal Server Error")

    if path == "/api/backtest":
        try:
            params = _body(environ)
            result = run_backtest(_DATA, _CONFIG, params.get("config_overrides", {}))
            return _json(start_response, {"report": result})
        except Exception as e:
            return _json(start_response, {"error": str(e)}, "500 Internal Server Error")

    r = _static(start_response, path)
    if r:
        return r
    return _json(start_response, {"error": "Not Found"}, "404 Not Found")


# ── Algorithm code (放在这里，运行时才调用) ──
def run_backtest(data_path, config_path, overrides=None):
    # 所有业务逻辑内联
    pass
```

### 注意事项

1. `api/__init__.py` **必须存在且为空** — 不要 import 任何东西
2. 路径计算：`Path(__file__).resolve().parent.parent` → `/var/task/`
3. 文件路径传给 `open()` 或 `json.load()` 时用 **`str(path)`** 显式转换
4. 不需要 `requirements.txt` — 纯标准库
5. `maxLambdaSize` 可降到 10mb — 纯标准库 < 1MB
6. POST body 读取：`environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))`
7. WSGI body 必须返回 **bytes list**：`[b'...']`
8. **⚠️ QUERY STRING 解析陷阱**：`environ.get("QUERY_STRING","")` 返回的原始字符串是 `"key=value&..."`（无 `?` 前缀）。**不要用 `urlparse(qs).query`**：

   ```python
   # ❌ 错误：urlparse 把整个字符串当 path，.query 返回 ""
   from urllib.parse import parse_qs, urlparse
   qs = parse_qs(urlparse(environ.get("QUERY_STRING", "")).query)  # qs == {}
   
   # ✅ 正确：直接用 parse_qs 处理 raw query string
   from urllib.parse import parse_qs
   qs = parse_qs(environ.get("QUERY_STRING", ""))  # qs == {"key": ["value"]}
   ```

   这个 bug 的特征：API 端点所有 query 参数都读不到，但 `environ.get("QUERY_STRING")` 输出看起来正常。调试时先加 `_sys.stderr.write(f"[HANDLER] qs={dict(qs)}\n")` 确认 qs 是否为空。

### 进阶：PWA 支持

详见 `references/pwa-vercel-deployment.md`：

- manifest.json、sw.js、icon.svg 三件套
- Serve from root path (browser restriction)
- Register SW in client-side JS

### 进阶：Vercel 模块级缓存

详见 `references/module-level-caching.md`：

- 利用 Lambda 热调用间模块变量持久性做内存缓存
- Cache warming 模式（主端点预填充缓存）
- 适用场景 & 约束

### 进阶：文件备份预计算缓存（File-Backed Precompute Cache）

详见 `references/file-backed-precompute-cache.md`：

- **什么时候需要**：Vercel 冷启动 + 重计算（Poisson 模型等）→ 10s 超时
- **解决**：预计算结果写入 JSON → API 从文件读而非重新计算
- **效果**：Portfolio API ~8s → ~0.06s，冷启动 100% 正常工作
- **关键陷阱**: 字段名兼容性（`team_a_win` vs `home_win`）、独立市场赔率计算
- **适用场景**: 数据预计算一次、多次读取、冷启动敏感的项目

### 进阶：Admin Panel SPA（Vanilla JS）

详见 `references/admin-panel-spa-vanilla.md`：

- 在 Python WSGI Vercel 项目上嵌入独立管理后台 SPA
- `/admin` 路由需要**显式 map**（`_serve_static` 不自动补 `.html`）
- 角色中间件、种子管理员、CRUD 用户 API、对话审查
- 纯 vanilla JS，无框架依赖

### 进阶：User Auth System（账户/密码重置/设置/聊天查看）

详见 `references/user-auth-system-vanilla.md`：

- 完整的用户系统：注册、登录、密码重置（token 式 2 步 UI）、修改资料
- Vercel SQLite 路径检测、角色权限中间件、Query string 解析陷阱
- Vanilla JS 模态状态机、富文本聊天查看器、点击外部关闭下拉菜单
- 全套数据库 Schema（users/sessions/chat/password_reset_tokens）
- 种子管理员创建模式、Enter 键提交模式

### 进阶：LLM API Proxy（stdlib-only）

详见 `references/llm-api-proxy-stdlib.md`：

- 用 `urllib.request` 调 DeepSeek/OpenAI API（零 pip 依赖）
- Context injection：每次请求重建 system prompt（读本地 JSON）
- 环境变量 `DEEPSEEK_API_KEY` + `DEEPSEEK_MODEL`（Vercel Dashboard 配置）
- 非流式 response 模式

### 进阶：SSE Streaming 超时诊断（Vercel Hobby 10s 限制）

详见 `references/sse-streaming-timeout-vercel.md`：

- **症状**：VisePanda 式 SSE chat 间歇性 "Connection error"，后端 curl 测试正常
- **根因**：Vercel Hobby 10s 超时限制 + 冷启动 3-5s + LLM API 2-8s = 容易超
- **两个错误路径**：`!resp.ok`（服务端错误）vs `catch`（网络中断/超时）
- **诊断**：curl 时序测试区分后端 vs 前端问题
- **修复**：强制重部署清除 + 前端 Retry 按钮

### 进阶：Frontend SPA "UI Dead" 诊断（HTML 渲染但 JS 未执行）

详见 `references/frontend-spa-dead-ui.md`：

- **症状**：用户说"抽屉、图片、tab 都没加载出来" — HTML 可见但交互无响应
- **三个根因**（按检查顺序）：
  1. 外部同步脚本（unpkg.com Leaflet.js）阻塞 `/app.js` 加载 — 最常见
  2. 裸域名→www 的 307 重定向影响所有资源
  3. JS 解析时 SyntaxError
- **诊断**：独立测试每个外部资源、检查重定向链、验证 JS 语法
### 与 FastAPI 对比

| 维度 | FastAPI | WSGI app |
|------|---------|----------|
| Vercel 检测 | ⚠️ 有时失败 | ✅ 可靠 |
| 路由 | @app.get() 装饰器 | 手动 if/elif |
| 请求解析 | Pydantic 模型 | 手动 json.loads |
| 静态文件 | FileResponse | 手动 read_bytes |
| 依赖 | fastapi + pydantic | 无 |
| 代码行数 | 较少 | 中等 |

---

## 6. 核选项：原始 handler(event, context)

### 风险提示

**2026-06 实测**：Vercel 最新 `@vercel/python` builder 可能已停止对 `handler(event, context)` 模式的静态扫描支持。即使 handler 定义在第 48 行、文件仅 2 行，构建阶段仍报 "Could not find a top-level handler"。

**优先尝试 WSGI 模式（第 5 节）而非此模式**。

### 模板

```python
"""Vercel native handler — single file, zero deps."""
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_DATA = str(_ROOT / "data" / "dataset.json")
_WEB = _ROOT / "web"
_CT = {".js": "application/javascript", ".css": "text/css", ".html": "text/html"}


def _js(data, status=200):
    return {"statusCode": status, "headers": {"content-type": "application/json"},
            "body": json.dumps(data, ensure_ascii=False)}


def _static(path):
    rel = "index.html" if path in ("", "/") else path.lstrip("/")
    fp = _WEB / rel
    if not fp.exists():
        return None
    ct = _CT.get(fp.suffix, "application/octet-stream")
    b = fp.read_bytes()
    return {"statusCode": 200, "headers": {"content-type": ct},
            "body": b.decode("utf-8") if fp.suffix in _CT else b.hex(),
            "encoding": "utf-8" if fp.suffix in _CT else "base64"}


# handler 必须在文件前 100 行
def handler(event, context):
    path = event.get("path", "/")

    if path == "/api/health":
        return _js({"status": "ok"})

    r = _static(path)
    if r:
        return r
    return _js({"error": "Not Found"}, 404)


# 算法代码放在 handler 下面
```

### 要点
1. handler 必须在文件前 100 行
2. api/__init__.py 不可省略（即使空）
3. 返回格式必须正确：`{"statusCode": N, "headers": {...}, "body": "..."}`
4. 二进制文件用 `isBase64Encoded: true` + body.hex()

---

## 7. 已知陷阱汇总

- **包不要放 `src/`**：Python 包放项目根目录比 `src/` 布局在 Vercel 上更稳定
- **pydantic-core glibc 不兼容**：锁定 pydantic 版本（`pydantic==2.10.6`）
- **Path 对象转 str**：`json.loads(open(str(path)).read())` 而非 `open(path)`
- **`api/__init__.py` 不可省略**：即使空文件，缺少可能导致 Vercel 报 "Could not find handler"
- **Vercel 静态扫描器有行数限制**：`handler`/`app` 在文件前 100 行内
- **handler(event, context) 可能已不支持**：优先用 WSGI app 模式
- **commit author 不匹配 Vercel 账号**：`git config user.email "verified@email.com"` → `git commit --amend --author="Name <email>" --no-edit` → `git push --force`。修正已有 commit 的 author 后 force push。
| Vercel CLI 从中国直连超时 | `vercel env pull`、`vercel deploy` 等 CLI 全挂 | 用 Vercel Dashboard 网页端配置。设置环境变量：Project Settings → Environment Variables → 加 `DEEPSEEK_API_KEY` 等 → Redeploy |
| **LLM API Key 变量名不兼容** | `FUNCTION_INVOCATION_FAILED` 或 API 返回 401 `Insufficient Account Balance` | **修复：代码里做双变量名兼容回退**。Vercel Dashboard 允许任意 env var 名，但用户可能用 `DEEPSEEK_API_KEY`、`LLM_API_KEY`、`OPENAI_API_KEY` 等。在 LLM 路由函数内用 `os.environ.get()` 链式回退：`api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")`。同理，`base_url` 也要双兼容：`base_url = os.environ.get("LLM_BASE_URL") or os.environ.get("BASE_URL") or "https://api.deepseek.com"`。**不要假设只有一个变量名**，用户可能在旧项目里配过不同的名。|
| **`.python-version` 与 uv builder 的 `requires-python` 冲突** | 构建日志：`uv sync` 下载 CPython 3.11.x 后报错 `incompatible with the project's Python requirement: ==3.12.*`。项目没有 `pyproject.toml`，但 Vercel 的 `@vercel/python` builder（2026年已默认用 uv）有内置 `requires-python` 校验。即使 `vercel.json` 设了 `runtime: python3.11` 也无法覆盖 uv 的版本选择。 | **原因**：uv 读 `.python-version` 选 Python 版本，然后与 builder 内置的 `requires-python` 做兼容性检查。如果 `.python-version` 写了旧版（如 3.11）但 builder 期望 3.12，立即报错。<br>**修复**：1) 把 `.python-version` 改回与项目历史一致的版本（旧项目曾用 3.12 能部署就保持 3.12）。2) 或者删除 `.python-version` 让 uv 自动选择。3) 添加空 `requirements.txt` 文件避免 uv 报找不到 manifest。<br>**预防**：新建项目时查 Vercel Dashboard 构建日志确认当前 builder 默认 Python 版本。旧项目保持 `.python-version` 不变即可。 |
- **Framework Preset 必须为 "Other"**：Vercel Dashboard 项目设置中检查
- **构建缓存干扰**：清除构建缓存后重试
- **`requirements.txt` 版本锁定**：用 `==` 而非 `>=`
| **局部 import 遮蔽全局（WSGI handler 致命陷阱）**：在 `app()` 函数内部用 `from module import fn` 会把 `fn` 标记为局部变量（即使顶部已有全局 import）。Python 编译 `app()` 时只要看到任何局部赋值（import 也是赋值），就把 `fn` 视作整个函数的局部变量。当 predict 端点的代码路径先于局部 import 执行 → `cannot access local variable 'fn' where it is not associated with a value`。**修复：永远在文件顶部 import，不在 handler 内部重复 import。即使只是 `/api/wc/markets` 路径内的 import 也会污染整个 `app()` 作用域** |
| **`urlparse(query_string).query` 对 raw query string 返回空**：WSGI handler 中 `environ.get("QUERY_STRING","")` 返回原始字符串 `"key=value..."`（无 `?` 前缀）。`urlparse(qs).query` 把整个字符串当 path 解析，`.query` 永远返回 `""`。**修复：直接用 `parse_qs(raw_qs)`，不要经过 `urlparse`**。详见 §5「注意事项」第 8 条。
