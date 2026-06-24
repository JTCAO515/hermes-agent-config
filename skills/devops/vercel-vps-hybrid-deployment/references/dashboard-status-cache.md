# Cron-Driven Dashboard Status Cache

A reusable pattern for keeping Vercel-VPS hybrid dashboard data fresh without overloading the API.

## Pattern

```
Cron (every 6h)
    ↓ runs
dashboard-status.py  ← collects git logs, sessions, errors, memory
    ↓ writes JSON
~/.hermes/data/dashboard/status.json  ← static cache file
    ↓ served via
hermes-api.py GET /api/hermes/all → dashboard_status field
    ↓ consumed by
index.html (Vercel frontend) — task history, issues, sessions cards
```

## Why not live API calls?

- **Efficiency**: Git log greps and SQLite queries take 3-10s. Doing this per-request would make the dashboard slow.
- **Batching**: Multiple data sources (every project's git, multiple DBs) → collect once, serve many.
- **Offline resilience**: Dashboard still shows data even if some sources are temporarily unavailable.

## Key Design Decisions

### Timestamps are mandatory
Every data point MUST include a unix timestamp (`timestamp: int`) for reliable client-side sorting. Human-readable "2 hours ago" strings cannot be sorted programmatically.

```python
# ✅ Correct: include both for display and sorting
commits = run_lines(f"cd {proj_dir} && git log --format='%h|%s|%at|%ar' ...")
for line in commits:
    parts = line.split("|")
    if len(parts) >= 4:
        items.append({
            "message": parts[1],
            "timestamp": int(parts[2]),     # sortable
            "time": parts[3],               # human-readable
        })
```

### All lists must be newest-first
User expects **every** chronological list to start with the most recent item — this applies equally to Recent Activity, Task History, Cross-Project Issues, and Sessions. Not just one list. Apply sort at ALL THREE levels:

1. **Cron generator** (`dashboard-status.py`): sort before writing to cache
   ```python
   sorted(get_cross_project_issues(), key=lambda x: x.get("timestamp", 0), reverse=True)[:30]
   ```

2. **API server** (`hermes-api.py`): sort live-fetched data
   ```python
   recent.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
   ```

3. **Frontend safety net** (`index.html`): re-sort client-side as defensive measure
   ```javascript
   items.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
   ```

This triple-layer approach handles three failure modes:
- **Layer 1 miss**: cron data arrives unsorted — frontend still gets it right
- **Layer 2 miss**: live API returns data in wrong order — frontend fixes it
- **No timestamp field**: sort falls back to `0` (items without timestamps sink to bottom, not crash)

### Cache location
Store under `~/.hermes/data/dashboard/status.json` — central location discoverable by both cron and API.
No need for data duplication.

## Cron Setup

```bash
# Place script (symlink or copy) in ~/.hermes/scripts/
cp /path/to/dashboard-status.py ~/.hermes/scripts/dashboard-status.py

# Cron: every 6 hours
# Use Hermes cron system via cronjob tool
# Schedule: 0 */6 * * *
```

## Related
- `vercel-vps-hybrid-deployment` — full deployment architecture
- References: `references/server-topology.md`