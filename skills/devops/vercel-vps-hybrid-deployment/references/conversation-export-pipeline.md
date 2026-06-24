# Conversation Export Pipeline

从 Hermes Agent 的 `state.db` 全量导出对话历史到 Dashboard 的完整管线。

## Pattern

```
state.db (SQLite, 186 sessions / 8K+ messages)
    ↓ reads
conversation-export.py
    ↓ exports
JSON (3.8MB, for API) + Markdown (1.4MB, human-readable)
    ↓ served via
hermes-api.py GET /api/hermes/conversations   → session list (summary, no message bodies)
hermes-api.py GET /api/hermes/conversations/:id  → full messages for one session
    ↓ consumed by
index.html (Vercel) — 💬 Conversations card with stats + expandable sessions
```

## Data Source

- **文件**: `~/.hermes/state.db`
- **表**: `sessions` (会话元数据) + `messages` (消息内容)
- **角色过滤**: 只导出 `role IN ('user', 'assistant')`，排除 `tool` 调用

```sql
-- 会话列表
SELECT id, source, user_id, title, started_at, ended_at, message_count
FROM sessions ORDER BY started_at DESC

-- 单会话消息
SELECT id, role, content, timestamp
FROM messages
WHERE session_id = ? AND role IN ('user', 'assistant')
ORDER BY id ASC
```

## 数据结构

### JSON 导出格式

```json
{
  "generated_at": "2026-06-16 19:43 UTC",
  "total_sessions": 186,
  "total_messages": 8274,
  "sessions": [
    {
      "id": "20260616_182141_ae75...",
      "source": "weixin",
      "source_label": "微信 (WeChat)",
      "title": "纳米数据存档数据清单 #3",
      "started_at": "2026-06-16 10:21 UTC",
      "message_count": 322,
      "messages": [
        {
          "id": 26040,
          "role": "user",
          "content": "...",
          "timestamp": 1781612148.925572,
          "time": "2026-06-16 11:43 UTC"
        }
      ]
    }
  ]
}
```

### Markdown 导出

按会话分节，每条消息用 ````text` 代码块包裹。长消息 (>500字符) 截断并标注。

## API 端点（3 层粒度）

| 端点 | 用途 | 数据量 | 响应时间 |
|------|------|--------|---------|
| `/api/hermes/conversations` | 完整会话列表（无消息体，每会话含120字符预览） | ~10KB | ~0.1s |
| `/api/hermes/conversations/:id` | 单会话详情（含全部消息体） | 平均 ~7KB | ~0.05s |
| `/api/hermes/all` → `.conversations` | Dashboard 用摘要（统计 + 最新10会话） | ~2KB | 同 /all |

**设计原则：** `/all` 和 `/conversations` 端点绝不传输消息体（只传预览），体量最大的消息体只在用户点击展开单会话时才按需加载。避免 3.8MB 全量数据每次自动刷新都传输。

### 前端渲染

点击会话行时，JS 动态 fetch 详情：

```javascript
fetch(`/api/hermes/conversations/${encodeURIComponent(session.id)}`)
  .then(r => r.json())
  .then(data => {
    // data.messages → 按时间顺序的 [{role, content, time}]
    renderMessages(data.messages);
  });
```

**关键注意：**
- `escapeHtml()` 必须用于 content 渲染（内容包含用户输入的任意文本）
- Session ID 不可截断 — 传给前端的是完整 ID，API 做全字匹配
- 每条消息显示 300 字符，过长则截断（避免单条长消息撑爆布局）

## 来源统计

| source | 中文标签 | Dashboard 图标 |
|--------|---------|---------------|
| `weixin` | 微信 (WeChat) | 💬 |
| `yuanbao` | 元宝 (WeCom) | 📱 |
| `cron` | 定时任务 | ⏰ |
| `cli` | 终端 (CLI) | 🖥 |
| `qqbot` | QQ Bot | 🐧 |

## Cron 配置

```bash
# 复制到 cron 可用目录
cp conversation-export.py ~/.hermes/scripts/conversation-export.py

# 每 6 小时自动更新
# schedule: 0 */6 * * *
# 脚本名: conversation-export.py
```

## 已知约束

- **SQLite 读取性能**: 186 会话 / 8274 消息 / 1.4MB 文本 → 全量导出约 15-30s
- **消息截断**: 前端展示截断 300 字符，Markdown 导出截断 500 字符
- **JSON 文件大小**: 3.8MB (含完整消息体) — 适合文件缓存，不适合高频 API 传输
- **会话标题**: 无标题的会话显示为 `(无标题)`，通常是 cron 触发的自动化任务

## 与 dashboard-status-cache 的异同

| 维度 | Dashboard Status Cache | Conversation Export |
|------|----------------------|-------------------|
| 数据源 | git logs, system state, errors | Hermes state.db (会话+消息) |
| 数据量 | ~50KB | ~3.8MB |
| 更新频率 | 每6h | 每6h (与状态同步) |
| 前端加载 | 启动时全量注入 (`/all`) | 按需加载 (`/:id`) |
| 可读导出 | 无 | Markdown 文件可用于离线阅读 |
