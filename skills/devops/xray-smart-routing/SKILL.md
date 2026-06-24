---
name: xray-smart-routing
description: "Xray 智能分流配置 — 按 VPS 地区策略：中国大陆 VPS 海外走代理，海外 VPS 仅被墙网站走代理。含 VLESS/REALITY 节点配置、geosite/geoip 路由、systemd 服务化、多节点对比测试。"
version: 1.1.0
---

# Xray 智能分流

> 在 VPS 上配置 Xray 智能分流。VPS 所在地区决定路由策略：
> - **中国大陆 VPS**：国内直连 + 指定海外域名走代理（`default=direct`，catch-all）
> - **海外 VPS（新加坡/日本/美国等）**：默认直连 + 仅被墙网站走代理（`default=direct`）

## 触发条件

- 「配代理」「搭建代理」「Xray」「分流」「翻墙」「科学上网」
- 服务器在中国大陆，需要访问海外服务（GitHub、Google 等）
- 或服务器在海外（新加坡/日本等），但需要代理访问被墙服务（Google/X/Twitter 等）
- 用户有现成的 VLESS/V2Ray 代理节点

## 安装 Xray

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

安装后 geo 文件在 `/usr/local/xray/geoip.dat` 和 `/usr/local/xray/geosite.dat`。

## 配置策略：按 VPS 地区选择

### 🏠 中国大陆 VPS — default=direct（catch-all）

```
geosite:cn + geoip:cn + geoip:private → direct（中国流量）
指定海外域名（geosite:google, geosite:github 等）→ proxy（海外流量）
其余所有未匹配流量     → direct（catch-all）
```

⚠️ **必须加 catch-all direct 规则**，否则未匹配域名走默认 outbound（proxy），造成不必要代理。

正确结构（最后一条规则 catch-all）：
```json
{
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {"type": "field", "outboundTag": "block", "domain": ["geosite:category-ads-all"]},
      {"type": "field", "outboundTag": "proxy", "domain": ["geosite:google", "geosite:github", ...]},
      {"type": "field", "outboundTag": "direct", "domain": ["geosite:cn"], "ip": ["geoip:cn", "geoip:private"]},
      {"type": "field", "outboundTag": "direct", "network": "tcp,udp"}  // ← catch-all
    ]
  }
}
```

**域名策略**：`IPIfNonMatch`（推荐）— 优先域名匹配，未匹配则解析 DNS 后查 IP 规则，能 catch 未显式列出的国内域名。

**使用 geosite 组**（替代逐个域名）：
- `geosite:google` → google.com, googleapis.com, youtube.com 等 50+
- `geosite:github` → github.com, githubusercontent.com
- `geosite:openai` → openai.com, chatgpt.com, oaistatic.com
- `geosite:telegram` → telegram.org, t.me
- `geosite:twitter` → twitter.com, x.com, twimg.com
- `geosite:facebook` → facebook.com, fbcdn.net, instagram.com
- `geosite:reddit`, `geosite:discord`, `geosite:cloudflare`

见 `templates/config-smart-routing.json`。

### 🌏 海外 VPS（新加坡/日本/美国等）— default=direct
```
被墙域名列表（Google/X/OpenAI等） → proxy（黑名单模式）
其余所有流量              → direct（默认）
```
默认直连比默认代理快得多。以新加坡 Vultr VPS 为例：
- GitHub API 直连 0.45s vs 代理 1.78s（快 4x）
- DeepSeek API 直连 0.36s vs 代理 0.34s（持平）
- raw.githubusercontent.com 直连 0.49s vs 代理 3.33s（快 7x）
- 仅 Google、X/Twitter、OpenAI、Claude 等被墙服务需代理

见 `templates/config-overseas-direct.json`。

### 1. 基础配置（智能分流）

Xray 配置由三部分组成：

**Inbounds** — 本地监听端口：
- `10808` SOCKS5 代理
- `10809` HTTP 代理

**Outbounds** — 出口链路：
- `proxy` — VLESS/REALITY 节点（海外）
- `direct` — freedom 直连（国内）
- `block` — blackhole 屏蔽广告

**Routing** — 分流规则（China VPS, catch-all=direct）：
- `geosite:category-ads-all` → block
- `geosite:google`, `geosite:github`, 及其他指定海外域名 → proxy
- `geosite:cn` + `geoip:cn` + `geoip:private` → direct
- 剩余流量 → direct（catch-all，非 proxy）

### 2. VLESS 节点配置格式

