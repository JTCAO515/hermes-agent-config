---
name: xcrawl-scrape
description: Single-page extraction via XCrawl Scrape APIs. Supports sync/async modes, JS rendering, proxy, JSON extraction with prompt or schema.
allowed-tools: Bash(curl:*) Bash(node:*) Read Write Edit Grep
metadata:
  version: 1.0.2
  xcrawl:
    skillKey: xcrawl-scrape
    homepage: https://www.xcrawl.com/
    requires:
      localFiles:
        - ~/.xcrawl/config.json
      anyBins:
        - curl
        - node
    apiKeySource: local_config
---

# XCrawl Scrape

Single-page extraction via XCrawl Scrape APIs. Returns upstream API response bodies as-is.

## Setup

```json
# ~/.xcrawl/config.json
{
  "XCRAWL_API_KEY": ""
}
```

Register at https://dash.xcrawl.com/ (free 1000 credits).

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `https://run.xcrawl.com/v1/scrape` | Start scrape (sync/async) |
| GET | `https://run.xcrawl.com/v1/scrape/{scrape_id}` | Poll async result |

**Header:** `Authorization: Bearer <XCRAWL_API_KEY>`

## Examples

### cURL — sync
```bash
API_KEY="$(node -e "const fs=require('fs');const p=process.env.HOME+'/.xcrawl/config.json';const k=JSON.parse(fs.readFileSync(p,'utf8')).XCRAWL_API_KEY||'';process.stdout.write(k)")"
curl -sS -X POST "https://run.xcrawl.com/v1/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","mode":"sync","output":{"formats":["markdown","links"]}}'
```

### cURL — async + poll
```bash
API_KEY="$(node -e "...")"
CREATE_RESP="$(curl -sS -X POST "https://run.xcrawl.com/v1/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"url":"https://example.com","mode":"async","output":{"formats":["json"]},"json":{"prompt":"Extract title and price."}}')"
SCRAPE_ID="$(node -e 'const s=process.argv[1];const j=JSON.parse(s);process.stdout.write(j.scrape_id||"")' "$CREATE_RESP")"
curl -sS -X GET "https://run.xcrawl.com/v1/scrape/${SCRAPE_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

### Node.js
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

## Parameters

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