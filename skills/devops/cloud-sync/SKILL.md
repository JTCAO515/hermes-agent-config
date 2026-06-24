---
name: cloud-sync
description: 云存储配置与文件同步。rclone + Alist 安装、配置、挂载工作流。支持 OneDrive/Google Drive/夸克网盘/阿里云盘等。自动上传、定时同步、WebDAV 挂载。
version: 1.0.0
triggers:
  - "云存储/云盘/网盘/同步/备份/上传到云"
  - "rclone/OneDrive/iCloud/夸克/阿里云盘/百度网盘"
  - "Alist/WebDAV挂载/文件云同步"
---

# 云存储同步 (Cloud Sync)

rclone + Alist 双引擎，覆盖国内外主流云存储。

## 工具选择

| 场景 | 推荐工具 | 说明 |
|------|---------|------|
| 国际云盘 (OneDrive/Google Drive/Dropbox) | **rclone** | 原生支持, 功能完整 |
| 国内云盘 (夸克/阿里云盘/天翼云/百度网盘) | **Alist** | 桥接为WebDAV, 再经rclone操作 |
| 需要双向同步 | **rclone bisync** | 文件变更双向同步 |

---

## rclone 安装与配置

### 安装 (免sudo)

```bash
# 从GitHub下载二进制
curl -L -o /tmp/rclone.zip \
  "https://github.com/rclone/rclone/releases/download/v1.69.1/rclone-v1.69.1-linux-amd64.zip"
unzip -o /tmp/rclone.zip -d /tmp/
mkdir -p ~/.local/bin
cp /tmp/rclone-v1.69.1-linux-amd64/rclone ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# 验证
rclone version
```

### 配置云盘 (OAuth流程)

#### OneDrive (headless服务器)

```bash
# 创建基础配置
mkdir -p ~/.config/rclone
rclone config create onedrive onedrive config_is_local=false 2>/dev/null

# 启动授权服务器
# ⚠️ 先清除代理! 否则local:53682走代理会失败
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
rclone authorize onedrive --auth-no-open-browser
# → 浏览器访问 http://127.0.0.1:53682/ → Microsoft登录 → 自动捕获token

# 验证
rclone lsd onedrive:
```

#### Google Drive (headless服务器)

```bash
rclone authorize "drive" --auth-no-open-browser
# 同样需先unset代理, 浏览器访问输出URL
```

#### iCloud Drive ⚠️ 中国区不可用

中国区iCloud（云上贵州）的认证服务器不同，rclone会报 `Invalid Session Token`。
**建议改用OneDrive或国内云盘方案。**

### 常用命令

```bash
# 列出文件
rclone ls onedrive:
rclone lsd onedrive:  # 目录

# 复制文件
rclone copy ~/local/file.mp4 onedrive:Videos/

# 同步目录 (单向)
rclone sync ~/yt-dlp/ onedrive:Videos/yt-dlp/

# 挂载为本地文件夹
mkdir -p ~/mnt/onedrive
rclone mount onedrive: ~/mnt/onedrive/ &
# 然后可以直接写入 ~/mnt/onedrive/ 目录
```

---

## Alist 安装与配置 (国内云盘桥接)

### 安装

```bash
# 用国内镜像下载
curl -L -o /tmp/alist.tar.gz \
  "https://github.com/AlistGo/alist/releases/latest/download/alist-linux-amd64.tar.gz"
tar -xzf /tmp/alist.tar.gz -C /tmp/
cp /tmp/alist ~/.local/bin/
chmod +x ~/.local/bin/alist

# 首次运行自动生成密码
alist server  # Ctrl+C 中断后设置密码
alist admin set YOUR_PASSWORD
```

### 启动

```bash
alist server  # 默认端口5244, Web管理: http://localhost:5244
```

管理员账号: `admin`，密码通过 `alist admin set xxx` 设置。

### 添加存储驱动 (以夸克网盘为例)

夸克网盘使用手机号+验证码登录（无密码），需从浏览器提取cookie：

