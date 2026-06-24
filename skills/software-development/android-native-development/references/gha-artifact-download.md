# GitHub Actions Artifact Download — Tencent Cloud Workaround

## 问题

GitHub Actions 构建通过后，从腾讯云上海服务器下载 Artifact（APK zip, ~2.2MB）始终超时。

### 现象

```bash
curl -L -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/Org/Repo/actions/artifacts/<id>/zip" \
  -o artifact.zip --max-time 90
# → curl: (28) Operation timed out after 88950ms with 1.3MB/2.2MB
```

- 每次下载到 60-70%（1.3MB/2.2MB）后卡死
- `gh run download` 同样超时
- 使用 `--retry 2 --retry-delay 5` 无用
- 非大小问题（更大的文件也可能被限速）
- 可能原因：GitHub Actions artifact CDN 节点对腾讯云回程限速或路由不佳

## 解决方案

### 方案 A（推荐）：直接从 GitHub Actions 页面下载

直接在浏览器中打开 Actions 页面，点击最新绿色构建 → Artifacts → 下载 zip。

```url
https://github.com/JTCAO515/<Repo>/actions
```

浏览器端下载通常正常（用户本地网络到 GitHub CDN 的连通性好于腾讯云服务器）。

### 方案 B：服务器本地编译 APK

如果服务器有 Android SDK，可以直接 `./gradlew assembleRelease` 本地编译，跳过 GitHub Actions 下载环节：

```bash
# 需要 ~8GB Android SDK（约 15 分钟安装）
sdkmanager "platforms;android-34" "build-tools;34.0.0"
./gradlew assembleRelease
# APK 在 app/build/outputs/apk/release/app-release.apk
```

### 方案 C：Web 代理下载

```bash
# 通过代理/隧道下载
gh run download <run-id> --name APK --dir /tmp/apk
# 或者 scp 从有更好网络的机器
```

## 现状

VisePanda-Android v0.1.0 构建通过但 APK 无法通过服务器下载到本地。用户需要在手机上打开 GitHub Actions 页面直接下载 Artifact zip，解压后安装。
