# SSE Event Format Alignment — Backend ↔ Android

> 后端（Python WSGI / FastAPI / Flask）发出的 SSE 事件格式与 Android OkHttp SseClient 解析格式不一致时的诊断与修复模式。

---

## 症状

Android App 编译通过，但 Chat 页面的 AI 消息为空或只显示初始状态。Web 端（浏览器）正常工作。

## 根因链

```
后端 emit {"token": "Hello"}        ← 旧格式 (key="token")
           ↓ 通过 HTTP SSE 传输
Android SseClient 解析 payload
           ↓ 查找 payload["type"]   ← 期待 {"type":"token","content":"Hello"}
           ↓ 找不到 "type" 字段 → type="" → else 分支 → trySend(SseEvent.Token(data))
           ↓ 结果：收到的 raw data 被当作 token 文本发送
```

## 诊断

```bash
# 1. 直接 curl 后端 SSE 端点看原始格式
timeout 15 curl -N --noproxy '*' \
  -X POST "https://go2china.space/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}]}' 2>&1 | head -20

# timeout 的重要性:
# - <1s 内返回 → 后端有语法错误（如 `name 're' is not defined`）
# - 15-30s 无响应 → API key 缺失或网络不通
# - 正常 → 收到 event: message / data: {...} 流
```

### 常见错误响应模式

| curl 行为 | 根因 | 修复 |
|-----------|------|------|
| 立即返回 `name 're' is not defined` | Python 后端缺少 `import re` | 在文件顶部追加 `import re` |
| 立即返回 `API_KEY not configured` | 环境变量缺失 | 检查 Vercel dashboard / .env 中的 `DEEPSEEK_API_KEY` 或 `LLM_API_KEY` |
| 15-60s 超时后无响应 | DeepSeek/GLM API key 无效 | 测试 key 有效性 (`curl api.deepseek.com/v1/models`) |
| 30s 超时后返回部分数据 | 代理/Vercel cold start | 重试，或加 `Connection: keep-alive` header |

## 后端 → Android 事件格式对照表

## 后端 → Android 事件格式对照表

| 事件类型 | Web 兼容旧格式 | Android 兼容新格式 | event 字段 |
|----------|--------------|-------------------|-----------|
| Token | `{"token": "..."}` | `{"type":"token","content":"...","token":"..."}` | `message` |
| Image | `{"image":{...}}` | `{"type":"image","content":{...,"image":...}}` | `message` |
| Split | `{"split":true}` | `{"type":"split","content":"---","split":true}` | `message` |
| FAQ | `{"faq":{...}}` | `{"type":"faq","content":"...","faq":{...}}` | `message` |
| Done | `{"done":true}` | `{"done":true}` (事件级) | `done` |
| Error | `{"error":"..."}` | `{"type":"error","content":"..."}` | `error` |

## 修复原则：向后兼容（双格式）

**不在旧格式上改——加新格式字段，保留旧字段。** Web 端解析 `data.token`，Android 端解析 `data.type`/`data.content`，互不干扰。

```python
# Before:
yield _sse_event(json.dumps({"token": "Hello"}))
yield _sse_event(json.dumps({"image": {"url": "/a.jpg"}}))
yield _sse_event(json.dumps({"split": True}))

# After:
yield _sse_event(json.dumps({
    "type": "token",
    "content": "Hello",
    "token": "Hello"                  # ← 保留旧字段
}))
yield _sse_event(json.dumps({
    "type": "image",
    "content": {"url": "/a.jpg"},
    "image": {"url": "/a.jpg"}        # ← 保留旧字段
}))
yield _sse_event(json.dumps({
    "type": "split",
    "content": "separator",
    "split": True                      # ← 保留旧字段
}))
```

## Android SseClient 解析逻辑

```kotlin
// SseClient.kt — 核心解析
when (currentEvent) {
    "message" -> {
        val payload = JsonParser.parseString(data).asJsonObject
        val type = payload.get("type")?.asString ?: ""    // 优先用新格式
        val content = payload.get("content")?.asString ?: data  // fallback 到 raw data

        when (type) {
            "token" -> trySend(SseEvent.Token(content))
            "split" -> trySend(SseEvent.Split(content))
            "image" -> trySend(SseEvent.Image(content))
            "faq" -> trySend(SseEvent.Faq(content))
            "done" -> { trySend(SseEvent.Done); close() }
            else -> trySend(SseEvent.Token(data))           // 无 type=旧格式 fallback
        }
    }
    "done" -> { trySend(SseEvent.Done); close() }
    "error" -> { trySend(SseEvent.Error(data)); close() }
}
```

## 预防

1. **建项目时就对齐格式** — 在 PRD 或 API 契约中明确 SSE 事件 schema
2. **后端 emit 时双格式** — 只要 Web 前端存活，后端永远发双格式（新旧兼容）
3. **Android SseClient 单元测试** — mock SSE 数据流验证解析正确性
4. **curl 抓 SSE 原始输出** — 不依赖 Postman 或浏览器 devtools，直接看 `event:` 和 `data:` 行

## 后端环境变量回退链

Python 后端需要 API key 才能调用 LLM。不同部署环境的 env var 名可能不同：

```python
# index.py — 推荐的环境变量回退链
DEEPSEEK_API_KEY = (
    os.environ.get("DEEPSEEK_API_KEY", "")     # 1. 标准 DeepSeek
    or os.environ.get("LLM_API_KEY", "")        # 2. GLM 旧版兼容
    or os.environ.get("AESCULAP_DEEPSEEK_KEY", "")  # 3. Hermes Agent 自愈系统所用
)
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL",
                 os.environ.get("LLM_MODEL", "deepseek-v4-flash"))  # 默认 V4 Flash
DEEPSEEK_BASE = (
    os.environ.get("DEEPSEEK_BASE_URL", "")
    or os.environ.get("LLM_BASE_URL", "")
    or "https://api.deepseek.com/v1"
)
```

**Vercel 部署注意事项:**
- `vercel env` 需要 token 登录才能管理环境变量
- 如果 Vercel CLI 未登录，通过 **Vercel dashboard → Project → Settings → Environment Variables** 手动设置
- `git push` 触发自动部署后，新环境变量才生效
- 测试部署是否成功：用 `timeout 15 curl` 看返回类型（语法错误 → 立即返回，缺 key → 超时，正常 → SSE 流）
