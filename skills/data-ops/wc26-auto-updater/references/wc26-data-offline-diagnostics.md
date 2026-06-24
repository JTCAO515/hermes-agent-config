# WC26 "Data Offline" / "No Signals" — Diagnostic Flow

> When the user reports "数据全部挂掉了", "没有投注信号", "离线模式", "实时盘口未能加载", or any variation — DO NOT assume data corruption. Follow this staged diagnostic pipeline.

**Key insight from production (2026-06-19):** The most common cause is **Vercel Hobby plan cold start latency** (5-10s). The data is fine; the user hit a cold-start window. Always verify against actual site state before assuming data pipeline failure.

---

## Stage 1 — Verify the Frontend

Visit the site directly in browser before touching any backend.

**What to check visually:**
- **Summary bar** (top of page): `总场次 104 · 已赛 N · 未赛 M` — if these show reasonable numbers, data is loading
- **Quant tab** (`📊 量化`): signals table rows vs "当前没有符合条件的投注信号" — if signals appear, the quant engine has data
- **Schedule tab** (`📅 赛程`): scroll down and verify scores display — if scores show, fifa sync worked
- **Match drawer** (click `›` on any match): check if odds display or "实时盘口未能加载" message appears

**Possible findings:**
| Frontend state | Likely cause | Action |
|---------------|-------------|--------|
| All data shows | User hit transient cold start | Refresh, confirm working, report "已正常" |
| Summary OK, quant empty | Cold start hit quant API timeout | Refresh after 10s |
| Everything spinning | Vercel cold deploy (just pushed) | Wait 30s for deploy to complete |
| All data stale (yesterday's matches only) | FIFA sync cron or odds fetch failed | Run Stage 2 |

---

## Stage 2 — Check Data Freshness (Backend Server)

Run this from the server:

```bash
python3 -c "
import json
from datetime import datetime, timezone
m = json.load(open('data/wc2026_matches.json'))
matches = m.get('matches', [])
print(f'Matches: {len(matches)}')
lu = m.get('last_updated', 'N/A')
print(f'Last updated: {lu}')
try:
    dt = datetime.fromisoformat(lu)
    age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    print(f'Data age: {age:.1f}h')
    if age > 6: print('⚠️  Data stale — run fifa_sync')
except: pass
r = sum(1 for match in matches if match.get('has_result'))
print(f'Matches with results: {r}')
o = json.load(open('data/live_odds.json'))
lu2 = o.get('last_updated', 'N/A')
odds_count = sum(1 for k in o.keys() if k != 'last_updated')
print(f'Odds last updated: {lu2}')
print(f'Odds entries: {odds_count}')
"
```

**Note:** The `status` field was never set by fifa_sync — `has_result=True` is what the frontend checks. This is by design, not a bug.

---

## Stage 3 — Run Data Syncs

```bash
cd ~/projects/WC26-Main

# FIFA sync (must go through Xray proxy from China VPS)
export https_proxy=http://127.0.0.1:10809
export http_proxy=http://127.0.0.1:10809
python3 data/fifa_sync.py

# Odds fetcher (direct connection, NO proxy)
unset https_proxy http_proxy
python3 data/odds_fetcher.py
```

**Interpreting FIFA sync output:**
| Output | Meaning | Action |
|--------|---------|--------|
| `📡 28 场已赛 (FIFA)` + `📊 更新 0 场, 当前已赛: 38 场` | **Normal.** All FIFA matches already have results locally. | ✅ Nothing |
| `📡 28 场已赛` + `📊 更新 5 场` | **New results synced.** Push to GitHub. | ✅ Push |
| `📡 0 场已赛` or SSL handshake timeout | **Proxy issue.** FIFA API blocked from China. | ❌ Fix proxy |

**Interpreting odds fetcher output:**
| Output | Meaning |
|--------|---------|
| `✅ 获取 44 场盘口` + `💾 保存 44 场盘口` | Normal |
| `❌ 请求失败` | API key/quota issue |
| `获取 0 场盘口` | Sport key may have changed |

---

## Stage 4 — Push & Deploy (if data was updated)

```bash
cd ~/projects/WC26-Main
git add data/wc2026_matches.json data/live_odds.json
git commit -m "data: refresh sync $(date +%Y-%m-%d)"
git push origin master  # NOT main — branch is master
```

Wait ~20-30s for Vercel auto-deploy, then verify APIs.

---

## Common False Alarms

| User report | Reality | Resolution |
|------------|---------|------------|
| "数据全部挂掉了" | Vercel cold start (5-10s) | Refresh, verify data exists |
| "当前没有符合条件的投注信号" | Quant returned 0 bets (legit) | Check if matches have +EV |
| "实时盘口未能加载" | odds-full fetch timed out | Frontend fallback (5s timeout) — data exists |
| "离线模式" | Usually cold start | Refresh |
| "版本号没有更新" | Vercel deploy not finished | Wait 20-30s, refresh |

**Production data baseline (verified 2026-06-19):**
- 104 matches ✓ | 37-38 with results ✓ | 44 with live odds ✓
- 57+ quant signals | $7,071.90 stake | 26.9% ROI | 0.690 model accuracy ✓
