# Showcase Display Multiplier Pattern

## Problem

Need to inflate display amounts (bankroll, stake, profit) for demo/showcase presentations without changing underlying compute logic. The math (Kelly, EV, Sharpe, Monte Carlo) must remain correct — only the displayed dollar amounts change.

## When to use

- User says "调高金额展示" / "价格全部翻X倍" / "展示金额放大"
- A demo/deck/showcase needs higher dollar figures while keeping all percentages, odds, probabilities, and risk metrics real
- Both WC26Nami (×170 later ×40) and WC26 (×10) use this pattern

## Implementation — Two Approaches

### Approach A: Helper function (recommended — cleaner, fewer SyntaxError risks)

#### 1. Add a multiplier constant

```python
# Near the top of the API module, after imports
SHOWCASE_MULTIPLIER: float = 10.0  # or whatever factor
```

#### 2. Add the transformer function

```python
def _multiply_showcase(d: dict) -> dict:
    """Deep-copy a dict and multiply all monetary values by SHOWCASE_MULTIPLIER.
    Handles nested dicts and lists of dicts. Only affects keys containing
    'stake', 'bankroll', 'return', 'profit', 'invest' (case-insensitive)."""
    m = SHOWCASE_MULTIPLIER
    if m == 1.0:
        return d
    import copy
    result = copy.deepcopy(d)
    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                kl = k.lower()
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if any(x in kl for x in ('stake', 'bankroll', 'return', 'profit', 'invest')):
                        obj[k] = round(v * m, 2)
                elif isinstance(v, (dict, list)):
                    _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
    _walk(result)
    return result
```

#### 3. Apply at the response boundary

Wrap the response dict right before json.dumps():

```python
# Instead of:
return _json(start_response, {
    "bankroll": bankroll,
    "total_stake": total_stake,
    ...
})

# Do:
return _json(start_response, _multiply_showcase({
    "bankroll": bankroll,
    "total_stake": total_stake,
    ...
}))
```

**⚠️ The closing parens must match:** `_multiply_showcase({...})` needs TWO extra closing parens at the end: `}))` (one for `_multiply_showcase()`, one for `_json()`). The dict itself closes with `}`, then `)` closes `_multiply_showcase(`, then `)` closes `_json(`.

**Verification trick (critical — avoid SyntaxError):**
```bash
python3 -c "
import ast
with open('api/index.py') as f:
    ast.parse(f.read())
    print('✅ Syntax OK')
"
```
Run this after EVERY patch to catch missing/wrong closing parens before commit.

### Approach B: Inline `_M` multiplier (simpler for single endpoints)

Used in WC26Nami where different endpoints needed different factors.

```python
# Inside the endpoint handler
_M = 40  # multiplier
# ...
return _json(start_response, {
    "params": {
        "bankroll": round(bankroll * _M, 2),
        # ...
    },
    "portfolio": {
        "total_stake": round(portfolio.total_stake * _M, 2),
        "expected_return": round(portfolio.expected_return * _M, 2),
        "allocations": [
            {
                "optimal_stake": round(a.optimal_stake * _M, 2),
                # ...
            }
            for a in portfolio.allocations
        ],
    },
})
```

**Pros:** No extra closing parens, no deepcopy, each endpoint can have a different multiplier.
**Cons:** Must manually apply to every field → easy to miss fields. More boilerplate.

## Keys matched (case-insensitive substring — for Approach A)

| Key contains | Example fields affected |
|---|---|
| `stake` | `total_stake`, `optimal_stake`, `recommended_stake`, `stake`, `avg_stake`, `open_exposure` |
| `bankroll` | `bankroll` |
| `return` | `expected_return`, `total_return` |
| `profit` | `net_profit`, `total_profit`, `profit` |
| `invest` | `invested_amount` |

## Keys NOT matched (kept unchanged)

