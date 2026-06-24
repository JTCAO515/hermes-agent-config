# Snap Chromium Cookie 提取

## 问题

Snap 版 Chromium 在磁盘上加密存储 cookie 值。用 `sqlite3` 或 Python 读取 `Cookies` 数据库时，`value` 字段全为空字符串：

```python
# ❌ 这样读出来的全是空值
import sqlite3
conn = sqlite3.connect('~/snap/chromium/common/chromium/Default/Cookies')
cur = conn.cursor()
cur.execute("SELECT host_key, name, value FROM cookies WHERE host_key LIKE '%quark%'")
# value 都是 ''
```

**原因：** Snap 版 Chromium 使用 Linux 内核密钥环（keyring）或加密存储，cookie 值只在浏览器进程内存中明文保存。

## 关键陷阱：httpOnly Cookie

`document.cookie` **只返回非 httpOnly 的 cookie。** 云盘等需要完整认证的场景，关键鉴权 cookie（如夸克的 `__user_token`、`__puus`）通常是 httpOnly 的，不会出现在 `document.cookie` 中。

**验证方式：** 如果提取结果包含 `ctoken=...; b-user-id=...` 等但缺少 `__puus`、`__user_token`、`__kp` 等关键字段，说明这些是 httpOnly cookie，需要用方案B或C提取。

## 解决方案

### 方案A：通过 DevTools Application 面板提取（✅ 推荐，能获取全部 cookie）

用户通过 noVNC 操作浏览器：

1. 浏览器已登录目标网站（如 pan.quark.cn）
2. 按 **F12** 打开 DevTools
3. 切到 **Application（应用）** 标签
4. 左侧展开 **Cookies** → 选择目标域名（如 `pan.quark.cn`）
5. 所有 cookie（含 httpOnly）会以表格显示
6. 在任意一行右键 → **Export as HAR**（推荐，会导出完整 cookie 字符串）或直接 Copy 所有行
7. 将完整 cookie 字符串复制给 Agent（格式应为 `key1=value1; key2=value2; key3=value3`）

**备用：通过 Console 获取（仅非 httpOnly cookie，不推荐作为唯一方法）**

如果确实不方便切换到 Application 面板，也可以通过 Console 获取，但请注意局限性：

```javascript
document.cookie
```

将完整输出复制给 Agent，并说明是否缺少 httpOnly 字段。

### 方案B：通过 CDP (Chrome DevTools Protocol) — Runtime.evaluate(document.cookie) ⚠️ 仅非 httpOnly

如果用户不能手动操作，重启 Chromium 并启用 remote debugging。此方案使用 `Runtime.evaluate` 执行 `document.cookie`，**同样只能获取非 httpOnly cookie**，效果等价于 Console 输入。如果需要 httpOnly cookie，见方案C。

```bash
# 杀掉已有 Chromium
killall chromium-browser 2>/dev/null

# 以 remote debugging 模式启动！关键参数：
#   --remote-allow-origins=* → 不加会被 WebSocket 403 拒绝
DISPLAY=:99 chromium-browser --no-sandbox \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  https://pan.quark.cn
```

然后通过 CDP 获取 cookie：

```python
import json, urllib.request, websocket

# 获取 WebSocket URL
resp = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(resp.read())
ws_url = tabs[0]['webSocketDebuggerUrl']

# 连接 CDP
ws = websocket.create_connection(ws_url, timeout=10)

# 发送 Runtime.evaluate 命令
ws.send(json.dumps({
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "document.cookie",
        "returnByValue": True
    }
}))
result = json.loads(ws.recv())
cookie_str = result["result"]["result"]["value"]
print(cookie_str)
```

**⚠️ 这个方案依然只返回非 httpOnly cookie**，用于夸克网盘等需要 httpOnly cookie 的云盘时，仍然会报 `require login [guest]`。

### 方案C：通过 CDP Network.getAllCookies ✅ 获取所有 cookie（含 httpOnly）

这是唯一能通过 CDP **获取 httpOnly cookie** 的方法。使用 Network 域的 `getAllCookies` 方法，该 API 返回浏览器中**所有** cookie。

```bash
# Chromium 启动方式同方案B
DISPLAY=:99 chromium-browser --no-sandbox \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  https://target-site.com
```

