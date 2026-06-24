---
name: odds-data-pipeline
category: data-ops
description: |
  Build a live betting odds data pipeline — fetch from The Odds API, normalize team names, merge with match data, and deploy via git push. Covers proxy routing, API quota management, cron scheduling, and verification.
triggers:
  - odds api
  - the-odds-api
  - live odds integration
  - betting odds pipeline
  - 赔率数据
  - 盘口同步
---

# Odds Data Pipeline — The Odds API Integration

Full workflow to integrate live sports betting odds into a project using [The Odds API](https://the-odds-api.com) (v4). Designed for projects that deploy via Vercel (git push → auto-deploy).

## Registration & Key

1. Go to `https://the-odds-api.com/account?initialAuthState=signUp`
2. Enter email → receive API key
3. Free tier: ~1000 requests/month
4. Pass key as query param: `?apiKey=KEY`

## Cost Formula

Each request costs: `[markets] × [regions]`

- 1 market + 1 region = 1 request
- 3 markets (h2h,spreads,totals) + 2 regions (eu,uk) = 6 requests
- See docs: `https://the-odds-api.com/liveapi/guides/v4/#overview`

## Key Endpoints

| Endpoint | Cost | Description |
|----------|------|-------------|
| `GET /v4/sports` | **Free** | List in-season sports |
| `GET /v4/sports/{sport}/odds` | 1+ | Odds for a sport |
| `GET /v4/sports/{sport}/scores` | 1-2 | Scores for a sport |
| `GET /v4/sports/{sport}/events` | **Free** | Event IDs + times |

## Connectivity

| Scenario | Works? | Notes |
|----------|--------|-------|
| Global VPS (AWS/GCP/Vultr) | ✅ Direct | No proxy needed |
| China VPS (Alibaba Cloud) | ✅ Direct | Works without proxy (tested) |
| Vercel Lambda | ✅ Direct | Serverless works |
| Via Xray/Proxy | ❌ | SSL handshake times out on Singapore relay |

**Key finding**: The Odds API works **directly** from Alibaba Cloud China VPS. No proxy needed. Adding a proxy (SOCKS5/HTTP) actually breaks the SSL handshake.

## Team Name Normalization

The Odds API uses different team names than many sports databases. Essential mapping table:

```python
NORMALIZE_TEAMS = {
    "Czech Republic": "Czechia",
    "United States": "USA",
    "South Korea": "Korea Republic",
    "Korea Republic": "Korea Republic",
    "IR Iran": "IR Iran",
    "Ivory Coast": "Côte d'Ivoire",
    "Cape Verde": "Cabo Verde",
    "DR Congo": "Congo DR",
    "Congo": "Congo DR",
    "Turkey": "Türkiye",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Korea DPR": "Korea Republic",
    "Bosnia": "Bosnia and Herzegovina",
    # Add more as needed
}
```

**Always apply normalization to BOTH:**
- Match pairing (`home_team` / `away_team` in odds response)
- Outcome names (`outcomes[].name` in h2h/spreads/totals markets)

## Pipeline Architecture

```
VPS Cron (every 30 min)
    │
    ▼
odds_fetcher.py ──► The Odds API (via direct HTTPS)
    │
    ├──► data/live_odds.json ──► raw odds data (all bookmakers)
    │
    ├──► data/wc2026_matches.json ──► merged with match data
    │
    └──► git add + commit + push ──► Vercel auto-deploy
```

### Multiple Projects (API Quota Sharing)

If you have multiple Vercel projects (e.g., main + fork), do NOT have both hit The Odds API directly — you'll exhaust the free quota.

**Best practice**: Designate ONE project as the primary fetcher. Others pull `live_odds.json` from the primary's GitHub raw URL:

```
Primary (Main):   odds_fetcher.py → API → git push
Secondary (Nami): curl raw.githubusercontent.com/.../live_odds.json → git push
```

## Verification Commands

```bash
# Test API key + sports list (free, doesn't count against quota)
curl -s "https://api.the-odds-api.com/v4/sports?apiKey=KEY" | jq '.[].key'

# Fetch FIFA World Cup odds
curl -s "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey=KEY&regions=eu&markets=h2h,spreads,totals&oddsFormat=decimal"

# Check remaining quota (from response headers)
curl -sI "...apiKey=KEY" | grep -i x-requests-remaining
```

## Pitfalls

1. **API key in header vs query param**: Must be a query parameter (`?apiKey=KEY`). Passing as HTTP header (`-H "apiKey: ..."`) returns "API key is missing".
2. **Proxy breaks SSL**: The Odds API's CDN doesn't connect via Xray/V2Ray HTTP proxy. Use direct connection.
3. **Team name mismatch**: Always normalize team names in BOTH the match pairing AND the outcome names within h2h/spreads/totals. If normalization misses, `h2h.get(team_name, 0)` returns 0 and the match gets zero odds.
4. **Free tier limit**: ~1000 requests/month. With 30-min sync and two projects, can exhaust in ~8 days. Monitor `x-requests-remaining` header.
5. **China VPS direct works**: Despite being a financial/sports API, The Odds API is not blocked in China. No proxy needed.
6. **No matches returned**: If no upcoming games exist for a sport, the API returns `[]` (empty array) — doesn't count against quota.
