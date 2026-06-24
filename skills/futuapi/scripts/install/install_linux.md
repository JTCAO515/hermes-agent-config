# Linux 安装步骤（Futu OpenD）

Linux 安装包是 **tar.gz 压缩包**，与 macOS 类似，解压后包含 GUI 版 AppImage。

## 压缩包内部结构（以 Ubuntu 为例，v10.5.6508+）

```
Futu_OpenD_x.x.xxxx_Ubuntu/
├── Futu_OpenD-GUI_x.x.xxxx_Ubuntu/
│   └── Futu_OpenD-GUI_x.x.xxxx_Ubuntu.AppImage  ← GUI 版（安装这个）
├── Futu_OpenD_x.x.xxxx_Ubuntu/
│   ├── FutuOpenD                                 ← 命令行版（不要运行）
│   ├── FutuOpenD.xml                             ← 配置文件模板
│   └── ...
└── README.txt
```

> **注意**：新版本（10.5.6508+）使用 AppImage 格式而非 .deb。旧文档中提到的 `Futu_OpenD-GUI_*.deb` 已不再提供。
> 如果下载到的是旧版 .deb 包，仍可使用 `sudo dpkg -i *.deb && sudo apt-get install -f -y` 安装。

## 第一步：下载并解压

下载前先清理已有文件，避免残留旧版本导致冲突：

```bash
rm -f ~/Desktop/FutuOpenD.tar.gz
rm -rf ~/Desktop/Futu_OpenD_*
```

**Ubuntu / CentOS**：
```bash
curl -L -o ~/Desktop/FutuOpenD.tar.gz "https://www.futunn.com/download/fetch-lasted-link?name=opend-{ubuntu|centos}"
tar -xzf ~/Desktop/FutuOpenD.tar.gz -C ~/Desktop/
rm ~/Desktop/FutuOpenD.tar.gz
```

如果用户通过 `-path` 指定了路径，将 `~/Desktop/` 替换为对应路径。

## 第二步：版本一致性校验

解压完成后、安装前，验证解压出的是预期版本：

```bash
APPIMAGE=$(find ~/Desktop -maxdepth 5 -name "*OpenD-GUI*${LATEST_VER}*.AppImage" -type f 2>/dev/null | head -1)
if [ -n "$APPIMAGE" ]; then
    echo "Version verified: found $(basename "$APPIMAGE") (matches expected $LATEST_VER)"
else
    ALL_APP=$(find ~/Desktop -maxdepth 5 -name "*OpenD-GUI*.AppImage" -type f 2>/dev/null)
    echo "WARNING: Expected version $LATEST_VER not found. Found: $ALL_APP"
    exit 1
fi
```

## 第三步：安装 GUI 版（AppImage）

将 AppImage 拷贝到 `/opt/` 并创建 symlink：

```bash
sudo mkdir -p /opt/Futu_OpenD
sudo cp "$APPIMAGE" /opt/Futu_OpenD/Futu_OpenD-GUI_${LATEST_VER}.AppImage
sudo chmod +x /opt/Futu_OpenD/Futu_OpenD-GUI_${LATEST_VER}.AppImage
sudo ln -sf /opt/Futu_OpenD/Futu_OpenD-GUI_${LATEST_VER}.AppImage /usr/local/bin/Futu_OpenD
```

同时拷贝 XML 配置模板：

```bash
XML_PATH=$(find ~/Desktop -maxdepth 5 -name "FutuOpenD.xml" -type f 2>/dev/null | head -1)
[ -n "$XML_PATH" ] && sudo cp "$XML_PATH" /opt/Futu_OpenD/FutuOpenD.xml
```

## 第四步：启动 GUI 版 OpenD

- **有图形界面的环境**：直接运行 `Futu_OpenD`
- **云服务器/无图形界面**：使用 Xvfb + VNC。详见 `references/headless-deployment.md`

```bash
# 有图形界面
nohup Futu_OpenD > /tmp/opend.log 2>&1 &

# 无图形界面（云服务器）
Xvfb :99 -screen 0 1280x720x24 &
DISPLAY=:99 nohup Futu_OpenD > /tmp/opend.log 2>&1 &
```

## 第五步：清理解压目录

```bash
EXTRACT_DIR=$(find ~/Desktop -maxdepth 1 -type d -name "Futu_OpenD_*" | head -1)
[ -n "$EXTRACT_DIR" ] && rm -rf "$EXTRACT_DIR" && echo "Cleaned up: $EXTRACT_DIR"
```
