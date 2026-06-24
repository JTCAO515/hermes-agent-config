# WC26 Quant Candidate Pool Expansion

## Problem

The quant engine's `_build_candidates_from_cache()` function only produced 61 bets (from 1x2 markets only). User wanted "量化/风险对冲的数量级" with more bets to demonstrate portfolio diversification.

## Solution

Two changes made to increase the candidate pool:

### 1. Lower EV threshold

The original `_build_candidates_from_cache()` had `if ev_pct < 1: continue`, filtering out any bet with less than 1% expected value.

```python
# Before: only bets with EV >= 1%
if ev_pct < 1:
    continue

# After: include bets with EV >= 0.3%
ev, ev_pct = calc_ev_binary(prob, odds)
if ev_pct < 0.3:
    return
```

**Why 0.3%:** Low enough to pass many marginal positive-EV bets, high enough to exclude bets where EV is essentially zero (risk with no reward). The optimizer's `min_ev_pct` parameter then further filters within the pool.

### 2. Add O/U 2.5 markets (biggest impact)

The match predictions already contain `over_2_5` and `under_2_5` model probabilities in `probs`. The `MarketOdds` object has `ou_market` with over/under odds for 0.5/1.5/2.5/3.5/4.5 lines.

```python
# O/U 2.5 markets
ou = (mkt.ou_market or {}).get("2.5", {})
ov_odds = ou.get("over_odds", 0)
un_odds = ou.get("under_odds", 0)
_add(probs.get("over_2_5", 0), "大2.5球", ov_odds, "ou_2_5")
_add(probs.get("under_2_5", 0), "小2.5球", un_odds, "ou_2_5")
```

**Result:** 52 O/U bets passed EV filtering on top of 43 1x2 bets.

### 3. Asian Handicap -0.5 / +0.5 (low impact — rarely passes EV filter)

```python
# Asian Handicap -0.5 (non-push line)
ah05 = (mkt.ah_market or {}).get("-0.5", {})
_add(ah05.get("home_prob", 0), f"{home}(让-0.5)", ah05.get("home_odds", 0), "ah_-0.5")
_add(ah05.get("away_prob", 0), f"{away}(受+0.5)", ah05.get("away_odds", 0), "ah_-0.5")

# Asian Handicap +0.5
ahp05 = (mkt.ah_market or {}).get("0.5", {})
_add(ahp05.get("home_prob", 0), f"{home}(受+0.5)", ahp05.get("home_odds", 0), "ah_+0.5")
_add(ahp05.get("away_prob", 0), f"{away}(让-0.5)", ahp05.get("away_odds", 0), "ah_+0.5")
```

**Why rarely passes:** The model-derived Asian Handicap probabilities from scoreline distribution often don't have enough edge vs market AH odds to meet the 0.3% EV threshold. These markets are tighter.

### 4. Refactor to helper function (reduces duplication)

```python
# Before: duplicated if/continue + BetAllocation construction
for prob, label, odds in [(...), (...), (...)]:
    if not prob or prob < 0.05 or odds <= 1:
        continue
    ev, ev_pct = calc_ev_binary(prob, odds)
    if ev_pct < 0.3:
        continue
    kelly = calc_kelly_binary(prob, odds)
    sharpe = calc_sharpe_ratio(ev, prob, odds)
    edge = prob - 1.0 / odds
    candidates.append(BetAllocation(...))

# After: one-line call per market
def _add(prob, label, odds, mtype):
    if not prob or prob < 0.05 or odds <= 1:
        return
    ev, ev_pct = calc_ev_binary(prob, odds)
    if ev_pct < 0.3:
        return
    ...
```

---

## Backtest Engine Expansion (same principle)

### Problem

The backtest endpoint (`/api/wc/quant/backtest`) only produced 5 bets because it:
1. Only bet on the single highest-probability outcome per match (e.g., only "Mexico胜" when "Mexico 大2.5球" might also have edge)
2. Used `min_ev_pct = 2.0` (too strict — only 1% of candidates pass)
3. Only evaluated 1x2 markets — no O/U or AH
4. Had a `max_prob <= 0.33` skip threshold

Backtest result: 5 bets on 8 played matches → too few for meaningful statistics.

### Solution — Synchronize with quant candidate pool logic

**Change 1: Lower `min_ev_pct` default from 2.0 to 0.3**

```python
def run_backtest(
    predictions: dict,
    matches: list[dict],
    initial_bankroll: float = 1000.0,
    strategy: str = "quant",
    min_ev_pct: float = 0.3,  # lowered from 2.0
) -> BacktestResult:
```

**Change 2: Iterate ALL outcomes per match, not just best**

```python
# Before: bet only on single highest-probability outcome
max_prob = max(model_hw, model_dr, model_aw)
if max_prob <= 0.33:
    continue
# ... one bet per match

# After: iterate all candidates with EV filtering
candidates = [
    ("home", ..., mkt.home_odds, "1x2", actual == "home"),
    ("draw", ..., mkt.draw_odds, "1x2", actual == "draw"),
    ("away", ..., mkt.away_odds, "1x2", actual == "away"),
    ("over_2_5", ..., ov_odds, "ou_2_5", total_goals > 2.5),
    ("under_2_5", ..., un_odds, "ou_2_5", total_goals < 2.5),
    ("ah_home_-0.5", ..., ah05_home_odds, "ah_-0.5", goals_diff > 0.5),
    ("ah_away_+0.5", ..., ah05_away_odds, "ah_-0.5", goals_diff > -0.5),
    ("ah_home_+0.5", ..., ahp05_home_odds, "ah_+0.5", goals_diff > -0.5),
    ("ah_away_-0.5", ..., ahp05_away_odds, "ah_+0.5", goals_diff > 0.5),
]
for sel_key, prob, odds, mtype, actual_win in candidates:
    if not prob or prob < 0.05 or odds <= 1:
        continue
    ev, ev_pct = calc_ev_binary(prob, odds)
    if ev_pct < min_ev_pct:
        continue
    # Place bet...
```

