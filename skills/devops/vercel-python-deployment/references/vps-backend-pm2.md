# VPS 后端服务管理（PM2 + Vercel Hybrid）

当应用采用「Vercel 静态前端 + VPS API 后端」的混合部署模式时，VPS 上的后端服务需要持久化管理。

## 技术栈

- **服务管理**: PM2 (Node.js 进程管理器，也支持 Python/任意脚本)
- **Python API 服务**: Python stdlib `http.server.HTTPServer` (零依赖)
- **Node.js API 服务**: Express + WebSocket
- **持久化存储**: Git 版本化 JSON 文件 / SQLite

## PM2 管理 Python 服务

```bash
# 启动 Python HTTP server
pm2 start /path/to/api-server.py --name my-api --interpreter python3

# 带参数启动
pm2 start /path/to/api-server.py --name my-api --interpreter python3 -- --port 8504

# 重启
pm2 restart my-api

# 查看日志
pm2 logs my-api --lines 20
```

### Python stdlib HTTP Server 模板

```python
import json
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.environ.get("PORT", 8504))

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        # CORS headers for Vercel rewrite (same-origin = no CORS needed)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        if path == "/api/health":
            data = {"status": "ok"}
        elif path == "/api/data":
            data = self.collect_data()
        else:
            data = {"error": "not found"}
        
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def collect_data(self):
        """Override with your data collection logic"""
        return {"message": "placeholder"}

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MyHandler)
    print(f"API server on :{PORT}")
    server.serve_forever()
```

## PM2 常见操作

```bash
# 查看所有服务
pm2 list

# 保存进程列表（重启后恢复）
pm2 save

# 开机自启（需要 sudo）
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u ubuntu --hp /home/ubuntu

# 查看进程详情
pm2 show hermes-api

# 内存/CPU 监控
pm2 monit

# 停止
pm2 stop mission-control

# 删除（从 PM2 列表移除）
pm2 delete hermes-api
```

## 混合部署常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `http_proxy` 干扰本地测试 | 服务器设置了 `http_proxy` 代理科学上网 | `curl --noproxy '*' http://localhost:PORT` |
| VPS 端口被防火墙拦截 | Vultr 云防火墙白名单机制 | 开端口：Vultr Dashboard → Firewall → Add Rule |
| 从 GitHub push 超时 | HTTPS TLS 握手失败（Vultr新加坡→GitHub不稳定） | 换 SSH: `git remote set-url origin git@github.com:user/repo.git` |
| Python 端口被占用 | 之前的手动启动进程未清理 | `kill $(lsof -ti :8504)` 后 `pm2 restart` |
