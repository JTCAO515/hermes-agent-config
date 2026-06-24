---
name: pwa-android-deployment
description: 将 PWA 打包为 Android APK/AAB 的完整工作流。含 PWA 检查、图标生成(Seedream)、manifest 配置、Bubblewrap/PWABuilder 打包、GitHub 仓库管理、Google Play 准备。
version: 1.1.0
triggers:
  - "打包APK"
  - "安卓应用"
  - "Android"
  - "移动端APP"
  - "PWA转APP"
  - "PWABuilder"
  - "Bubblewrap"
  - "TWA"
  - "Google Play"
  - "上架"
  - "apk"
  - "aab"
  - "app icon"
  - "应用图标"
  - "手机应用"
mutating: false
---

# PWA -> Android APK Deployment

> 将一个已部署的 PWA 打包为 Android 原生安装包的工作流。
>
> 路线: 修复 PWA -> 生成图标 -> PWABuilder/Bubblewrap -> APK -> GitHub 仓库

## 核心原则

1. **PWA 必须先通过** -- PWABuilder 和 Bubblewrap 都是基于 PWA URL 打包，PWA 不通过什么也打不出来
2. **图标是第一印象** -- 不要用默认 SVG 转 PNG，用 AI 生成高质量图标（Seedream 推荐）
3. **分开仓库** -- PWA 代码在 A 仓库，Android 打包产物在 B 仓库（如 WC26 -> WC26-adr）
4. **版本号同步** -- PWA 版本号变了，Android 应用的 versionCode/versionName 也要改

## 工作流

### Phase 1: PWA 资质检查

#### PWA 必备要素

- manifest.json -- 存在且正确
- Service Worker -- 存在，注册正确
- HTTPS -- 必须（Vercel 默认已配）
- 响应式 viewport -- `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
- 图标 -- 至少 192x192 + 512x512 PNG
- 离线能力 -- Service Worker 缓存策略

#### 常见缺失（需要修复）

| 问题 | 症状 | 修复 |
|------|------|------|
| manifest 引用不存在的图标 | PWA 安装横幅不弹出 | 检查 manifest.json icons 数组中每个 src 是否真实存在 |
| 缺少 maskable 图标 | Android 添加主屏幕时图标被裁剪 | 加 `purpose: maskable` 的 512x512 图标 |
| 缺少 apple-touch-icon | iOS 添加到主屏幕用截图替代 | `<link rel="apple-touch-icon" href="/icon-512.png">` |
| manifest display 不是 standalone | 浏览器全屏模式不生效 | `display: standalone` |
| 缺少 apple-mobile-web-app-capable | iOS 不识别 PWA | `<meta name="apple-mobile-web-app-capable" content="yes">` |

### Phase 2: 图标生成

#### 方法 A：Seedream 5.0（推荐，国内可用）

```bash
# 1. 调用 Seedream 生成 1920x1920 图片
IMAGE_URL=$(curl -s --max-time 120 -X POST "$VOLCENGINE_BASE_URL/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VOLCENGINE_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "PROMPT",
    "n": 1,
    "size": "1920x1920"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])")

