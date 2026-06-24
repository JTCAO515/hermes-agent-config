#!/usr/bin/env python3
"""
足球赔率查询工具 — Football Odds CLI
支持：OddsPapi / Odds-API.io / Polymarket
"""

import json, os, sys, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError

# ─── Config ───
CACHE_DIR = os.path.expanduser("~/.cache/football-odds")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 120  # seconds

# ─── Helpers ───

def _fetch(url, headers=None, timeout=15):
    """HTTP GET with retry."""
    h = headers or {}
    h.setdefault("User-Agent", "Mozilla/5.0 (compatible; Hermes-Football-Odds/1.0)")
    for attempt in range(2):
        try:
            req = Request(url, headers=h)
            with urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except URLError as e:
            if attempt == 0:
                time.sleep(1)
                continue
            raise Exception(f"请求失败: {url} — {e}")

def _cache_get(key):
    path = os.path.join(CACHE_DIR, key + ".json")
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if age < CACHE_TTL:
            with open(path) as f:
                return json.load(f)
    return None

def _cache_set(key, data):
    with open(os.path.join(CACHE_DIR, key + ".json"), "w") as f:
        json.dump(data, f)

def _pct(v):
    """Format as percentage string."""
    return f"{v*100:.1f}%" if v < 1 else f"{v:.1f}%"

def _to_odds(p, vig=1.05):
    """Probability → decimal odds with overround."""
    if p <= 0.001: return "∞"
    return f"{(1/p * vig):.2f}"

def _fmt_flag(code):
    """Country code or name → emoji flag (best-effort)."""
    flags = {"Germany":"🇩🇪","France":"🇫🇷","Spain":"🇪🇸","Italy":"🇮🇹",
             "England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Portugal":"🇵🇹","Netherlands":"🇳🇱","Belgium":"🇧🇪",
             "Brazil":"🇧🇷","Argentina":"🇦🇷","Uruguay":"🇺🇾","Colombia":"🇨🇴",
             "USA":"🇺🇸","Mexico":"🇲🇽","Canada":"🇨🇦","Japan":"🇯🇵",
             "Korea Rep":"🇰🇷","Australia":"🇦🇺","Morocco":"🇲🇦","Senegal":"🇸🇳",
             "Nigeria":"🇳🇬","Ghana":"🇬🇭","Cameroon":"🇨🇲","Egypt":"🇪🇬",
             "Tunisia":"🇹🇳","Algeria":"🇩🇿","Saudi Arabia":"🇸🇦","Iran":"🇮🇷",
             "Qatar":"🇶🇦","United Arab Emirates":"🇦🇪","Iraq":"🇮🇶","Oman":"🇴🇲",
             "Croatia":"🇭🇷","Denmark":"🇩🇰","Sweden":"🇸🇪","Norway":"🇳🇴",
             "Switzerland":"🇨🇭","Poland":"🇵🇱","Austria":"🇦🇹","Czechia":"🇨🇿",
             "Turkey":"🇹🇷","Ukraine":"🇺🇦","Serbia":"🇷🇸","Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿",
             "Wales":"🏴󠁧󠁢󠁷󠁬󠁳󠁿","Curaçao":"🇨🇼","Bosnia":"🇧🇦","Paraguay":"🇵🇾",
             "Ecuador":"🇪🇨","Haiti":"🇭🇹","South Africa":"🇿🇦","Côte d'Ivoire":"🇨🇮"}
    return flags.get(code, "🌍")


# ═══════════════════════════════════════
# Provider: OddsPapi
# ═══════════════════════════════════════

