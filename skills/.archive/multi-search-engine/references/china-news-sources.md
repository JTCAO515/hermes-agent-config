# Chinese News API Fallbacks

When search engines block curl requests (Baidu CAPTCHA, Bing/360 JS rendering), these direct APIs work.

## Sina Finance Roll API

**Base URL**: `https://feed.mix.sina.com.cn/api/roll/get`

**Parameters**:
- `pageid=153` — rolling news page ID (use 153 for news)
- `lid` — category ID (see mapping below)
- `k=` — keyword filter (optional, leave empty for all)
- `num=20` — results per page
- `page=1` — page number
- `callback=` — leave empty for raw JSON (no JSONP wrapper)

**Response format**:
```json
{
  "result": {
    "status": {"code": 0, "msg": "succ"},
    "data": [
      {
        "title": "新闻标题",
        "intro": "新闻摘要",
        "url": "https://finance.sina.com.cn/...",
        "ctime": "1779478110",  // Unix timestamp
        "docid": "comos:...",
        "media_name": "来源媒体"
      }
    ]
  }
}
```

### Verified lid Mappings

| lid | Category | Status | Notes |
|-----|----------|--------|-------|
| 2509 | 财经 | ✅ Active | US/global stocks, economics. Fresh data (within hours). Most reliable. |
| 2515 | 科技/商业 | ✅ Active | Tech, enterprise, business reports. ~1 day delay. Mixed quality. |
| 2510 | 科技 | ❌ Stale | Returns 2024-2025 cached content |
| 2511 | 国内 | ❌ Stale | Returns 2024-2025 content, mostly international |
| 2512 | 国际(?) | ❌ Wrong | Returns sports (围棋) content |
| 2513 | 社会 | ⚠️ Partial | Has recent content but JSON often malformed (truncation at 20K chars) |
| 2514 | 国际 | ❌ Stale | Returns 2023 content |
| 2505 | 全部 | ❌ Empty | Returns empty data |
| 296 | 滚动 | ❌ Empty | Returns empty data |

**Usage example**:
```bash
curl -s -H "User-Agent: Mozilla/5.0 ..." \
  "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1&callback="
```

## Toutiao Hot Board

**URL**: `https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc`

Returns trending topics with hot values. JSON can exceed 20KB — use `json.loads()` with full output, not regex.

**Response format**:
```json
{
  "data": [
    {
      "Title": "热点标题",
      "HotValue": "1234567",
      "Label": "标签",
      "Url": "https://www.toutiao.com/trending/...",
      "ClusterId": 7642559819941462026
    }
  ]
}
```

## ThePaper.cn Headlines

**URL**: `https://www.thepaper.cn/`

Server-rendered HTML. Extract headlines from h2/h3 tags:

```python
import re
titles = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', html)
```

## Bing RSS (Targeted Queries)

**URL pattern**: `https://cn.bing.com/search?q={specific_keywords}&ensearch=1&format=rss`

Only works for SPECIFIC queries (person names, event names). Broad queries like "国际新闻" or "社会热点" return source websites, not news articles.

Working example: `?q=凯文·沃什+美联储+主席+2026&format=rss` — returns actual news items.

## Sources That Do NOT Work (as of 2026-05)

| Source | Issue |
|--------|-------|
| Baidu (www, m) | CAPTCHA: "百度安全验证" |
| Bing HTML search | JS-rendered, curl gets only CSS |
| 360 so.com | JS-rendered, curl gets only CSS |
| Zhihu hot API | Requires authentication |
| Weibo hot API | Returns 403 Forbidden |
| 163 news mobile API | Returns cached 2018 data |
| QQ News API | Returns `data: null` |
| CLS (财联社) API | Returns 405 / HTML redirect |
| Xinhua / People | Returns 0 bytes (blocked) |
| Google News RSS | Returns 0 bytes (blocked in CN) |
| EastMoney API | Returns empty |
| Reuters API | Returns 0 bytes (blocked) |