**REALITY 模式（常见）**：
```json
{
  "tag": "proxy",
  "protocol": "vless",
  "settings": {
    "vnext": [{
      "address": "<host>",
      "port": <port>,
      "users": [{
        "id": "<uuid>",
        "encryption": "none",
        "flow": "xtls-rprx-vision"
      }]
    }]
  },
  "streamSettings": {
    "network": "tcp",
    "security": "reality",
    "realitySettings": {
      "serverName": "<domain>",
      "fingerprint": "chrome",
      "publicKey": "<public_key>",
      "shortId": "<short_id>"
    }
  }
}
```

**TLS 模式（备选）**：
```json
{
  "tag": "proxy",
  "protocol": "vless",
  "settings": {
    "vnext": [{
      "address": "<host>",
      "port": <port>,
      "users": [{
        "id": "<uuid>",
        "encryption": "none",
        "flow": ""
      }]
    }]
  },
  "streamSettings": {
    "network": "tcp",
    "security": "tls",
    "tlsSettings": {
      "serverName": "<domain>",
      "fingerprint": "chrome"
    }
  }
}
```

## 从订阅链接更新节点

代理提供商通常给一个订阅 URL（如 `https://example.com/sub?token=xxx`），返回 Base64 编码的 VLESS/VMess 链接列表。

### 工作流

```bash
# 1. 获取订阅内容（Base64 编码）
curl -sL "https://example.com/sub?token=xxx" | base64 -d
```

订阅解码后是 VLESS URI 格式（每行一个节点）：

```
vless://<uuid>@<host>:<port>?security=tls&type=ws&host=<sni>&fp=chrome&sni=<sni>&path=%2F&encryption=none#节点名称
```

### VMess URI 解析

VMess URI 格式与 VLESS 不同 — 服务器地址/端口/密码/加密方式都编码在 Base64 部分中，而查询参数包含路径/伪装等。

**格式**：
```
vmess://base64(method:uuid@server:port)?path=<path>&remarks=<备注>&obfsParam=<host>&obfs=websocket&tls=1&peer=<sni>&udp=1&alterId=0
```

**Base64 解码示例**：
```bash
echo "YXV0bzo0MzFhYTMxOS1mZGQzLTQ4YmMtOGUwZC0zZTYzYjdiZmNhZTdAY2xvdWRmbGFyZS1lY2guY29tOjQ0Mw" | base64 -d
# → auto:431aa319-fdd3-48bc-8e0d-3e63b7bfcae7@cloudflare-ech.com:443
#   ↑method ↑uuid                      ↑server              ↑port
```

**VMess URI → Xray JSON 映射**：

| URI 字段 | 来源 | Xray JSON 位置 |
|---|---|---|
| `uuid` | Base64 部分 | `settings.vnext[].users[].id` |
| `server` | Base64 部分 `@` 后 | `settings.vnext[].address` |
| `port` | Base64 部分 `:` 后 | `settings.vnext[].port` |
| `method` | Base64 部分 `:` 前 | `settings.vnext[].users[].security`（通常"auto"→aes-128-gcm） |
| `alterId` | 查询参数 | `settings.vnext[].users[].alterId` |
| `obfs=websocket` | 查询参数 | `streamSettings.network: "ws"` |
| `tls=1` | 查询参数 | `streamSettings.security: "tls"` |
| `peer` | 查询参数 | `streamSettings.tlsSettings.serverName` |
| `obfsParam` | 查询参数 | `streamSettings.wsSettings.headers.Host`（旧语法）或 `streamSettings.wsSettings.host`（新语法） |
| `path` | 查询参数 | `streamSettings.wsSettings.path` |

**VMess WS+TLS 配置模板**：
```json
{
  "tag": "proxy",
  "protocol": "vmess",
  "settings": {
    "vnext": [{
      "address": "<server>",
      "port": <port>,
      "users": [{
        "id": "<uuid>",
        "security": "auto",
        "alterId": 0
      }]
    }]
  },
  "streamSettings": {
    "network": "ws",
    "security": "tls",
    "tlsSettings": {
      "serverName": "<peer/sni>",
      "fingerprint": "chrome"
    },
    "wsSettings": {
      "path": "/<path>",
      "headers": {
        "Host": "<obfsParam>"
      }
    }
  }
}
```

### VLESS URI → Xray JSON 映射

