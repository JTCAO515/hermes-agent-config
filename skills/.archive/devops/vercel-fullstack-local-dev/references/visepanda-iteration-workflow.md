# VisePanda Rapid Iteration Workflow

> 本文件记录 VisePanda (v2) 项目的持续迭代模式。新会话接手时参考此流程。

## 核心原则

用户要求**不间断自动化迭代**：自行判断需求 → 实现 → 本地测试 → 部署 → 进入下一轮，不等待用户验证。

## 迭代节奏

- **计划粒度**：每 3 次迭代为一组，提前规划并告知用户
- **单次迭代**：聚焦一个主题，1-5 个改动点，5-10 分钟完成
- **阻塞处理**：遇需人工介入的环节（如缺密码）→ 先尝试绕过 → 无法绕过则记录并跳过

## 标准操作流程

```
计划 3 轮 → 逐轮执行 →
  1. 写代码（优先用 Python 脚本做字符串替换，避免 patch 转义问题）
  2. 同步 index.py：cp api/main.py api/index.py
  3. 本地验证：uvicorn + curl grep 关键特征
  4. 更新 docs/ITERATION_LOG.md
  5. git commit + push
  6. VERCEL_TOKEN=... vercel deploy --prod --yes --no-color
  7. 检查构建日志（无 curl 验证——中国服务器访问不了 Vercel）
```

## 已验证的测试命令模板

```bash
cd ~projects/vise-panda-2 && python3 -m uvicorn api.main:app --port 8765 &

# 通用验证
curl -s http://localhost:8765/api/health
curl -s http://localhost:8765/ | grep -c "feature_pattern"

# 检查 JS/CSS 特征存在于渲染的 HTML 中
curl -s http://localhost:8765/chat | grep -c "function_name"
curl -s http://localhost:8765/chat | grep -c "css_class"
```

## 部署命令模板

```bash
cp api/main.py api/index.py
git add -A && git commit -m "feat(iterN): description" && git push
VERCEL_TOKEN=vcp_xxx vercel deploy --prod --yes --no-color
```

## 已完成的迭代（截至 2026-05-24）

| Iter | 主题 | 关键文件改动 |
|------|------|-------------|
| 0 | 从零重写 | `api/main.py` 内核 |
| 1 | 移动端 + 聊天历史 | CSS @media, loadHistory(), GET /api/trips/{id}/messages |
| 2 | ~~Supabase Postgres~~ | 跳过——缺 DB 密码 |
| 3 | 首页卡片 + 行程样式 | .card CSS, goChat(), .skeleton, .trip-card, M() 增强 |
| 4 | 时间戳 + 智能滚动 + 清空 + 游客持久化 | .time CSS, smartScroll(), clearChat(), vp_trip localStorage |
| 5 | 错误处理 + 安全 | 重试按钮, 断线提示, favicon 204, health 增强 |
| 6 | SEO + 404 | og:title/meta desc, 404 handler, ⚠️ 域名未绑定 |
| 7 | 空态欢迎页 | .welcome CSS, welcome-chip 引导, loadHistory 隐藏逻辑 |
| 8 | XSS 净化 + 限流 | _sanitize(), _RATE_LIMIT, IP 级 20次/60s |
| 9 | 行程列表页 | /trips 页面, GET /api/trips, 自动 trip title |
| 10 | 行程管理 | PUT/DELETE /api/trips/{id}, 重命名+删除按钮, API 404→JSON |
| 11 | 分享行程 | Trip.share_id, POST /api/trips/{id}/share, /share/{sid} 只读页 |
| 12 | ~~双语切换~~ | **被 f-string 转义瓶颈阻断**——JS 花括号在内联 f-string 中需全部写成 `{{}}`，i18n JSON 对象手写双转义极易出错，三次尝试均污染其他页面 |
| 13 | **JS 拆分 → static/** | 4 个静态 JS 文件, app.mount StaticFiles, 解除 f-string 限制 | |
| 14 | **结构化行程 + SSE 增强 + 分享卡** | `_parse_itinerary()`, SSE event_id, 前端指数退避重连, SVG 1200×630 card, Trip detail API, SupabaseDB proxy env-fix | |

## 新模式：结构化行程解析（Iter 14）

LLM 输出后自动检测结构化行程并保存到 Trip.current_itinerary。

**触发流程**：
1. User 在聊天中描述行程需求（如"成都5天"）
2. LLM 输出 day-by-day 格式（含 `**Day 1 — ...**` 等标记）
3. `chat_endpoint` 的 `generate()` 在保存 assistant 消息后自动调用 `_parse_itinerary()`
4. 解析结果写入 `Trip.current_itinerary` JSON 字段
5. 前端收到 `trip_update` SSE 事件，显示"📋 Itinerary saved — 成都 · 5 days"

⚠️ `_parse_itinerary()` 只保存一次，后续对话更新行程不会覆盖已有数据。

## 新模式：SSE event_id + 前端重连

```python
# 后端：每条 token 前加 "id: {递增序号}\n"
yield f"id: {event_id}\n{chunk}"
```

```javascript
// 前端：fetch 失败时指数退避重试 3 次
for (let retries = 0; retries < 3; retries++) {
    await new Promise(r => setTimeout(r, 1000 * Math.pow(2, retries)));
    r = await fetch('/api/chat', { ... });
    if (r.ok) break;
}
// 流中断：保留已收到内容 + 显示 retry 链接
```

## 新模式：SVG 卡片 (OG Image)

GET /api/trips/{trip_id}/card 返回 1200x630 SVG，用于 og:image。服务器端生成，零依赖。包含：渐变暗色背景、天数、城市名、酒店摘要、预算档次、VisePanda品牌。通过 og:image 元标签嵌入分享页。

## 新模式：SupabaseDB 代理环境变量化

之前硬编码 127.0.0.1:10809，Vercel 上无代理直接抛异常。修复后通过 SUPABASE_HTTP_PROXY 环境变量控制，仅在 IS_DEV=1 且设了代理时才启用。

## 已知未解决问题

1. **Supabase Postgres 密码** — 数据库 URL: `postgresql://postgres:[PWD]@db.jdlinmdhmulozrjeseyc.supabase.co:5432/postgres`
2. **go2china.space 域名** — 被 5 个旧 Vercel 项目占用，`vercel domains rm` CLI 交互式卡死，需登录 Dashboard 手动移除再绑定
3. **Iter 12 双语切换** — 被 f-string 瓶颈阻断。**Iter 13 的 JS 拆分已解除此限制**，可重试
4. **合同审阅 skill** — 用户在本会话开头提到，但 task 切换到 VisePanda 迭代后未实现

## 架构速查

- **主文件** `api/main.py`（~500 行，JS 已外移），`api/index.py` 为副本（Vercel 入口）
- **静态 JS** `static/` 目录：`landing.js`, `chat.js`, `auth.js`, `trips.js`（纯 JS，零 f-string 转义）
- 后端渲染 HTML，Supabase 配置通过 f-string 注入 `<script>window.__SUPABASE_CONFIG__</script>`
- LLM: GLM 5.1 @ `https://open.bigmodel.cn/api/paas/v4`
- GitHub: `JTCAO515/vise-panda-2`, SSH key: `~/.ssh/vise_github`
- Vercel 项目: `jtcao515s-projects/vise-panda-2`
- 文档: `docs/ITERATIONS.md`（路线图）, `docs/ITERATION_LOG.md`（执行记录）
