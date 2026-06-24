# WC26 Backtest Baseline (2026-06-18)

## Model Configuration

| Parameter | Value |
|-----------|-------|
| parameter_set | default |
| scoreline_model | bivariate_poisson |
| max_goals | 10 |
| shared_lambda | 0.14 |
| model_confidence | 0.84 |
| risk_modifier | 0.86 |
| minimum_xg | 0.20 |

## Results

| Metric | Value |
|--------|-------|
| **Total matches** | 104 |
| **Played matches** | 32 |
| **Brier WDL** | **0.68824** |
| **Brier O/U 2.5** | **0.46754** |
| Future records (leakage) | 55 |
| Visible market odds | 8 |

### Brier Score Interpretation

- **0.0** = perfect prediction
- **0.25** ≈ random guessing (3-way WDL)
- **0.33** ≈ always picking the most common outcome
- **0.5** = coin flip
- **1.0** = always wrong

Current baseline (WDL 0.69) is above random guessing. Pure Poisson models are better at scoreline distributions than match outcome direction. Expected improvement areas:
- Incorporating market odds (only 8/32 matches had visible odds)
- Better xG estimates
- Lineup confidence adjustments

## Last 5 Played Results (as of 2026-06-18)

| Team A | Score | Team B |
|--------|-------|--------|
| Côte d'Ivoire | 1-0 | Ecuador |
| Canada | 1-1 | Bosnia and Herzegovina |
| Switzerland | 1-1 | Qatar |
| Tunisia | 1-5 | Sweden |
| Japan | 2-2 | Netherlands |

## Result Format Note

`wc2026_matches.json` stores results with dual key formats:
- `team_a_goals` / `team_b_goals` — used by `backtest.py`
- `home_score` / `away_score` — used by `odds_engine.py`

Both are written by `fifa_sync.py`. Verify with:
```bash
python3 -c "
import json
m = json.load(open('data/wc2026_matches.json'))
both = sum(1 for mt in m['matches'] if mt.get('result') and 'team_a_goals' in mt['result'] and 'home_score' in mt['result'])
print(f'Dual-format results: {both}')
"
```
