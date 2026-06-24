---
name: "multi-search-engine"
description: "Multi search engine integration with 16 engines (7 CN + 9 Global). Supports advanced search operators, time filters, site search, privacy engines, and WolframAlpha knowledge queries. No API keys required."
---

# Multi Search Engine

Integration of 16 search engines for web crawling without API keys.

> **⚠️ Fallback only.** For most searches, use `tavily-search` instead — faster, more reliable, structured results. This skill is the backup when Tavily is rate-limited or unavailable.

## Workflow

1. **Preparation**: AI Agent initializes an empty in-memory cookie store. Cookies are only acquired dynamically during search operations when access is denied

2. **Language Evaluation**: Detect the language attribute of the search query. If the query is in Chinese, use Domestic search engines (Baidu, Bing CN, Bing INT, 360, Sogou, WeChat, Shenma). If the query is non-Chinese, use International search engines (Google, Google HK, DuckDuckGo, Yahoo, Startpage, Brave, Ecosia, Qwant, WolframAlpha). Select engines based on query relevance and availability.

3. **Controlled Search**: Use web_fetch to execute search requests with rate limiting:
   - Add 1-2 second delay between requests to respect server load
   - Batch requests in groups of 3-4 engines with sequential execution between batches
   - Include standard browser headers to identify as legitimate user agent
   - If access is denied (403/429), fetch engine homepage to obtain fresh session cookies

4. **Cookie Management**: 
   - Cookies are stored ONLY in memory during runtime
   - Cookies are acquired on-demand when search requests fail
   - No cookies are read from or written to config.json or any file
   - Cookies are cleared after search session completes
   - Only session cookies from search engine domains are captured

5. **Retry Mechanism**: If a search fails due to cookie/session issues, retry once with freshly acquired cookies after a 2-second delay

6. **Result Aggregation**: Consolidate successful results from search engines, organize and summarize them to output a core search report

## Search Engines

### Domestic (7)
- **Baidu**: `https://www.baidu.com/s?wd={keyword}`
- **Bing CN**: `https://cn.bing.com/search?q={keyword}&ensearch=0`
- **Bing INT**: `https://cn.bing.com/search?q={keyword}&ensearch=1`
- **360**: `https://www.so.com/s?q={keyword}`
- **Sogou**: `https://sogou.com/web?query={keyword}`
- **WeChat**: `https://wx.sogou.com/weixin?type=2&query={keyword}`
- **Shenma**: `https://m.sm.cn/s?q={keyword}`

### International (9)
- **Google**: `https://www.google.com/search?q={keyword}`
- **Google HK**: `https://www.google.com.hk/search?q={keyword}`
- **DuckDuckGo**: `https://duckduckgo.com/html/?q={keyword}`
- **Yahoo**: `https://search.yahoo.com/search?p={keyword}`
- **Startpage**: `https://www.startpage.com/sp/search?query={keyword}`
- **Brave**: `https://search.brave.com/search?q={keyword}`
- **Ecosia**: `https://www.ecosia.org/search?q={keyword}`
- **Qwant**: `https://www.qwant.com/?q={keyword}`
- **WolframAlpha**: `https://www.wolframalpha.com/input?i={keyword}`

## Quick Examples

```javascript
// Basic search
web_fetch({"url": "https://www.google.com/search?q=python+tutorial"})

// Site-specific
web_fetch({"url": "https://www.google.com/search?q=site:github.com+react"})

// File type
web_fetch({"url": "https://www.google.com/search?q=machine+learning+filetype:pdf"})

// Time filter (past week)
web_fetch({"url": "https://www.google.com/search?q=ai+news&tbs=qdr:w"})

// Privacy search
web_fetch({"url": "https://duckduckgo.com/html/?q=privacy+tools"})

// DuckDuckGo Bangs
web_fetch({"url": "https://duckduckgo.com/html/?q=!gh+tensorflow"})

// Knowledge calculation
web_fetch({"url": "https://www.wolframalpha.com/input?i=100+USD+to+CNY"})
```

## Advanced Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:github.com python` | Search within site |
| `filetype:` | `filetype:pdf report` | Specific file type |
| `""` | `"machine learning"` | Exact match |
| `-` | `python -snake` | Exclude term |
| `OR` | `cat OR dog` | Either term |