| URI 参数 | Xray JSON 位置 |
|---|---|
| `uuid` | `settings.vnext[].users[].id` |
| `@host:port` | `settings.vnext[].address`, `settings.vnext[].port` |
| `type=ws` | `streamSettings.network: "ws"` |
| `security=tls` | `streamSettings.security: "tls"` |
| `host=<sni>` | `streamSettings.tlsSettings.serverName` + `streamSettings.wsSettings.headers.Host` |
| `sni=<sni>` | `streamSettings.tlsSettings.serverName` |
| `fp=chrome` | `streamSettings.tlsSettings.fingerprint: "chrome"` |
| `path=%2F` | `streamSettings.wsSettings.path: "/"` |

**注意**：Xray 26.x 起 `"host" in "headers"` 已废弃，应改用独立的 `"host"` 字段：
```json
"wsSettings": {
  "path": "/",
  "host": "your-domain.com"  // 推荐（新语法）
  // "headers": {"Host": "your-domain.com"}  // 不推荐（旧语法，有 deprecation warning）
}
```

### 更新配置步骤

```bash
# 1. 提取订阅链接，解码并选择节点
curl -sL "订阅链接" | base64 -d

# 2. 生成新配置 → 写入临时文件
cat > /tmp/xray-config.json << 'EOF'
{...新配置...}
EOF

# 3. 替换并重启
sudo cp /tmp/xray-config.json /usr/local/xray/config.json
sudo systemctl restart xray.service

# 4. 验证
curl -x http://127.0.0.1:10809 -s -o /dev/null -w "%{http_code}|%{time_total}s\n" https://www.google.com
```

### 备选节点策略

订阅通常返回多个 IP（同一 UUID 走的 Cloudflare 不同边缘节点）。推荐：
- 选**第一个**作为主节点
- 额外挑 2-3 个不同 IP 段（如不同 Cloudflare anycast IP）作为备用
- 用不同的 outbound tag（`proxy`, `proxy-bak1`, `proxy-bak2`）但主路由只指向 `proxy`
- 如果主节点挂了，手动改 routing 切到备用 tag

多节点测速对比：
```bash
for port in 10809 10811 10812; do
  echo "端口 $port: $(curl -x http://127.0.0.1:$port -s -o /dev/null -w '%{http_code}|%{time_total}s|%{speed_download}B/s\n' https://www.google.com)"
done
```

### 常见坑

- **SOCKS5 超时但 HTTP 代理正常**：Socks5 的 UDP 支持在某些 Xray 版本/节点组合下会异常慢。测试时优先用 HTTP 代理（:10809），SOCKS5 可用但设 30s+ 超时。
- **URL 路径 `/` 用 `%2F` 编码**：解码后直接写 `"path": "/"`，Xray 会自动处理。
- **订阅链接本身需要代理才能访问**：先在 Xray 里手动配一个节点访问订阅，拿到更多节点。
- **Xray 26.x WS deprecation**：WebSocket 传输在 Xray 26.x 被标记为 deprecated，建议迁移到 XHTTP H2/H3。但 WS 短期内仍可用，不影响功能。

## 从 Shadowrocket JSON 提取节点参数

当用户发来 Shadowrocket 格式的节点 JSON 时，映射关系如下：

| Shadowrocket 字段 | Xray 配置位置 |
|---|---|
| `host` | `outbounds[].settings.vnext[].address` |
| `port` | `outbounds[].settings.vnext[].port` |
| `uuid` | `outbounds[].settings.vnext[].users[].id` |
| `type` | `protocol`（VLESS/VMess） |
| `tls: true` + `publicKey` | `streamSettings.security: "reality"` |
| `tls: true` 无 publicKey | `streamSettings.security: "tls"` |
| `xtls: 2` | `flow: "xtls-rprx-vision"` |
| `peer` | `realitySettings.serverName` |
| `publicKey` | `realitySettings.publicKey` |
| `shortId` | `realitySettings.shortId` |

## 完整配置模板

见 `templates/config-smart-routing.json`。

## 启动与持久化

### 手工启动
```bash
/usr/local/xray/xray run -c /usr/local/xray/config.json
```

### systemd 服务
```ini
[Unit]
Description=Xray Proxy Service (Smart Routing)
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/xray/xray run -c /usr/local/xray/config.json
Restart=on-failure
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable xray.service
sudo systemctl start xray.service
```

### 环境变量持久化
```bash
echo 'export http_proxy=http://127.0.0.1:10809' >> ~/.bashrc
echo 'export https_proxy=http://127.0.0.1:10809' >> ~/.bashrc
echo 'export HTTP_PROXY=http://127.0.0.1:10809' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:10809' >> ~/.bashrc
echo 'export NO_PROXY=localhost,127.0.0.1,.local,.cn' >> ~/.bashrc
```

