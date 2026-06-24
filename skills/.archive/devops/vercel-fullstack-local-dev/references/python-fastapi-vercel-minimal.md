# Minimal Python FastAPI → Vercel 部署清单

纯计算型 FastAPI 项目（无 DB、无外部服务）部署到 Vercel 的标准结构。

## 项目文件清单

```
project-root/
├── api/
│   ├── __init__.py          # 空文件，使 api 成为 Python 包
│   ├── index.py             # Vercel 入口 — re-export app
│   └── main.py              # FastAPI app 定义
├── core/                    # 业务逻辑模块（任意名称均可）
│   ├── __init__.py
│   └── *.py
├── decision/                # 更多模块
│   ├── __init__.py
│   └── *.py
├── api/static/              # （可选）静态文件
│   └── index.html
├── requirements.txt         # ✅ 必须 — 项目根目录
├── vercel.json              # ✅ 必须 — 路由配置
├── runtime.txt              # ✅ 推荐 — Python 版本
└── .vercelignore            # ✅ 推荐 — 排除无用文件
```

## api/index.py — 入口模板

```python
"""
Vercel Serverless Function 入口。
"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，使 for core/ decision/ 等模块可被 import
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app
```

**关键规则**：
- 必须 `sys.path.insert(0, ...)` 将项目根加入路径，不能用 `PYTHONPATH` 环境变量——Vercel 不认
- `Path(__file__).parent.parent` → 项目根目录（`api/` 的父目录）
- 建议 re-export 而非 copy-paste，保持主逻辑在 `main.py`

## api/main.py — App 模板

```python
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="App Name", version="1.0.0")

# （可选）静态文件挂载
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

## requirements.txt

Vercel uv 构建器扫描**项目根目录**寻找依赖清单。

```txt
fastapi>=0.104.0
pydantic>=2.0.0
```

- ⚠️ 即使 `api/` 下有 `requirements.txt`，根目录也必须有一份（uv 构建器只看根目录）
- 不需要 `uvicorn`（Vercel 内部处理 ASGI server）
- 不需要 `Jinja2`、`httpx` 等非必需依赖（减少 Lambda 包体积）

## vercel.json

```json
{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

**注意事项**：
- `functions` 块在较新版 Vercel 中已废弃——直接删掉，Vercel 自动检测 `api/` 下的 Python 文件
- 一条 `"/(.*)" → "api/index.py"` 即可处理所有路由（包括静态文件和 API）
- `runtime: python3.11` 建议与 `runtime.txt` 保持一致

## runtime.txt

```txt
python-3.11
```

如果不指定，Vercel 默认为 Python 3.9，可能导致语法兼容问题。

## .vercelignore

```txt
__pycache__
*.pyc
.git
.env
tests/
.gitignore
README.md
ITERATION_LOG.md
```

减小上传包体积，加快部署。**`__pycache__` 必须排除**，否则可能污染 Python 模块缓存。

## 模块导入架构

### 纯计算型（推荐，如麻将引擎、扑克引擎）

```
core/tile.py         # 数据模型+算法
core/win_checker.py  # 规则验证
core/fan_calculator.py
decision/listen_engine.py

api/main.py 从这些模块 import：
    from core.tile import encode, decode
    from core.shanten import calculate_shanten
    from decision.listen_engine import analyze_listen
```

所有模块无外部 API 依赖，纯数学计算。Vercel 冷启动极快（<500ms）。

### 导入路径规则

- `api/index.py` → `from api.main import app`（相对项目根）
- `api/main.py` → `from core.tile import ...`（依赖 `sys.path.insert`）
- 所有 `__init__.py` 必须存在（使目录成为 Python 包）

## 常见部署错误速查

| 错误 | 根因 | 修复 |
|------|------|------|
| `500 | 0ms` | 函数在导入阶段崩溃 | 检查 `requirements.txt` 是否存在、`sys.path` 是否正确 |
| `ModuleNotFoundError: No module named 'core'` | `sys.path.insert` 丢失或路径不对 | 确认 `api/index.py` 和 `api/main.py` 都有 `sys.path.insert(0, parent_parent)` |
| `could not impo…`（日志截断） | 依赖缺失或跨文件 import 失败 | 确认根目录有 `requirements.txt`，检查 `from X import Y` 路径 |
| 构建日志 "No Python manifest found" | uv 构建器找不到根目录的 `requirements.txt` | 在**项目根目录**放一份 `requirements.txt` |
| `FUNCTION_INVOCATION_FAILED` | 冷启动时崩溃 | 检查是否有写文件系统操作（Vercel 只读，仅 `/tmp` 可写） |
| 静态文件 404 | 路径不对或 `static_dir` 未挂载 | 确认 `api/static/` 存在，`Path(__file__).parent / "static"` 正确 |

## 部署验证流程

```bash
# 1. 本地测试 import
cd /path/to/project
python3 -c "
import sys; sys.path.insert(0, '.')
from api.index import app
print('OK:', app.title, 'Routes:', [r.path for r in app.routes])
"

# 2. 本地 HTTP 测试（使用 TestClient）
python3 -c "
from api.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
r = client.get('/api/health')
print(f'Health: {r.status_code} {r.json()}')
"

# 3. GitHub 推送后，Vercel 自动部署
# 4. 用户在浏览器中测试（国内服务器无法 curl Vercel 域名）
```

## 与 TXPokerAssist 和 General Mahjong Assist 的差异

| 项目 | 入口模式 | 静态文件位置 | 特殊依赖 |
|------|----------|-------------|----------|
| TXPokerAssist | `api/index.py` → `from main import app`（main.py 副本） | `api/static/` | 无 |
| General Mahjong Assist | `api/index.py` → `from api.main import app`（re-export） | `api/static/` | 无 |
| VisePanda | `api/index.py` → `from main import app`（副本） | `static/` + 后端渲染 | SQLite(只读), Supabase SDK |

**教训**：`from main import app`（副本模式）在 Vercel 上更稳定（消除跨文件导入失败），但维护两份文件。`from api.main import app`（re-export 模式）更干净但多一层 import 链。两者都可行。
