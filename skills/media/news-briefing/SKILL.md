---
name: news-briefing
description: 每日新闻推送系统 — 从中国可访问的实时新闻 API 直连抓取，零第三方 Key 依赖。支持早报/晚报双时段、4 类新闻、Markdown 交付到微信。触发词：每日新闻 / 新闻推送 / 早报 / 晚报 / news briefing / 新闻 cron
---

# 每日新闻推送 (News Briefing)

## 概述

自建新闻推送系统，直接从中国可访问的新闻源 API 抓取实时内容，无需 Tavily/天行数据等第三方 Key。

**核心架构：**

```
cron (7:00 / 22:00)
  → news_morning.py / news_evening.py (wrapper scripts)
    → news_briefing.py (核心引擎)
      ├── 新浪财经滚动 API → 财经新闻
      ├── 新华网国际 h3 抓取 → 国际新闻
      ├── 36氪快讯 API → 科技新闻
      └── 澎湃新闻热榜 API → 国内热点
        → 格式化 Markdown → 推送到微信
```

## 文件结构

```text
~/.hermes/scripts/
├── news_briefing.py     ← 核心引擎（4 源抓取 + 格式化）
├── news_morning.py      ← 早报 wrapper（直接发送到微信）
├── news_evening.py      ← 晚报 wrapper（直接发送到微信）
└── weixin_send.py       ← 同步 HTTP iLink API 投递助手
```

另有副本存档于 skill 目录：`~/.hermes/skills/media/news-briefing/scripts/weixin_send.py`

## 数据源详情

| 类别 | 数据源 | URL | 方式 |
|------|--------|-----|:----:|
| 💰 财经 | 新浪财经滚动 | `https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=8` | JSON API |
| 🌍 国际 | 新华网国际 | `https://www.xinhuanet.com/world/` | h3 标签抓取 |
| 🌍 国际(备用) | Reuters China | `https://www.reuters.com/world/china/` | h2/h3 标签抓取 |
| 🔬 科技 | 36氪快讯 | `https://36kr.com/api/newsflash` | JSON API |
| 🔥 国内热点 | 澎湃新闻热榜 | `https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar` | JSON API |

### 财经源说明

新浪财经滚动 API 参数：
- `pageid=153` — 滚动新闻
- `lid=2516` — 财经分类
- 返回 JSON 含 `result.data[].title` + `url`

### 国际源说明

- **首选**：新华网 `xinhuanet.com/world/` — 从中国直连稳定
- **备用**：Reuters China 页面抓取 — 慢但内容丰富
- **兜底**：从澎湃热榜中提取含国际关键词（美国/俄罗斯/欧盟等）的条目

### 科技源说明

36氪 API 返回 `data.items[]`，每项含 `title`（标题）+ `widget_title`（备选标题）+ `url`

### 热点源说明

澎湃新闻热榜返回 `data.hotNews[]`，每项含 `name`（标题）

## 格式化

输出为标准 Markdown：

```
🌙 每日晚报 | 2026年05月25日 周一

💰 财经速览
• 标题 · [链接](url)

🌍 国际局势
• 标题 · [链接](url)

🔬 科技前沿
• 标题

🔥 国内热点
• 标题
```

每个分类最多 4 条，按时间倒序。

## Weixin 交付架构（重要）

### ⚠️ 已知问题：Hermes Gateway 异步上下文 Bug

Hermes Agent 0.12.0 的 Weixin Gateway 使用 aiohttp 异步 HTTP 客户端。当 cron 定时任务触发 `deliver: origin` 投递到微信时，会报错：

```
Timeout context manager should be used inside a task
```

根源：cron 的运行环境未正确初始化异步事件循环，而 Weixin Gateway 的 `send_message` 使用 `async with session.post(..., timeout=aiohttp.ClientTimeout(...))` 依赖活动的事件循环。

### 修复方案

**不要依赖 `deliver: origin` 投递到微信**，改用同步 REST API 直接发送。

架构改为：

