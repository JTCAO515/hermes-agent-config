# Poker Game Theory Engine — Detailed Reference

> Absorbed from standalone `poker-game-theory` skill (2026-06-02). The game theory engine is already covered in txpokerassist's "game_theory.py" module section. This file captures the full reference including the range definitions.

## Four-Stage Pipeline

1. **Intent Reverse Engineering** — infer opponent range + motive from action patterns
2. **Situation Assessment** — SPR, position, pot odds, remaining players
3. **Decision Tree** — compute EV for fold/call/raise/all-in with fold equity
4. **Optimal Move** — highest EV branch + risk-adjusted alternative

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

### Raise EV
```
EV_raise = FE * pot + (1-FE) * ev_if_called
```

## Intent Tag Taxonomy

| Tag | Meaning | Recognition |
|-----|---------|-------------|
| value | Value bet | pot 40-75%, short think |
| bluff | Bluff | pot > 80%, long think or unnatural |
| semi_bluff | Semi-bluff | Draw + aggressive |
| probe | Probe bet | pot < 40%, small test |
| trap | Trap | Slow-play strong hand, insta-call |
| steal | Steal | BTN/CO position, preflop raise |
| defense | Defense | BB resistance |

## Intention Signals

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

Detect flush draws (hero suited + 2-3 suited on board) and straight draws (4-card sequences with 1 or 0 gaps). For wheel: include A=1 for A-2-3-4-5 straight detection.

## Preflop Hand Description

When `len(community_cards) == 0`:
- Pocket pairs: `"One Pair, Xs"`
- Suited: `"XYs"`
- Offsuit: `"XYo"`

## API Endpoints

- `POST /api/calculate` — quick decision (uses decision_engine)
- `POST /api/analyze` — full game theory analysis (uses game_theory.analyze)

Both accept `hand`, `board`, `pot`, `call`, `stack`, `players`, `sims`, `ranges`.

`/api/analyze` additionally accepts `position` (0=BTN) and `actions[]` with `{player_id, action, amount, street, timing_s}`.

## Verification Pattern

Always verify with concrete scenarios:
- Strong hand → all-in
- Weak hand → fold
- Marginal draw → call
- Blocker/value hand → raise
