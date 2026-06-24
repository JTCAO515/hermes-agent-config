---
name: poker-game-theory
description: 德州扑克博弈预测引擎 — 意图逆向工程 + 决策树 + 最优解。构建对手建模/范围约束/决策树生成的完整工作流。
---

# Poker Game Theory Engine

## Overview
Build a multi-player poker analysis engine that goes beyond raw equity to produce actionable strategic decisions. The engine has four stages:

1. **Intent reverse engineering** — infer opponent range + motive from action patterns
2. **Situation assessment** — SPR, position, pot odds, remaining players
3. **Decision tree** — compute EV for fold/call/raise/all-in with fold equity
4. **Optimal move** — highest EV branch + risk-adjusted alternative

## Architecture

```
game_theory.py
├── Data models (PlayerAction, PlayerProfile, DecisionBranch, GameTheoryResult)
├── Rules engine (position multipliers, intent tag taxonomy)
├── Engine (analyze() — orchestrates the 4-stage pipeline)
├── Math utilities (EV formula, required fold equity, raise EV)
├── Text generation (reasoning, risk, insight)
└── Formatter (format_game_theory — structured output)
```

## Key Formulas

### EV (call)
```
EV = effective_win * pot - effective_lose * to_call
effective_win = win_rate + tie_rate * 0.5
```

### Required Fold Equity (raise)
```
FE_needed = -ev_if_called / (pot - ev_if_called)
```
Where `ev_if_called` is the EV if opponent calls the raise.

### Raise EV
```
EV_raise = FE * pot + (1-FE) * ev_if_called
```

## Intention Reverse Engineering

Infer opponent intent from three signals:

| Signal | Pattern | Inference |
|--------|---------|-----------|
| Bet sizing | < 40% pot | Information bet |
| Bet sizing | 40-75% pot | Standard value/semi-bluff |
| Bet sizing | > 75% pot | Overbet (bluff or monster) |
| Timing | < 1.5s fast call | Made hand (not draw) |
| Timing | > 5s long think | Strong hand (considering raise) |
| Position | BTN + raise | Wide range (steal) |
| Position | Blind + raise | Narrow range (defense) |

## Draw Detection (Flop+)

Detect flush draws (hero suited + 2-3 suited on board) and straight draws (4-card sequences with 1 or 0 gaps). Output as appended description e.g. "同花听牌+两头顺听牌".

## Preflop Hand Description

When `len(community_cards) == 0`, describe directly from hero cards:
- Pocket pairs: `"One Pair, Xs"` 
- Suited: `"XYs"`
- Offsuit: `"XYo"`

## Verification Pattern

Always verify with concrete scenarios showing the engine makes correct decisions:

```python
# Strong hand → all-in
# Weak hand → fold  
# Marginal draw → call
# Blocker/value hand → raise
```

## API Integration

Two endpoints:
- `POST /api/calculate` — quick decision (uses decision_engine)
- `POST /api/analyze` — full game theory analysis (uses game_theory.analyze)

Both accept `hand`, `board`, `pot`, `call`, `stack`, `players`, `sims`, `ranges`.

`/api/analyze` additionally accepts `position` (0=BTN) and `actions[]` with `{player_id, action, amount, street, timing_s}`.

## Frontend (html/css/js)

Dual-mode UI:
1. **Quick mode** — same as before, calls `/api/calculate`
2. **GT mode** — adds opponent action recorder, range selector, position input. Calls `/api/analyze`. Renders: situation insight → equity gauge → optimal action → reasoning → alternative → decision tree.

When building a two-mode UI, prefix all GT-mode IDs with `gt` to avoid collision: `gtHeroCards`, `gtCardGrid`, `gtCalcBtn`.

## References

See `references/` for:
- `range-definitions.md` — Preset range hand compositions
- `output-format.md` — Structured output schema

## Scripts

`scripts/verify-scenarios.py` — Re-runnable verification test for all 5 decision scenarios.
