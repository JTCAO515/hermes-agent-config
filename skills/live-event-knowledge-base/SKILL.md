---
name: live-event-knowledge-base
version: 1.0.0
description: |-
  Build a structured, multi-dimensional knowledge base about a live or upcoming
  event (sports tournament, election, awards show, financial event) for use in
  a prediction or analysis product. Performs parallel web research across all
  relevant dimensions, cross-references sources, tracks temporal vs static info,
  and structures output for direct model consumption.
triggers:
  - "build a knowledge base about"
  - "knowledge base for prediction"
  - "research the tournament"
  - "who's playing in"
  - "comprehensive guide to"
  - "赛事知识库"
  - "赛程/队伍资料"
  - "建立一个关于...的知识库"
  - "预测模型需要的数据"
tools:
  - web_search
  - web_extract
  - write_file
  - read_file
mutating: true
---

# Live Event Knowledge Base

Build a comprehensive, structured knowledge base about a live or upcoming event
by doing multi-dimensional parallel web research. Designed specifically for
prediction/analysis products that need structured domain data as model input.

## When to Use

- User says "build a knowledge base about X for prediction/analysis"
- User wants to research a sports tournament, election, awards show, or financial event
- User needs structured data for a prediction model (teams, odds, schedules, context)
- Trigger words: "知识库", "赛事", "赛程", "预测需要的资料", "comprehensive guide"

Do NOT use for: single-answer questions, general curiosity research, or deep-dive
on a single dimension (those go to `data-research` or `perplexity-research`).

## Phase 1: Identify All Research Dimensions

Before searching, identify the complete set of dimensions needed for this event type.

### Sports Tournament Example (from 2026 World Cup session)
| # | Dimension | Data Needed | Sources Used |
|---|-----------|-------------|-------------|
| 1 | **Tournament Basics** | Format, dates, hosts, rules, prize money | FIFA.com, Wikipedia, ESPN |
| 2 | **Venues/Logistics** | Stadiums, capacities, locations (for travel/climate impact) | FIFA Venues page, StadiumDB |
| 3 | **Participants** | All teams/entrants, groups/seeding | Wikipedia, FIFA qualified list |
| 4 | **Squad Details** | Key players, captains, coaches, age extremes, debutants | Wikipedia squad page, ESPN |
| 5 | **Current Status** | Already happened matches? Live scores? Standings? | FIFA scores, SofaScore, ESPN live |
| 6 | **Schedule** | All remaining matches, dates, venues, kickoff times | ESPN schedule, FIFA fixtures |
| 7 | **Market Odds** | Betting favorites, group odds, tournament winner odds | VegasInsider, DraftKings, FanDuel |
| 8 | **Storylines** | Legacy players, debuts, rivalries, notable absentees | News articles, analysis pieces |
| 9 | **Data Sources** | Where to get xG, stats, historical data for model | FBref, Understat, SofaScore, FIFA |
| 10 | **Models/Odds** | Existing prediction models, historical baselines | Betting previews, analysis articles |

### Election Example
| # | Dimension |
|---|-----------|
| 1 | Candidates and parties |
| 2 | Polling data (national/state) |
| 3 | Electoral system and rules |
| 4 | Key issues and voter sentiment |
| 5 | Campaign finance and endorsements |
| 6 | Historical voting patterns |
| 7 | Prediction markets |

### Awards Show Example
| # | Dimension |
|---|-----------|
| 1 | Nominees per category |
| 2 | Voting body and rules |
| 3 | Historical trends (who wins what) |
| 4 | Precursor awards results |
| 5 | Betting odds per category |
| 6 | Expert predictions |

## Phase 2: Temporal Awareness Check

**CRITICAL FIRST STEP:** Check if the event is already underway.

- Search "event name 2026 date" or "event name schedule 2026"
- If underway: prioritize current results/standings over pre-event analysis
- If future: focus on qualification status, team profiles, and pre-event data
- Tag every piece of data: `[confirmed]` vs `[speculative]` vs `[historical]`

