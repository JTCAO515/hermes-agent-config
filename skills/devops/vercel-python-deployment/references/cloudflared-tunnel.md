# Cloudflared Tunnel — 端口受限 VPS 反向代理方案

> **适用场景**：VPS 防火墙只开放少数端口（如 Vultr 仅开 22/8000/5055/8502），无法新增端口时，用 cloudflared 建立出站隧道暴露内网服务。

## 原理

cloudflared 从 VPS 主动发起 **出站连接** 到 Cloudflare 边缘网络，Vultr 防火墙不会拦截出站连接。Cloudflare 返回一个公开可访问的 `*.trycloudflare.com` URL，所有到达该 URL 的请求通过隧道转发到本地端口。

```
Client → https://xxx.trycloudflare.com → Cloudflare Edge → Tunnel ← VPS:cloudflared → localhost:PORT
```

## 快速启动（Quick Tunnel）

```bash
# 暴露 localhost:8504
cloudflared tunnel --url http://localhost:8504

# 输出示例：
# Your quick Tunnel has been created! Visit it at:
# https://query-cosmetics-parties-executed.trycloudflare.com
```

### 使用 PM2 持久化

```bash
pm2 start cloudflared --name hermes-tunnel -- tunnel --url http://localhost:8504
pm2 save
```

> **注意**：Quick Tunnel URL **每次重启会变**！PM2 可以减少重启频率，但不能保证永久稳定。正式环境建议用 Named Tunnel。

## 与 Vercel 配合

在 `vercel.json` 中设置 rewrite 指向 tunnel URL：

```json
{
  "rewrites": [
    {
      "source": "/api/hermes/(.*)",
      "destination": "https://xxxx.trycloudflare.com/api/hermes/$1"
    }
  ]
}
```

> **每次 tunnel URL 变更后**，需更新 `vercel.json` 并重新推送部署。

## Named Tunnel（永久域名，推荐生产）

需要 Cloudflare 账户 + API Token：

```bash
# 1. 登录（需要 CLOUDFLARE_API_TOKEN）
cloudflared tunnel login

# 2. 创建命名隧道
cloudflared tunnel create hermes-api

# 3. 配置 DNS
cloudflared tunnel route dns hermes-api api.hermes.yourdomain.com

# 4. 创建配置文件 ~/.cloudflared/config.yml
tunnel: hermes-api
credentials-file: /home/ubuntu/.cloudflared/hermes-api.json
ingress:
  - hostname: api.hermes.yourdomain.com
    service: http://localhost:8504
  - service: http_status:404

# 5. 启动
cloudflared tunnel run hermes-api
```

## 系统代理干扰

此 VPS 设了 `http_proxy=http://127.0.0.1:10809`，但 cloudflared 本身不受影响（它用 QUIC/HTTP3 而不是 HTTP 代理）。只有本地测试 curl 时需要 `--noproxy '*'`。

## 优缺点

| 维度 | 评价 |
|------|------|
| 零端口开放 | ✅ 出站连接，防火墙不拦截 |
| 设置快捷 | ✅ Quick Tunnel 一行命令搞定 |
| URL 稳定性 | ❌ Quick Tunnel 重启即变；Named Tunnel 需 Cloudflare 账户 |
| 性能 | ✅ Cloudflare 边缘网络，延迟低 |
| 安全性 | ⚠️ Quick Tunnel 无认证，任何人可访问 tunnel URL |
| 带宽 | ⚠️ Cloudflare 免费计划 100MB/文件，无限请求 |