class OddsPapiProvider:
    """Free tier: 350+ bookmakers, World Cup 2026 support."""

    BASE = "https://api.oddspapi.io/v1"

    def __init__(self, api_key):
        self.key = api_key
        self._headers = {"apiKey": api_key, "Accept": "application/json"}

    def get_sports(self):
        """List available sports."""
        cache = _cache_get("ops_sports")
        if cache: return cache
        data = _fetch(f"{self.BASE}/sports", self._headers)
        _cache_set("ops_sports", data)
        return data

    def get_tournaments(self, sport="soccer"):
        """List football tournaments/leagues."""
        key = f"ops_tournaments_{sport}"
        cache = _cache_get(key)
        if cache: return cache
        data = _fetch(f"{self.BASE}/tournaments?sport={sport}", self._headers)
        _cache_set(key, data)
        return data

    def get_fixtures(self, tournament_ids, limit=20, sport="soccer"):
        """Get upcoming fixtures + odds for one or multiple tournaments."""
        ids = ",".join(tournament_ids) if isinstance(tournament_ids, list) else tournament_ids
        key = f"ops_fixtures_{ids}_{limit}"
        cache = _cache_get(key)
        if cache: return cache
        data = _fetch(
            f"{self.BASE}/fixtures?tournamentIds={ids}&sport={sport}&limit={limit}",
            self._headers
        )
        _cache_set(key, data)
        return data

    def get_match_odds(self, fixture_id):
        """Get all markets for a specific fixture."""
        key = f"ops_odds_{fixture_id}"
        cache = _cache_get(key)
        if cache: return cache
        data = _fetch(f"{self.BASE}/odds?fixtureId={fixture_id}", self._headers)
        _cache_set(key, data)
        return data

    def search_world_cup(self):
        """Search for 2026 World Cup tournaments."""
        tours = self.get_tournaments("soccer")
        results = []
        if isinstance(tours, dict):
            items = tours.get("data", tours.get("tournaments", [tours]))
        elif isinstance(tours, list):
            items = tours
        else:
            items = []
        for t in items:
            name = (t.get("name") or t.get("tournamentName") or t.get("title") or "").lower()
            if "world cup" in name or "worldcup" in name:
                results.append(t)
        return results

    # ─── Odds Parsing ───

    def parse_1x2(self, odds_data):
        """Extract 1X2 odds from fixture odds response."""
        markets = odds_data.get("markets", odds_data.get("data", []))
        for m in markets:
            mkt = m.get("marketName", m.get("market", "")).lower()
            if "1x2" in mkt or "match winner" in mkt or "full time result" in mkt or "moneyline" in mkt:
                outcomes = m.get("outcomes", m.get("selections", []))
                result = {}
                for o in outcomes:
                    label = o.get("label", o.get("name", "")).lower()
                    price = o.get("price", o.get("odds", 0))
                    if "home" in label or "1" == label.strip():
                        result["home"] = price
                    elif "away" in label or "2" == label.strip():
                        result["away"] = price
                    elif "draw" in label or "x" == label.strip():
                        result["draw"] = price
                return result
        return {}

    def parse_ou(self, odds_data):
        """Extract Over/Under odds."""
        markets = odds_data.get("markets", odds_data.get("data", []))
        results = {}
        for m in markets:
            name = m.get("marketName", m.get("market", "")).lower()
            if "over under" in name or "total goals" in name:
                outcomes = m.get("outcomes", m.get("selections", []))
                line_info = {"over": None, "under": None}
                for o in outcomes:
                    label = o.get("label", o.get("name", "")).lower()
                    price = o.get("price", o.get("odds", 0))
                    if "over" in label:
                        line_info["over"] = price
                    elif "under" in label:
                        line_info["under"] = price
                # Extract line number
                for part in name.split():
                    try:
                        line = float(part)
                        results[line] = line_info
                        break
                    except ValueError:
                        continue
        return results


# ═══════════════════════════════════════
# Provider: Odds-API.io
# ═══════════════════════════════════════

class OddsApiIoProvider:
    """100 requests/hour free tier, 250+ bookmakers."""

    BASE = "https://api.odds-api.io/v1"

    def __init__(self, api_key):
        self.key = api_key

    def get_sports(self):
        cache = _cache_get("oai_sports")
        if cache: return cache
        data = _fetch(f"{self.BASE}/sports?apiKey={self.key}")
        _cache_set("oai_sports", data)
        return data

    def get_odds(self, sport="soccer", region="us", markets="h2h,spreads,totals"):
        """Get upcoming odds for a sport."""
        key = f"oai_odds_{sport}_{region}"
        cache = _cache_get(key)
        if cache: return cache
        data = _fetch(
            f"{self.BASE}/odds?sport={sport}&region={region}&markets={markets}&apiKey={self.key}"
        )
        _cache_set(key, data)
        return data


# ═══════════════════════════════════════
# Comparison Engine
# ═══════════════════════════════════════

def compute_ev(model_prob, market_decimal_odds, stake=1.0):
    """
    Calculate Expected Value.
    EV = (market_odds × model_prob - 1) × stake
    """
    if market_decimal_odds <= 0 or model_prob <= 0:
        return -stake, 0
    ev = (market_decimal_odds * model_prob - 1) * stake
    roi_pct = (market_decimal_odds * model_prob - 1) * 100
    return ev, roi_pct

def market_odds_to_prob(decimal_odds):
    """Decimal odds → implied probability (with overround)."""
    if decimal_odds <= 0:
        return 0
    return 1 / decimal_odds

