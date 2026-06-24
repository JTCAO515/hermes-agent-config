# Hermes 系统监控 API — stdlib Python HTTP Server

> 用 Python 标准库 `http.server` 构建轻量系统监控 API，通过 PM2 持久化运行在 VPS 上。

## 架构

```
VPS (Python 3.11 stdlib)
  └── hermes-api.py → HTTPServer(:8504)
       ├── /api/hermes/system    → 系统信息（CPU/Mem/Disk/Uptime）
       ├── /api/hermes/hermes    → Hermes Agent 状态
       ├── /api/hermes/projects  → 项目列表 + git 记录
       ├── /api/hermes/services  → PM2 服务状态
       ├── /api/hermes/recent    → 最近 git 活动
       └── /api/hermes/all       → 全部数据（合并请求）

前端 (Vercel)
  └── hermes.html → fetch('/api/hermes/all') → 渲染 Linear 风格暗色面板
```

## 核心实现

### 数据采集

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, subprocess, time, yaml

def _run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return None

def get_system_info():
    mem = _run("free -b | awk 'NR==2{print $2,$3,$4,$7}'")
    disk = _run("df -B1 / | awk 'NR==2{print $2,$3,$4}'")
    load = _run("cat /proc/loadavg")
    return {
        "hostname": _run("hostname"),
        "uptime": float(_run("cat /proc/uptime | cut -d' ' -f1") or 0),
        "cpu": {"cores": int(_run("nproc") or 0), "load": load.split()[:3]},
        "memory": dict(zip(["total","used","free","available"], mem.split())),
        "disk": dict(zip(["total","used","free"], disk.split())),
    }
```

### CORS 处理

对每个响应都加 `Access-Control-Allow-Origin: *` 头，以支持 Vercel rewrite 失败时的直连调试：

```python
self.send_header("Access-Control-Allow-Origin", "*")
```

### PM2 持久化

```bash
pm2 start hermes-api.py --name hermes-api --interpreter python3
pm2 save
```

## 可用端点

| 端点 | 数据 | 响应体大小 |
|------|------|-----------|
| `/api/hermes/health` | `{"status":"ok"}` | ~20 bytes |
| `/api/hermes/system` | 系统信息 | ~300 bytes |
| `/api/hermes/hermes` | Agent+Skill+Log 状态 | ~500 bytes |
| `/api/hermes/projects` | 项目列表(19+) | ~5KB |
| `/api/hermes/services` | PM2 服务状态 | ~200 bytes |
| `/api/hermes/recent` | 最近20条 git 活动 | ~2KB |
| `/api/hermes/all` | 以上全部合并 | ~8KB |

## 扩展

### 添加新端点

1. 在 HermesAPIHandler 的 `do_GET()` 中添加路径处理
2. 创建对应的数据采集方法
3. 可选：加入 `/api/hermes/all` 的合并

### 更多数据源

- **日志行数**：`wc -l ~/.hermes/logs/errors.log`
- **会话数**：`ls ~/.hermes/data/history/ | wc -l` （如果启用）
- **网络流量**：`cat /proc/net/dev`

## 陷阱

- **端口冲突**：如果进程启动时端口已被占用 → `OSError: [Errno 98] Address already in use`。PM2 重启前先 `kill $(lsof -ti :PORT)`
- **`http_proxy` 环境变量**：本地 curl 测试要用 `--noproxy '*'`，否则请求被代理拦截
- **`yaml` 非标准库**：仅在读取 `config.yaml` 时使用，pypi 需安装 `pyyaml`
- **`subprocess.run` 超时**：某些命令（`free`、`df`）可能在容器中执行很慢，设 5s 超时
- **`subprocess.PIPE` 不设 `text=True`** 返回 bytes，需要手动 `.decode()`
