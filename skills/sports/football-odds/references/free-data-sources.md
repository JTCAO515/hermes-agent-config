# Free Football Odds Data Sources — Audit Log

## ✅ Works (no API key)

### ESPN Scoreboard
```
GET https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard
```
- League IDs: `fifa.world` (WC26), `eng.1` (EPL), `esp.1` (La Liga), `ita.1` (Serie A), `ger.1` (Bundesliga)
- Returns: live scores, fixtures, team names, match status
- **Does NOT include betting odds** for World Cup (odds field is null)
- Rate limit: unknown but generous
- Gzipped response — use `Accept-Encoding: gzip` header + gunzip

### OpenLigaDB
```
GET https://api.openligadb.de/getmatchdata/{league}/{season}
```
- League slugs: `bl1` (Bundesliga), `bl2` (2. Bundesliga)
- Returns: teams, scores, match date
- German football only
- No odds data

## ❌ Failed (blocked)

| Source | URL | Failure | Root Cause |
|--------|-----|---------|------------|
| **Sofascore** | `api.sofascore.com` | HTTP 403 | Cloudflare bot detection |
| **Flashscore** | `flashscore.com` | Dynamic JS render | No API, pure client-side React |
| **Oddsportal** | `oddsportal.com` | 404 + dynamic | Anti-scraping, requires Selenium |
| **Flashscore JSON** | `flashscore-json.pages.dev` | 404 | No longer available |

## ⚠️ Requires registration

| Service | Free Tier | Signup | Notes |
|---------|-----------|--------|-------|
| **OddsPapi** (推荐) | Full free, 350+ books | oddspapi.io/signup | Best WC26 coverage |
| **Odds-API.io** | 100 req/h | odds-api.io/pricing/free | Official Python SDK |
| **The Odds API** | 1000 req/mo (~33 req/day) | the-odds-api.com | 40+ bookmakers, 45+ sports, Pinnacle/Betfair/SkyBet, ✅ 世界杯 `soccer_fifa_world_cup`, 直连中国VPS可用 |
| **SharpAPI** | 12 req/min, no card | sharpapi.io/pricing | Built-in +EV detection |

## Strategy Summary

For WC26 Edge Lab with no API key:
1. **Model data** (Poisson engine) → 23 market types, no external deps
2. **Polymarket** (already integrated) → tournament-level live odds
3. **ESPN** (free) → fixture/scores for verification
4. No reliable free source for real-time match-level bookmaker odds without API key
