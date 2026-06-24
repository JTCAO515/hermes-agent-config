# Debug FUNCTION_INVOCATION_FAILED 实录

来自 World Cup Edge Lab 部署（2026-06-03）。

## 症状

```
$ curl https://worldcup.jtcao.space/api/health
A server error has occurred
FUNCTION_INVOCATION_FAILED
sin1::tjdxw-1780470673971-ee0a52a1d6dd
HTTP_CODE:500

$ curl https://worldcup.jtcao.space/
A server error has occurred
FUNCTION_INVOCATION_FAILED
icn1::nphlp-1780470783861-bdb79b163ab2
HTTP_CODE:500
```

**关键诊断信号**：所有端点（根路由 `/` + API 端点）都返回相同错误。
→ 说明 FastAPI 根本没启动，错误发生在模块**加载/导入**阶段，而非请求处理阶段。

## 排查步骤

### Step 1: 确认错误范围
先打 health 和 root 两个端点。两个都挂 → 导入期错误。
如果只有 API 挂但根路由正常 → 可能是 FastAPI 路由配置或业务逻辑错误。

### Step 2: 检查 dependencies
```
requirements.txt — 只有 fastapi+pydantic
football_predictor 子模块 — 全部用标准库（math, json, datetime, pathlib）
→ dependencies 不是问题
```

### Step 3: 检查项目结构
```
# 有问题的结构：
world-cup-edge-lab/
├── src/
│   └── football_predictor/  ← 藏在 src/ 里
├── api/index.py
│   ├── sys.path.insert(0, str(ROOT / "src"))
│   └── from football_predictor.backtest import ...

# 修后的结构（GMA 模式）：
world-cup-edge-lab/
├── football_predictor/      ← 放项目根目录
├── api/index.py             ← 薄入口，只 re-export
├── api/main.py              ← 真正的 FastAPI 应用
```

### Step 4: 本地 import 验证
```bash
cd ~/projects/world-cup-edge-lab
python3 -c "
import sys; sys.path.insert(0, '.')
from api.index import app
from fastapi.testclient import TestClient
c = TestClient(app)
print('GET /', c.get('/').status_code)
print('GET /api/health', c.get('/api/health').status_code)
"
```

### Step 5: 彻底测试
```bash
python3 -m pytest -q   # 17/17 passed
```

### Step 6: git push → 自动重部署
```bash
git add -A
git commit -m "fix: restructure for Vercel deployment"
git push origin master
```

Vercel 自动检测 GitHub push 后重部署。重新 curl 确认修复。

### Step 7: 修复后依然报错 — 排查自动部署

```bash
# curl 后检查响应头
$ curl -sI https://worldcup.jtcao.space/api/health
HTTP/2 500
x-vercel-cache: MISS       # MISS = 新调用（不是缓存）
x-vercel-id: sin1::...     # 每次不同 = 函数在运行
x-vercel-error: FUNCTION_INVOCATION_FAILED
```

**这里容易误判**：每次 `x-vercel-id` 都不同，说明函数在被调用——但**不代表是新代码**。Vercel 可能仍在运行旧版本的函数。

**排除方法**：
1. 检查 DNS：`host worldcup.jtcao.space` → 确认指向 Vercel DNS
2. 对比 local git log 与 Vercel Dashboard 上的 Deployments 列表
3. 如果 Dashboard 上没有最新 commit 的部署记录 → **自动构建未触发**

**修复**：
- 用户需要去 Vercel Dashboard → Deployments → 点「Redeploy」（选择最新 commit）
- 或者检查 Build Logs 看是否有 pip install 失败等构建错误

### Step 8: 对比已知可工作项目

当完全卡住时，找同一个模式的可工作项目做逐文件对比：