## 验证测试：确认分流策略正确

### 方法1：对比直连 vs 走代理的速度差

```bash
echo "=== 直连 ==="
for url in "https://api.github.com" "https://www.google.com" "https://api.deepseek.com"; do
  timeout 8 curl -s --noproxy '*' -o /dev/null -w "$url → %{http_code}|%{time_total}s\n" "$url"
done

echo "=== 走代理 ==="
for url in "https://api.github.com" "https://www.google.com" "https://api.deepseek.com"; do
  timeout 8 curl -s -x http://127.0.0.1:10809 -o /dev/null -w "$url → %{http_code}|%{time_total}s\n" "$url"
done
```

**解读**：
- 如果直连比代理快 → 该域名应走 direct 路由
- 如果代理比直连快（或直连超时）→ 该域名应走 proxy 路由
- 以新加坡 VPS 为例：GitHub 直连比代理快 4x → direct；Google 直连超时 → proxy

### 方法2：路由规则生效验证

```bash
# 应走代理（查看 Xray 日志确认）
curl -s --noproxy '*' https://www.google.com
# 应走直连  
curl -s --noproxy '*' https://api.github.com
curl -s --noproxy '*' https://api.deepseek.com/v1/models
```

### 方法3：git 连通性测试

```bash
# HTTPS 直连
timeout 15 git ls-remote https://github.com/USER/REPO.git

# HTTPS 走代理
timeout 15 git -c http.proxy=http://127.0.0.1:10809 ls-remote https://github.com/USER/REPO.git
```

```bash
# 国内（应走直连，快速响应）
curl -x http://127.0.0.1:10809 -s -o /dev/null -w "%{http_code} | %{time_total}s\n" https://www.baidu.com

# 海外（应走代理）
curl -x http://127.0.0.1:10809 -s -o /dev/null -w "%{http_code} | %{time_total}s\n" https://www.google.com
curl -x http://127.0.0.1:10809 -s -o /dev/null -w "%{http_code} | %{time_total}s\n" https://api.github.com
```

## 多节点对比测试

可用两份配置分别跑在不同端口上并行对比：

```bash
# 节点A (主配置, 端口 10808/10809)
/usr/local/xray/xray run -c /usr/local/xray/config.json

# 节点B (SG/备用, 端口 10810/10811)
/usr/local/xray/xray run -c /tmp/xray-sg-config.json

# 对比测试
for url in "https://www.google.com" "https://api.github.com" "https://www.youtube.com"; do
  echo "节点A: $(curl -x http://127.0.0.1:10809 -s -o /dev/null -w '%{http_code}|%{time_total}s|%{speed_download}B/s' $url)"
  echo "节点B: $(curl -x http://127.0.0.1:10811 -s -o /dev/null -w '%{http_code}|%{time_total}s|%{speed_download}B/s' $url)"
done
```

## 常见坑

### 🔴 节点连接失败：000 HTTP 码

现象：所有请求返回 `000|0.2s` — 连接立即失败。

排查步骤：
1. 验证节点可达：`host <address>` + `timeout 10 bash -c 'echo >/dev/tcp/<host>/<port>'`
2. **SSL_ERROR_SYSCALL** → REALITY 握手失败，检查 `publicKey`/`shortId`/`serverName`
3. **wrong version number** → 服务端非 TLS，试试 `security: "reality"` 而非 `"tls"`
4. 节点可能对该 IP 有限制，换节点测试

### 🟡 应用通过代理连接时 — httpx.Client() proxy 参数

不同 httpx 版本的代理参数名不同：

| httpx 版本 | 参数名 |
|---|---|
| < 0.28 | `proxies="http://..."` |
| >= 0.28 | `proxy="http://..."` |

**症状**：`TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`

**修复**：检查 httpx 版本，使用正确的参数名：
```bash
python3 -c "import httpx; print(httpx.__version__)"
```
```python
# httpx >= 0.28
client = httpx.Client(proxy="http://127.0.0.1:10809")

# httpx < 0.28
client = httpx.Client(proxies="http://127.0.0.1:10809")
```

### 🟡 geosite:cn 不生效

