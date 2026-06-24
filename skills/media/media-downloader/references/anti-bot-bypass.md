# yt-dlp Bot 检测绕过

> 来源: 2026-05-29 实战会话 (中国服务器, headless环境)
> 问题: `Sign in to confirm you're not a bot`

## 绕过方法

### 方法1: 使用 extractor-args (推荐)

```bash
yt-dlp --extractor-args "youtube:player_client=android" "URL"
```

原理: 模拟 Android 客户端请求, bot 检测比 web 客户端宽松。

也可组合多个客户端:
```bash
yt-dlp --extractor-args "youtube:player_client=android,web" "URL"
```

### 方法2: 使用 cookies

从本地浏览器导出 cookies:
```bash
yt-dlp --cookies-from-browser chrome "URL"
```

或手动导出 cookies.txt 使用:
```bash
yt-dlp --cookies cookies.txt "URL"
```

### 验证方法

用 `--print` 参数先测试是否能获取元数据(不下载):
```bash
yt-dlp --extractor-args "youtube:player_client=android" \
  --print title --print duration "URL"
```

## 已知限制

- 中国服务器可能 YouTube 直连不通, 需要 `--proxy`
- deno 必须安装, 否则某些格式/元数据提取失败
- `Sign in` 报错时, `player_client=android` 成功概率 >80%
