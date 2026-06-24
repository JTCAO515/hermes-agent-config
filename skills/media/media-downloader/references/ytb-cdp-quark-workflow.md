# YouTube → Quark Cloud Disk Workflow

> Absorbed from standalone `ytb-download` skill (2026-06-02). Specific China-server workflow: download YouTube videos via yt-dlp with CDP cookie extraction, then upload to Quark cloud disk via Alist API.

## Overview

```text
User: "ytb下载: URL"
  ↓
1. Extract YouTube cookie via CDP (Chrome DevTools Protocol)
2. yt-dlp download video (max 1080p, mp4, embedded metadata)
3. Upload via Alist API to /夸克网盘/YouTube/
4. Clean up temp files
```

## ⚠️ Cookie Extraction is Critical

YouTube has strong bot detection since 2025. Must pass valid cookie.

### Snap Chromium Cookie Trap

Server uses Snap Chromium — cookies are AES-encrypted on disk. **These DON'T work:**
- `--cookies-from-browser chromium` — can't find Snap's cookie dir
- `sqlite3` direct read — all value fields are empty (encrypted)

**Only works:** CDP extraction from a running browser process.

### CDP Cookie Extraction

#### Step 1: Start Chromium with remote debugging

```bash
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu \
  --proxy-server=http://127.0.0.1:10809 \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --start-maximized https://www.youtube.com
```

**Key params:** `--remote-debugging-port=9222`, `--remote-allow-origins=*`, proxy for China.

**Do NOT** use `--headless` — user needs to log in via noVNC.
**Do NOT** kill the browser — cookies are only in running process memory.

#### Step 2: User logs in via noVNC

http://122.51.121.116:6080/vnc.html → open YouTube → sign in with Google.

#### Step 3: Extract cookies via CDP

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

#### Step 4: Save as Netscape format

⚠️ **Format trap:** Domain must keep leading dot (`.youtube.com`, not `youtube.com`) — Python `http.cookiejar` asserts `domain_specified == initial_dot`.

⚠️ **Session cookies:** `expires=-1` cookies are skipped by yt-dlp. Set to future timestamp instead.

```python
FUTURE = int(time.time()) + 365*86400
with open("/tmp/yt-cookies.txt", "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for c in cookies_data:
        domain = c['domain']  # keep leading dot
        include_sub = "TRUE" if domain.startswith('.') else "FALSE"
        path = c.get('path', '/')
        secure = "TRUE" if c.get('secure', False) else "FALSE"
        expires = int(c.get('expires', 0))
        if expires <= 0: expires = FUTURE
        f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{c['name']}\t{c['value']}\n")
```

## Download Script

```python
ytdlp = "/home/ubuntu/.hermes/hermes-agent/venv/bin/yt-dlp"
cmd = [ytdlp, "--proxy", "http://127.0.0.1:10809",
       "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
       "-o", f"{download_dir}/%(title).100B.%(ext)s",
       "--embed-thumbnail", "--embed-metadata",
       "--merge-output-format", "mp4",
       "--js-runtimes", "deno:/home/ubuntu/.deno/bin/deno",
       "--cookies", "/tmp/yt-cookies.txt", URL]
```

## Alist Upload

```python
# Login
token = json.loads(urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:5244/api/auth/login",
    data=json.dumps({"username": "admin", "password": "admin123"}).encode(),
    headers={"Content-Type": "application/json"})).read())['data']['token']

# Upload
with open(video_path, 'rb') as f:
    data = f.read()
urllib.request.urlopen(urllib.request.Request(
    "http://127.0.0.1:5244/api/fs/put",
    data=data, headers={"Authorization": token,
        "File-Path": f"/夸克网盘/YouTube/{video_name}",
        "Content-Type": "video/mp4"}))
```

## Important Notes

1. **DNS/Proxy:** Server in China, must use `http://127.0.0.1:10809` proxy for YouTube
2. **Cookie priority:** No cookie = failure. CDP extraction is the only reliable method
3. **CDP port:** Chromium must start with `--remote-debugging-port=9222 --remote-allow-own-origins=*`
4. **Deno PATH:** `/home/ubuntu/.deno/bin/` in PATH for yt-dlp JS challenge solver
5. **Cleanup:** Download and cookie files stored in /tmp/, delete after upload
