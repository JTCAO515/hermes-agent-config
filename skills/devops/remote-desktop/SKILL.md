---
name: remote-desktop
description: 设置 Xvfb + x11vnc + websockify/noVNC，通过浏览器远程控制服务器桌面。适用于需要用户在服务器上操作浏览器登录网站（夸克网盘、微信开放平台等）的场景。
version: 1.1.0
triggers:
  - "VNC/远程桌面/noVNC/Xvfb/x11vnc"
  - "需要用户登录网站/需要浏览器验证/滑块验证/手机验证码登录"
  - "服务器上没有浏览器/无法直接访问网站"
  - "远程控制/桌面环境/headless桌面"
  - "夸克网盘登录/阿里云盘登录/云盘cookie"
---

# 远程桌面 (Remote Desktop via noVNC)

在 headless 服务器上搭建虚拟桌面环境，用户通过浏览器即可远程操作桌面浏览器，适用于需要用户手动登录网站（验证码/滑块/OAuth）的场景。

## 工作流程

```
┌─────────────┐     VNC      ┌──────────┐   WebSocket   ┌───────────┐   HTTPS    ┌──────────┐
│  Xvfb :99   │◄──────────►│ x11vnc   │◄────────────►│ websockify │◄──────────►│ 用户浏览器 │
│ (虚拟显示器)  │   5900/tcp  │ :5900    │   6080/tcp    │ :6080      │            │          │
└─────────────┘             └──────────┘               └───────────┘            └──────────┘
```

## 安装依赖

```bash
# Ubuntu
sudo apt-get install -y xvfb x11vnc xdotool

# websockify (Python)
pip3 install websockify

# 浏览器 (可选, 用于在桌面内操作)
sudo snap install chromium
# 或 apt 版
sudo apt-get install -y chromium-browser

# noVNC 前端 (通常随 websockify 或 apt 安装)
# apt: /usr/share/novnc/
# pip: <venv>/share/novnc/
```

## 启动步骤

### 1. 启动 Xvfb 虚拟显示器

```bash
Xvfb :99 -screen 0 1280x720x24 &
```

- `:99` — 显示编号，可自定义
- `1280x720x24` — 分辨率 1280×720, 24bit 色深
- 手机壁纸等操作建议 `1080x1920x24`

### 2. 启动 x11vnc

```bash
x11vnc -display :99 -forever -shared -nopw -quiet &
```

- `-forever` — 持续运行（默认客户端断开后退出）
- `-shared` — 允许多客户端同时连接
- `-nopw` — 无密码（环境内网，HTTP 隧道仅限本地）

### 3. 启动 websockify + noVNC

```bash
# 确认 noVNC 前端文件位置
ls /usr/share/novnc/vnc.html 2>/dev/null || find / -name "vnc.html" -path "*/novnc/*" 2>/dev/null

# 启动 websockify，绑定 noVNC 前端
websockify --web=/usr/share/novnc 0.0.0.0:6080 localhost:5900 &
```

### 4. 窗口管理器（推荐，提升桌面观感）

```bash
sudo apt-get install -y openbox  # 轻量级窗口管理器
DISPLAY=:99 openbox --sm-disable &
```

没有窗口管理器时浏览器窗口无边框、无法拖动。openbox 是最轻量的选择（~1MB）。

### 5. 启动浏览器（可选）

```bash
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu \
  --start-maximized https://pan.quark.cn &
```

⚠️ **Snap 版 Chromium**：Ubuntu 默认安装的是 snap 版本。需要 `--no-sandbox` 参数才能在有 Xvfb 的环境运行。如果 snap 版本有问题，安装 apt 版：
```bash
sudo apt-get install -y chromium-browser  # 会自动安装 snap 版
# 如果需要非 snap 版：
sudo snap remove chromium
sudo apt-get install -y chromium-browser  # 这次装 apt 版
```

### 6. 启动桌面实用工具（可选）

```bash
# 计算器
sudo apt-get install -y gnome-calculator
DISPLAY=:99 gnome-calculator &
```

## 进程验证

启动后验证所有组件是否正常运行：