# 2. 立即下载（URL 24h 过期）
curl -s -L -o icon-original.jpg "$IMAGE_URL"
```

**App 图标准用 Prompt（已验证有效）：**
```
Mobile app icon for [项目名]. Square 1:1 format. Clean composition:
[主体描述, 如 "a golden football/soccer ball integrated with a dollar currency symbol $"],
surrounded by subtle glowing circuit board traces and data graph lines.
Dark background (#08090a), neon accent colors (cyan #5e6ad2 and gold).
Professional fintech sports style. Vector-quality flat design. No text.
High contrast, suitable for app launcher icon.
```

**Prompt 技巧：**
- 指定 `Square 1:1`、`app launcher icon`、`dark background`、`no text`
- 指定品牌色：`dark background (#08090a), accent color (#5e6ad2)`
- 风格词：`professional fintech sports style`, `vector-quality flat design`, `high contrast`
- **确认 Prompt 包含主体和元素的精确语义关系**（如 "golden football integrated with a dollar symbol" 比 "football and money" 更准确）
- 用 VLM（Doubao-Seed-2.0-Lite）检查生成效果

**VLM 检查图标质量：**
```python
import requests, base64, os, json
with open("icon-original.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
resp = requests.post(
    "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    headers={"Authorization": f"Bearer {os.environ['VOLCENGINE_API_KEY']}", "Content-Type": "application/json"},
    json={
        "model": "doubao-seed-2-0-lite-260215",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片的内容和风格。它适合作为一个App图标吗？颜色、布局、主体是什么？只用中文回答，简洁明了"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        "max_tokens": 300
    }
)
print(resp.json()["choices"][0]["message"]["content"])
```

**注意：** base64 编码大图片时不要用 bash 管道传参（`Argument list too long`），必须用 Python 或临时文件方式调用 API。

#### 方法 B：SVG 转 PNG（备选，适合极简图标）

```bash
# 需要 apt install librsvg2-bin
rsvg-convert -w 192 -h 192 icon.svg -o icon-192.png
rsvg-convert -w 512 -h 512 icon.svg -o icon-512.png
```

#### 图标尺寸

| 文件名 | 尺寸 | 用途 |
|--------|------|------|
| icon-192.png | 192x192 | 小图标 / 浏览器 PWA |
| icon-512.png | 512x512 | 大图标 / 启动屏 |
| icon-maskable-512.png | 512x512 | Android 自适应图标（maskable） |
| icon.svg | 任意 | SVG 图标（浏览器/favicon 用） |

#### 生成代码（Pillow）

```python
from PIL import Image
img = Image.open("icon-original.jpg")
img.resize((192, 192), Image.LANCZOS).save("icon-192.png")
img.resize((512, 512), Image.LANCZOS).save("icon-512.png")
img.resize((512, 512), Image.LANCZOS).save("icon-maskable-512.png")
```

#### Android mipmap 图标（原生 App 用）

Android App 需要密度限定符的图标文件，用于旧版本 Android（低于 API 26）：

```python
from PIL import Image
import os

img = Image.open("icon-original.jpg")
base = "app/src/main/res"
sizes = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

for folder, sz in sizes.items():
    os.makedirs(os.path.join(base, folder), exist_ok=True)
    img.resize((sz, sz), Image.LANCZOS).save(os.path.join(base, folder, "ic_launcher.png"))
```

同时创建自适应图标（API 26+）：

```xml
<!-- app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
```

ic_launcher_foreground 用 512x512 版本放到 `app/src/main/res/drawable/ic_launcher_foreground.png`。

### Phase 3: manifest.json 配置

```json
{
  "name": "完整应用名",
  "short_name": "缩写",
  "description": "一句话描述",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#08090a",
  "theme_color": "#5e6ad2",
  "orientation": "any",
  "categories": ["sports", "utilities"],
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

### Phase 4: HTML header 补全

```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#5e6ad2">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/icon-512.png">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### Phase 5: 打包 Android APK

有两种主流工具可用：

#### 方案 A：Bubblewrap CLI（Google 官方，推荐本地构建）

```bash
# 1. 安装（需要 Node.js + Java 11+）
npm install -g @bubblewrap/cli

# 2. 生成签名密钥
keytool -genkey -v -keystore android.keystore -alias myapp -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass 密码 -keypass 密码 \
  -dname "CN=名字, OU=部门, O=组织, L=城市, ST=省份, C=CN"

# 3. 初始化 TWA 项目
npx bubblewrap init --manifest=https://your-site.com/manifest.json

# 4. 构建 APK
npx bubblewrap build

# 产物: app-release-signed.apk
```

**⚠️ Bubblewrap 交互陷阱：** `bubblewrap init` 是交互式 CLI（inquirer），会询问 JDK 安装路径，`echo "Y" | bubblewrap init` 会触发 JDK 自动安装（耗时 2min+ 超时），`echo "N"` 也会因 inquirer 的特殊输入处理而卡住。解决方案：

1. 预先安装 JDK：`sudo apt-get install -y openjdk-17-jdk-headless`
2. 导出 JAVA_HOME：`export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`
3. 不要让 bubblewrap 安装 JDK —— 否则在服务器上会超时

如果 bubblewrap 非交互模式仍然失败，使用 **方案 C（手动创建 TWA 项目）** 替代。

#### 方案 B：PWABuilder CLI（备选，云打包）

```bash
npm install -g @pwabuilder/pwabuilder-android-cli
npx pwabuilder-android-cli -u https://your-site.com -p com.yourdomain.appname
cd androidApp && ./gradlew assembleRelease
```

**注意：** PWABuilder.com 网页端是基于 SPA 的单页应用，在 headless browser 中可能渲染不全（文本模式下几乎空白）。如果要用网页版，直接访问：
```
https://pwabuilder.com/pages/package?url=https://your-site.com
```

或者用云服务替代：
- https://pwa2apk.com
- https://appmaker.xyz/pwa-to-apk

#### 方案 C：手动创建 TWA 项目（推荐当自动化工具失败时）

当 Bubblewrap/PWABuilder 都不奏效时，手动创建完整 Android TWA 项目：

**项目结构：**
```
WC26-adr/
├── README.md
├── .gitignore
├── build.gradle.kts            # 顶级构建: Android Gradle Plugin 8.2.2
├── settings.gradle.kts          # 包含 :app 模块
├── gradle.properties            # android.useAndroidX=true
├── gradlew / gradlew.bat        # Gradle Wrapper
├── gradle/wrapper/
│   ├── gradle-wrapper.jar       # 从 GitHub raw/gradle 下载
│   └── gradle-wrapper.properties
├── android.keystore             # keytool 生成
└── app/
    ├── build.gradle.kts         # 应用模块: androidbrowserhelper 依赖
    ├── proguard-rules.pro
    └── src/main/
        ├── AndroidManifest.xml
        ├── res/
        │   ├── xml/network_security_config.xml
        │   ├── values/{strings,themes,colors}.xml
        │   ├── drawable/ic_launcher_foreground.png
        │   ├── mipmap-anydpi-v26/ic_launcher.xml
        │   ├── mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png
        │   └── ...
        └── ...
```

**关键文件模板：**

`app/build.gradle.kts`:
```kotlin
plugins { id("com.android.application") }
android {
    namespace = "space.jtcao.wc26"
    compileSdk = 34

    // ⚠️ signingConfigs 必须在 android 层级，不能写在 buildTypes 内部！
    signingConfigs {
        create("release") {
            storeFile = file("../android.keystore")
            storePassword = "密码"
            keyAlias = "别名"
            keyPassword = "密码"
        }
    }

    defaultConfig {
        applicationId = "space.jtcao.wc26"
        minSdk = 24; targetSdk = 34
        versionCode = 1; versionName = "1.0.0"
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            // 在 buildTypes.release 里只能引用，不能 create
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
dependencies {
    implementation("com.google.androidbrowserhelper:androidbrowserhelper:2.4.0")
}
```

**`settings.gradle.kts` (Kotlin DSL)：**
```kotlin
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
// ⚠️ 必须用 dependencyResolutionManagement，不要用 dependencyResolution（那是 Groovy DSL 写法，Kotlin DSL 编译不过）
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}
rootProject.name = "WC26"
include(":app")
```

`AndroidManifest.xml`:
```xml
<manifest ...>
  <uses-permission android:name="android.permission.INTERNET" />
  <application ... android:networkSecurityConfig="@xml/network_security_config">
    <activity android:name="com.google.androidbrowserhelper.trusted.LauncherActivity"
      android:exported="true" android:launchMode="singleTask">
      <meta-data android:name="android.support.customtabs.trusted.DEFAULT_URL"
        android:value="https://your-site.com" />
      <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
      </intent-filter>
      <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" android:host="your-site.com" />
      </intent-filter>
    </activity>
  </application>
</manifest>
```

**Gradle Wrapper 下载：**
```bash
# gradle-wrapper.jar 从 GitHub raw 下载（注意代理问题）
curl -sL --max-time 60 \
  "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar" \
  -o gradle/wrapper/gradle-wrapper.jar
```

`gradle/wrapper/gradle-wrapper.properties`:
```
distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
```

**gradlew 脚本：** 使用 Gradle 官方标准脚本（从标准 Gradle 模板复制）。

### Phase 6: Digital Asset Links（TWA 必须）

Trusted Web Activity 需要 Digital Asset Links 来验证 App 和网站的所有权关系。不配置的话，TWA 运行时会显示 Chrome Custom Tab 而非全屏模式。

#### 1. 生成 assetlinks.json

```bash
# 从 keystore 获取 SHA256 指纹
keytool -list -v -keystore android.keystore -storepass 密码 -alias 别名 | grep SHA256

# 去掉冒号，生成 assetlinks.json
```
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "space.jtcao.wc26",
    "sha256_cert_fingerprints": [
      "B8:83:5A:B8:E6:35:E0:CC:15:EA:E3:6B:33:04:1F:55:1B:74:22:B9:9B:4A:85:83:2A:B5:6B:EC:5A:21:81:14"
    ]
  }
}]
```

#### 2. 部署到网站

assetlinks.json 必须部署在网站根目录的 `/.well-known/assetlinks.json`：
- 对于静态站点：放到 `public/.well-known/assetlinks.json`
- 对于 Vercel Python API：添加路由处理
```python
if path == "/.well-known/assetlinks.json":
    return _json(start_response, json.loads(assetlinks_content))
