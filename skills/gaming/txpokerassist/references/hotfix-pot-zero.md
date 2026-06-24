# Hotfix: pot=0 ZeroDivisionError in game theory analysis

## Root Cause

`_raise_reasoning()` in `game_theory.py`:

```python
f"加注到 ${raise_amt}（{raise_amt/pot:.1f}x 底池）。"
```

When `pot=0` (user didn't fill in pot field), `raise_amt/pot` raises `ZeroDivisionError`.

**Cascade:** FastAPI catches this in the generic `except Exception` handler → returns "500 Internal server error" → frontend shows red error.

## Secondary Failure: SPR=inf → JSON serialization

`_calculate_spr(hero_stack, pot)` returns `float('inf')` when `pot=0`. JSON cannot serialize `inf`:

```
ValueError: Out of range float values are not JSON compliant
```

This hits BEFORE the ZeroDivisionError in some code paths.

## Fix Pattern

### For formatted output strings:
```python
pot_mult = f"{raise_amt/pot:.1f}x" if pot > 0 else "?"
f"加注到 ${raise_amt}（{pot_mult} 底池）。"
```

### For SPR in API response:
```python
spr=round(result.spr, 1) if result.spr != float('inf') else 0.0
```

### For SPR in formatted text:
```python
spr_str = f"{spr:.1f}" if spr != float('inf') else "∞"
```

## Scan Checklist

Check ALL f-strings containing division by `pot` or any user-input denominator:

| Location | Expression | Fixed? |
|----------|-----------|--------|
| `_raise_reasoning` | `raise_amt/pot` | ✅ pot>0 guard |
| `_infer_intent` | `action.amount / max(pot, 1)` | ✅ max(pot,1) |
| `_calculate_spr` | `stack / pot` | ✅ pot>0 check |
| API response `spr` | `result.spr` (inf) | ✅ inf→0.0 |
| `situation_insight` | `spr:.1f` | ✅ inf→∞ |
| `_call_reasoning` | `to_call / (pot + to_call)` | ✅ pot+call>0 |
| `_ev_raise` | `pot + raise_amount - to_call` | ✅ no division |

## Simpsons Rule

If a division in formatted output creates a readable ratio (like "2.0x pot", "SPR=3.5"), ALWAYS add a guard. The user WILL trigger it by leaving a field empty.