def remove_vig(probs):
    """Remove overround from implied probabilities."""
    total = sum(probs.values())
    if total <= 0:
        return probs
    return {k: v/total for k, v in probs.items()}

def compare_model_vs_market(model_probs, market_probs, market_label="市场"):
    """
    Compare model probabilities with market-implied probabilities.
    Returns sorted list of (outcome, model_prob, market_prob, ev, roi_pct).
    """
    results = []
    for key in model_probs:
        mp = model_probs[key]
        mkp = market_probs.get(key, 0)
        if mkp > 0:
            implied_odds = 1 / mkp
            ev, roi = compute_ev(mp, implied_odds)
        else:
            ev, roi = 0, 0
        results.append((key, mp, mkp, ev, roi))
    # Sort by EV descending
    results.sort(key=lambda x: x[3], reverse=True)
    return results


# ═══════════════════════════════════════
# Formatter
# ═══════════════════════════════════════

def format_match_odds(match_info, odds_data, model_data=None):
    """Format a match with its odds for output."""
    home = match_info.get("homeTeam", match_info.get("home", "?"))
    away = match_info.get("awayTeam", match_info.get("away", "?"))
    kickoff = match_info.get("startTime", match_info.get("kickoff", ""))
    comp = match_info.get("tournamentName", match_info.get("group", match_info.get("phase", "")))

    lines = []
    lines.append(f"\n{_fmt_flag(home)} {home} vs {away} {_fmt_flag(away)}")
    if comp:
        lines.append(f"  📋 {comp}")
    if kickoff:
        try:
            dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
            lines.append(f"  🕐 {dt.strftime('%m/%d %H:%M')} UTC")
        except:
            lines.append(f"  🕐 {kickoff}")

    # 1X2
    wdl = odds_data.get("1x2", {})
    if wdl:
        h_odds = wdl.get("home", 0)
        d_odds = wdl.get("draw", 0)
        a_odds = wdl.get("away", 0)
        h_prob = market_odds_to_prob(h_odds)
        d_prob = market_odds_to_prob(d_odds)
        a_prob = market_odds_to_prob(a_odds)
        # Remove vig
        fair = remove_vig({"home": h_prob, "draw": d_prob, "away": a_prob})
        total_vig = h_prob + d_prob + a_prob

        lines.append(f"\n  🎯 胜平负 (1X2)")
        lines.append(f"    {_fmt_flag(home)} {home}:  {h_odds:.2f}  ({fair['home']*100:.1f}%)")
        lines.append(f"     平局:     {d_odds:.2f}  ({fair['draw']*100:.1f}%)")
        lines.append(f"    {_fmt_flag(away)} {away}:  {a_odds:.2f}  ({fair['away']*100:.1f}%)")
        lines.append(f"    抽水: {(total_vig-1)*100:.1f}%")

        # Model comparison
        if model_data:
            mp = model_data.get("probabilities", {})
            mhw = mp.get("home_win", mp.get("team_a_win", 0))
            mdr = mp.get("draw", 0)
            maw = mp.get("away_win", mp.get("team_b_win", 0))
            ev_results = compare_model_vs_market(
                {"home": mhw, "draw": mdr, "away": maw},
                {"home": fair["home"], "draw": fair["draw"], "away": fair["away"]}
            )
            for key, mp_val, mkp_val, ev_val, roi in ev_results:
                if ev_val > 0.02:
                    label = {home: "主胜", "draw": "平局", away: "客胜"}.get(key, key)
                    lines.append(f"    ⚡ +EV: {label} 模型{mp_val*100:.1f}% vs 市场{mkp_val*100:.1f}% → ROI +{roi:.1f}%")

    # OU
    ou = odds_data.get("ou", {})
    if ou:
        lines.append(f"\n  📊 大小球")
        for line in sorted(ou.keys()):
            o = ou[line].get("over", 0)
            u = ou[line].get("under", 0)
            if o and u:
                o_prob = market_odds_to_prob(o)
                u_prob = market_odds_to_prob(u)
                fair_ou = remove_vig({"over": o_prob, "under": u_prob})
                lines.append(f"    OU {line}: 大{_to_odds(fair_ou['over'])} ({fair_ou['over']*100:.1f}%) | "
                           f"小{_to_odds(fair_ou['under'])} ({fair_ou['under']*100:.1f}%)")

    return "\n".join(lines)


# ═══════════════════════════════════════
# CLI
# ═══════════════════════════════════════