检查 `domainStrategy`：
- `IPIfNonMatch`（推荐）— 优先域名匹配，未匹配则解析 DNS 后查 IP 规则。未显式列出的国内域名也能被 `geoip:cn` catch。
- `AsIs` — 仅用域名匹配。如果 `geosite:cn` 版本过旧，新出现的国内域名可能不命中。此时设 `IPIfNonMatch` 让 DNS 解析后二次匹配 `geoip:cn`。

### 🟡 `--noproxy '*'` 必须用——不限于 localhost

设置了 `http_proxy` 环境变量后，`curl` 会把**所有**请求（包括外网 IP 如 `64.176.82.81`）都发往代理，导致测试结果不可靠。

**症状**：
- `curl http://localhost:8000/` → 503（通过代理发到本地）
- `curl http://64.176.82.81:8504/api/` → 503（代理返回不可达）
- 误判为端口不通或服务不可用

**修复**：测试时始终加 `--noproxy '*'` 绕过全局代理
```bash
# ✅ 正确：直连测试
curl --noproxy '*' http://localhost:8504/api/hermes/health

# ✅ 正确：外网测试（SSH 不走 http_proxy，但 curl 走）
curl --noproxy '*' http://64.176.82.81:8504/api/hermes/health

# ❌ 错误：会走代理
curl http://localhost:8504/api/hermes/health
```

**`NO_PROXY` 环境变量不保证被所有工具读取**，curl 通常读取但不一定生效。当怀疑代理干扰时：
1. 先用 `env | grep -i proxy` 确认代理环境变量
2. 测试时始终 `--noproxy '*'`
3. 生产脚本考虑 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY`

### 🟡 订阅链接返回「订阅链接无效」

节点 JSON 中的 `data` 字段通常是 Shadowrocket 订阅 URL。常见失败原因：
- 链接已过期（需重新生成）
- 需要从源服务器通过代理才能访问（先在 Xray 配置文件里配一个节点，再去请求订阅）
- URL 路径编码问题（中文路径 `%E6%9E%81%E9%80%9FVPN` 可能不兼容）

### 🟡 systemd 服务文件常见错误

创建 `.service` 文件时，容易把 `[Service]` 和 `Type=simple` 写在同一行变成 `[Type=simple`。正确写法：
```ini
[Service]
Type=simple
```

用 `sudo systemctl status xray.service` 验证服务状态。如果显示 `inactive (dead)`，检查 `journalctl -u xray.service` 看错误日志。

### 🟡 codeload.github.com 通过代理超时

`codeload.github.com`（GitHub 源码下载 CDN）在某些代理节点下可能超时或极慢。如果该域名被列入 proxy 路由，`git clone` 或 `curl` 下载 tar.gz 文件可能挂起。

**修复**：将 `domain:codeload.github.com` 加入 direct 路由规则。

### 🟡 未匹配域名意外走代理（catch-all 缺失）

**症状**：没列入 proxy 规则的国外域名（如 `npmjs.org`, `vscode.dev`, `sentry.io`）也走代理，速度变慢。

**原因**：Xray 默认用第一个 outbound（proxy）处理未匹配流量。如果 direct 规则只列国内域名而没加 catch-all，其余流量全走代理。

**修复**：在 routing 最后加一条 catch-all direct：
```json
{"type": "field", "outboundTag": "direct", "network": "tcp,udp"}
```

同时设 `domainStrategy: "IPIfNonMatch"` 让不明确的域名通过 DNS 解析后匹配 `geoip:cn`。

### 🟡 旧 Xray 进程残留

当用 `sudo systemctl restart xray` 重启后，旧的手动启动的 Xray 进程（`/usr/local/xray/xray run -c ...` 不带 systemd）可能仍在运行，占用端口 10808/10809，导致新配置不生效。

**症状**：改了配置重启后，测试仍走旧路由。

**修复**：
```bash
# 找出并杀掉所有旧 Xray 进程
ps aux | grep xray | grep -v grep
sudo kill <old_pid_1> <old_pid_2>
# 确认只剩 systemd 管理的进程
sudo systemctl status xray
```

Google 本身在中国大陆访问慢，走代理后从海外节点出去反而更快。这是正常现象。

## 参考

- `references/cloudflare-ech-proxy.md` — Cloudflare ECH + Argo Tunnel 节点配置、VMess 订阅解码、SOCKS5 超时排查
- `references/nodes.md` — 节点测试记录和诊断日志
- `references/supabase-via-proxy.md` — 通过代理使用 Supabase Management API 的实践
- `references/subscription-workflow.md` — 订阅链接解码 → 生成 WS+TLS 节点配置的工作流