```bash
# 对比项目结构
tree general-mahjong-assist/ --charset=utf-8 | head -20
tree world-cup-edge-lab/ --charset=utf-8 | head -20

# 逐文件 diff
diff general-mahjong-assist/vercel.json world-cup-edge-lab/vercel.json
diff general-mahjong-assist/api/index.py world-cup-edge-lab/api/index.py
diff general-mahjong-assist/requirements.txt world-cup-edge-lab/requirements.txt
```

从本次会话发现的差异：
- GMA 的 `api/index.py` → `api/main.py` re-export：完全一致 ✅
- GMA 的 `vercel.json` routes：`"/(.*)"` 单条 vs 我们原来两条路由
- GMA 的 Python 包（`core/`, `decision/`）在项目根目录 vs 我们原来在 `src/` 里

## 额外诊断技术

### 检查 Vercel 是否能找到 `app`

```python
import sys; sys.path.insert(0, '.')
from api.index import app
import inspect
print(type(app))          # <class 'fastapi.applications.FastAPI'>
print('app in api.index:', 'app' in dir(app))  # True

# 检查 __init__.py 不影响导入
import api
hasattr(api, 'app')       # False = 正常，app 只在 api.index 不在 api package
```

### 响应头分析

| 头 | 含义 |
|----|------|
| `x-vercel-cache: MISS` | 函数被新调用（非缓存） |
| `x-vercel-id: sin1::...` | 执行环境标识 |
| `x-vercel-error: FUNCTION_INVOCATION_FAILED` | 模块导入期错误 |
| `x-vercel-region: sin1` | 新加坡区域 |

### 确认本地环境和 Vercel 一致

```bash
# 在干净 venv 中安装 requirements.txt
python3 -m venv /tmp/test-venv
/tmp/test-venv/bin/pip install -q -r requirements.txt
/tmp/test-venv/bin/python -c "import fastapi; print(fastapi.__version__)"
```

## 关键教训

1. **`src/` 布局在 Vercel 上不可靠**。即使本地 `sys.path.insert` 工作正常，Vercel Lambda 环境下可能导致导入失败。Python 包直接放项目根目录。
2. **`api/index.py` 只做一件事**：设路径 + re-export `app`。所有业务逻辑在 `api/main.py`。
3. **vercel.json routes 用单条 `/(.*)`** 通吃，让 FastAPI 内部路由。
4. **修复后依然报错 ≠ 代码还有问题**。先确认 Vercel 是否真部署了新代码。
5. **逐文件对比可工作项目**是最直接的调试手段——从结构差异中找根因。
6. **Vercel 静态扫描器有行数限制**：即使用了 `handler(event, context)` 原生模式，如果 `def handler(...)` 定义在文件第 363 行，Vercel 也找不到它。必须保持在前 ~100 行内。
7. **`api/__init__.py` 不可省略**：即使空文件也必须存在。缺少时 Vercel 报 "Could not find a top-level handler"。
8. **核选项（单文件零依赖 handler）**：当所有其他手段失败时，放弃 FastAPI，用 Vercel 原生 `handler(event, context)` + 全部算法内联 + 零 pip 依赖。这是最彻底的解决方案。
9. **HTTPS git push 可能超时**：VPS 网络环境可能 HTTPS 超时但 SSH 可用。切换到 SSH remote 解决。

---

## 补充：第 2 轮修复详细记录（2026-06-03 第二诊）

### 问题复现

上一轮修复（GMA 模式重构 + 版本锁定）后，依然 `FUNCTION_INVOCATION_FAILED`。

### 诊断过程

#### 尝试 1：去掉 re-export 模式

将 `api/index.py` 从"薄层 re-export"改为**单文件自包含**，所有 routes 和 import 在同一个文件。

**结果**：Vercel Dashboard 报 "Could not find a top-level `app`, `application`, or `handler` in 'api/index.py'"

#### 尝试 2：切换到原始 handler(event, context)

放弃 FastAPI，使用 Vercel 原生 handler 模式。

**handler 定义位置**：第 363 行
**结果**：Vercel 依然报 "Could not find a top-level handler"