- `roi` / `expected_roi` / `roi_pct` — percentages
- `ev_pct` — edge percentages
- `kelly_pct` / `kelly_fraction` — Kelly percentages
- `win_rate` — win rate %
- `sharpe` / `portfolio_sharpe` / `sortino` / `calmar` — risk ratios
- `edge` — edge decimal
- `model_prob` / `market_implied_prob` — probabilities
- `decimal_odds` / `odds` — odds
- `total_bets` / `count` / `matches_covered` — counts
- `max_drawdown_est` / `concentration` — risk metrics (percentages)
- `exposure_pct` / `total_exposure_pct` / `max_exposure` — exposure percentages
- `total_candidates` / `excluded_count` — counts

## Bet Journal Sync (critical when amplifying stored data)

The bet journal (`/api/wc/quant/journal`) stores real bet records with `stake` and `profit` fields per bet, plus aggregate `stats`. When adding a showcase multiplier:

**Must multiply both:**
1. `stats` dict fields: `total_stake`, `total_profit`, `total_payout`, `avg_stake`, `open_exposure`
2. Each individual `bet` dict: `stake`, `profit` (if not None)

```python
# Pattern for amplifying journal response
bets = list_bets()
stats = compute_stats()
_M = 40
# Multiply stats
for k in ('total_stake', 'total_profit', 'total_payout', 'avg_stake', 'open_exposure'):
    if k in stats:
        stats[k] = round(stats[k] * _M, 2)
# Multiply individual bets
for bet in bets:
    if 'stake' in bet:
        bet['stake'] = round(bet['stake'] * _M, 2)
    if 'profit' in bet and bet['profit'] is not None:
        bet['profit'] = round(bet['profit'] * _M, 2)
return _json(start_response, {"bets": bets, "stats": stats})
```

Otherwise the journal shows $2 bets while the portfolio claims $20k → inconsistency.

## Verification

After deploying, test the endpoint to confirm:

```python
# Quick test
from your_api import SHOWCASE_MULTIPLIER, _multiply_showcase

resp = {
    'bankroll': 1000.0,
    'total_stake': 492.0,
    'expected_return': 118.0,
    'expected_roi': 0.24,    # should NOT change
    'allocations': [{'optimal_stake': 72.0, 'model_prob': 0.35}]
}
r = _multiply_showcase(resp)
assert r['bankroll'] == 10000.0
assert r['total_stake'] == 4920.0
assert r['expected_return'] == 1180.0
assert r['expected_roi'] == 0.24   # unchanged
assert r['allocations'][0]['optimal_stake'] == 720.0
assert r['allocations'][0]['model_prob'] == 0.35  # unchanged
```

## Projects using this pattern

| Project | Factor | Approach | Total stake (original) | Total stake (showcase) |
|---|---|---|---|---|
| WC26Nami (v6.1.5) | ×170 | Inline `_M` | ~$492 | ~$83,771 |
| WC26 (v5.9.1) | ×10 | Helper function | ~$492 | ~$4,927 |
| WC26Nami (v6.1.6) | ×40 | Inline `_M` | ~$492 | ~$19,253 |

## Pitfalls

1. **WSGI closing parens** — In WSGI apps (WC26), `_multiply_showcase({...})` wrapper needs an extra closing `)`. Triple-check: `_json(start_response, _multiply_showcase({...}))` → `}))` at the end.

2. **AST verify after every patch** — After adding/modifying a `_multiply_showcase` wrapper, immediately run:
   ```bash
   python3 -c "import ast; ast.parse(open('api/index.py').read()); print('✅ Syntax OK')"
   ```
   This catches missing `)` before you commit.

3. **deepcopy performance** — For very large response dicts, deepcopy is safe but not free. For sub-millisecond endpoints this is fine; for latency-sensitive endpoints, consider targeted multiply instead.

4. **Key collision risk** — The substring matching can theoretically match unintended keys containing "return" (like "return_url"). In practice this doesn't occur in quant/trading API responses. Review if applying to a different domain.

5. **Journal inconsistency** — Forgetting to sync the bet journal creates visible inconsistency: portfolio shows $20k but journal shows $2 bets. Always apply the multiplier to both stats and individual bet records.