**Live event trap:** When the user says "build a World Cup knowledge base" in June 2026,
the tournament may have already started. Default assumption should be CHECK FIRST.

## Phase 3: Parallel Web Search

Run searches for ALL dimensions simultaneously. Do not search sequentially —
this is the key efficiency gain.

**Search pattern per dimension:**
```
Search 1: "<event> <dimension1>"
Search 2: "<event> <dimension2>"
...
Search N: "<event> <dimensionN>"
```

### Pro tip: Source diversity
For sports tournaments, use at minimum:
- **Wikipedia** — comprehensive structured data (teams, groups, format, history)
- **FIFA.com** — official source for fixtures, results, standings
- **ESPN** — match schedule, betting odds, analysis
- **Betting sites** — VegasInsider, DraftKings, FanDuel for market odds
- **SofaScore** — real-time scores and live data

## Phase 4: Extract and Cross-Reference

For each dimension:
1. Extract structured data from the best source
2. Cross-reference against another source for verification
3. Flag discrepancies (different scores, dates, etc.)
4. Note when data is time-sensitive (odds change, standings update)

**For squads/team lists:** Use Wikipedia squad page — it's the most comprehensive
single source for player names, ages, captains, and debutants.

**For match results:** Use FIFA official site or ESPN — cross-reference with
SofaScore for live/real-time data.

## Phase 5: Structure for Prediction Model

The knowledge base should be structured so each section maps to a model input:

| KB Section | Model Input |
|------------|-------------|
| Team profiling | Expected goals (xG), attack/defense strength |
| Tournament format | Match count, group vs knockout model switch |
| Venue info | Home advantage, travel distance, climate |
| Odds data | Market probability → edge calculation |
| Recent results | Form rating, momentum factor |
| Squad depth | Injury/availability adjustments |
| Storylines | Narrative factor (last dance, debut) |

## Phase 6: Write the Knowledge Base

Structure as markdown with tiered headers. Include:

1. **Event Overview** — one table with key facts
2. **Venues** — if location matters for prediction
3. **Participants/Groups** — full list
4. **Current Status** — what has already happened (if live)
5. **Schedule** — what's coming next
6. **Market + Odds** — betting market consensus
7. **Storylines** — qualitative context
8. **Data Sources** — where to get ongoing/updated data
9. **Appendix** — raw extracted data tables

Style: tables for structured data, paragraphs for context. Keep it scanable.

## Pitfalls

- ❌ **Assuming the event hasn't started** — always check current date vs event dates
- ❌ **Single-source dependency** — cross-referencing catches errors
- ❌ **Stale odds** — betting odds fluctuate; note the snapshot date
- ❌ **Season context missing** — World Cup happens after club season; player fatigue matters
- ❌ **Ignoring the timezone** — schedules in local time vs user's timezone
- ❌ **No data source map** — the KB should tell future agents where to get updated data
- ❌ **Not noting debutants** — first-time participants have no historical data for the event
- ❌ **Over-relying on FIFA rankings** — they don't always reflect current form
- ❌ **Single-bookie odds dependency** — odds vary between sportsbooks; check 2-3 (FanDuel/DraftKings/VegasInsider) to get a market consensus range rather than a single book's margin
- ❌ **One-model-fits-all-stages** — group-stage and knockout-stage matches behave differently. Groups: more variance, lower-scoring draws common, weaker teams park the bus. Knockouts: smaller teams get eliminated, stronger teams face each other, extra time alters fatigue dynamics. A Poisson model calibrated on group data will systematically misprice knockout matches. The KB should flag which stage each data point belongs to.
- ❌ **Ignoring host/venue climate** — co-hosted events (USA/Mexico/Canada in 2026) span different climates: altitude in Mexico City (~2,250m), humidity in Miami/Houston, potential rain in Seattle/Vancouver. These affect expected goals and should be noted for xG model adjustments.
- ❌ **Only team-level data, no context** — raw xG numbers without context (friendlies vs qualifiers, B squad vs A squad, pre-tournament rust) lead to stale model inputs. Tag each data point with match type and squad strength if available.