```python
import json, urllib.request, websocket

# 获取 WebSocket URL
resp = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(resp.read())
ws_url = tabs[0]['webSocketDebuggerUrl']

# 连接 CDP
ws = websocket.create_connection(ws_url, timeout=10)

# 启用 Network 域
ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
ws.recv()

# 获取所有 cookie（含 httpOnly）
ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
resp = json.loads(ws.recv())
cookies = resp['result']['cookies']
ws.close()

# cookies 中每个元素包含: name, value, domain, path, expires, httpOnly, secure, sameSite
# 重建 cookie 字符串
cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
print(cookie_str)

# 如果需要保存为 yt-dlp 可用的 Netscape 格式
with open("/tmp/yt-cookies.txt", "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for c in cookies:
        domain = c['domain']  # 保留前导点！如 .youtube.com — 去掉会导致 assert 失败
        include_sub = "TRUE" if c['domain'].startswith('.') else "FALSE"
        path = c.get('path', '/')
        secure = "TRUE" if c.get('secure') else "FALSE"
        expires = int(c.get('expires', 0)) or 0
        f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{c['name']}\t{c['value']}\n")
```

**⚠️ Nescape 格式关键陷阱：必须保留 domain 前导点 `.`**

Python `http.cookiejar` 要求：如果一个 cookie 在浏览器中的 domain 是 `.youtube.com`（前导点，表示子域名共享），则 cookies.txt 中的 domain 字段**必须写 `.youtube.com`**，同时 `includeSubdomains=TRUE`。

如果去掉前导点写成 `youtube.com + TRUE`，Python 解析时会 assert 失败：
```
AssertionError: assert domain_specified == initial_dot
yt-dlp 报错：invalid Netscape format cookies file
```

**✅ 正确写法：**
```python
domain = c['domain']  # 保留前导点如 .youtube.com
include_sub = "TRUE" if domain.startswith('.') else "FALSE"
```

**❌ 错误写法（会导致 AssertionError）：**
```python
domain = c['domain'].lstrip('.')  # ⚠️ 去掉前导点后 + TRUE 会触发 assert 失败
```

**⚠️ Session cookie 的 expires 处理：** `expires=-1` 的 cookie 会被 yt-dlp 跳过。应记为未来时间戳（如当前时间 + 1年）。

```python
import time
FUTURE = int(time.time()) + 365*86400
expires = int(c.get('expires', 0))
if expires <= 0:
    expires = FUTURE
```

完整正确的 Netscape 格式写入代码：
```python
import time
FUTURE = int(time.time()) + 365*86400
with open("/tmp/cookies.txt", "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for c in cookies:
        domain = c['domain']           # 保留前导点如 .youtube.com ✅
        include_sub = "TRUE" if domain.startswith('.') else "FALSE"
        path = c.get('path', '/')
        secure = "TRUE" if c.get('secure') else "FALSE"
        expires = int(c.get('expires', 0))
        if expires <= 0:               # 修复 session cookie 的 -1 问题
            expires = FUTURE
        f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{c['name']}\t{c['value']}\n")
```
- 格式错误的 cookies.txt 会导致 yt-dlp 报 `invalid Netscape format` 错误

**注意：** xdotool 方案很脆弱，窗口焦点的变化可能导致按键打到错误位置。推荐优先用方案A或方案C。

```bash
# 确保 DISPLAY 正确
export DISPLAY=:99

# 聚焦 Chromium 窗口
xdotool search --name "Chromium" windowactivate

# 打开 DevTools (F12)
xdotool key F12
sleep 2

# 切换到 Console（如果 DevTools 默认不是 Console 标签）
xdotool key ctrl+shift+i  # 或者根据实际情况调整

# 输入 JS 代码
xdotool type "document.cookie"
sleep 1
xdotool key Return
```

**注意：** xdotool 方案很脆弱，窗口焦点的变化可能导致按键打到错误位置。推荐优先用方案A。

## 验证

提取后的 cookie 应该是一个分号分隔的 `key=value` 字符串，如：
```
__pus=xxx; __uu=yyy; __user_token=zzz; __quark__platId=1; ...
```

如果提取结果只有 `key=` 没有 `value`（如 `__puus=`），说明 cookie 仍是加密/空状态，需要按方案A或B在浏览器运行时获取。
