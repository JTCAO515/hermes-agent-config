# The Odds API v4 集成指南 — WC26 实时盘口

> 2026-06-19 接入。Provider: the-odds-api.com, API Key: 7bd3207b09a2b09053a7df453b33623d

## 端点测试结果

| 测试 | 结果 | 备注 |
|------|------|------|
| /v4/sports (列表, 免费) | ✅ 44 sports | 不消耗 quota |
| /v4/sports/soccer_fifa_world_cup/odds | ✅ 44 matches | cost=6/req (eu+uk × h2h+spreads+totals) |
| 直连（中国 VPS） | ✅ 无墙 | api.the-odds-api.com 直连可用 |
| 通过 Xray 代理 | ❌ 超时 | 新加坡中继无法到达该 API |

## 关键限制

### API Quota 审计

免费层: **1000 requests/month**（不是 1000 quota units）
每次请求消耗 quota = regions × markets

当前方案：
- 每 30 分钟一次
- 2 regions (eu, uk) × 3 markets (h2h, spreads, totals) = 6 cost
- 月消耗 = 48 次 × 6 = **288 quota/月** ✅（在 1000 限额内）

⚠️ 之前误算为 8640 — 纠正：cost 指 quota 消耗，不是 API call 消耗。
1000 / 6 = ~166 次请求/月。每 30 分钟 = 1440 次/月 → **严重超限（14.4×）**。

### 可持续方案

| 方案 | 月请求 | 月 quota | 是否 OK |
|------|--------|---------|---------|
| 当前: 30min × 2reg × 3mkts | 1440 | 8640 | ❌ 14× 超限 |
| 每 2h × 2reg × 3mkts | 360 | 2160 | ❌ 2× 超限 |
| 每 2h × 1reg(eu) × 1mkt(h2h) | 360 | 360 | ✅ |
| 每 1h × 1reg(eu) × 2mkts(h2h+totals) | 720 | 1440 | ❌ 略超 |
| **推荐: 每 2h × 1reg(eu) × 1mkt(h2h)** | **360** | **360** | **✅** |

**推荐方案：** 每 2 小时同步，只拉 eu 区 h2h（1X2），spreads/totals 用模型生成。

## 同步脚本结构

### odds_fetcher.py 核心流程

```
1. GET /v4/sports/soccer_fifa_world_cup/odds?regions=eu,uk&markets=h2h,spreads,totals
2. 遍历 odds_data 中的 44 场比赛
3. 对每场比赛，尝试找 Pinnacle bookmaker（首选）
4. 对 outcomes 中的每支球队名做 normalize_teams()
5. 写入 live_odds.json（原始数据存档）
6. 合并到 wc2026_matches.json 的 match.live_odds 字段
```

### 合并代码片段（odds_fetcher.py 核心）

```python
# 匹配比赛：用无序集合避免 home/away 方向歧义
for m in matches:
    ta, tb = m["team_a"], m["team_b"]
    team_set = {ta, tb}
    for om in odds_data:
        home = normalize_teams(om["home_team"])
        away = normalize_teams(om["away_team"])
        if {home, away} == team_set:
            # 找 Pinnacle
            pinnacle = next((b for b in om["bookmakers"] if b["key"] == "pinnacle"), None)
            best_bm = pinnacle or om["bookmakers"][0]
            # 提取 markets
            markets_data = {}
            for mk in best_bm["markets"]:
                outcomes = {}
                for o in mk["outcomes"]:
                    outcomes[normalize_teams(o["name"])] = o["price"]
                markets_data[mk["key"]] = outcomes
            m["live_odds"] = {
                "bookmaker": best_bm["title"],
                "total_bookmakers": len(om["bookmakers"]),
                "markets": markets_data,
            }
```

## API 集成代码（api/index.py）

在 `_get_cached_matches_fast()` 中，盘口处理在构建 market 数据之后：

```python
# ── Real Odds: The Odds API (v6.2) ──
live = match.get("live_odds", {})
mkts = live.get("markets", {})
h2h = mkts.get("h2h", {})

if h2h:
    home_name = match.get("team_a", "")
    away_name = match.get("team_b", "")
    markets["real_home_odds"] = h2h.get(home_name, 0)
    markets["real_draw_odds"] = h2h.get("Draw", 0)
    markets["real_away_odds"] = h2h.get(away_name, 0)
    markets["odds_source"] = live.get("bookmaker", "the-odds-api")
    # … 计算去水概率 + EV + best_bet
```

重要：队名通过已经归一化的 `live_odds.markets.h2h` keys 匹配，用 match 中的 `team_a`/`team_b` 直接查。

## 已验证的数据完整性

- 44 场匹配比赛全部正确配对（无序集合匹配）
- 40 家博彩公司覆盖
- Pinnacle 首选（sharp 博彩）
- 1X2 + 让球 + 大小球市场
- 队名归一化后全部匹配（已验证 Czechia/Czech Republic、Korea Republic/South Korea 等）
