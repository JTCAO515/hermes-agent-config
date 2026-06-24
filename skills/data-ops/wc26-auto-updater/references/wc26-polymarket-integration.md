# WC26 — Live Polymarket Integration

> Integrated in v3.4. Fetches real-time Polymarket prediction market odds for display.
> Source: `data/polymarket_live.py`

## Architecture

```
Polymarket Gamma API (gamma-api.polymarket.com)
    ↓ (Python urllib with ssl.CERT_NONE workaround for China GFW)
data/polymarket_live.py  (5-min cached fetcher)
    ↓ (imported by API handler)
/api/wc/polymarket  →  Frontend summary card shows Top5
```

## API Endpoint

`GET /api/wc/polymarket`

Response:
```json
{
  "updated_at": 1718380800.0,
  "winner_market": [{"team": "Spain", "price_pct": 16.6, "volume": 43569459}, ...],
  "group_winners": [{"group": "A", "teams": [{"team": "Mexico", "price_pct": 62.5}, ...]}, ...],
  "golden_boot": [{"player": "Kylian Mbappe", "price_pct": 15.5}, ...]
}
```

## Three Data Sources

| Market | Search Query | Coverage | Limitation |
|--------|-------------|----------|------------|
| Winner | `World Cup Winner 2026` (filter T20) | 25 teams ($2.2B) | None |
| Group Winners | `Group Winner World Cup` | Groups A-E only | F-L not returned by search |
| Golden Boot | `slug=world-cup-golden-boot-winner` | 30 players ($7.1M) | None |

## China GFW Workaround

Polymarket's API is accessible from China servers BUT Python's default SSL context hangs.
Use `ssl.CERT_NONE` context in `urllib`:

```python
import ssl, urllib.request, json
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
req = urllib.request.Request(url, headers={"User-Agent": "WC26-Edge-Lab/1.0"})
with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
    data = json.loads(resp.read().decode())
```

## Question Parsing

All WC26 markets use binary Yes/No markets. Team/player names are in the `question` field:

- **Winner:** `"Will {Team} win the 2026 FIFA World Cup?"`
- **Group Winner:** `"Will {Team} win Group {X} in the 2026 FIFA World Cup?"`  
- **Golden Boot:** `"Will {Player} be the top goalscorer at the 2026 FIFA World Cup?"`

Extract by removing prefix/suffix, never use `outcomes` field (always `["Yes","No"]`).

## Vercel Deployment: Static Fallback Pattern

**Problem:** Polymarket's Gamma API (gamma-api.polymarket.com) is reachable from the dev server but frequently **times out on Vercel's serverless runtime** (network restrictions from Vercel's AWS infra). This causes the `/api/wc/polymarket` endpoint to return empty data.

**Solution (implemented in `api/index.py` v5.0.1+):** Three-tier fallback:

```
1. Live Gamma API  →  2. Static polymarket_odds.json  →  3. Never empty
```

```python
# In api/index.py — /api/wc/polymarket handler
try:
    from data.polymarket_live import get_live_data
    data = get_live_data()
    if data.get("winner_market") or data.get("group_winners"):
        return _json(start_response, data)
except Exception:
    pass

# Fallback: read static polymarket_odds.json
pm_static = _load_json(THIS_DIR.parent / "data" / "polymarket_odds.json")
if pm_static:
    winner_market = [
        {"team": t, "price_pct": round(p*100, 1), "volume": 0}
        for t, p in sorted(
            pm_static["markets"]["world_cup_winner"]["probabilities"].items(),
            key=lambda x: -x[1]
        )[:25] if p > 0.001
    ]
    return _json(start_response, {
        "source": "polymarket_odds.json (static fallback)",
        "winner_market": winner_market,
        "last_updated": pm_static.get("last_updated"),
    })
```

**Updating static data:** The `polymarket_odds.json` file must be manually refreshed when significant market shifts happen. Run locally:
```bash
cd /home/ubuntu/projects/world-cup-edge-lab
python3 -c "
from data.polymarket_live import get_live_data
import json; from pathlib import Path
data = get_live_data()
# Transform to static format
static = {
    'last_updated': 'YYYY-MM-DD',
    'markets': {
        'world_cup_winner': {
            'probabilities': {t['team']: t['price_pct']/100 for t in data['winner_market']}
        }
    }
}
Path('data/polymarket_odds.json').write_text(json.dumps(static, indent=2))
"
```

**`_load_json` utility** (added in api/index.py v5.0.1):
```python
def _load_json(path):
    try:
        p = Path(path) if not isinstance(path, Path) else path
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None
```
This is a reusable function. If it doesn't exist in a new handler, define it first.

## Frontend Integration

- Summary card (`#sum-polymarket`) shows Top5 winner teams with live %
- Loaded on init via `fetchJSON("/api/wc/polymarket")`
- Graceful failure: shows "🔄 稍后加载" on error
