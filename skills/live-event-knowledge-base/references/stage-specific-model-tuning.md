# Stage-Specific Model Tuning

> Derived from: 2026 World Cup Edge Lab (JTCAO515/26-WorldCup-Edge)
> Tournament: June 11 – July 19, 2026 (48 teams, 12 groups, 104 matches)

## Model Architecture (from world-cup-edge-lab)

The core model is a **bivariate Poisson distribution** with configurable
shared-lambda correlation factor. It takes team attack strength (xG/90) and
opponent defense strength (xGA/90) to produce a full scoreline probability
matrix (0-0 through 10-0+), then aggregates to WDL and O/U 2.5 probabilities.

```python
# Pseudocode
P(X=x, Y=y) = (λ1^x * e^-λ1 / x!) * (λ2^y * e^-λ2 / y!) * f(ρ, x, y)
# where λ1 = home_attack_strength * away_defense_weakness * λ_cov
#       λ2 = away_attack_strength * home_defense_weakness * λ_cov
```

## Parameter Defaults

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `shared_lambda` | 0.15 | 0.0–0.5 | Correlation between team scores (0=independent) |
| `lineup_impact_multiplier` | 1.0 | 0.5–2.0 | Scale factor when a key player is missing |
| `minimum_xg` | 0.3 | 0.1–0.8 | Floor for any team's expected goals |
| `risk_modifier` | 1.0 | 0.5–1.5 | Multiplier on Kelly fraction for bet sizing |

## Stage-Based Tuning

### Group Stage — Matchday 1