```

#### 3. 验证

Android 设备首次打开 TWA 时，系统会自动请求网站的 assetlinks.json。可以用 [Statement List Generator and Tester](https://developers.google.com/digital-asset-links/tools/generator) 在线验证，或直接 curl 确认 200：
```bash
curl -s -o /dev/null -w "%{http_code}" https://your-site.com/.well-known/assetlinks.json
# 应返回 200
```

### Phase 7: GitHub 仓库管理

```bash
# 创建新仓库（Android 打包产物不应放在 PWA 源码仓库）
curl -s -X POST -H "Authorization: Bearer $GH_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/user/repos \
  -d '{"name":"WC26-adr","private":false,"description":"WC26 Android App"}'

# 初始化并推送
cd /path/to/android-project
git init
git remote add origin git@github.com:JTCAO515/WC26-adr.git
git add -A && git commit -m "feat: initial Android TWA project"
git push -u origin main
```

### Phase 8: GitHub Actions 自动编译 APK（推荐）

当 Android 项目推送到 GitHub 后，使用 GitHub Actions 云端自动编译 APK。用户无需本地安装 Android SDK，推代码即得可安装 APK。

#### GitHub Actions Workflow 模板

`.github/workflows/build-apk.yml`：

```yaml
name: Build APK

on:
  push:
    branches: [master, main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: 17
          distribution: temurin
      - name: Make gradlew executable
        run: chmod +x gradlew
      - name: Build Release APK
        run: ./gradlew assembleRelease
      - uses: actions/upload-artifact@v4
        with:
          name: APPNAME-APK
          path: app/build/outputs/apk/release/*.apk
          if-no-files-found: error
```

**⚠️ 不要加 `gradle/actions/setup-gradle`**：该 action 在 Node.js 24 环境下（2026年6月起默认）有兼容问题，且与直接 `./gradlew` 执行冲突。

**⚠️ gradlew 权限**：GitHub 上 `write_file` 创建的文件默认 644 权限，gradlew 需要 `chmod +x` 步骤，否则报 `exit code 126` (Permission denied)。

#### 用户下载 APK

1. GitHub 仓库 → **Actions** → **Build APK** → 最新成功运行
2. **Artifacts** → 下载 `APPNAME-APK.zip`
3. 解压 → `app-release.apk` → 传到手机安装

#### 打 Tag 自动发布 Release

```yaml
      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v2
        with:
          files: app/build/outputs/apk/release/*.apk
```

用法：`git tag v1.0.0 && git push origin v1.0.0`

#### CI 注意事项

- 首次运行约 2-3 分钟（下载 Gradle + Android SDK）
- 后续构建使用缓存 ~30-60s
- 不需要本地安装 Android 工具
- `workflow_dispatch:` 允许 GitHub UI 手动触发

### Phase 9: Google Play 上架（可选）

前提:
- Google Play 开发者账号（一次性 $25）
- 签名后的 AAB/APK
- 应用截图（至少 2 张手机截图 + 1 张平板截图）
- 隐私政策 URL
- 内容分级问卷

## 数据一致性原则

当将 Web 应用转化为 App 时，Tab 内所有 UI 数据必须同源：

```
错误模式：
  KPI -> API A (不同数字)
  明细 -> API B (不同数字)
  绩效 -> API C (不同数字)

正确模式：
  所有区域 -> API A (一致数字)
```

修复方法：
1. 在数据类中增加明细字段（如 BacktestResult.bets）
2. API 端点同时返回汇总 + 明细
3. 前端所有区域渲染同一个 API 响应的不同字段

## 陷阱

### 图标文件缺失
manifest.json 中声明的图标文件如果在服务器上不存在，Chrome 不会弹出 PWA 安装横幅。每次更新 manifest 后必须 curl 确认每个文件返回 200。

### 漫画/艺术风格图标不适合
App 图标需要高对比度、主体突出、简洁。Seedream 生成时务必指定 `app launcher icon` 和 `high contrast`。

### 基础 URL 变化
如果 PWA 部署域名变化（如从 dev 到 prod），manifest.json 的 start_url 和 service worker 的 CACHE key 都需要更新。

### Android 签名密钥丢失
bubblewrap init 生成的 signing.keystore 文件必须备份。丢了就不能更新已有的 Google Play 应用。

### gradlew 权限
```bash
chmod +x gradlew
```

### `--noproxy '*'` 代理问题
如果服务器有 `http_proxy` 环境变量，本地 curl 测试 assetlinks 或图标文件时必须加 `--noproxy '*'`，否则走代理反而连不上本地网络。

### Gradle wrapper.jar 下载超时
GitHub Raw 在大陆/某些 VPS 上可能超时。使用带 `--max-time 60` 的重试：
```bash
curl -sL --max-time 60 \
  "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar" \
  -o gradle/wrapper/gradle-wrapper.jar
```
如果持续失败，可以先装 Gradle 再 `gradle wrapper` 生成。

### base64 大图片导致 Argument list too long
不要用 `B64=$(base64 image.jpg | tr -d '\n')` 然后 `curl -d "..."` 的方式传图片给 VLM。bash 命令行有长度限制（~2MB），大图片 base64 后约 2.5MB 会触发此错误。改用 Python 脚本：

```python
import requests, base64, os
with open("image.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
resp = requests.post(..., json={
    "messages": [{"content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
    ]}]
})
```

### 大文件传参导致 Argument list too long
Seedream 返回的图片 URL 24h 过期，必须立即下载。
VLM 调用时 base64 编码的图片过大会导致 bash 命令行超长，用 Python 脚本代替 bash -d 参数传参。

## 参考

- `references/seedream-icon-prompts.md` — 已验证的 App 图标 Prompt 模板（足球+金钱、熊猫+指南针）
- image-generation skill -- 图标生成（Seedream/GPT-image-2 等更多选项）
- github-repo-management skill -- GitHub 仓库创建和管理
