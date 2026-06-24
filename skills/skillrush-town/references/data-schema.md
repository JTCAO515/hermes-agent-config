# ClawHub Snapshot JSON Schema

This document describes the JSON structure of snapshot files
(`data/snapshots/YYYY-MM-DD.json` and `data/latest.json`)
so agents can parse them without probing the keys each time.

## Top-Level Keys

| Key | Type | Description |
|-----|------|-------------|
| `snapshot_date` | str | e.g. `"2026-05-30"` |
| `fetched_at` | str | ISO-8601 timestamp with timezone |
| `source` | dict | Request params: url, api, path, args, page_size, pages_requested, pages_succeeded |
| `source.diagnostics` | dict | Optional: e.g. fallback `get_api_v1_skills` response |
| `comparison_basis` | dict | Previous snapshot reference + diff semantics |
| `comparison_basis.previous_snapshot` | str | e.g. `"data/snapshots/2026-05-29.json"` |
| `comparison_basis.strict_daily` | bool | `true` if comparing consecutive days |
| `comparison_basis.note` | str | Human-readable note about comparison |
| `items` | list[dict] | **All ranked items** — this is the main data array |
| `limitations` | list[str] | Known issues with the snapshot |
| `dropped_items` | list[dict] | Items that existed in previous snapshot but are gone now |

There is NO `top10`, `top100`, `potential_skills`, or `new_entries` key.
These are **derived** from `items` by sorting and filtering.

## Item (dict inside `items`)

| Field | Type | Description |
|-------|------|-------------|
| `rank` | int | Current rank (1-based) |
| `name` | str | Skill display name |
| `author` | str | Author username |
| `slug` | str | Unique URL slug on ClawHub |
| `downloads_raw` | float | Raw download count (float from API) |
| `downloads` | int | Integer download count |
| `installs_raw` | float | Raw install count |
| `installs` | int | Integer install count |
| `stars_raw` | float | Raw star count |
| `stars` | int | Integer star count |
| `versions` | int | Number of published versions |
| `latest_version` | str | Version string (e.g. `"1.0.0"`) |
| `summary` | str | Truncated description (first ~120 chars) |
| `compare_key` | str | Stable dedup key (usually `slug`) — used for cross-snapshot matching |
| `prev_rank` | int or null | Previous rank. **null = new entry** (was not in previous snapshot). |
| `download_delta` | int | `downloads - previous_downloads` |
| `star_delta` | int | `stars - previous_stars` |
| `rank_change` | int | `prev_rank - rank` (positive = climbed, negative = fell, 0 = same) |

## Common Derived Queries

### Top10
```python
items[:10]
```

### Biggest download growth (outside Top10)
```python
sorted(items[10:], key=lambda x: -x.get('download_delta', 0))[:10]
```

### Biggest star growth
```python
sorted(items, key=lambda x: -x.get('star_delta', 0))[:30]
```

### New entries
```python
[i for i in items if i.get('prev_rank') is None]
```

### Biggest climbers (rank up)
```python
[i for i in items if i.get('rank_change', 0) > 0]
# sorted by -rank_change
```

### Biggest fallers
```python
[i for i in items if i.get('rank_change', 0) < 0]
# sorted by rank_change (ascending)
```

### Potential skills (per skill criteria)
```python
new_entries = [i for i in items if i.get('prev_rank') is None]
big_climbers = [i for i in items if i.get('rank_change', 0) >= 8]

# Download delta Top20
sorted_dl = sorted(items, key=lambda x: -x.get('download_delta', 0))[:20]
dl_top20_names = {i['name'] for i in sorted_dl}

# Star delta Top30
sorted_star = sorted(items, key=lambda x: -x.get('star_delta', 0))[:30]
star_top30_names = {i['name'] for i in sorted_star}

# Dual growth: items in both Top20 dl AND Top30 star
dual_growth = [i for i in items if i['name'] in dl_top20_names
               and i['name'] in star_top30_names]

# Combine: new entries + big climbers + dual growth, dedup by name, cap at 10
```

## Limitations Field Examples

```json
["Top100 不完整：本次只得到 99 条"]
["本次为首次运行，无历史对比"]
["无项目因任何原因被丢弃 (dropped_items 为空)"]
```
