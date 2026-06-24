# Python stdlib System Data API — 零依赖 VPS 后端

> 用于混合部署模式（Vercel 静态前端 + VPS API 后端）中，在 VPS 上快速搭建轻量数据 API。纯 Python 标准库，零 pip 依赖。

## 适用场景

- **服务器信息面板** — CPU/内存/磁盘/运行时长等系统指标
- **Agent 状态仪表盘** — Hermes/Claude/OpeanClaw 等 AI agent 的运行状态
- **项目管理看板** — 从文件系统读取的项目/仓库状态
- **日志查看器** — 实时服务日志聚合
- **其他轻量数据 API** — 任何需要持久化运行、但不需复杂框架的场景

## 完整模板

```python
#!/usr/bin/env python3
"""
System Data API — Zero-dependency Python stdlib HTTP server.
Serves JSON data for Vercel-hosted frontend via hybrid deployment.
Usage: python3 this_script.py [PORT]
"""
import json
import os
import subprocess
import time
import glob
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HOME = os.path.expanduser("~")
PORT = int(os.environ.get("PORT", 8504))

class DataAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler dispatching by path. Add new endpoints by extending the routing table."""

    def do_GET(self):
        path = urlparse(self.path).path
        router = {
            "/api/health":           {"status": "ok"},
            "/api/system":           self.get_system_info(),
            "/api/services":         self.get_services(),
            "/api/projects":         self.get_projects(),
            "/api/recent":           self.get_recent_activity(),
        }

        if path in router:
            data = router[path]
        elif path == "/api/all":
            data = {
                "system": self.get_system_info(),
                "services": self.get_services(),
                "projects": self.get_projects(),
                "recent": self.get_recent_activity(),
                "timestamp": time.time()
            }
        else:
            self._respond(404, {"error": "not found"})
            return

        # Collect data for dynamic endpoints (those that call functions)
        if path == "/api/services":
            data = self.get_services()
        elif path == "/api/projects":
            data = self.get_projects()
        elif path == "/api/recent":
            data = self.get_recent_activity()

        self._respond(200, data)

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    # ── Helpers ────────────────────────────────────────────────

    def _run(self, cmd, timeout=5):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip()
        except:
            return None

    def _parse_int(self, val, default=0):
        try: return int(val)
        except: return default

    # ── Data Collectors ────────────────────────────────────────

    def get_system_info(self):
        mem = self._run("free -b | awk 'NR==2{print $2,$3,$4,$7}'")
        mp = mem.split() if mem else ["0","0","0","0"]
        disk = self._run("df -B1 / | awk 'NR==2{print $2,$3,$4}'")
        dp = disk.split() if disk else ["0","0","0"]
        load = self._run("cat /proc/loadavg")
        lp = load.split()[:3] if load else ["0","0","0"]
        uptime = self._run("cat /proc/uptime | cut -d' ' -f1")

        return {
            "hostname": self._run("hostname"),
            "platform": self._run("uname -sr"),
            "uptime": float(uptime or 0),
            "cpu": {
                "cores": self._parse_int(self._run("nproc")),
                "load_1m": float(lp[0]),
                "load_5m": float(lp[1]),
                "load_15m": float(lp[2]),
            },
            "memory": {
                "total": self._parse_int(mp[0]),
                "used": self._parse_int(mp[1]),
                "free": self._parse_int(mp[2]),
                "available": self._parse_int(mp[3]),
            },
            "disk": {
                "total": int(dp[0]),
                "used": int(dp[1]),
                "free": int(dp[2]),
            }
        }

    def get_services(self):
        raw = self._run("pm2 list 2>/dev/null | grep '│' | grep -v '┬\\|┴\\|├\\|└'")
        services = []
        if raw:
            for line in raw.split("\n"):
                parts = [p.strip() for p in line.split("│") if p.strip()]
                if len(parts) >= 4:
                    services.append({
                        "name": parts[1] if len(parts) > 1 else "?",
                        "status": parts[4] if len(parts) > 4 else "?",
                        "memory": parts[6] if len(parts) > 6 else "?",
                    })
        return services

    def get_projects(self):
        projects_dir = os.path.join(HOME, "projects")
        if not os.path.isdir(projects_dir):
            return []
        projects = []
        for name in sorted(os.listdir(projects_dir)):
            d = os.path.join(projects_dir, name)
            if not os.path.isdir(d) or name.startswith("."):
                continue
            projects.append({
                "name": name,
                "git": {
                    "branch": self._run(f"cd {d} && git rev-parse --abbrev-ref HEAD 2>/dev/null"),
                    "last_commit": self._run(f"cd {d} && git log --oneline -1 2>/dev/null"),
                    "remote": self._run(f"cd {d} && git remote -v 2>/dev/null | head -1 | awk '{{print $2}}'"),
                }
            })
        return projects

    def get_recent_activity(self):
        projects_dir = os.path.join(HOME, "projects")
        if not os.path.isdir(projects_dir):
            return []
        recent = []
        for name in sorted(os.listdir(projects_dir)):
            d = os.path.join(projects_dir, name)
            if not os.path.isdir(d) or name.startswith("."):
                continue
            commits = self._run(f"cd {d} && git log --oneline -3 --format='%h|%s|%ar' 2>/dev/null")
            if commits:
                for line in commits.split("\n")[:3]:
                    parts = line.split("|")
                    if len(parts) == 3:
                        recent.append({
                            "project": name,
                            "hash": parts[0],
                            "message": parts[1],
                            "ago": parts[2],
                        })
        return recent[:20]


if __name__ == "__main__":
    port = PORT
    server = HTTPServer(("0.0.0.0", port), DataAPIHandler)
    print(f"Data API server on http://0.0.0.0:{port}")
    print(f"Endpoints: /api/health, /api/system, /api/services, /api/projects, /api/recent, /api/all")
    server.serve_forever()
```

## PM2 启动

```bash
# 启动
pm2 start /path/to/api.py --name data-api --interpreter python3

# 带端口参数
pm2 start /path/to/api.py --name data-api --interpreter python3 -- --port 8504

# 保存进程列表
pm2 save
```

## 扩展示例 — 添加自定义数据

```python
# 在 do_GET 路由表中添加：
"/api/hermes": self.get_hermes_info(),

# 添加收集方法：
def get_hermes_info(self):
    import yaml  # 可选；也可以用 os.listdir + open 手动解析
    config_path = os.path.join(HOME, ".hermes", "config.yaml")
    config = {}
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except:
        pass
    
    skills_dir = os.path.join(HOME, ".hermes", "skills")
    skills_count = len(os.listdir(skills_dir)) if os.path.isdir(skills_dir) else 0
    
    return {
        "model": config.get("model", {}).get("default", "?"),
        "provider": config.get("model", {}).get("provider", "?"),
        "skills": skills_count,
    }
```

## 常见陷阱

| 陷阱 | 现象 | 修复 |
|------|------|------|
| `http_proxy` 干扰 | 本地 `curl localhost:PORT` 返回 503 | 用 `curl --noproxy '*' http://localhost:PORT` |
| Vultr 防火墙拦截 | 外网无法访问该端口 | Vultr Dashboard → Firewall → Add Rule（TCP, 端口号, 0.0.0.0/0） |
| 端口被占用 | Python 启动报 `Address already in use` | `kill $(lsof -ti :PORT)` 后重启 |
| PM2 反复重启 | Python 脚本有语法错误或 import 失败 | `pm2 logs data-api --lines 20` 查看错误 |
| JSON 序列化失败 | 400/500 错误 | 确保所有数据是 JSON 可序列化的类型 |