**Characteristics:**
- No in-tournament form data available
- Teams may be rusty (club season ended 2-4 weeks ago)
- Conservative play common (don't want to lose first match)
- Host teams have significant crowd advantage

**Recommended settings:**
- `shared_lambda`: 0.10 (lower — more independence early on)
- `lineup_impact_multiplier`: 1.2 (higher — first-choice lineup matters more)
- `minimum_xg`: 0.4 (higher floor — conservatism inflates lower team)
- Data source weight: 80% pre-tournament / 20% no-tournament-data-yet
- **Confidence intervals wider** — ±15-20% on probability estimates
- Host advantage: +0.15-0.25 xG boost for home nation

### Group Stage — Matchday 2

**Characteristics:**
- One match of tournament form available per team
- Winners want to secure qualification; losers are desperate
- Elimination math starts mattering (goal difference)
- Higher variance — desperation leads to chaotic matches

**Recommended settings:**
- `shared_lambda`: 0.12
- `lineup_impact_multiplier`: 1.0 (default)
- Blend: 60% pre-tournament / 40% tournament form
- Watch for **red-card risk** — desperation teams commit more fouls
- Confidence intervals: ±12-15%

### Group Stage — Matchday 3

**Characteristics:**
- Simultaneous kickoffs (synchronized for fairness)
- Some teams already qualified (may rotate squad)
- Complex qualification scenarios (GD, H2H, fair play tiebreakers)
- High variance — dead rubber matches vs must-win battles

**Recommended settings:**
- `shared_lambda`: 0.15 (default)
- `lineup_impact_multiplier`: 1.3 (higher — rotation matters more)
- Blend: 40% pre-tournament / 60% tournament form
- **CRITICAL: Check qualification scenarios** — a team needing a draw plays
  differently from a team needing a win
- Flag dead rubber matches separately (lower confidence, may be unpredictable)
- Confidence intervals: ±15-20%

### Round of 32 (New for 2026!)

**Characteristics:**
- First knockout round in the expanded format
- Some third-place qualifiers may be tired (played 3 hard group matches)
- Group winners face potentially weaker opponents
- Extra time possible (30 min + pens)
- Debutant teams may be overwhelmed by knockout pressure

**Recommended settings:**
- `shared_lambda`: 0.18 (higher — knockout correlation increases)
- `lineup_impact_multiplier`: 1.0
- Source: 70% tournament form / 30% pre-tournament
- Add **extra-time fatigue factor**: -0.05 xG per team in ET periods
- Add **penalty lottery factor**: ±5% variance on very close matchups
- Confidence intervals: ±10-12%

### Round of 16

**Characteristics:**
- Strong teams start to face each other
- Group winners largely eliminated weakest third-place teams
- Tactical conservatism increases (one mistake ends tournament)
- Extra time common in tight matches

**Recommended settings:**
- `shared_lambda`: 0.20
- ET fatigue factor: -0.08 xG
- Source: 80% tournament form / 20% pre-tournament
- Confidence intervals: ±8-10%

### Quarterfinals

**Characteristics:**
- Top 8 teams — lowest variance matchups
- Experience matters: teams with deep tournament history have edge
- Media pressure intensifies
- Refs may be more conservative (fewer cards?)

**Recommended settings:**
- `shared_lambda`: 0.22
- Reduce `minimum_xg` to 0.25 (these are elite attacks, no floor needed)
- Add **experience factor**: +0.05 xG for teams with 3+ QF appearances in
  last 10 years
- Confidence intervals: ±8%

### Semifinals

**Characteristics:**
- One match from the final
- Most conservative play of the tournament
- Usually low-scoring, tight margins
- Fatigue is real — players have played 5-6 matches in 5 weeks

**Recommended settings:**
- `shared_lambda`: 0.25
- ET fatigue factor: -0.10 xG
- Add **fatigue decay**: reduce team xG by 3% per accumulated match minute
  beyond 450' (5 full matches)
- Confidence intervals: ±8%

### Final

**Characteristics:**
- Single biggest match in world football
- Extreme conservatism first 30-45' (feeling out)
- Either a tight 1-0/2-1 or a surprise blowout
- Penalties are 25-30% likely
- Narrative factors (last dance for legends, first title for debutants)

**Recommended settings:**
- `shared_lambda`: 0.28 (highest correlation — both teams react to each other)
- First 30-minute adjustment: reduce combined xG by 15%
- ET fatigue factor: -0.12 xG
- Penalty probability: weighted by historical final frequency (not group match)
- **Narrative adjustment**: +0.08 xG for teams with generational players in
  likely last tournament (Messi 2026, Ronaldo 2026 are examples)
- Confidence intervals: ±10% (final is inherently less predictable)

## Odds-to-Probability Conversion (for Edge Calculation)

```python
# Basic: Remove bookmaker margin
def de_dutch(odds):
    implied = [1/o for o in odds]  # 1/decimal_odds
    margin = sum(implied) - 1
    fair = [p / (1 + margin) for p in implied]
    return fair

# For 1X2: separate home/draw/away
# For O/U 2.5: binary, simpler margin removal
# For Asian Handicap: use Poisson matrix directly instead
```

## Data Freshness Weight Decay

```python
# Weight decays linearly from match day to today
# Formula: weight = max(0, 1 - (days_since / decay_window))
DECAY_WINDOW = 60  # days — older data gets zero weight

# Tournament-specific:
# - Pre-2026 friendlies: full decay (weight by recency)
# - Qualifying matches (2024-2025): less decay (competitive)
# - 2022 World Cup: included only for teams with no 2026 data
```

## Key Assumptions for the 2026 World Cup

1. **Host advantage is real** — Mexico at Azteca (+0.2 xG), USA at SoFi (+0.15),
   Canada at BC Place (+0.1). Spread across 3 time zones.
2. **Altitude matters** — Mexico City (2,250m) vs sea level. Visiting teams get
   a -5% xG penalty in the first 60 minutes.
3. **Debutant volatility** — Cape Verde, Curaçao, Jordan, Uzbekistan have no
   World Cup data. Use CAF/AFC/CONCACAF qualifying + ELO as proxy.
4. **Messi/Ronaldo factor** — generational players can single-handedly change
   match outcomes. Add +0.05 xG when on the pitch in knockout stages.
5. **European season timing** — World Cup is in June-July (summer), not
   November-December (winter like 2022). Players are well-rested after club
   season, not mid-season fatigued.