```
cron (7:00 / 22:00)
  → news_morning.py / news_evening.py (wrapper scripts)
    → news_briefing.py (核心引擎，生成 Markdown)
    → weixin_send.py (同步 HTTP 调用 iLink REST API)
    → stdout 输出（供 cron 日志记录）
```

关键变更：
- `deliver: local` — cron 只保存日志到本地，不做 Gateway 投递
- `prompt: [SILENT]` — 跳过 LLM 处理环节（脚本已经发送并输出）
- 脚本本身负责调用 `weixin_send.py` 完成实际推送

### weixin_send.py（同步投递助手）

位置：`~/.hermes/scripts/weixin_send.py`

**请求方式：** 纯同步 HTTP（requests 库），完全脱离 Hermes 异步 Gateway

**API 端点：** `https://ilinkai.weixin.qq.com/ilink/bot/sendmessage`

**请求头：**
```python
{
    "Content-Type": "application/json",
    "AuthorizationType": "ilink_bot_token",
    "Authorization": f"Bearer {TOKEN}",
    "X-WECHAT-UIN": random_wechat_uin(),
    "iLink-App-Id": "bot",
    "iLink-App-ClientVersion": str((2 << 16) | (2 << 8) | 0),
    "Content-Length": str(len(body.encode("utf-8"))),
}
```

**请求体格式：**
```python
{
    "base_info": {"channel_version": "2.2.0"},
    "msg": {
        "from_user_id": ACCOUNT_ID,
        "to_user_id": TARGET_USER_ID,
        "client_id": ACCOUNT_ID,
        "message_type": 1,     # MSG_TYPE_BOT
        "message_state": 4,    # MSG_STATE_FINISH
        "item_list": [{"type": 1, "text_item": {"text": "消息内容"}}]
    }
}
```

**凭证来源（环境变量）：**
- `WEIXIN_TOKEN` — `{account_id}:{token_value}` 格式
- `WEIXIN_ACCOUNT_ID` — 机器人账号 ID
- `WEIXIN_BASE_URL` — `https://ilinkai.weixin.qq.com`
- `WEIXIN_HOME_CHANNEL` — 默认接收用户 ID

## Cron 配置

### 早报 (7:00)

```json
{
  "id": "33d32c99dfb4",
  "schedule": "0 7 * * *",
  "script": "news_morning.py",
  "prompt": "[SILENT]",
  "deliver": "local"
}
```

### 晚报 (22:00)

```json
{
  "id": "920ad9fe397e",
  "schedule": "0 22 * * *",
  "script": "news_evening.py",
  "prompt": "[SILENT]",
  "deliver": "local"
}
```

**关键设置：**
- `script` 必须是 `~/.hermes/scripts/` 下的文件名（相对路径）
- `skills` 设为空数组 `[]`（脚本自包含，无需外部 skill）
- `prompt` 设为 `[SILENT]`（脚本自行发送到微信，无需 LLM 处理）
- `deliver` 设为 `local`（仅保存日志，不依赖 Gateway 投递）

## 故障模式与处理

| 问题 | 表现 | 处理 |
|------|------|------|
| 新浪 API 超时 | 财经栏为空 | 跳过该栏，其他栏正常 |
| 新华网页面改版 | 国际栏为空 | 自动切到 Reuters fallback |
| 澎湃 API 限流 | 热点栏为空 | 跳过该栏 |
| 36Kr API 改版 | 科技栏为空 | 跳过该栏 |
| 全源失效 | 4 栏全空 | 每条显示 "暂未获取到 XX 数据" |
| Weixin Gateway 异步 bug | 后台报 `Timeout context manager should be used inside a task` | 改用 `weixin_send.py` 同步 REST 投递，cron 的 `deliver` 设为 `local` |

## 历史

- **v1 (旧)**: 使用 Tavily Search API，返回 portal 索引页链接而非实时文章
- **v2 (当前)**: 直连中文新闻源 API，零外部 Key 依赖，获取今日实时内容