```bash
# 检查所有关键进程
ps aux | grep -E 'Xvfb|x11vnc|websockify|openbox|chromium' | grep -v grep

# 检查端口监听
ss -tlnp | grep -E '5900|6080'

# 检查桌面窗口
DISPLAY=:99 xdotool search . 2>/dev/null
for wid in $(DISPLAY=:99 xdotool search . 2>/dev/null); do
  echo "Window $wid: $(DISPLAY=:99 xdotool getwindowname $wid 2>/dev/null)"
done

# 检查外部连通性
curl -s -o /dev/null -w "%{http_code}" "http://<公网IP>:6080/vnc.html"
```

## 访问方式

### 方式A：通过浏览器访问（推荐）

用户直接访问 noVNC 页面：

```
http://<服务器公网IP>:6080/vnc.html
```

点击 **Connect** 按钮即可看到桌面。

**⚠️ 网络注意：**
- 如果服务器在海外，国内用户可能延迟较高
- 如果服务器端口被防火墙/安全组封锁，需要：
  - 在云服务商安全组开放 TCP:6080 端口
  - 如果是 NAT 网关模式，还需添加端口转发规则（公网IP:6080 → 内网IP:6080）
- 可用 `curl -s -o /dev/null -w "%{http_code}" http://<公网IP>:6080/vnc.html` 测试连通性

### 方式B：通过隧道工具（当端口不能开放时）

如果服务器端口被防火墙/NAT 封锁，使用隧道工具让用户访问 noVNC：

```bash
# bore (免注册, 极简)
curl -LO https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz
tar xzf bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz
mv bore ~/.local/bin/
bore local 6080 --to bore.pub
# → 输出类似: "listening at bore.pub:xxxxx"
# → 用户访问 http://bore.pub:xxxxx/vnc.html
# ⚠️ bore.pub 在国内可能被墙，连接不上

# cloudflared (需 Cloudflare 账号)
cloudflared tunnel --url http://localhost:6080
# → 输出类似: "https://xxxxx.trycloudflare.com"
# ⚠️ Cloudflare Tunnel 在国内通常能通但速度慢
```

## 用 xdotool 操控桌面

```bash
export DISPLAY=:99

# 查找窗口
xdotool search --name "Chromium"

# 激活窗口
xdotool windowactivate <WINDOW_ID>

# 模拟按键
xdotool key F12           # 打开 DevTools
xdotool key Ctrl+T        # 新标签页
xdotool key Ctrl+L        # 聚焦地址栏
xdotool type "text here"  # 输入文字
xdotool key Return

# 获取窗口标题
xdotool getactivewindow getwindowname
```

## 获取浏览器 Cookie（关键操作）

见 `cloud-sync` skill 的 `references/snap-chromium-cookie-extraction.md`。

## 清理

```bash
sudo pkill -f "Xvfb :99"
sudo pkill -f "x11vnc.*:99"
sudo pkill -f "websockify.*6080"
killall chromium-browser 2>/dev/null
```

## 常见问题

### 1. 外部无法访问 6080 端口

所有端口返回 503 → 云服务商安全组/NAT 网关未放行。
- 检查安全组入站规则：TCP:6080 来源 0.0.0.0/0
- 检查 NAT 网关端口转发：公网IP:6080 → 内网IP:6080

### 2. Chromium 无法启动

```bash
# 检查错误
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu 2>&1 | head -20

# 缺少库时
sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libxss1 libxtst6 xdg-utils libatspi2.0-0 libdrm2 libgbm1
```

### 3. 浏览器黑屏 / 只显示白色

- 确认 Xvfb 在运行：`ps aux | grep Xvfb`
- 尝试不同分辨率：`Xvfb :99 -screen 0 1920x1080x24`
- 安装窗口管理器：`sudo apt install -y openbox && DISPLAY=:99 openbox &`

### 4. xdotool 找不到窗口

```bash
# 查看所有窗口
xdotool search . 2>/dev/null
xdotool getactivewindow getwindowname 2>/dev/null
```

### 5. 腾讯云服务器所有外网端口返回 503

说明服务器没有直接绑定公网 IP，而是通过 NAT 网关映射。解决方法：
1. 在 **腾讯云控制台 → 安全组** 添加入站规则放行 TCP:6080
2. 在 **腾讯云控制台 → NAT 网关 → 端口转发** 添加转发规则
