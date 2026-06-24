---
name: xcrawl-map
description: Use this skill for XCrawl map tasks, including site URL discovery, regex filtering, scope estimation, and crawl planning before full-site crawling.
allowed-tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep
metadata:
  version: 1.0.2
  xcrawl:
    skillKey: xcrawl-map
    homepage: https://www.xcrawl.com/
    requires:
      localFiles:
        - ~/.xcrawl/config.json
      anyBins:
        - curl
        - node
    apiKeySource: local_config
---

# XCrawl Map

Site URL discovery via XCrawl Map API. Returns upstream response as-is.

## Setup

```json
# ~/.xcrawl/config.json
{
  "XCRAWL_API_KEY": ""
}
```

## API

**POST** `https://run.xcrawl.com/v1/map`
**Auth:** `Authorization: Bearer <XCRAWL_API_KEY>`

## Parameters

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `url` | string | Yes | – | Site entry URL |
| `filter` | string | No | – | Regex filter for URLs |
| `limit` | integer | No | 5000 | Max URLs (up to 100000) |
| `include_subdomains` | boolean | No | true | Include subdomains |
| `ignore_query_parameters` | boolean | No | true | Ignore query params |

## Response

| Field | Type | Description |
|-------|------|-------------|
| `map_id` | string | Task ID |
| `status` | string | `completed` |
| `data.links` | string[] | URL list |
| `data.total_links` | integer | URL count |

## Examples

### cURL
```bash
API_KEY="$(node -e "const fs=require('fs');const p=process.env.HOME+'/.xcrawl/config.json';const k=JSON.parse(fs.readFileSync(p,'utf8')).XCRAWL_API_KEY||'';process.stdout.write(k)")"
curl -sS -X POST "https://run.xcrawl.com/v1/map" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","filter":"/docs/.*","limit":2000,"include_subdomains":true}'
```

### Node.js
```bash
node -e '
const fs=require("fs");
const apiKey=JSON.parse(fs.readFileSync(process.env.HOME+"/.xcrawl/config.json","utf8")).XCRAWL_API_KEY;
const body={url:"https://example.com",filter:"/docs/.*",limit:3000,include_subdomains:true};
fetch("https://run.xcrawl.com/v1/map",{
  method:"POST",
  headers:{"Content-Type":"application/json",Authorization:`Bearer ${apiKey}`},
  body:JSON.stringify(body)
}).then(async r=>{console.log(await r.text());});
'
```

## Workflow

1. Restate mapping objective (discovery / crawl planning / structure analysis)
2. Build and execute `POST /v1/map` with explicit filters
3. Return raw API response — do not synthesize summaries unless requested

## Guardrails

- Do not claim full site coverage if `limit` is reached
- Do not mix inferred URLs with returned URLs