#### 尝试 3：handler 移到第 48 行 + 删除 api/__init__.py

**结果**：Vercel 报同一错误
**修复**：加回 api/__init__.py（空文件）
**推测**：缺少 __init__.py 时 Vercel 无法正确解析包结构

#### 尝试 4：所有算法内联进单文件 + handler 在第 48 行 + __init__.py 存在

**状态**：已推送，等待验证

#### 尝试 5（终极隔离诊断）：2 行 handler 在 api/ping.py

创建 `api/ping.py`：
```python
def handler(event, context):
    return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": '{"status":"ok"}'}
```

vercel.json 指向 ping.py，git push 部署验证。

**预期**：
- ✅ 返回 `{"status":"ok"}` → 问题在代码文件
- ❌ 仍报 Could not find handler → Vercel 项目配置 / 构建系统问题

**实际**：等待用户验证

### 最终代码结构（第 2 轮修复后）

```
world-cup-edge-lab/
├── api/
│   ├── __init__.py      # 空文件
│   └── index.py         # 全部代码：handler(event, context) + 所有算法 + 静态文件服务
├── data/
├── configs/
├── web/
├── vercel.json
├── requirements.txt     # 空（纯 stdlib）
├── football_predictor/  # 保留用于本地测试
└── tests/
```

### api/index.py 核心指标

| 指标 | 值 |
|------|-----|
| handler 位置 | 第 48 行（前 100 行内） |
| 总行数 | ~395 行 |
| 外部依赖 | 零（仅 stdlib） |
| pip 包 | 无（requirements.txt 为空） |
| maxLambdaSize | 10mb（实际 < 500kb） |
| 算法行数 | ~300 行（5 个模块内联） |

### git push 技巧

HTTPS push 反复超时：
```
$ git push origin master
[Command timed out after 120s]
```

切换到 SSH 后成功：
```
$ git remote set-url origin git@github.com:JTCAO515/world-cup-edge-lab.git
$ git push origin master
To github.com:JTCAO515/world-cup-edge-lab.git
   ... -> master
```

### 最终解决（2026-06-03 第三诊）

#### 关键发现

**`handler(event, context)` 原始模式在较新 Vercel 上已不可用！** 即使：

- handler 定义在第 48 行
- 文件仅 2 行（`def handler(...): return ...`）
- 无任何外部 import

Vercel 构建阶段依然报 "Could not find a top-level handler"。

#### 最终方案：WSGI app

切换到 WSGI `def app(environ, start_response)` 模式后成功：

```python
def app(environ, start_response):
    start_response("200 OK", [("Content-Type", "application/json")])
    return [b'{"status":"ok"}']
```

**项目重新 Import** 时在 Vercel Dashboard 选 **Framework Preset = "Other"**（之前可能是默认的 "Next.js" 或其他框架，导致 Vercel 用错误构建管道）。

#### 最终项目结构

```
world-cup-edge-lab/
├── api/
│   ├── __init__.py        # 空文件（必须存在）
│   └── index.py           # WSGI app(environ, start_response) + 全部算法
├── web/                   # 前端静态文件
├── data/
├── configs/
├── vercel.json
└── requirements.txt       # 零依赖（纯 stdlib）
```

#### 调试时间线总结

| 轮次 | 方案 | 结果 |
|------|------|------|
| 1 | FastAPI 双文件 re-export (GMA模式) | ❌ FUNCTION_INVOCATION_FAILED |
| 2 | FastAPI 单文件 + 版本锁定 | ❌ 同错 |
| 3 | 原始 handler(event, context) + 移到行48 | ❌ Build: "Could not find handler" |
| 4 | 2行 handler(event, context) 隔离测试 | ❌ Build: 同错 |
| 5 | 2行 WSGI app(environ, start_response) | ✅ 返回 {"status":"ok"} |
| 6 | 完整 WSGI app + 全部算法内联 | ✅ 待验证 |
