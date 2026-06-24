# Range Definitions Reference

## Preset Ranges (in ranges.py)

| Name | Hands | Type Count | Description |
|------|-------|-----------|-------------|
| any | All 1326 combos | N/A | Random |
| top5 | AA, KK, QQ, JJ, TT, AKs, AKo, AQs | 8 | Premium only |
| top10 | +99, 88, AQo, AJs, KQs | 13 | Tight |
| top15 | +77, ATs, KJs, QJs, JTs | 18 | Standard tight |
| top20 | TT+, ATs+, KJs+, QJs, JTs, T9s, 98s, AJo+, KQo | 18 | Mid |
| top35 | 77+, A9s+, KTs+, QTs+, J9s+, T8s+, 97s+, 87s, 76s, ATo+, KJo+, QJo | 27 | Loose |
| top50 | 22+, A2s+, K7s+, Q9s+, J8s+, T7s+, 97s+, 86s+, 75s+, 64s+, 54s, A8o+, KTo+, QTo+, JTo | 41 | Very loose |
| pair+ | 22+ | 13 | Any pair |
| broadway | ATs+, KTs+, QTs+, JTs, ATo+, KTo+, QTo+, JTo | 16 | Two cards T+ |
| suited-connector | 54s+, 65s+, 76s+, 87s+, 98s+, T9s+, JTs+ | 10 | Suited connectors |

## Custom Range Syntax

```
"AA, KK, AKs, AKo"           # Explicit hands
"TT+, AJs+, KQo"              # With "+" expansion
"22+"                         # All pockets
"ATs+"                        # AKs, AQs, AJs, ATs
"98s+"                        # 98s, T9s, JTs, QJs, KQs, AKs
"98o+"                        # 98o, T9o, JTo, QJo, KQo, AKo
```

## Implementation Notes

- Ranges are stored as `Set[HandType]` where `HandType = (r1_idx, r2_idx, suited)`
- r1_idx/r2_idx use RANKS index: `A=0, K=1, Q=2, J=3, T=4, ..., 2=12`
- Pockets stored with `suited=True` (actual suit doesn't matter)
- Precomputed via `build_range_pool()` — O(n²) once per call, not per simulation
- Monte Carlo uses `random.choice(pool)` for O(1) range sampling
