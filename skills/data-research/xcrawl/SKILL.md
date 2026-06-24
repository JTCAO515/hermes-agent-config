---
name: xcrawl
description: Default entry point for XCrawl web data requests (scrape, map, crawl, search). Routes to the appropriate XCrawl API based on task type.
allowed-tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep
metadata:
  version: 1.0.2
  xcrawl:
    skillKey: xcrawl
    homepage: https://www.xcrawl.com/
    requires:
      localFiles:
        - ~/.xcrawl/config.json
      anyBins:
        - curl
        - node
    apiKeySource: local_config
---

# XCrawl — Consolidated Web Data Extraction

XCrawl is a web data extraction API with 4 operations: Scrape, Map, Crawl, and Search. All share the same auth, base URL, and config.

## Required Local Config

**File:** `~/.xcrawl/config.json`

```json
{
  "XCRAWL_API_KEY": ""
}
```

API key is read from local config file only — no global env vars.

**Credits:** Free 1000 credits at [dash.xcrawl.com](https://dash.xcrawl.com/).

## Auth (all operations)

```bash
API_KEY="$(node -e "const fs=require('fs');const p=process.env.HOME+'/.xcrawl/config.json';const k=JSON.parse(fs.readFileSync(p,'utf8')).XCRAWL_API_KEY||'';process.stdout.write(k)")"
```

**Header:** `Authorization: Bearer <XCRAWL_API_KEY>`

---

## A. Scrape — Single-Page Extraction

**Endpoint:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `https://run.xcrawl.com/v1/scrape` | Start scrape (sync/async) |
| GET | `https://run.xcrawl.com/v1/scrape/{scrape_id}` | Poll async result |

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `url` | string | Yes | – | Target URL |
| `mode` | string | No | `sync` | `sync` / `async` |
| `proxy` | object | No | – | Proxy config (location, sticky_session) |
| `request` | object | No | – | locale, device, cookies, headers |
| `js_render` | object | No | – | JS rendering config |
| `output` | object | No | – | formats, screenshot, json.prompt, json.json_schema |
| `webhook` | object | No | – | Async webhook (mode=async only) |

**output.formats:** `html`, `raw_html`, `markdown`, `links`, `summary`, `screenshot`, `json`

**cURL — sync:**
```bash
curl -sS -X POST "https://run.xcrawl.com/v1/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","mode":"sync","output":{"formats":["markdown","links"]}}'
```

**cURL — async + poll:**
```bash
CREATE_RESP="$(curl -sS -X POST "https://run.xcrawl.com/v1/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","mode":"async","output":{"formats":["json"]},"json":{"prompt":"Extract title and price."}}')"
SCRAPE_ID="$(node -e 'const s=process.argv[1];const j=JSON.parse(s);process.stdout.write(j.scrape_id||"")' "$CREATE_RESP")"
curl -sS -X GET "https://run.xcrawl.com/v1/scrape/${SCRAPE_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

**Node.js:**
```bash
node -e '
const fs=require("fs");
const apiKey=JSON.parse(fs.readFileSync(process.env.HOME+"/.xcrawl/config.json","utf8")).XCRAWL_API_KEY;
const body={url:"https://example.com",mode:"sync",output:{formats:["markdown","json"]},json:{prompt:"Extract title and date."}};
fetch("https://run.xcrawl.com/v1/scrape",{
  method:"POST",
  headers:{"Content-Type":"application/json",Authorization:`Bearer ${apiKey}`},
  body:JSON.stringify(body)
}).then(async r=>{console.log(await r.text());});
'
```

---

## B. Map — Site URL Discovery

**Endpoint:** `POST https://run.xcrawl.com/v1/map`

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `url` | string | Yes | – | Site entry URL |
| `filter` | string | No | – | Regex filter for URLs |
| `limit` | integer | No | 5000 | Max URLs (up to 100000) |
| `include_subdomains` | boolean | No | true | Include subdomains |

**Response:** `{map_id, status, data: {links: string[], total_links}}`

**cURL:**
```bash
curl -sS -X POST "https://run.xcrawl.com/v1/map" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","filter":"/docs/.*","limit":2000,"include_subdomains":true}'
```

**Node.js:**
```bash
node -e '
const fs=require("fs");
const apiKey=JSON.parse(fs.readFileSync(process.env.HOME+"/.xcrawl/config.json","utf8")).XCRAWL_API_KEY;
fetch("https://run.xcrawl.com/v1/map",{
  method:"POST",
  headers:{"Content-Type":"application/json",Authorization:`Bearer ${apiKey}`},
  body:JSON.stringify({url:"https://example.com",filter:"/docs/.*",limit:3000,include_subdomains:true})
}).then(async r=>{console.log(await r.text());});
'
```

---

## C. Crawl — Full-Site or Scoped Crawling

**Endpoint:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `https://run.xcrawl.com/v1/crawl` | Start crawl |
| GET | `https://run.xcrawl.com/v1/crawl/{crawl_id}` | Read result |

**Crawler parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 100 | Max pages |
| `include` | string[] | – | Include only URLs matching regex |
| `exclude` | string[] | – | Exclude URLs matching regex |
| `max_depth` | integer | 3 | Max depth from entry |
| `include_entire_domain` | boolean | false | Crawl full site |
| `include_subdomains` | boolean | false | Include subdomains |

**output.formats**: `html`, `raw_html`, `markdown`, `links`, `summary`, `screenshot`, `json`

**cURL:**
```bash
CREATE_RESP="$(curl -sS -X POST "https://run.xcrawl.com/v1/crawl" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","crawler":{"limit":100,"max_depth":2},"output":{"formats":["markdown","links"]}}')"
CRAWL_ID="$(node -e 'const s=process.argv[1];const j=JSON.parse(s);process.stdout.write(j.crawl_id||"")' "$CREATE_RESP")"
curl -sS -X GET "https://run.xcrawl.com/v1/crawl/${CRAWL_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

**Node.js — advanced:**
```bash
node -e '
const fs=require("fs");
const apiKey=JSON.parse(fs.readFileSync(process.env.HOME+"/.xcrawl/config.json","utf8")).XCRAWL_API_KEY;
const body={url:"https://example.com",crawler:{limit:300,max_depth:3,include:["/docs/.*"],exclude:["/blog/.*"]},request:{locale:"ja-JP"},output:{formats:["markdown","links","json"]}};
fetch("https://run.xcrawl.com/v1/crawl",{
  method:"POST",
  headers:{"Content-Type":"application/json",Authorization:`Bearer ${apiKey}`},
  body:JSON.stringify(body)
}).then(async r=>{console.log(await r.text());});
'
```

---

## D. Search — Keyword-Based Discovery

**Endpoint:** `POST https://run.xcrawl.com/v1/search`

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `query` | string | Yes | – | Search query |
| `location` | string | No | US | Location (name or ISO code) |
| `language` | string | No | en | Language (ISO 639-1) |
| `limit` | integer | No | 10 | Max results (1-100) |

**cURL:**
```bash
curl -sS -X POST "https://run.xcrawl.com/v1/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"query":"AI web crawler API","location":"US","language":"en","limit":20}'
```

**Node.js:**
```bash
node -e '
const fs=require("fs");
const apiKey=JSON.parse(fs.readFileSync(process.env.HOME+"/.xcrawl/config.json","utf8")).XCRAWL_API_KEY;
fetch("https://run.xcrawl.com/v1/search",{
  method:"POST",
  headers:{"Content-Type":"application/json",Authorization:`Bearer ${apiKey}`},
  body:JSON.stringify({query:"web scraping pricing",location:"DE",language:"de",limit:30})
}).then(async r=>{console.log(await r.text());});
'
```

## Workflow

1. Restate the task objective
2. Pick the right section (A–D) based on the goal
3. Build and execute the API call
4. Return raw API response — do not synthesize summaries unless requested

## Guardrails

- Respect `limit` — do not claim exhaustive coverage if limit is reached
- Do not fabricate results between polls
- Do not mix inferred URLs with returned URLs
- Do not claim ranking guarantees the API does not expose