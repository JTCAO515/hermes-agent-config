# Cloudflare ECH + Argo Tunnel 代理节点

## 场景

用户搭建自己的 VPS 代理，通过 Cloudflare ECH (Encrypted Client Hello) + Argo Tunnel 隐藏真实 IP。订阅链接格式为 `vless://` 或 `vmess://`，所有节点共享同一 UUID，走不同 Cloudflare 边缘 IP。

## 特征识别

- 协议: VLESS 或 VMess
- 传输层: WebSocket + TLS
- 地址: `cloudflare-ech.com:443`（Cloudflare ECH 域名）
- SNI/Peer: `*.trycloudflare.com`（Argo Tunnel 生成的随机域名，如 `billing-richmond-pamela-comedy.trycloudflare.com`）
- Host: 同 SNI
- Path: `/<uuid>-vm` 或 `/<uuid>` 格式
- UUID 通常与 Path 中的 UUID 相同（可能有 `-vm` 后缀）

## VMess 订阅链接 → Xray JSON 转换

### 链接格式

```
vmess://base64(method:uuid@server:port)?path=<path>&remarks=<备注>&obfsParam=<sni>&obfs=websocket&tls=1&peer=<sni>&udp=1&alterId=0
```

### 解码步骤

```bash
# 1. 提取 Base64 部分（介于 vmess:// 和 ? 之间）
echo "YXV0bzo0MzFhYTMxOS1mZGQzLTQ4YmMtOGUwZC0zZTYzYjdiZmNhZTdAY2xvdWRmbGFyZS1lY2guY29tOjQ0Mw" | base64 -d
# → auto:431aa319-fdd3-48bc-8e0d-3e63b7bfcae7@cloudflare-ech.com:443
#   ↑method ↑uuid                      ↑server              ↑port
```

### 生成的 Xray JSON

```json
{
  "tag": "proxy",
  "protocol": "vmess",
  "settings": {
    "vnext": [{
      "address": "cloudflare-ech.com",
      "port": 443,
      "users": [{
        "id": "431aa319-fdd3-48bc-8e0d-3e63b7bfcae7",
        "security": "auto",
        "alterId": 0
      }]
    }]
  },
  "streamSettings": {
    "network": "ws",
    "security": "tls",
    "tlsSettings": {
      "serverName": "billing-richmond-pamela-comedy.trycloudflare.com",
      "fingerprint": "chrome"
    },
    "wsSettings": {
      "path": "/431aa319-fdd3-48bc-8e0d-3e63b7bfcae7-vm",
      "headers": {
        "Host": "billing-richmond-pamela-comedy.trycloudflare.com"
      }
    }
  }
}
```

## 性能特征

- Google/YouTube/GitHub: ✅ 可用，但延迟较高（2-10s，取决于 Cloudflare 边缘节点）
- OpenAI/Claude: ❌ 403（Cloudflare IP 被 WAF 拦截，常见于所有 Cloudflare 代理）
- 国内直连规则不受影响

## 排查

### SOCKS5 超时但 HTTP 正常

现象: `curl -x socks5h://127.0.0.1:10808` 超时，但 `curl -x http://127.0.0.1:10809` 正常

原因: Xray 26.x 的 WebSocket 传输 + SOCKS5 UDP 支持存在兼容性问题。

修复:
- 用 HTTP 代理（:10809）替代 SOCKS5 作为默认
- SOCKS5 设 30s+ 超时可工作，但首次连接慢