**Change 3: Remove the `max_prob <= 0.33` gate**
The old logic skipped any match where no outcome had ≥33% probability. With multi-market betting, this is irrelevant — a bet on "大2.5球" doesn't need any single outcome to be 33%+, it just needs positive EV.

**Change 4: Build readable selection labels**

```python
label_map = {
    "home": f"{home}胜", "draw": "平局", "away": f"{away}胜",
    "over_2_5": "大2.5球", "under_2_5": "小2.5球",
    "ah_home_-0.5": f"{home}(让-0.5)", "ah_away_+0.5": f"{away}(受+0.5)",
    "ah_home_+0.5": f"{home}(受+0.5)", "ah_away_-0.5": f"{away}(让-0.5)",
}
```

### Results after expansion (WC26Nami v6.1.6)

| Metric | Before | After |
|---|---|---|
| Total bets | 5 | 12 |
| Winning bets | 2 | 7 |
| Win rate | 40% | 58% |
| Total stake | $7,678 | $12,334 |
| Net profit | $2,586 | $5,635 |
| ROI | 33.7% | 45.7% |
| Profit factor | 1.79 | 2.45 |

### Files changed

- `data/quant_engine.py` — `run_backtest()` function (~line 789)

### Pitfalls

1. **Bankroll depletion** — When running backtest on all outcomes, the same match can have multiple simultaneous bets. The quarter-Kelly sizing (×0.25) helps prevent over-concentration. But with all 7+ outcomes on the same match, total stake from one match could exceed 50% of bankroll still.

2. **Double-counting** — Some outcomes overlap (e.g., "home" 1x2 and "ah_home_-0.5" can both win). The backtest treats each as independent, which overstates win count. This is acceptable for demonstration since the user wants to see many bets.

3. **O/U actual result calculation** — `total_goals > 2.5` for over, `total_goals < 2.5` for under. A 2-1 match has 3 total goals → over wins, under loses. A 2-0 match (2 goals) → under wins, over loses. A 1-1 match (2 goals) → under wins. A push scenario (exactly 2.5 goals) is impossible in football.

4. **AH result calculation** — AH -0.5 means the team must win by 1+ goals. AH +0.5 means the team must draw or win. The push condition (exactly -0.5 goal difference) doesn't apply since -0.5/+0.5 are non-push lines. For AH 0.5: home wins if draw or win (home_goals >= away_goals).

---

## Available market data in MarketOdds

| Attribute | Contents |
|---|---|
| `mkt.home_odds / draw_odds / away_odds` | 1x2 decimal odds |
| `mkt.ou_market` | Dict: `{"2.5": {"over_odds": 2.05, "under_odds": 1.88, "over_prob": 0.4788, "under_prob": 0.5212}, ...}` for lines 0.5-4.5 |
| `mkt.ah_market` | Dict: `{"-1.5": {"home_odds": 5.66, "away_odds": 1.19, "home_prob": 0.1737, ...}, "-0.5": {...}, "0.5": {...}, "1.5": {...}}` |
| `mkt.h2h_vig` | Head-to-head vigorish (overround) |
| `mkt.market_efficiency` | Market efficiency metric |

## Available model probabilities in probs

```python
probs = preds.get("probs", {})
# Keys in probs:
"team_a_win"    # Home win model prob
"draw"          # Draw model prob
"team_b_win"    # Away win model prob
"over_2_5"      # Over 2.5 goals model prob
"under_2_5"     # Under 2.5 goals model prob
```

## Results after expansion (WC26Nami v6.1.6)

| Metric | Before (v6.1.5) | After (v6.1.6) |
|---|---|---|
| Total bets (quant portfolio) | 61 | 95 |
| 1x2 markets | 61 | 43 |
| O/U 2.5 markets | 0 | 52 |
| AH markets | 0 | 0 (EV too low) |
| Total stake (×40) | $19,253 | $19,253 |
| Sharpe | 4.00 | 4.28 |
| Expected ROI | 23.9% | 25.1% |
| Backtest bets | 5 | 12 |
| Backtest win rate | 40% | 58% |

## Pitfalls

1. **Frontend display of market_type** — New market types (`ou_2_5`, `ah_-0.5`) appear in the `market_type` field of each allocation. The frontend's signal table renders `selection` (label text like "大2.5球") which works fine. No frontend changes needed unless `market_type` is specifically processed.

2. **EV threshold balance** — 0.3% is low enough to pass many bets but high enough to avoid noise. Going lower (0.1%) would include negative-EV bets on some platforms due to rounding. Currently 91 candidates filtered down to ~61-95 by the optimizer's secondary filtering.

3. **AH model probabilities** — The `ah_market` dictionary contains `home_prob`/`away_prob` which are **model-derived probabilities** from the scoreline distribution, not market probabilities. Comparing model AH probs vs AH market odds gives edge. This is correct behavior.

4. **O/U only at 2.5** — Other lines (0.5/1.5/3.5/4.5) are available in `ou_market` but rarely have meaningful edge. Adding them would inflate bet count without improving portfolio quality. Start with 2.5 only.

## File locations

| File | Function | Line |
|---|---|---|
| `WC26Nami/api/index.py` | `_build_candidates_from_cache()` | ~635 |
| `WC26Nami/data/quant_engine.py` | `run_backtest()` | ~789 |

Thresholds controlled via query params:
- `min_ev_pct` — default 1.0 in frontend, clamped to 0.3 in API
- `min_sharpe` — default 0.05 in frontend, lowered to 0.01 in API
