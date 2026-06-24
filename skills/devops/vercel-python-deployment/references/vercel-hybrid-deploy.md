# Vercel 混合部署模式 — 静态前端 + VPS API 代理

> 用于部署有状态/持久化后端应用，前端在 Vercel 静态托管，API 通过 rewrites 反向代理到 VPS。

## 适用项目

| 项目 | 前端 (Vercel) | 后端 (VPS) | 后端端口 |
|------|--------------|------------|----------|
| JARVIS Mission Control | `index.html` + CSS/JS | Node.js Express (`~/projects/jarvis-mission-control/server/`) | 8503 |
| Hermes Agent Dashboard | `hermes.html` + 内联 JS | Python stdlib HTTPServer (`hermes-api.py`) | 8504 |

## Vercel 配置

### vercel.json

```json
{
  "version": 2,
  "builds": [{ "src": "**/*", "use": "@vercel/static" }],
  "rewrites": [
    { "source": "/api/service-a/(.*)", "destination": "http://VPS_IP:PORT_A/api/service-a/$1" },
    { "source": "/api/service-b/(.*)", "destination": "http://VPS_IP:PORT_B/api/service-b/$1" },
    { "source": "/page-x", "destination": "/page-x.html" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### 路径优先级

Vercel rewrites 按声明顺序匹配 — 更具体的路径（`/api/hermes/...`）放前面，通配符 `/(.*)` 放最后。

## 多项目同域名

同一个 Vercel 项目可以包含多个独立页面：

```
project-root/
├── index.html         # 主应用（mission-control）
├── hermes.html        # 子页面（Hermes 状态面板）
├── vercel.json        # rewrites 配置
├── js/                # 共享或独立 JS
├── css/
└── ...
```

通过 rewrites 将 `/hermes` → `/hermes.html` 实现路由。

## VPS 端配置

### 防火墙

Vultr 新加坡防火墙默认只开放 22/8000/5055/8502。混合部署模式需要额外开放端口：

```bash
# 检查当前端口状态
sudo ss -tlnp | grep <port>
```

### DNS

`hermes.jtcao.space` 的 CNAME 指向 `cname.vercel-dns.com`（由 Vercel 自动管理）。

## 调试

### API 代理是否工作

```bash
# 通过 Vercel + rewrite 测试（从外网）
curl -s https://yourdomain.com/api/hermes/health

# 直接测试 VPS 后端（跳过 Vercel）
curl -s --noproxy '*' http://VPS_IP:PORT/api/hermes/health
```

### 常见失败模式

| 模式 | 现象 | 原因 |
|------|------|------|
| `/api/*` 返回 502 | Vercel 无法连接 VPS | VPS 服务没启动 / 端口关闭 / 防火墙拦截 |
| `/api/*` 返回 404 | Vercel rewrite 匹配不到 | `vercel.json` 路径不匹配 |
| 前端页面 404 | 路由不匹配 | SPA 路由不存在 / vercel.json 没有 fallback |
| 页面加载但 API 超时 | 前端JS里用的是WebSocket | Vercel 不支持 WS 反向代理 |
