---
name: media-downloader
description: 视频/音频下载工具链。yt-dlp + deno + ffmpeg 安装、配置、下载工作流。支持 YouTube 等数百个网站，自动嵌入元数据/字幕/封面。
version: 1.0.0
triggers:
  - "下载视频/下载音频/yt-dlp/YouTube下载/视频下载工具"
  - "配置yt-dlp/安装deno/ffmpeg配置"
---

# 媒体下载器 (Media Downloader)

yt-dlp + deno + ffmpeg 构成的下载工具链。

## 首次安装后的测试流程

安装完 yt-dlp + deno + ffmpeg 后，**必须先测试**再正式下载，避免跑通了才发现bot检测或缺失依赖：

```bash
# 1. 先测试基础连通性
yt-dlp --print title --print duration "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# 2. 如果返回bot检测错误，尝试 Android 客户端模拟
yt-dlp --extractor-args "youtube:player_client=android" --print title "URL"

# 3. 如果Android客户端也不行，尝试组合客户端
yt-dlp --extractor-args "youtube:player_client=android,web" --print title "URL"

# 4. 实在不行再上cookies
# yt-dlp --cookies-from-browser chrome "URL"
```

## 安装

```bash
# yt-dlp (pip)
# 中国网络环境下用清华镜像加速
pip3 install yt-dlp -i https://pypi.tuna.tsinghua.edu.cn/simple
# ⚠️ 确认安装成功: yt-dlp --version

# deno (JavaScript运行时, 用于youtube提取)
# 先确认YouTube连通性(中国网络可直达youtube.com→200)
curl -s -o /dev/null -w "%{http_code}" "https://www.youtube.com"
# 安装deno
curl -fsSL https://deno.land/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"
echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc
# ⚠️ 安装后立即验证 PATH 生效: deno --version
# yt-dlp 通过 $PATH 自动发现 deno，无需额外配置

# ffmpeg (视频音频合并)
sudo apt install ffmpeg  # Ubuntu/Debian
which ffmpeg && ffmpeg -version | head -1  # 验证
```

## 配置

### yt-dlp 配置文件 `~/.config/yt-dlp/config`

```ini
# JavaScript运行时
--js-runtimes deno

# 输出路径和命名
--output ~/yt-dlp/%(title)s.%(ext)s

# 最佳画质(1080p封顶)
-f bestvideo[height<=1080]+bestaudio/best[height<=1080]

# 嵌入元数据
--embed-metadata
--embed-thumbnail

# 字幕
--sub-langs all
--embed-subs

# 写入信息文件
--write-info-json
--write-description

# 避免重复下载
--no-overwrites
```

## 常用命令

### 下载视频（最佳质量）
```bash
yt-dlp "https://www.youtube.com/watch?v=..."
```

### 仅下载音频（MP3）
```bash
yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=..."
```

### 指定画质
```bash
# 最高4K
yt-dlp -f "bestvideo[height<=2160]+bestaudio/best[height<=2160]" "URL"

# 仅720p
yt-dlp -f "best[height<=720]" "URL"
```

### 下载播放列表
```bash
yt-dlp --playlist-start 1 --playlist-end 10 "https://www.youtube.com/playlist?list=..."
```

### 自定义文件名
```bash
yt-dlp -o "%(playlist_index)s-%(title)s.%(ext)s" "URL"
```

### 测试/预览(不下载)
```bash
# 先测试能否获取元数据(不下载,快速验证)
yt-dlp --extractor-args "youtube:player_client=android" \
  --print title --print duration "URL"

# 列出所有可用格式
yt-dlp -F "URL"

# 跳过bot检测直接预览
yt-dlp --extractor-args "youtube:player_client=android" \
  --print title --print filename "URL"
```

## 常见问题

### 1. "Sign in to confirm you're not a bot"

server 环境没有浏览器 cookie，**推荐使用 Android 客户端模拟**（成功率 >80%）：

