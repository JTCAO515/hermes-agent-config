# Vercel WSGI 代理子模块模式

> 模式描述：将 API 路由拆分为独立子模块，返回 `(body, headers)` 由主 handler 统一处理。

## 动机

大型 WSGI 应用中，所有路由 if/elif 挤在单个 `app()` 函数里 → 超过100行 → 难以维护、路径解析 bug、局部 import 污染。

**解决方案**：将一组相关路由（如外部 API 代理）拆出到独立模块，返回 `(body_bytes_list, headers_list)` 由主 handler 做 `start_response()` 和 `return body`。

## 架构

```
api/
├── index.py         # 主 WSGI app — 负责 start_response + 返回 body
└── myproxy.py       # 子模块代理 — 返回 (body_list, headers_list) 或 None
```

### 主 handler (api/index.py)

```python
def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    
    # 委托给子模块
    from api.myproxy import myproxy_endpoint
    result = myproxy_endpoint(environ)
    if result is not None:
        body, headers = result
        start_response("200 OK", headers)
        return body
    
    # 默认路由
    return _json_error(start_response, "Not found", status="404 Not Found")
```

### 子模块 (api/myproxy.py)

```python
import json
from urllib.parse import parse_qs

def _respond(payload: Any) -> tuple[list[bytes], list]:
    """返回 (body_bytes_list, headers_list) 供主 handler 处理。"""
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    return [body], [("Content-Type", "application/json; charset=utf-8")]

def _qs(environ: dict, key: str, default=None) -> str | None:
    qs = parse_qs(environ.get("QUERY_STRING", ""))
    vals = qs.get(key, [])
    return vals[0] if vals else default

def myproxy_endpoint(environ: dict) -> tuple[list[bytes], list] | None:
    """
    返回 (body_bytes_list, headers_list) 或 None（不匹配本路由）。
    不调用 start_response — 由主 handler 处理。
    """
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    
    if not path.startswith("/api/myproxy/"):
        return None
    
    ep = path[len("/api/myproxy/"):]
    
    if ep == "health":
        return _respond({"status": "ok"})
    
    if ep == "data":
        mid = _qs(environ, "id")
        if not mid:
            return _respond({"error": True, "message": "缺少参数: id"})
        result = fetch_data(mid)
        return _respond(result)
    
    return _respond({"error": True, "message": f"未知端点: {ep}"})
```

## 关键约定

| 项 | 规则 |
|-----|------|
| 返回值 | `(body_bytes_list, headers_list)` — 不要调 `start_response` |
| None | 路径不匹配时返回 `None`，让主 handler 继续尝试其他路由 |
| 参数 | 所有 query 参数通过 `_qs()` 只读 |
| JSON | `_respond()` 负责序列化，模块内只用 `return _respond(data)` |
| 路由表 | 在模块底部维护显式 `ROUTES` 字典（自文档 + 校验） |

## 与 FastAPI router 对比

| 维度 | FastAPI APIRouter | WSGI 子模块 |
|------|------------------|-------------|
| 注册 | `app.include_router(router)` | 手动 if/elif |
| 返回 | Pydantic model | raw dict → _respond() |
| 依赖注入 | FastAPI Depends | 手动 |
| 灵感 | Flask Blueprint | 更轻量，零依赖 |

## 何时使用本模式

- 外部 API 代理（转发、缓存、认证注入）
- 从主 WSGI 应用分离出清晰的功能模块
- 第三方 API 接口封装（纳米数据、Polymarket 等）
