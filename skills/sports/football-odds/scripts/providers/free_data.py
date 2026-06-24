#!/usr/bin/env python3
"""
Free football odds data - no API key required.
Sources: OpenLigaDB, international football data, ESPN.
"""

import json, re, time
from urllib.request import urlopen, Request

CACHE = {}
CACHE_TTL = 300

def _fetch(url, headers=None, timeout=15):
    h = headers or {"User-Agent": "Mozilla/5.0"}
    req = Request(url, headers=h)
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")

def _cached(key, fn, ttl=CACHE_TTL):
    now = time.time()
    if key in CACHE and now - CACHE[key]["time"] < ttl:
        return CACHE[key]["data"]
    data = fn()
    CACHE[key] = {"data": data, "time": now}
    return data

# ─── OpenLigaDB (German football, free, no key) ───

def openligadb_teams(league_slug="bl1", season=2025):
    """Get teams for a league. bl1=Bundesliga, bl2=2.Bundesliga"""
    url = f"https://api.openligadb.de/getavailableteams/{league_slug}/{season}"
    return json.loads(_fetch(url))

def openligadb_matches(league_slug="bl1", season=2025):
    """Get match data for a league. Returns matches with scores."""
    url = f"https://api.openligadb.de/getmatchdata/{league_slug}/{season}"
    data = json.loads(_fetch(url))
    matches = []
    for m in data:
        home = m.get("team1", {}).get("teamName", "?")
        away = m.get("team2", {}).get("teamName", "?")
        match_dt = m.get("matchDateTime", "")
        results = m.get("matchResults", [])
        score_h = None
        score_a = None
        for r in results:
            if r.get("resultTypeId") == 2:  # Final result
                score_h = r.get("pointsTeam1")
                score_a = r.get("pointsTeam2")
                break
        matches.append({
            "home": home, "away": away,
            "datetime": match_dt,
            "home_score": score_h, "away_score": score_a,
            "finished": score_h is not None
        })
    return matches

# ─── Free international football data (fixtures and results, no key) ───

def get_espn_football_scores(league_id=10.114072):
    """
    ESPN football scores. No API key needed.
    league_id examples: 1 (FIFA World Cup - 'fifa.world'), 10.23 (EPL - 'eng.1'), 10.86 (La Liga - 'esp.1')
    Also accepts abbreviation string like 'fifa.world'.
    Returns list of matches with scores.
    """
    # Handle string slugs directly
    if isinstance(league_id, str):
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard"
    else:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard"
    try:
        data = json.loads(_fetch(url))
    except Exception:
        return []

    matches = []
    events = data.get("events", [])
    for ev in events:
        comps = ev.get("competitions", [{}])
        c = comps[0] if comps else {}
        competitors = c.get("competitors", [])
        if len(competitors) >= 2:
            home = competitors[0].get("team", {}).get("displayName", "?")
            away = competitors[1].get("team", {}).get("displayName", "?")
            home_score = competitors[0].get("score")
            away_score = competitors[1].get("score")
            status = c.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
            matches.append({
                "home": home, "away": away,
                "home_score": int(home_score) if home_score and home_score.isdigit() else None,
                "away_score": int(away_score) if away_score and away_score.isdigit() else None,
                "status": status,
                "finished": status == "STATUS_FINAL"
            })
    return matches

def get_wc26_fixtures_espn():
    """Get 2026 FIFA World Cup fixtures/scores from ESPN (free, no key)."""
    return get_espn_football_scores("fifa.world")

# ─── Text format ───

def format_free_data(data, title="足球赛果"):
    """Format free data for display."""
    if not data:
        return f"📋 {title}\n  暂无数据"
    
    lines = [f"📋 {title}"]
    for m in data[:15]:
        home = m.get("home", m.get("team1", "?"))
        away = m.get("away", m.get("team2", "?"))
        h_s = m.get("home_score")
        a_s = m.get("away_score")
        finished = m.get("finished", False)
        dt = m.get("datetime", m.get("date", ""))
        
        if finished and h_s is not None:
            score = f"{h_s}-{a_s}"
            lines.append(f"   ✅ {home} {score} {away}")
        else:
            lines.append(f"   🔮 {home} vs {away}")
            if dt:
                lines[-1] += f"  ({dt[:16]})"
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    print("=== WC26 (ESPN) ===")
    wc = get_wc26_fixtures_espn()
    print(format_free_data(wc, "2026 FIFA World Cup"))
    
    print("\n=== OpenLigaDB Bundesliga ===")
    try:
        bl = openligadb_matches("bl1", 2025)
        print(format_free_data(bl, "Bundesliga 2025"))
    except Exception as e:
        print(f"OpenLigaDB error: {e}")