```bash
# 推荐: 模拟Android客户端(最有效)
yt-dlp --extractor-args "youtube:player_client=android" "URL"

# 也可组合多个客户端
yt-dlp --extractor-args "youtube:player_client=android,web" "URL"

# 预处理: 先用--print测试是否绕过成功
yt-dlp --extractor-args "youtube:player_client=android" \
  --print title "URL"
```

备选方案：
- 用 `--cookies-from-browser chrome`（需要本机有浏览器）
- 或用 `--cookies cookies.txt`（手动导出的cookies）

> 详细绕过方法见 `references/anti-bot-bypass.md`

### 2. 没有 JS 运行时

```
WARNING: No supported JavaScript runtime could be found
```
→ 安装 deno 并配置 `--js-runtimes deno`

### 3. ffmpeg 未找到
```
ERROR: Post-processing: ffmpeg not found
```
→ 安装 ffmpeg

### 5. 中国网络下的代理冲突（新增）

如果服务器配置了 HTTP_PROXY（如 `http://127.0.0.1:10809`），yt-dlp 自身不受影响，但**rclone OAuth 授权时会出问题**：

```bash
curl访问 localhost:53682 → 走代理 → 代理返回503 → 授权失败
```

**解决：启动 rclone authorize 前清除代理变量**
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
rclone authorize onedrive --auth-no-open-browser
```
如果 YouTube 无法直接访问，需要配置代理：
```bash
yt-dlp --proxy socks5://127.0.0.1:1080 "URL"
```

## Absorbed Sub-Skills

### YouTube → Quark Cloud Disk (`references/ytb-cdp-quark-workflow.md`)
Specific China-server workflow for downloading YouTube videos via yt-dlp with CDP cookie extraction from Snap Chromium, then uploading to Quark cloud disk via Alist API. Includes full cookie extraction procedure (CDP WebSocket, Netscape format trap), yt-dlp download script, and Alist upload steps. Trigger: `ytb下载：网址`.

## 集成云存储

配合 rclone 或 Alist 将下载文件自动上传到云盘：

### rclone（通用方案，支持OneDrive/Google Drive/Dropbox等）

```bash
# 先下载到本地
yt-dlp "URL" -o "~/yt-dlp/%(title)s.%(ext)s"

# 再同步到云盘
rclone copy ~/yt-dlp/ onedrive:Videos/yt-dlp/

# 或一条命令完成(下载到挂载目录)
yt-dlp "URL" -o "~/mnt/onedrive/yt-dlp/%(title)s.%(ext)s"
```

⚠️ **headless服务器OAuth问题**：rclone授权需要浏览器，headless环境下：
- 用 `rclone authorize "驱动名" --auth-no-open-browser` 启动本地OAuth服务器
- 然后浏览器访问 `http://127.0.0.1:53682/` 完成登录
- ⚠️ 中国网络下直连local:53682可能被代理拦截，需 `unset http_proxy https_proxy` 或在浏览器工具中设置 no_proxy

### Alist（中国云盘方案，支持夸克/阿里云盘/百度网盘等）

> 详细配置见 `references/alist-quark-setup.md`

```bash
# 安装Alist
curl -L -o /tmp/alist.tar.gz \
  "https://github.com/AlistGo/alist/releases/latest/download/alist-linux-amd64.tar.gz"
tar -xzf /tmp/alist.tar.gz -C /tmp/
mkdir -p ~/.local/bin
cp /tmp/alist ~/.local/bin/

# 启动
alist server  # 默认端口5244
# Web管理: http://localhost:5244
# 默认账号: admin  (首次启动会输出随机密码, 或用 alist admin set xxx 修改)
```

Alist管理后台添加存储驱动后，挂载为WebDAV，yt-dlp可直接写入：

```bash
# 方法1: yt-dlp下载到Alist的本地挂载目录
# 方法2: rclone mount Alist的WebDAV后持续写入
```
