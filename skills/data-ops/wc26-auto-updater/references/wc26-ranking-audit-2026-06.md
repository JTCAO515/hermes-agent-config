# WC26 FIFA Ranking Audit — June 2026

**Audit Date:** 2026-06-14
**Source:** ESPN / SofaScore / Wikipedia "FIFA Men's World Ranking"
**Snapshot:** Pre-World Cup rankings (released ~June 11, 2026)

## Key Discrepancies Found

These are teams from our dataset that had **significant** ranking errors (>3 positions):

| Team | Dataset Rank | Real Rank | Δ | Impact on Prediction |
|------|:-----------:|:---------:|:-:|:-------------------:|
| Norway | 14 | 31 | +17 | Was massively overrated — predicted as dark horse, should be mid-tier |
| Morocco | 12 | 7 | -5 | Was underrated — predicted as mid, should be elite challenge |
| Uruguay | 11 | 16 | +5 | Slightly overrated |
| Colombia | 10 | 13 | +3 | Slightly overrated |
| Ghana | 38 | 73 | +35 | Was massively overrated (database said 38, real rank 73) |
| Bosnia | 48 | 64 | +16 | Was overrated |
| Scotland | 30 | 42 | +12 | Was overrated |
| Czechia | 36 | 40 | +4 | Minor |
| South Africa | 59 | 60 | +1 | Minimal |
| Panama | 55 | 34 | -21 | Was massively underrated |
| Haiti | 70 | 83 | +13 | Was overrated |
| New Zealand | 95 | 85 | -10 | Was underrated |

## Top 10 Real vs Dataset

| Real Rank | Real Team | Dataset Rank | Match? |
|:---------:|-----------|:-----------:|:------:|
| 1 | Argentina | 1 | ✅ |
| 2 | Spain | 3 | ❌ (was 3) |
| 3 | France | 2 | ❌ (was 2) |
| 4 | England | 4 | ✅ |
| 5 | Portugal | 6 | ❌ (was 6) |
| 6 | Brazil | 5 | ❌ (was 5) |
| 7 | Morocco | 12 | ❌ (was 12) |
| 8 | Netherlands | 7 | ❌ (was 7) |
| 9 | Belgium | 9 | ✅ |
| 10 | Germany | 8 | ❌ (was 8) |

**Finding:** The top 6 had even-number asymmetry (1 vs 2, 2 vs 3, etc.) — the original dataset was close but never exactly right.

## Rating Calculation Formula (from `correct_data.py`)

```python
MAX_RANK = 85  # New Zealand (lowest-ranked qualified team)
norm = (fifa_rank - 1) / (MAX_RANK - 1)
base = 1.0 - norm
attack = round(0.55 + base * 1.65, 2)
defense = round(1.45 - base * 0.85, 2)

tier_map = {
    rank <= 6: "elite",
    rank <= 14: "strong",
    rank <= 20: "good",
    rank <= 40: "average",
    rank <= 60: "lower",
    else: "weak",
}
```

This gives a smooth gradient: top team (Argentina #1) → attack 2.20 / defense 0.60, bottom team (New Zealand #85) → attack 0.55 / defense 1.45.

## Future Audit Points

- FIFA rankings are updated monthly — next update is after WC26 ends
- The ranking formula used here is a proxy; real xG data from FBref/Understat would be more accurate
- Team ratings should ideally be weighted by: 50% FIFA rank, 25% recent qualifying form, 25% historical WC performance
