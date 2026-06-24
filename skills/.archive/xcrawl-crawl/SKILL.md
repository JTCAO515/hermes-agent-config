---
name: xcrawl-crawl
description: Full-site or scoped crawling via XCrawl Crawl API. Supports depth control, include/exclude patterns, JS rendering, async polling, and webhook delivery.
allowed-tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep
metadata:
  version: 1.0.2
  xcrawl:
    skillKey: xcrawl-crawl
    homepage: https://www.xcrawl.com/
    requires:
      localFiles:
        - ~/.xcrawl/config.json
      anyBins:
        - curl
        - node
    apiKeySource: local_config
---

# XCrawl Crawl

Full-site or scoped crawling via XCrawl Crawl API. Returns upstream response as-is.

## Setup

```json
# ~/.xcrawl/config.json
{
  "XCRAWL_API_KEY": ""
}
```

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `https://run.xcrawl.com/v1/crawl` | Start crawl |
| GET | `https://run.xcrawl.com/v1/crawl/{crawl_id}` | Read result |

**Auth:** `Authorization: Bearer <XCRAWL_API_KEY>`

## Parameters

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `url` | string | Yes | – | Entry URL |
| `crawler` | object | No | – | Crawler behavior (see below) |
| `proxy` | object | No | – | Proxy config |
| `request` | object | No | – | Request config |
| `js_render` | object | No | – | JS rendering |
| `output` | object | No | – | Output formats |
| `webhook` | object | No | – | Async callback |

### `crawler`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 100 | Max pages |
| `include` | string[] | – | Include only URLs matching regex |
| `exclude` | string[] | – | Exclude URLs matching regex |
| `max_depth` | integer | 3 | Max depth from entry |
| `include_entire_domain` | boolean | false | Crawl full site |
| `include_subdomains` | boolean | false | Include subdomains |
| `include_external_links` | boolean | false | Include external links |
| `sitemaps` | boolean | true | Use site sitemap |

### `output.formats`

`html`, `raw_html`, `markdown`, `links`, `summary`, `screenshot`, `json`

## Examples

### cURL
```bash
API_KEY="$(node -e "const fs=require('fs');const p=process.env.HOME+'/.xcrawl/config.json';const k=JSON.parse(fs.readFileSync(p,'utf8')).XCRAWL_API_KEY||'';process.stdout.write(k)")"
CREATE_RESP="$(curl -sS -X POST "https://run.xcrawl.com/v1/crawl" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","crawler":{"limit":100,"max_depth":2},"output":{"formats":["markdown","links"]}}')"
CRAWL_ID="$(node -e 'const s=process.argv[1];const j=JSON.parse(s);process.stdout.write(j.crawl_id||"")' "$CREATE_RESP")"
curl -sS -X GET "https://run.xcrawl.com/v1/crawl/${CRAWL_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

### Node.js — advanced
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

## Response

| Field | Type | Description |
|-------|------|-------------|
| `crawl_id` | string | Task ID |
| `status` | string | `pending` → `crawling` → `completed` |
| `data` | object | Crawl results (pages with output formats) |

## Workflow

1. Define crawl scope (entry URL, depth, include/exclude patterns)
2. POST to `/v1/crawl` → get `crawl_id`
3. Poll `GET /v1/crawl/{crawl_id}` until `status=completed`
4. Return raw response

## Guardrails

- Respect `limit` — do not claim exhaustive coverage
- Do not fabricate results between polls