## Verification

After writing, check:
- [ ] Are there confirmed matches/results? Verify against 2+ independent sources
- [ ] Are the dates and times correct? (timezone conversion)
- [ ] Is the format/structure right? (48 teams → 12 groups of 4, not 16 groups of 3)
- [ ] Are betting odds from the right timeframe?
- [ ] Does every section map to a model input or qualitative context?
- [ ] Is the data source list actionable (not just URLs, but what to scrape)?

## Post-KB: What Comes Next

After the knowledge base is built, the prediction product workflow follows this
pipeline:

```
KB ──▶ Model Calibration ──▶ Live Prediction ──▶ Validation Loop ──▶ Iterate
```

### 1. Model Calibration
- Extract team attack/defense parameters from KB data (xG/90, xGA/90)
- Apply venue/home adjustments (altitude, climate, crowd)
- Apply squad availability modifiers (key player injuries)
- Calibrate baseline lambda values for Poisson model

### 2. Live Prediction
- For upcoming matches: run calibrated model → output probability matrix
- Compare to market odds (from KB odds section) → compute Edge
- Generate recommendation: strong/medium/weak/watch/avoid
- Timestamp every prediction for future validation

### 3. Validation Loop
- After each match result: compare predicted probability vs actual outcome
- Compute Brier Score (overall calibration) and log loss
- Flag systematic biases (overrating favorites? underrating hosts?)
- Update calibration parameters for next match

### 4. Data Freshness Rules
| Data Type | Update Frequency | Source |
|-----------|-----------------|--------|
| Match results | Immediately after FT | FIFA/ESPN/SofaScore |
| Standings | After each matchday | FIFA |
| Knockout bracket | After each round | FIFA |
| Player availability | Daily (injury news) | News/betting sites |
| Market odds | Daily (snapshot) | Betting sites |

### 5. Model Tuning for Tournament Stage

| Stage | Model Behavior | Adjustment |
|-------|---------------|------------|
| Group stage (Matchday 1) | High uncertainty, no in-tournament form data | Use pre-tournament xG/qualifying data; widen confidence intervals |
| Group stage (Matchday 2-3) | In-tournament form emerges | Blend pre-tournament data with tournament results (weighted) |
| Knockout stage | Lower variance, stronger teams, potential ET/pens | Reduce shared_lambda correlation bias; add extra-time fatigue penalty |
| Final | Smallest sample, highest pressure | Use full tournament data + historical final patterns |

## Debutant Team Handling

Teams with no World Cup history (e.g. Cape Verde, Curaçao, Jordan, Uzbekistan
in 2026) have no in-event baseline. Use these workarounds:

1. **Qualifying data as baseline** — their most recent competitive matches (last
   12 months) are the best proxy for current strength
2. **xG from club-level players** — if key players play in top European leagues,
   use their club xG as a signal (adjusted for opponent strength difference)
3. **Wider confidence intervals** — debutant predictions should have ±30-50%
   wider uncertainty bands than established teams
4. **ELO-based fallback** — use global ELO ratings (eloratings.net) as a
   secondary signal when FIFA ranking is unreliable

## References

See `references/tournament-session-2026wc.md` for the full session trace from
the 2026 World Cup knowledge base build — shows the exact search queries,
source URLs, and cross-referencing decisions made.

See `references/stage-specific-model-tuning.md` for detailed model parameter
adjustments per tournament stage (group matchday 1/2/3, knockout rounds,
final) — including shared_lambda, lineup_impact_multiplier, and
data_freshness_weight values used in the 2026 World Cup Edge Lab project.
