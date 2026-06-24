---
name: xcrawl-search
description: Use this skill for XCrawl search tasks, including keyword search request design, location and language controls, result analysis, and follow-up crawl or scrape planning.
allowed-tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep
metadata:
  version: 1.0.2
  xcrawl:
    skillKey: xcrawl-search
    homepage: https://www.xcrawl.com/
    requires:
      localFiles:
        - ~/.xcrawl/config.json
      anyBins:
        - curl
        - node
    apiKeySource: local_config
---

# XCrawl Search

Keyword-based search via XCrawl Search API. Returns upstream response as-is.

## Setup

```json
# ~/.xcrawl/config.json
{
  "XCRAWL_API_KEY": ""
}
```

## API

**POST** `https://run.xcrawl.com/v1/search`
**Auth:** `Authorization: Bearer <XCRAWL_API_KEY>`

## Parameters

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `query` | string | Yes | – | Search query |
| `location` | string | No | US | Location (name or ISO code) |
| `language` | string | No | en | Language (ISO 639-1) |
| `limit` | integer | No | 10 | Max results (1-100) |

## Examples

### cURL
```bash
API_KEY="$(node -e "const fs=require('fs');const p=process.env.HOME+'/.xcrawl/config.json';const k=JSON.parse(fs.readFileSync(p,'utf8')).XCRAWL_API_KEY||'';process.stdout.write(k)")"
curl -sS -X POST "https://run.xcrawl.com/v1/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"query":"AI web crawler API","location":"US","language":"en","limit":20}'
```

### Node.js
```bash
node -e '
const fs=require("fs");
const apiKey=JSON.parse(fs.readFileSync(process.env.HOME+"/.xcrawl/config.json","utf8")).XCRAWL_API_KEY;
const body={query:"web scraping pricing",location:"DE",language:"de",limit:30};
fetch("https://run.xcrawl.com/v1/search",{
  method:"POST",
  headers:{"Content-Type":"application/json",Authorization:`Bearer ${apiKey}`},
  body:JSON.stringify(body)
}).then(async r=>{console.log(await r.text());});
'
```

## Response

| Field | Type | Description |
|-------|------|-------------|
| `search_id` | string | Task ID |
| `status` | string | `completed` |
| `query` | string | Search query |
| `data` | object | Search results |

## Workflow

1. Rewrite request as clear search objective (entity, geography, language)
2. Execute `POST /v1/search`
3. Return raw API response — do not summarize unless asked

## Guardrails

- Do not claim ranking guarantees the API does not expose
- Do not fabricate unavailable filters or response fields