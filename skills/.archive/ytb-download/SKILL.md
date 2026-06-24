---
name: ytb-download
description: 下载 YouTube 视频并上传到夸克网盘（Alist）。触发词：ytb下载：网址
category: media
---

# YouTube 下载 → 夸克网盘

## 触发方式

用户发送：`ytb下载：网址` 或 `ytb下载：https://www.youtube.com/watch?v=xxx`

## ⚠️ 先决条件：YouTube Cookie

**2025年起 YouTube 有强 bot 检测，必须传入有效 cookie 才能下载。** 没有 cookie 会报 `"Sign in to confirm you're not a bot"`。

## ⚡ 关键经验（从实际失败中总结）

### Snap Chromium Cookie 加密陷阱

服务器安装的是 **Snap 版 Chromium**，其 cookie 在磁盘上用 OSCrypt/AES 加密存储。以下方法**不可行**：
- `--cookies-from-browser chromium` → 找不到 Snap 的 cookie 目录
- `sqlite3` 直接读取 Cookies 数据库 → 所有 value 字段为空（加密）
- 拷贝 cookie 数据库到其他目录 → 加密不兼容

**唯一可行的方法**：通过 CDP (Chrome DevTools Protocol) 从**正在运行**的浏览器进程中提取。

### 致命重灾区：先登录再重启浏览器会丢失 Cookie

用户登录后若杀进程重启浏览器，**登录状态会丢失**（Snap 加密存储无法从磁盘恢复）。  
**正确流程**：浏览器必须从**一开始**就以 `--remote-debugging-port` 启动，用户登录后直接从运行中进程提取 cookie。

### Cookie 获取的正确完整流程

#### 步骤 1：启动 Chromium（带 remote debugging + 代理）

```bash
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu \
  --proxy-server=http://127.0.0.1:10809 \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --start-maximized https://www.youtube.com
```

**关键参数：**
- `--proxy-server=http://127.0.0.1:10809` — YouTube 在中国被墙，必须过代理
- `--remote-debugging-port=9222` — 启用 CDP 接口
- `--remote-allow-origins=*` — 允许 WebSocket 连接（不加会被 403 拒绝）
- **不要加 `--headless`** — 用户需要在 noVNC 里操作登录
- **不要中途杀浏览器** — 登录后 cookie 只在内存进程里有效

#### 步骤 2：用户登录 YouTube

