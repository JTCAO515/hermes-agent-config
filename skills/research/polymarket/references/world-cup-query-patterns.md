# World Cup 2026 — Polymarket Query Patterns

> Common query patterns for fetching World Cup 2026 prediction market data.
> Last tested: 2026-06-14 (v3.4). Polymarket total WC volume: ~$2.2B.

## Key Search Queries

| Purpose | Query String | Volume Range |
|---------|-------------|-------------|
| Outright winner | `World Cup+Winner+2026` (filter out T20) | $2.2B |
| Group winners | `Group+Winner+World+Cup` (returns A-E only) | $300k–$900k per group |
| Golden Boot | `slug=world-cup-golden-boot-winner` (events endpoint) | $7.1M |
| Third-place advancement | `World Cup: Third-Place Teams to Advance` | $4.4k |
| Opening ceremony | `2026 World Cup Opening Ceremony` | $14k |
| Squad selection | `Player to make <country> Squad` | $300k–$400k |

**Important:** The Gamma API returns per-team binary Yes/No markets (not multi-outcome).
`outcomes` is always `["Yes", "No"]` — the team/player name is in the `question` field.

## Winner Market — Response Parsing (Python)

```python
import json, ssl, urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://gamma-api.polymarket.com/public-search?q=World+Cup+Winner+2026&limit=3"
req = urllib.request.Request(url, headers={"User-Agent": "WC26-Edge-Lab/1.0"})
with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
    data = json.loads(resp.read().decode())

for event in data.get("events", []):
    title = event.get("title", "")
    if "World Cup Winner" not in title or "T20" in title:
        continue
    for market in event.get("markets", []):
        q = market.get("question", "")
        prices = json.loads(market.get("outcomePrices", "[]"))
        pct = float(prices[0]) * 100 if prices else 0
        vol = float(market.get("volume", 0))
        if pct > 0.3:
            # Extract team name from: "Will Spain win the 2026 FIFA World Cup?"
            team = q.replace("Will ", "").replace(" win the 2026 FIFA World Cup?", "").strip()
            print(f"{team}: {pct:.1f}% (${vol:,.0f})")
```

## Group Winner — Response Parsing

```python
# Search
url = "https://gamma-api.polymarket.com/public-search?q=Group+Winner+World+Cup&limit=15"

for event in data.get("events", []):
    title = event.get("title", "")
    if "Group " not in title or "Winner" not in title:
        continue
    # "World Cup Group B Winner" → "B"
    group = title.replace("World Cup ", "").replace("Group ", "").replace(" Winner", "").strip()
    for market in event.get("markets", []):
        q = market.get("question", "")
        # "Will Canada win Group B in the 2026 FIFA World Cup?" → "Canada"
        team = q.replace("Will ", "").replace(f" win Group {group} in the 2026 FIFA World Cup?", "").strip()
```

**Known limitation:** search only returns groups A-E. Groups F-L are not accessible via search.

## Golden Boot — Response Parsing

```python
# Events endpoint (not public-search) by slug
url = "https://gamma-api.polymarket.com/events?slug=world-cup-golden-boot-winner&limit=3"

for event in data:  # events endpoint returns a list, not {events: [...]}
    for market in event.get("markets", []):
        q = market.get("question", "")
        prices = json.loads(market.get("outcomePrices", "[]"))
        pct = float(prices[0]) * 100 if prices else 0
        # "Will Kylian Mbappe be the top goalscorer at the 2026 FIFA World Cup?" → "Kylian Mbappe"
        player = q.replace("Will ", "").replace(" be the top goalscorer at the 2026 FIFA World Cup?", "").strip()
```

## Winner Market — Top Probabilities (as of 2026-06-14)

| Team | Polymarket % | Volume |
|------|:-----------:|:------:|
| Spain | 16.6% | $43.6M |
| France | 16.2% | $50.0M |
| Portugal | 11.7% | $45.8M |
| England | 9.7% | $37.2M |
| Argentina | 7.8% | $40.6M |
| Brazil | 7.4% | $39.8M |
| Germany | 5.1% | $41.9M |
| Netherlands | 5.0% | $45.6M |

## Golden Boot — Top Probabilities (as of 2026-06-14)

| Player | Polymarket % |
|--------|:-----------:|
| Kylian Mbappe | 15.5% |
| Harry Kane | 14.5% |
| Erling Haaland | 8.5% |
| Mikel Oyarzabal | 8.5% |
| Lionel Messi | 5.3% |
| Lamine Yamal | 5.1% |
| Cristiano Ronaldo | 4.3% |
| Vinicius Junior | 4.3% |

## Group Winner Markets (as of 2026-06-14)

| Group | 1st | % | 2nd | % | 3rd | % |
|:-----:|-----|:-:|-----|:-:|-----|:-:|
| A | Mexico | 62.5% | South Korea | 33.5% | Czechia | 3.3% |
| B | Switzerland | 46.5% | Canada | 36.5% | Bosnia | 15.5% |
| C | Brazil | 60.5% | Morocco | 28.5% | Scotland | 11.1% |
| D | USA | 71.5% | Australia | 19.1% | Türkiye | 8.0% |
| E | Germany | 66.0% | Ecuador | 23.5% | Ivory Coast | 12.2% |

## Endpoints Used

```bash
# Winner market (filter out T20 Cricket result)
curl -s "https://gamma-api.polymarket.com/public-search?q=World+Cup+Winner+2026&limit=3"

# Group winners (only A-E)
curl -s "https://gamma-api.polymarket.com/public-search?q=Group+Winner+World+Cup&limit=15"

# Golden Boot (events endpoint, not search)
curl -s "https://gamma-api.polymarket.com/events?slug=world-cup-golden-boot-winner&limit=3"

# Note: tag=world-cup-2026 does NOT work — returns irrelevant old events
```

## Notes

- Polymarket prices ARE probabilities (not bookmaker odds with overround)
- Volume-weighted consensus across thousands of traders
- Total $2.2B in WC markets across Polymarket
- Prices incorporate real-money risk → more reliable than sportsbook odds for calibration
- Double-encoded JSON fields (`outcomePrices`, `outcomes`, `clobTokenIds`) must be parsed with `json.loads()`
- From China, Python urllib needs `ssl.CERT_NONE` context (see SKILL.md for workaround)
- Group winner search only returns Groups A-E (F-L require direct slugs or event IDs)