## Time Filters

| Parameter | Description |
|-----------|-------------|
| `tbs=qdr:h` | Past hour |
| `tbs=qdr:d` | Past day |
| `tbs=qdr:w` | Past week |
| `tbs=qdr:m` | Past month |
| `tbs=qdr:y` | Past year |

## Privacy Engines

- **DuckDuckGo**: No tracking
- **Startpage**: Google results + privacy
- **Brave**: Independent index
- **Qwant**: EU GDPR compliant

## Bangs Shortcuts (DuckDuckGo)

| Bang | Destination |
|------|-------------|
| `!g` | Google |
| `!gh` | GitHub |
| `!so` | Stack Overflow |
| `!w` | Wikipedia |
| `!yt` | YouTube |

## WolframAlpha Queries

- Math: `integrate x^2 dx`
- Conversion: `100 USD to CNY`
- Stocks: `AAPL stock`
- Weather: `weather in Beijing`

## Pitfalls: Chinese Search Engine Blocking

When scraping Chinese engines from non-browser environments (curl, headless HTTP):

- **Baidu**: Returns "百度安全验证" CAPTCHA page for all curl requests, including mobile (`m.baidu.com`). Effectively blocked without a real browser or cookie session from prior human interaction.
- **Bing CN / Bing INT**: HTML results are rendered client-side via JavaScript — curl gets CSS/JS boilerplate only. Use `format=rss` for XML results, but these return source websites (not news articles) for broad queries.
- **360 (so.com)**: Same JS-rendering issue as Bing. Search results load dynamically.
- **Sogou / WeChat search**: Same JS-rendering issue.

### Working Fallbacks for Chinese News

When search engines fail, use direct news APIs:

- **Sina Finance Roll API**: `https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&k=&num=20&page=1`
  - `lid=2509` = 财经 (finance) — reliable, returns current news
  - `lid=2515` = 科技/商业 (tech/business) — mixed content, ~1 day delay
  - `lid=2510,2511,2512,2513,2514` = various categories but often return stale/cached data
  - Returns JSON with `title`, `intro`, `url`, `ctime` (Unix timestamp) fields

- **Toutiao Hot Board**: `https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc`
  - Returns JSON with trending topics (`Title`, `HotValue`, `Label`, `Url`)
  - JSON can be large (>20KB); parse with `json.loads()` not regex

- **ThePaper.cn**: `https://www.thepaper.cn/`
  - HTML with server-rendered h2/h3 headlines
  - Extract with: `re.findall(r'<h[23][^>]*>(.*?)</h[23]>', text)`

- **Bing RSS** (for specific topics): Works for targeted queries like `?q=凯文·沃什+美联储+主席+2026&format=rss`
  - Returns actual news items when query is specific enough
  - Broad queries (`国际新闻`, `社会热点`) return only source websites

See `references/china-news-sources.md` for detailed API parameter mappings.

## Documentation

- `references/advanced-search.md` - Domestic search guide
- `references/international-search.md` - International search guide
- `references/china-news-sources.md` - Chinese news API fallbacks and lid mappings
- `CHANGELOG.md` - Version history

## License

MIT

## Security & Privacy Notice

### Cookie Handling
- **Purpose**: Cookies are used ONLY to maintain search session state when access is denied (403/429 errors)
- **Storage**: Cookies are kept STRICTLY in memory during runtime - NEVER persisted to disk or config files
- **Acquisition**: Cookies are acquired on-demand from search engine homepages only when search requests fail
- **Scope**: Only session cookies from the specific search engine domain are captured
- **Lifecycle**: Cookies are cleared immediately after the search session completes
- **No Pre-configuration**: No cookies are loaded from config.json or any external file at startup
- **No API Keys**: This tool uses standard web search URLs, no authentication required

### Crawling Ethics
- **Rate Limiting**: Implement reasonable delays between requests (recommend 1-2 seconds)
- **Respect robots.txt**: Honor search engine crawling policies
- **Terms of Service**: Users are responsible for complying with search engine ToS
- **Purpose**: Designed for legitimate search aggregation, not mass data scraping

### Data Handling
- **No Personal Data**: Tool does not collect or transmit user personal information
- **Local Execution**: All operations run locally, no external data transmission
- **Session Isolation**: Cookies are session-specific and cleared after use
