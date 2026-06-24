---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history."
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## China / GFW Access

When running from a server behind China's GFW, Python's default `urllib.request.urlopen()` will hang during SSL handshake. **Workaround:**

```python
import ssl, urllib.request, json
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request(url, headers={"User-Agent": "WC26-Edge-Lab/1.0"})
with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
    data = json.loads(resp.read().decode())
```

`curl` works fine from China — the issue is only with Python's default SSL context. Apply the `CERT_NONE` context to all Polymarket API calls.

## WC26-Specific: Question Pattern Parsing

World Cup 2026 markets on Polymarket use per-team/per-player **binary Yes/No markets**, not multi-outcome markets. Each team has its own market like "Will Spain win the 2026 FIFA World Cup?" — the `outcomes` field is always `["Yes", "No"]`.

### Winner Market Questions
Pattern: `"Will {Team} win the 2026 FIFA World Cup?"`
Extract team: `q.replace("Will ", "").replace(" win the 2026 FIFA World Cup?", "").strip()`

### Group Winner Questions
Pattern: `"Will {Team} win Group {X} in the 2026 FIFA World Cup?"`
Extract team: `q.replace("Will ", "").replace(f" win Group {group} in the 2026 FIFA World Cup?", "").strip()`

### Golden Boot Questions
Pattern: `"Will {Player} be the top goalscorer at the 2026 FIFA World Cup?"`
Extract player: `q.replace("Will ", "").replace(" be the top goalscorer at the 2026 FIFA World Cup?", "").strip()`

### Search Coverage Limitation
The Gamma API's `public-search` endpoint returns **only 5 group winner markets** (Groups A-E) out of 12. Groups F-L are not returned by search. To get all groups, you need to know the slug or use direct event IDs.

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible
- Group winner search only returns ~5 groups (A-E); F-L need direct event slugs