def format_free_match(m):
    """Format a free data match entry."""
    home = m.get("home", "?")
    away = m.get("away", "?")
    flag = "✅" if m.get("finished") else "🔮"
    if m.get("finished") and m.get("home_score") is not None:
        return f"  {flag} {_fmt_flag(home)} {home} {m['home_score']}-{m['away_score']} {away} {_fmt_flag(away)}"
    else:
        return f"  {flag} {_fmt_flag(home)} {home} vs {away} {_fmt_flag(away)}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Football Odds CLI")
    parser.add_argument("--provider", choices=["oddspapi", "oddsapio", "free"], default="free",
                        help="赔率来源 (默认: free - 无需Key)")
    parser.add_argument("--today", action="store_true", help="查询今日赛事")
    parser.add_argument("--world-cup", action="store_true", help="查询2026世界杯赛程")
    parser.add_argument("--compare", action="store_true", help="对比模型 vs 市场赔率")
    parser.add_argument("--search", type=str, help="搜索联赛/赛事")
    parser.add_argument("--league", type=str, help="ESPN联赛ID (如: eng.1, esp.1, fifa.world)")

    args = parser.parse_args()

    # ── Free Data Mode (no API key needed) ──
    if args.provider == "free":
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "providers"))
        from free_data import get_wc26_fixtures_espn, get_espn_football_scores, openligadb_matches, format_free_data as ffd

        if args.world_cup:
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("🌍 2026 FIFA World Cup")
            print("📡 来源: ESPN (免费)")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            wc = get_wc26_fixtures_espn()
            if wc:
                for m in wc:
                    print(format_free_match(m))
            else:
                print("  暂无数据或API请求失败")

        elif args.today:
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📅 今日足球赛程")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            print("\n🌍 WC26:")
            wc = get_wc26_fixtures_espn()
            if wc:
                for m in wc:
                    print(format_free_match(m))
            else:
                print("  暂无数据")

            print("\n🇩🇪 Bundesliga:")
            try:
                bl = openligadb_matches("bl1", 2025)
                if bl:
                    for m in bl[:8]:
                        print(format_free_match(m))
            except Exception:
                print("  (请求失败)")

            print("\n🇩🇪 2. Bundesliga:")
            try:
                bl2 = openligadb_matches("bl2", 2025)
                if bl2:
                    for m in bl2[:5]:
                        print(format_free_match(m))
            except Exception:
                print("  (请求失败)")

        elif args.league:
            print(f"\n📋 联赛赛程 (ID: {args.league})")
            data = get_espn_football_scores(args.league)
            if data:
                for m in data:
                    print(format_free_match(m))
            else:
                print("  暂无数据")

        else:
            print("\n⚽ Football Odds — 免费数据")
            print("  使用: --world-cup 查看世界杯赛程")
            print("  使用: --today 查看今日赛事")
            print("  使用: --league <id> 查看指定联赛")
            print("  使用: --provider oddspapi 查看真实赔率 (需API Key)")
            print()
            print("  免费注册 OddsPapi Key: https://oddspapi.io/signup")
            print("  设置: export ODDS_PAPI_KEY=\"your_key\"")
        return

    # ── API Key Required Mode ──
    if args.provider == "oddspapi":
        key = os.environ.get("ODDS_PAPI_KEY")
        if not key:
            print("⚠️  未设置 ODDS_PAPI_KEY")
            print("   免费注册: https://oddspapi.io/signup")
            print("   之后: export ODDS_PAPI_KEY=\"your_key\"")
            sys.exit(1)
        provider = OddsPapiProvider(key)
    else:
        key = os.environ.get("ODDS_API_IO_KEY")
        if not key:
            print("⚠️  未设置 ODDS_API_IO_KEY")
            print("   免费注册: https://odds-api.io/pricing/free")
            sys.exit(1)
        provider = OddsApiIoProvider(key)

    try:
        if args.world_cup:
            print("\n🌍 2026 FIFA World Cup — 赔率查询")
            print("  📡 来源:", args.provider)
            wc = provider.search_world_cup()
            if wc:
                for t in wc[:5]:
                    tid = t.get("id", t.get("tournamentId", "?"))
                    name = t.get("name", t.get("tournamentName", "?"))
                    print(f"  📋 找到赛事: {name} (ID={tid})")
                    fixtures = provider.get_fixtures(str(tid), limit=10)
                    matches = fixtures if isinstance(fixtures, list) else fixtures.get("data", fixtures.get("fixtures", []))
                    for m in matches[:10]:
                        print(f"  → {m.get('homeTeam','?')} vs {m.get('awayTeam','?')}")
            else:
                print("  未找到世界杯比赛数据。")

        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