通过 noVNC (http://122.51.121.116:6080/vnc.html) 打开 YouTube，右上角登录 Google 账号。

#### 步骤 3：Agent 通过 CDP 提取 cookie（Python）

```python
import json, urllib.request, websocket

resp = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
tabs = json.loads(resp.read())
ws_url = tabs[0]['webSocketDebuggerUrl']

ws = websocket.create_connection(ws_url, timeout=10)
ws.send(json.dumps({"id": 1, "method": "Network.enable"})); ws.recv()
ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
resp = json.loads(ws.recv()); ws.close()
```

#### 步骤 4：保存为有效 Netscape 格式

⚠️ **格式陷阱：必须保留前导点 `.`**

Python `http.cookiejar` 要求：如果一个 cookie 在浏览器中的 domain 是 `.youtube.com`（前导点），则 cookies.txt 中的 domain 字段必须写 `.youtube.com`，同时 `includeSubdomains=TRUE`。  
如果去掉前导点写成 `youtube.com + TRUE`，Python 解析时会 assert 失败：

```
AssertionError: assert domain_specified == initial_dot
```

⚠️ **Session cookie 的 expires 处理**：`expires=-1` 的 cookie 会被 yt-dlp 跳过。  
应记为未来时间戳（如当前时间 + 1年）。

```python
import time
FUTURE = int(time.time()) + 365*86400

with open("/tmp/yt-cookies.txt", "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for c in cookies_data:
        domain = c.get('domain', '')     # 保留前导点如 .youtube.com
        include_sub = "TRUE" if domain.startswith('.') else "FALSE"
        path = c.get('path', '/')
        secure = "TRUE" if c.get('secure', False) else "FALSE"
        expires = int(c.get('expires', 0))
        if expires <= 0:                 # session cookie → 设未来时间
            expires = FUTURE
        name = c.get('name', '')
        value = c.get('value', '')
        f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
```

### CDP 启动方式

如果 noVNC 的 Chromium 未以 remote debugging 模式启动，需要重启：

```bash
killall chromium-browser 2>/dev/null
sleep 2
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --start-maximized https://www.youtube.com
```

**关键参数：**
- `--remote-debugging-port=9222` — CDP 端口
- `--remote-allow-origins=*` — 允许 WebSocket 连接（不加会被 403 拒绝）

## 工作流程

```
用户说 ytb下载: URL
     ↓
1. 获取 YouTube cookie（见上方）
     ↓
2. yt-dlp 下载视频（最高 1080p，mp4，嵌入元数据）
     ↓
3. 通过 Alist API 上传到 /夸克网盘/YouTube/
     ↓
4. 清理临时文件
     ↓
输出结果给用户
```

## 完整执行脚本

使用 `execute_code` 执行以下 Python 脚本：

```python
import os, subprocess, json, urllib.request, glob, websocket

URL = "用户提供的 YouTube URL"
os.environ['PATH'] = f"/home/ubuntu/.deno/bin:{os.environ.get('PATH', '')}"
os.environ['no_proxy'] = '*'

# ========== 1. 获取 cookie（CDP 方式）==========
# 假设 Chromium 已在 :99 上以 remote debugging 模式运行
try:
    resp = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5)
    tabs = json.loads(resp.read())
    ws_url = tabs[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Network.enable"})); ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
    cookies_data = json.loads(ws.recv())['result']['cookies']
    ws.close()

    # 保存为 Netscape 格式
    FUTURE = int(time.time()) + 365*86400
    with open("/tmp/yt-cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
        for c in cookies_data:
            domain = c['domain']           # 保留前导点如 .youtube.com
            include_sub = "TRUE" if domain.startswith('.') else "FALSE"
            path = c.get('path', '/')
            secure = "TRUE" if c.get('secure') else "FALSE"
            expires = int(c.get('expires', 0))
            if expires <= 0:               # 修复 session cookie 的 -1 问题
                expires = FUTURE
            f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{c['name']}\t{c['value']}\n")
    COOKIE_ARG = ["--cookies", "/tmp/yt-cookies.txt"]
    print("✅ Cookie extracted via CDP")
except Exception as e:
    print(f"⚠️ CDP failed: {e}, trying without cookies...")
    COOKIE_ARG = []
# ========== 2. 下载 ==========
download_dir = "/tmp/ytb-download"
os.makedirs(download_dir, exist_ok=True)
os.system(f"rm -rf {download_dir}/*")

ytdlp = "/home/ubuntu/.hermes/hermes-agent/venv/bin/yt-dlp"
cmd = [ytdlp, "--proxy", "http://127.0.0.1:10809",
       "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
       "-o", f"{download_dir}/%(title).100B.%(ext)s",
       "--embed-thumbnail", "--embed-metadata",
       "--merge-output-format", "mp4",
       "--js-runtimes", "deno:/home/ubuntu/.deno/bin/deno",
       *COOKIE_ARG, URL]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if result.returncode != 0:
    print(f"ERROR: {result.stderr[-1000:]}")
    exit(1)

import glob
files = glob.glob(f"{download_dir}/*.mp4")
video_path = files[0]
video_name = os.path.basename(video_path)
file_size = os.path.getsize(video_path)
print(f"✅ {video_name} ({file_size/1024/1024:.1f}MB)")

# ========== 3. 上传到夸克 ==========
token = json.loads(urllib.request.urlopen(
    urllib.request.Request("http://127.0.0.1:5244/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}).encode(),
        headers={"Content-Type": "application/json"})).read())['data']['token']

urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:5244/api/fs/mkdir",
    data=json.dumps({"path": "/夸克网盘/YouTube"}).encode(),
    headers={"Authorization": token, "Content-Type": "application/json"}))

with open(video_path, 'rb') as f:
    data = f.read()
urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:5244/api/fs/put",
    data=data, headers={"Authorization": token,
        "File-Path": f"/夸克网盘/YouTube/{video_name}",
        "Content-Type": "video/mp4"}))

# ========== 4. 清理 ==========
os.system(f"rm -rf {download_dir} /tmp/yt-cookies.txt 2>/dev/null")
print(f"✅ 上传完成 /夸克网盘/YouTube/{video_name}")
```

## 注意事项

1. **DNS/代理** — 服务器在中国，必须走 `http://127.0.0.1:10809` 代理访问 YouTube
2. **Cookie 是第一优先级** — 无 cookie 必失败，优先启动 CDP 获取
3. **CDP 端口争议** — Chromium 必须以 `--remote-debugging-port=9222 --remote-allow-origins=*` 启动
4. **Netscape 格式** — yt-dlp 的 --cookies 严格解析 cookies.txt。**domain 字段必须保留前导点**（如 `.youtube.com`），因为 Python http.cookiejar 会 assert `domain_specified == initial_dot`。同时 session cookie 的 `expires=-1` 要改为未来时间戳。
5. **Alist API 注意事项** — `--noproxy "*"` 绕过代理；`/api/admin/storage/update` 用 POST 不是 PUT；上传用 `/api/fs/put`
6. **文件清理** — 下载和 cookie 文件存储在 /tmp/，上传完成后立即删除
7. **Deno** — /home/ubuntu/.deno/bin/ 需要在 PATH 中供 yt-dlp 的 JS challenge solver 使用

## 参考

- Cookie 提取详细技术方案：参见 `cloud-sync` skill 的 `references/snap-chromium-cookie-extraction.md`
