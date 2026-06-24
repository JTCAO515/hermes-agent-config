# WC26 Quant Engine — Frontend Troubleshooting

The WC26 quant engine (`/api/wc/quant/*` endpoints) powers the **量化工具 (Quant Tools)** tab on `worldcup.jtcao.space`.

## Data Source Architecture (Critical)

The quant tab has **three distinct data sources** that must be kept consistent:

| Source | Endpoint | Purpose |
|--------|----------|---------|
| **Backtest** | `/api/wc/quant/backtest` | Historical simulation — 29 actual trades from model predictions on settled matches. **Must be used for KPI cards, 回测绩效, and 回测明细.** |
| **Portfolio** | `/api/wc/quant/portfolio` | Forward-looking optimization — expected return, signals for upcoming matches. **Use for signal table only, NOT for KPIs.** |
| **Arbitrage** | `/api/wc/quant/arbitrage` | Arbitrage scanning — cross-market surebet opportunities. **Independent, no overlap with others.** |

**Golden rule: All three sections that describe "results so far" must use the same backtest API call.** Never mix portfolio expected data with backtest realized data on the same panel.

### The 3-data-silo problem (v6.1.1 fix)

Until v6.1.1, the quant tab had a **fourth data source**: the Bet Journal (`/api/wc/quant/journal`), which stored manually recorded bets in a separate SQLite table. This meant:

- KPI cards → backtest API (-$2,088 / 29 bets)
- Bet journal → journal API (+$25 / 3 manual entries)
- Data could never reconcile

**Fix:** Replace the journal section with backtest detail:
1. Add `bets: list = field(default_factory=list)` to `BacktestResult` dataclass in `data/quant_engine.py`
2. Store `bets_log` (built during `run_backtest()`) in the result
3. API `/api/wc/quant/backtest` returns both aggregates + individual bets
4. Frontend `renderJournal()` → fetches from `/api/wc/quant/backtest`, renders individual bets table
5. Remove `journalAddBet()`, `journalSettle()`, `journalDelete()` functions
6. Remove journal add form / stats cards HTML

Now all three display sections (KPI, 回测绩效, 回测明细) read from the same `Promise.all` response at line 919 of `app.js`.

---

## Bug 1: Stale Cache Lock Prevents Re-fetch

**Symptom:** Sliding the date range slider or clicking refresh doesn't re-fetch quant data. Page refresh fixes it temporarily.

**Root cause:** `app.js` `renderQuant()` function had a guard at the top:
```javascript
// BAD — prevents re-fetch after initial load
if (quantSignalsData.length > 0) return;
```

This assumed `quantSignalsData` was a one-time load. After the initial fetch populated it, every subsequent call (slider change, refresh) hit the guard and returned immediately.

**Fix:** Remove the guard or replace with a force-refresh flag:
```javascript
function renderQuant(forceRefresh) {
  if (!forceRefresh && quantSignalsData.length > 0) return;
  // ... rest of function
}
```

**Location:** `~/projects/world-cup-edge-lab/web/app.js`, look for `quantSignalsData.length > 0`.

## Bug 2: KPI Data Source Mismatch

**Symptom:** Top KPI cards (e.g. "预期收益 +$11,040 / +46.33%") disagreed with the "回测绩效" (backtest performance) section below ("回测净值 -$2,088 / -21.5%").

**Root cause:** Two different API endpoints feeding the same page:
- Top KPI cards used `/api/wc/quant/portfolio` → **expected** (forward-looking) data
- Backtest performance used `/api/wc/quant/backtest` → **realized** (historical) data

**Fix:** Change KPI data source from portfolio API to backtest API:
```javascript
fetch('/api/wc/quant/backtest').then(r => r.json()).then(btData => {
  // btData.total_bets, btData.net_profit, btData.roi_pct
  updateKpiCards(btData);
});
```
If backtest data is empty, fall back to portfolio data but show "(预期)" label.

## Bug 3: Bet Journal Data Silo (v6.1.1)

*See "The 3-data-silo problem" above for full details.*

**Symptom:** 下注记录 section showed +$25 from journal API while all other quant data showed -$2,088.

**Root cause:** Separate journal API using a manually populated SQLite table. This was the only quant section not reading from the backtest.

**Fix steps:**
1. `data/quant_engine.py` — Add `bets` field to `BacktestResult` dataclass with `field(default_factory=list)`
2. `run_backtest()` — Pass `bets=bets_log` to the returned BacktestResult
3. `api/index.py` — Add `"bets": getattr(bt, "bets", [])` to backtest endpoint response
4. `web/index.html` — Replace "下注记录" section with simplified "回测明细" table (8 cols, no forms)
5. `web/app.js` — Rewrite `renderJournal()` to fetch from `/api/wc/quant/backtest`; delete `journalAddBet()`, `journalSettle()`, `journalDelete()`

## Related Endpoints

| Endpoint | Data | Purpose |
|----------|------|---------|
| `/api/wc/quant/portfolio` | Expected return | Forward-looking, NOT for KPI cards |
| `/api/wc/quant/backtest` | Realized return + individual bets | **Use for KPI + 回测明细** |
| `/api/wc/quant/arbitrage` | Arbitrage opportunities | Independent |
| `/api/wc/quant/journal` | (Removed v6.1.1) | Was manual bet journal |

## Pitfalls

- **Don't cache in global state** — `quantSignalsData.length > 0` guards break slider/refresh
- **Don't use expected data for realized KPIs** — portfolio API shows future predictions, not past performance
- **Don't introduce separate data sources** — every quant sub-section must trace to one of the three canonical endpoints
- **Version numbers** — update in 4 places in `index.html` (title, nav-title, nav-badge, loading-text) + `api/index.py` `/api/version`
- **`_multiply_showcase()` walks nested dicts** — when adding new fields to backtest response, ensure monetary keys (containing 'stake', 'profit', 'bankroll', 'return', 'invest') are correctly multiplied for display
- **Dataclass mutable defaults** — `BacktestResult` is a `@dataclass`. New list fields must use `field(default_factory=list)` not `= []`
