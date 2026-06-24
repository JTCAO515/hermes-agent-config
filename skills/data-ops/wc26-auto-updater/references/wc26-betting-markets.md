# WC26 Betting Markets — Poisson-Derived Multi-Market System

> Added in V3.2. Extends `aggregate_markets()` in `football_predictor/scorelines.py`.
> All markets are derived mathematically from the scoreline probability matrix — no external odds required.

## Market Types & Derivation

| Market | Derivation | Data Key | Frontend |
|--------|-----------|----------|----------|
| **1X2 (WDL)** | Sum `P(goals_a > goals_b)`, `P(=)`, `P(<)` | `team_a_win` / `draw` / `team_b_win` | 🎯 WDL bar |
| **Over/Under 0.5–4.5** | Sum `P(total_goals > line)` vs complement | `ou_05`–`ou_45` each `{over, under}` | 🎯 OU table |
| **Both Teams to Score** | Sum `P(goals_a>0 & goals_b>0)` vs complement | `btts` `{yes, no}` | 🎯 BTTS bar |
| **Double Chance** | WDL pairwise sums: 1X, X2, 12 | `double_chance` `{1X, X2, 12}` | 🎯 DC cards |
| **Draw No Bet** | WDL after removing draw, renormalized | `draw_no_bet` `{1, 2}` | API only |
| **Exact Scores** | Sort all matrix cells by probability, take top 15 | `exact_scores` `[{score, probability}]` | 🎯 Scores grid (top 8) |
| **Total Goals Distribution** | Group probability by total goals (0,1,2,3,4,5,6+) | `total_goals` `{"0":.., "6p":..}` | 🎯 TG bars |

## API Endpoint

```
GET /api/wc/markets?pm_weight=0.3
→ { count: N, matches: [{ id, team_a, team_b, has_result, kickoff, group, expected_goals, markets }]}
```

The `markets` field contains the full output of `aggregate_markets()` for the last checkpoint.

## Backward Compatibility

The existing `probabilities` field in checkpoints still contains only `{team_a_win, draw, team_b_win, over_2_5, under_2_5}`.
The expanded market data lives in a separate `markets` field on the checkpoint dict.

## Implementation Files

| File | Change |
|------|--------|
| `football_predictor/scorelines.py` | `aggregate_markets()` — expanded from 5→13 field returns |
| `football_predictor/backtest.py` | `_checkpoint_report()` — added `markets` field, `basic_probs` for compat |
| `api/index.py` | New `GET /api/wc/markets` endpoint |
| `web/index.html` | New `🎯 市场` tab button + section |
| `web/app.js` | `renderMarkets()`, `renderMarketCard()`, filter event handlers |
| `web/app.css` | `.mkt-*` component styles |

## Frontend Architecture (v3.3+)

Since v3.3, the standalone Markets tab has been **removed**. Markets are now rendered **inline** inside each schedule card via an expand/collapse toggle.

### How it works

1. **`renderSchedule()`** in `app.js` is the entry point
2. After grouping matches by date (today-first), it calls **`fetchMarketsInline()`** — an async function that fetches `/api/wc/markets?pm_weight=0.3` once and builds a `{ match_id → markets }` lookup map
3. Each match card has a `.schedule-match-main` div with `onclick` toggling `.schedule-markets--open` on the sibling `.schedule-markets` div
4. When expanded, each card shows same 7 market types as before: WDL bar → OU table → BTTS → DC → Exact Scores → Total Goals

### Key differences from standalone tab

| Aspect | Old (v3.2) | New (v3.3+) |
|--------|-----------|------------|
| Tab | Separate `🎯 市场` tab | Inline in `📅 赛程` |
| Data fetch | Lazy on tab switch | Eager inside `renderSchedule()` | 
| Filter | `data-market` buttons: all/ou/btts/dc/scores | None (all markets always shown) |
| Layout | One card per match, full-width | Nested inside schedule date groups |
| Toggle | Always visible | Hidden by default, click to expand |
| Played matches | Excluded | Included (no expand, shows score) |

### Expand/collapse implementation

```javascript
// In renderSchedule() template
const mkId = 'mkt-' + m.id.replace(/[^a-zA-Z0-9]/g,'');

// The onclick controls the expand/collapse
`<div class="schedule-match-main" onclick="
  document.getElementById('${mkId}').classList.toggle('schedule-markets--open')
">`

// Markets div starts hidden
`<div class="schedule-markets" id="${mkId}">`
```

CSS:
```css
.schedule-markets { display: none; }
.schedule-markets.schedule-markets--open { display: block; }
```

### Async data flow

`fetchMarketsInline()` is called inside `renderSchedule()`, which means there's a brief moment when the schedule DOM renders before markets data arrives. The markets sections are initially empty (no OU/BTTS/DC data) until the promise resolves. This is acceptable because:
- The WDL bar is derived from `predictionsData` (always available), not from the markets endpoint
- The markets data only fills the expandable sections below the fold
- The fetch typically resolves within the same frame as render

### Related CSS

All `.mkt-*` styles are defined in `app.css` and shared between the old standalone tab and the new inline rendering. The expandable-specific additions:

- `.schedule-match-main` — clickable row
- `.schedule-match-expand` — ▾ arrow (rotates on open via CSS)
- `.schedule-match-wdl` / `.wdl-bar-*` — mini WDL bar shown inline before expand
- `.schedule-markets` / `.schedule-markets--open` — expand/collapse
