# Alist + 夸克网盘 配置参考

## Alist 安装

```bash
curl -L -o /tmp/alist.tar.gz \
  "https://github.com/AlistGo/alist/releases/latest/download/alist-linux-amd64.tar.gz"
tar -xzf /tmp/alist.tar.gz -C /tmp/
mkdir -p ~/.local/bin
cp /tmp/alist ~/.local/bin/
```

## Alist 运行

```bash
# 启动服务（默认端口5244）
alist server

# 首次启动后设置管理员密码
alist admin set <YOUR_PASSWORD>

# 首次运行会自动生成随机密码，用以下命令查看
alist admin

# Web管理: http://localhost:5244
# 默认账号: admin
```

## 夸克网盘存储驱动

Alist管理后台 → 存储 → 添加驱动 → 选择 "Quark"

### 需要的参数

| 参数 | 说明 | 获取方式 |
|------|------|----------|
| `cookie` | 夸克登录cookie | 从浏览器登录pan.quark.cn后，在Network请求头中复制 |
| `root_folder_id` | 根目录ID | 默认 `0` 表示根目录 |
| `use_transcoding_address` | 视频转码 | 建议 `true` |

### Cookie 获取方式

推荐方案: 浏览器登录夸克网盘
1. 打开 https://pan.quark.cn 并登录
2. F12 → Network → 刷新页面
3. 点击第一个 `pan.quark.cn` 请求
4. 找到 `cookie:` 请求头，完整复制

手机号+验证码登录方式:
1. 访问 https://uop.quark.cn/cas/custom/login?custom_login_type=mobile&client_id=532&display=pc
2. 输入手机号
3. 需通过滑块验证码后才能发送短信
4. 输入验证码登录
5. 登录后提取cookie

注意：夸克的登录页面有滑块验证码，自动化流程较困难，建议手动登录后提取cookie。

## yt-dlp + Alist 集成

```bash
# 方式1: 下载到本地，然后复制到Alist管理的目录
yt-dlp "URL" -o "~/yt-dlp/%(title)s.%(ext)s"
cp ~/yt-dlp/*.mp4 ~/alist-data/quark/

# 方式2: 通过rclone挂载Alist的WebDAV后直接写入
# 先在Alist中启用WebDAV
# 再用rclone mount
rclone mount alist_webdav: /mnt/alist --daemon
yt-dlp "URL" -o "/mnt/alist/yt-dlp/%(title)s.%(ext)s"
```

## 已验证可用的中国云盘（Alist + rclone）

| 云盘 | 存储驱动名 | Alist支持 | rclone支持 | 备注 |
|------|-----------|-----------|-----------|------|
| 夸克网盘 | Quark | ✅原生 | ❌ | 通过Alist的WebDAV桥接 |
| 阿里云盘 | Aliyundrive | ✅原生 | ✅(s3) | 需要refresh_token |
| 天翼云盘 | 189Cloud | ✅原生 | ❌ | 需要手机号+密码 |
| 百度网盘 | BaiduNetdisk | ✅原生 | ❌ | 需要OAuth |
| PikPak | - | ❌ | ✅原生 | 东南亚云盘，国内友好 |
