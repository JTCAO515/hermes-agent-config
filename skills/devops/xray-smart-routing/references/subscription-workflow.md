# 订阅链接 → Xray 节点配置工作流

> 从 Base64 编码的 VLESS 订阅链接转换为 Xray JSON config

## 订阅解码

```bash
# 订阅链接
curl -sL "https://example.com/sub?token=xxx" | base64 -d
```

解码输出示例（每行一个 VLESS URI）：

```
vless://1229655a-9766-4a4d-8305-351f11631472@188.164.248.192:2096?security=tls&type=ws&host=jtccc.cc.cd&fp=chrome&sni=jtccc.cc.cd&path=%2F&encryption=none#节点名
```

## URI 解析

| 部分 | 值 | 说明 |
|------|-----|------|
| protocol | vless | 留用 |
| uuid | `1229655a-9766-4a4d-8305-351f11631472` | 用户 ID |
| host | `188.164.248.192` | CF anycast IP |
| port | `2096` | 端口 |
| security | tls | 启用 TLS |
| type/network | ws | WebSocket 传输 |
| host (param) | `jtccc.cc.cd` | WS Host 头 |
| sni | `jtccc.cc.cd` | TLS SNI |
| fp | chrome | 指纹 |
| path | `/` | WS 路径 |

## Xray JSON Outbound 模板

### 主节点 (WS + TLS, 无 deprecated headers)

```json
{
  "tag": "proxy",
  "protocol": "vless",
  "settings": {
    "vnext": [{
      "address": "188.164.248.192",
      "port": 2096,
      "users": [{
        "id": "1229655a-9766-4a4d-8305-351f11631472",
        "encryption": "none"
      }]
    }]
  },
  "streamSettings": {
    "network": "ws",
    "security": "tls",
    "tlsSettings": {
      "serverName": "jtccc.cc.cd",
      "fingerprint": "chrome"
    },
    "wsSettings": {
      "path": "/",
      "host": "jtccc.cc.cd"
    }
  }
}
```

### 备用节点（同 UUID, 不同 CF IP）

```json
{
  "tag": "proxy-bak1",
  "protocol": "vless",
  "settings": {
    "vnext": [{
      "address": "104.17.218.63",
      "port": 8443,
      "users": [{
        "id": "1229655a-9766-4a4d-8305-351f11631472",
        "encryption": "none"
      }]
    }]
  },
  "streamSettings": {
    "network": "ws",
    "security": "tls",
    "tlsSettings": {
      "serverName": "jtccc.cc.cd",
      "fingerprint": "chrome"
    },
    "wsSettings": {
      "path": "/",
      "host": "jtccc.cc.cd"
    }
  }
}
```

## 关键区别: WS+TLS vs Reality+TCP

| 维度 | Reality+TCP | WS+TLS (CF) |
|------|-------------|-------------|
| network | `"tcp"` | `"ws"` |
| security | `"reality"` | `"tls"` |
| tlsSettings | N/A (用 realitySettings) | `serverName`, `fingerprint` |
| wsSettings | N/A | `path`, `host` |
| 流控 | `flow: "xtls-rprx-vision"` | 无 `flow` (或空字符串) |
| publicKey | 需要 | 不需要 |
| shortId | 需要 | 不需要 |

## 验证命令

```bash
# HTTP 代理测试（最可靠）
curl -x http://127.0.0.1:10809 -s -o /dev/null -w "%{http_code}|%{time_total}s\n" https://www.google.com

# SOCKS5 可能超时——设 30s 超时
curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -w "%{http_code}|%{time_total}s\n" --max-time 30 https://www.google.com

# 出口 IP 确认
curl -x socks5h://127.0.0.1:10808 -s --max-time 10 https://httpbin.org/ip
```

## Cloudflare 节点 IP 范围

CF 节点通常是 anycast IP，常见端口：
- 443 (HTTPS)
- 8443, 2053, 2083, 2087, 2096 (替代端口)
- 2052 (HTTP, 非 TLS)
