# Cloudflare ECH + Argo Tunnel + VMess 节点配置

> 2026-06-18 验证的完整工作流。节点类型：VMess+WebSocket+TLS，后端是 Cloudflare ECH (cloudflare-ech.com) + Argo Tunnel (trycloudflare.com)。

## 节点特征

```
协议:    VMess
传输:    WebSocket + TLS
地址:    cloudflare-ech.com:443 （Cloudflare ECH 专用域名）
UUID:    431aa319-fdd3-48bc-8e0d-3e63b7bfcae7
SNI:     billing-richmond-pamela-comedy.trycloudflare.com （Argo Tunnel 自动生成域名）
Path:    /431aa319-fdd3-48bc-8e0d-3e63b7bfcae7-vm
```

**关键区别 vs 标准 Cloudflare CDN 节点：**
- `cloudflare-ech.com` 是 Cloudflare 的 ECH (Encrypted Client Hello) 接入点——不是随机 CDN IP
- Argo Tunnel 域名 (`*.trycloudflare.com`) 作为 SNI——不是 CNAME 过来的源站域名
- VMess 协议（不是 VLESS）——Base64 部分包含 server/port/uuid

## 订阅解码 → Xray 配置

### 1. 获取订阅

```bash
# 订阅链接返回 Base64 编码的 VMess URI 列表
curl -sL "https://jtccc.cc.cd/sub?token=c9d4e835836c26e8a092511a60a6ae8d" | base64 -d
```

解码后：
```
vless://1229655a-...@104.17.177.28:443?security=tls&type=ws&... # 第一批 VLESS
vmess://YXV0bzo...                               # 第二批 VMess
```

### 2. VMess URI 解析

```
vmess://YXV0bzo0MzFhYTMxOS1mZGQzLTQ4YmMtOGUwZC0zZTYzYjdiZmNhZTdAY2xvdWRmbGFyZS1lY2guY29tOjQ0Mw
         ↕ base64 decode
         auto:431aa319-fdd3-48bc-8e0d-3e63b7bfcae7@cloudflare-ech.com:443
         ↑method ↑uuid                         ↑server            ↑port
```

查询参数：
```
path=431aa319-fdd3-48bc-8e0d-3e63b7bfcae7-vm
obfs=websocket       → network: "ws"
tls=1                → security: "tls"
peer=billing-...trycloudflare.com  → tlsSettings.serverName
obfsParam=billing-...trycloudflare.com  → wsSettings.headers.Host
udp=1
alterId=0
```

### 3. 配置生成

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

### 4. 部署

```bash
# 写配置
sudo cp /tmp/xray-config.json /usr/local/xray/config.json

# 重启
sudo systemctl restart xray.service

# 检查启动
sudo systemctl status xray.service --no-pager | head -10

# 常见警告（不影响功能）：
# - "WebSocket transport is deprecated" (Xray 26.x)
# - "\"host\" in \"headers\" is deprecated" → 后续迁移到独立 "host" 字段
```

## 连通性验证

### HTTP 代理（快，推荐）
```bash
curl -x http://127.0.0.1:10809 -s -o /dev/null -w "HTTP: %{http_code} | %{time_total}s\n" --max-time 15 https://www.google.com
# ✅ HTTP: 200 | 2-10s
```

### SOCKS5（慢，需长超时）
```bash
# ❌ 10s 超时不够 — Cloudflare ECH 节点 TLS 握手慢
curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -w "HTTP: %{http_code} | %{time_total}s\n" --max-time 10 https://www.google.com
# → HTTP: 000 | 10.0s（超时）

# ✅ 30s 超时可行
curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -w "HTTP: %{http_code} | %{time_total}s\n" --max-time 30 https://www.google.com
# → HTTP: 200 | 2.1s
```

**坑点**：SOCKS5 超时不是节点问题，是 Xray 的 SOCKS inbound + UDP 模式在 CF ECH 组合下慢。HTTP 代理始终正常。

### 批量测试
```bash
echo "📡 被墙站点"
for url in "https://www.google.com" "https://www.youtube.com" "https://github.com"; do
  code=$(curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -w "%{http_code} | %{time_total}s" --max-time 30 "$url" 2>&1)
  echo "  $url → $code"
done

echo "📡 国内站点（应走直连）"
for url in "https://www.baidu.com" "https://www.bilibili.com"; do
  code=$(curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -w "%{http_code} | %{time_total}s" --max-time 10 "$url" 2>&1)
  echo "  $url → $code"
done
```

### 出口 IP 验证
```bash
echo "代理出口: $(curl -x socks5h://127.0.0.1:10808 -s --max-time 10 https://httpbin.org/ip 2>&1)"
echo "直连出口: $(curl -s --max-time 10 https://httpbin.org/ip 2>&1)"
# 两者应不同（Cloudflare 边缘 IP），确认流量走节点
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| OpenAI/Claude 返回 403 | Cloudflare IP 被 AI 公司 WAF 拦截 | 非代理问题，浏览器直接访问 |
| SOCKS5 10s 超时 | CF ECH TLS 握手慢 | 用 HTTP 代理（:10809）或设 30s+ 超时 |
| google.com 返回 301 | 正常 HTTP 重定向 | 确认是 301 不是 000，加 `-L` 跟重定向 |
| `http_proxy` 环境变量干扰本地测试 | 服务器设了全局代理 | 所有 curl 加 `--noproxy '*'` |
| Xray 报 "deprecated" 警告 | Xray 26.x 的 WebSocket 废弃 | 不影响功能，可继续用 |