**方法A: 用浏览器登录提取cookie**
1. 在 noVNC 桌面打开 https://pan.quark.cn
2. 使用手机号+验证码登录
3. **关键步骤（不要用 Console 的 document.cookie）：**
   - 按 **F12** → **Application（应用）** 标签
   - 左侧 **Cookies → pan.quark.cn**
   - 查看/复制所有 cookie（含 httpOnly 字段）
   - 格式：`ctoken=xxx; b-user-id=xxx; __puus=xxx; ...`
   - 用完整字符串（分号+空格分隔）配置到 Alist

   ⚠️ **`document.cookie` 的致命陷阱：** `document.cookie` 只返回非 httpOnly 的 cookie。夸克网盘的关键认证字段（如 `__user_token`、`__puus`、`__kp`）通常是 httpOnly 的，不会被 `document.cookie` 包含。仅用 `document.cookie` 提取的 cookie 配置到 Alist 会报 `"require login [guest]"`，因为缺少核心认证字段。

   **验证：** 提取后检查是否包含 `__puus`、`__user_token`、`__kp` 等字段。如果只有 `ctoken`、`b-user-id`、`__wpkreporterwid_` 等非 httpOnly 字段，说明提取不完整，必须用 Application 面板重提。

   **⚠️ Snap Chromium 陷阱：** 如果服务器上装的是 Snap 版 Chromium (`/snap/chromium/`)，cookie 值在 SQLite 数据库中被加密存储，`sqlite3` 读到的 `value` 字段全是空字符串。**此时不能通过读磁盘文件获取 cookie**，必须用以上手动方式提取。

4. 将完整的 cookie 字符串（全部字段，分号+空格分隔）复制到 Alist 存储配置的 `cookie` 字段中。
5. 保存后，在 Alist Web 后台手动切换一次存储状态（禁用→启用）触发重连。

**方法B: 手动从浏览器提取**
1. F12 → Network → 刷新页面
2. 点击任意 `pan.quark.cn` 请求
3. 复制 Request Headers 中的 Cookie 值

### Alist API 调用注意

**⚠️ HTTP 代理陷阱：** 中国服务器经常有 `http_proxy` 环境变量指向本地代理（如 `127.0.0.1:10809`）。当用 curl/Python 调用 Alist 本地 API（127.0.0.1:5244）时，代理会拦截请求并返回 405/502/503 错误。

```bash
# ❌ 坏现象：curl 返回 405 Method Not Allowed 或 503 Service Unavailable
# 根本原因：请求被代理拦截，代理不认识 PUT/DELETE 等本地 API 方法

# ✅ 方案A：用 --noproxy "*" 跳过本地请求的代理
curl --noproxy "*" -s -X POST http://127.0.0.1:5244/api/admin/storage/list \
  -H "Authorization: $TOKEN"

# ✅ 方案B：Python 中设置环境变量
import os
os.environ['no_proxy'] = '*'  # 设置后 urllib.request 不走代理

# ✅ 方案C：临时清除代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
# 操作完成后恢复
export http_proxy=http://127.0.0.1:10809
```

**⚠️ Alist API 方法注意：** Alist 的 `/api/admin/storage/update` 使用 **POST** 而不是 PUT。用 PUT 会返回 `405 Method Not Allowed`。

```bash
# ✅ 正确：POST
curl -X POST http://127.0.0.1:5244/api/admin/storage/update

# ❌ 错误：PUT → 405
curl -X PUT http://127.0.0.1:5244/api/admin/storage/update
```

**⚠️ 删除存储参数格式：** `/api/admin/storage/delete` 使用 query parameter 传递 id：

```bash
# ✅ 正确
curl -X POST "http://127.0.0.1:5244/api/admin/storage/delete?id=2"

# ❌ 错误：JSON body 会报 strconv.Atoi error
curl -X POST http://127.0.0.1:5244/api/admin/storage/delete \
  -d '{"id":2}'  # ← 不会解析成功
```

