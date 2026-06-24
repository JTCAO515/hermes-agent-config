# Poker Equity Calculator — Detailed Reference

> Absorbed from standalone `poker-equity` skill (2026-06-02). This condensed knowledge bank is for deep equity computation detail. The core modules are already documented in the txpokerassist SKILL.md "模块详解" section; this file captures the full reference.

## Card Encoding (6-bit)

`(suit << 4) | rank` where rank=2-14, suit=0-3 (c,d,h,s)

```python
def encode_card(rank, suit): return (suit << 4) | rank
def card_rank(card):         return card & 0x0F
def card_suit(card):         return (card >> 4) & 0x3
```

**Key constraint:** Use `if not: raise ValueError` over `assert` (assert disabled in `python -O`).

## Hand Evaluation

**10 hand ranks** (HandRank): HIGH_CARD=0 → ROYAL_FLUSH=9

- `evaluate_5`: From 5 cards, find best combination
- `evaluate_7`: Enumerate C(7,5)=21 combinations, pick highest
- `compare_hands`: Must use `max(len(k1), len(k2))` for kicker comparison (not zip truncation)

## Monte Carlo — Critical Formulas

**💣 EV Formula (correct):**
```
Win$ = pot         # call amount is NOT profit
EV = win% * Win$ - lose% * Lost$
```

**💣 Multi-way pot stats:**
```
WRONG: win_rate = total_wins / (sims * num_opponents)
RIGHT: whole-pot counting — win/tie/lose are mutually exclusive per simulation
```

## Range Pre-filtering

- Use `build_range_pool()` — precompute all valid combinations (O(n²) once)
- Do NOT use rejection sampling (4% hit rate fails frequently with tight ranges)
- Pre-filter complete → O(1) random selection

## Common Pitfalls Table

| # | Pitfall | Fix |
|---|---------|-----|
| 1 | EV includes call amount | Win$ = pot |
| 2 | Multi-way per-opponent accumulation | Whole-pot stats |
| 3 | Rejection sampling on tight ranges | Pre-filter O(n²) once |
| 4 | `assert` disabled by -O | `if not: raise ValueError` |
| 5 | `compare_hands` zip truncates | `max(len)` bitwise comparison |
| 6 | f-string + CSS conflict | Use `python3 << 'PYEOF'` heredoc |

## Vercel Serverless Constraints

| Environment | Default behavior | Notes |
|-------------|-----------------|-------|
| Local dev | Single process (1 worker) | Can enable multi-process explicitly |
| Vercel prod | Forced single-process | fork blocked, multi-process crashes |
| CLI use | Single process | Auto-selects optimal mode |
