# AnySearch MCP Server

> 专为 AI Agent 设计的统一搜索基础设施。支持通用网页搜索 + 22 个垂直领域（金融/学术/代码/安全等）+ URL全文提取。

**官网:** https://www.anysearch.com
**GitHub:** https://github.com/anysearch-ai/anysearch-mcp-server
**API 文档:** https://www.anysearch.com/docs

## 核心能力

| 工具 | 说明 |
|------|------|
| `search` | 通用/垂直领域搜索，22 domains × 9 content types |
| `batch_search` | 并行搜索 ≤5 个查询，结果合并返回 |
| `extract` | 抓取 URL 全文，返回干净 Markdown（截断 50,000 字符） |

## 传输协议

原生支持 **Streamable HTTP**（MCP 2025-03-26 规范），无需代理中转。

| 协议 | 原生支持？ | 适用场景 |
|------|-----------|---------|
| Streamable HTTP | ✅ 原生 | Hermes Agent, OpenCode, Claude Desktop 2025.6+ |
| SSE | 需 supergateway 中转 | Cursor, Windsurf |
| stdio | 需 mcp-remote 中转 | VS Code Copilot, Cline |

## Hermes 配置

### 匿名额度（免费，速率较低）

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  anysearch:
    url: https://api.anysearch.com/mcp
```

### 带 API Key（更高并发）

```yaml
mcp_servers:
  anysearch:
    url: https://api.anysearch.com/mcp
    headers:
      Authorization: "Bearer YOUR_ANYSEARCH_API_KEY"
    timeout: 180
    connect_timeout: 30
```

### 获取 API Key

免费 Key 从 https://anysearch.com/console/api-keys 创建。

## REST API（非 MCP 场景）

```bash
curl -X POST https://api.anysearch.com/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Go 1.22 release notes",
    "max_results": 5,
    "domains": ["code", "tech"],
    "content_types": ["web", "doc"]
  }'
```

**Request 参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | string (必填) | 搜索查询 |
| `max_results` | int | 1-100，默认 10 |
| `domains` | string[] | 22 个领域：general, code, tech, finance, academic, legal, security, news... |
| `content_types` | string[] | web, news, code, doc, academic, data, image, video, audio |
| `zone` | string | `cn` 或 `intl` |
| `freshness` | string | day, week, month, year |
| `providers` | string[] | 显式指定搜索提供商 |

**Response 字段：**

| 字段 | 说明 |
|------|------|
| `title`, `url`, `description` | 基本元信息 |
| `content` | 清洗后正文 |
| `raw_content` | 原始正文 |
| `source` | web / code / academic / news 等 |
| `score` / `quality_score` | 相关性和质量评分 |
| `published_at` | RFC3339 时间戳 |

## 已知问题

- **中国网络兼容性**：`api.anysearch.com` 从中国服务器可达（已验证 HTTP 200）
- **匿名额度有限**：每日免费配额用完后返回 402 `daily_free_quota_exhausted`
- **MCP 工具前缀**：Hermes 注册为 `mcp_anysearch_search`、`mcp_anysearch_batch_search`、`mcp_anysearch_extract`
- **配置后需新会话**：MCP 服务器在 Hermes 启动时发现，`/reset` 或重启后生效