**方法C: 用现有token/值拼接（不推荐，容易出错）**
如果只有单值（如 `13b44d60-5b0a-11f1-8d75-e163ffccaf07`），它可能是 `__user_token=...` 的一部分，但不是完整的 cookie 字符串。完整 cookie 通常包含：
- `__pus=...` (Push token)
- `__uu=...` (User UUID)
- `__user_token=...` (Auth token)
- `__quark__platId=...` (Platform ID)

**⚠️ 陷阱：单个 token 值不足以通过 Alist 的 Quark 驱动认证**
- 只给一个 UUID 格式的值（如 `13b44d60-xxxx`），Alist 会报 `require login [guest]`
- 必须提供完整的 cookie 字符串：`key1=value1; key2=value2; key3=value3`
- 从浏览器 Network 面板直接复制是最可靠的方式

Alist存储配置参数:
| 参数 | 说明 |
|------|------|
| driver | Quark |
| mount_path | /quark (挂载路径) |
| cookie | 上面提取的cookie |
| root_folder_id | 0 (根目录) |
| use_transcoding_address | true (视频转码) |

### 其他国内云盘

| 云盘 | Alist驱动名 | 认证方式 |
|------|------------|---------|
| 夸克网盘 | Quark | Cookie |
| 阿里云盘 | Aliyundrive | RefreshToken |
| 天翼云盘 | 189Cloud | 手机号+密码 |
| 百度网盘 | BaiduNetdisk | OAuth |
| 123云盘 | 123Pan | 账号+密码 |

### Alist + rclone 联合使用

```bash
# 方法1: 通过WebDAV挂载Alist
rclone config create alist webdav url=http://localhost:5244/dav vendor=other user=admin pass=YOUR_PASSWORD

# 方法2: 直接mount
rclone mount alist: ~/mnt/alist/ &

# 然后yt-dlp直接下载到挂载目录
yt-dlp "URL" -o "~/mnt/alist/quark/%(title)s.%(ext)s"
```

---

## 代理注意事项

中国网络下服务器常配 HTTP_PROXY，会影响本地OAuth流程:

```bash
# 检查是否设了代理
echo $http_proxy $https_proxy

# rclone authorize 前必须清除
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
rclone authorize onedrive --auth-no-open-browser
# 浏览器工具访问 http://127.0.0.1:53682/ 完成登录
```

## 常见问题

### 1. rclone authorize 看不到URL输出

后台进程的标准错误可能不被捕获。直接检查端口:
```bash
ss -tlnp | grep 53682
# 然后浏览器访问 http://127.0.0.1:53682/
```

### 2. "Invalid Session Token" (iCloud)

中国区iCloud（云上贵州）不兼容rclone的iclouddrive后端。换OneDrive或国内云盘。

### 3. OAuth授权后浏览器报错"Failure! No code returned"

需要访问 `/auth?state=XXX` 完整路径（含state参数）。
启动授权后先捕获输出中的URL，再导航浏览器到正确地址。

### 4. Alist 夸克网盘报 "require login [guest]"

**常见原因（按频率排序）：**

1. **`document.cookie` 遗漏了 httpOnly cookie（最常见）** ← 这是本会话的教训
   - `document.cookie` 只返回非 httpOnly 的 cookie
   - 夸克的关键认证字段 `__puus`、`__user_token`、`__kp` 等都是 httpOnly
   - 仅用 `document.cookie` 提取 → 报 "require login [guest]"
   - ✅ **解决方法：** F12 → Application → Cookies → pan.quark.cn → 复制完整 cookie 字符串

2. cookie 过期（夸克网盘 cookie 有效期通常 1-7 天）

3. cookie 格式不正确（缺少分号分隔、值被截断、包含特殊字符转义问题）

4. 更新 cookie 后未触发重连（需要在 Alist Web 后台手动禁用→启用该存储）

### 5. Alist 夸克网盘报 "failed init storage but storage is already created"

**解释：** 存储记录已创建（有 ID），但初始化（连接）失败。登录凭证无效。
**处理：** 更新 cookie 后，手动禁用再启用该存储，或直接删除重建。
