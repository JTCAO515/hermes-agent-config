# Dashboard Status Aggregation — Reference Implementation

## Architecture

```
cron (0 */6 * * *)
  └── ~/.hermes/scripts/dashboard-status.py
        ├── Git: sweep ~/projects/ for fix/bug commits + dirty repos
        ├── Sessions: query ~/.hermes/state.db for recent sessions
        ├── Cron: read cron output dirs for task history
        ├── Errors: read error logs
        ├── Scrub PAT/tokens from output
        └── Write: ~/.hermes/data/dashboard/status.json
                            │
hermes-api.py (:8504)       │
  └── /api/hermes/all        │
        ├── system           │
        ├── hermes           │
        ├── projects         │
        ├── services         │
        ├── recent           │
        ├── soul_md          │
        ├── agents_md        │
        └── dashboard_status └── reads cached JSON
                                ├── task_history (30 items)
                                ├── cross_project_issues (48 items)
                                ├── recent_sessions (10 items)
                                ├── memory (0 items — see note)
                                └── errors
```

## Key Implementation Details

### Git Issue Detection

```python
# Look for TODO/FIXME/BUG/HACK in recent commit messages
for proj_name in sorted(os.listdir(PROJECTS_DIR)):
    commits = run_lines(f"cd {proj_dir} && git log --all --oneline -20 --grep='fix\\|bug\\|error\\|hotfix\\|patch\\|issue'")
    
    # Check for uncommitted changes (dirty repos)
    status = run(f"cd {proj_dir} && git status --short")
```

### Session Query

```python
cur.execute("""
    SELECT s.id, s.source, MIN(m.id), MAX(m.id), COUNT(m.id)
    FROM sessions s
    JOIN messages m ON m.session_id = s.id
    GROUP BY s.id
    ORDER BY MAX(m.id) DESC
    LIMIT 10
""")
```

### Data Scrubbing

The script must NOT log or write PAT tokens, API keys, or secrets. The git log scraping only reads commit messages (not code diffs), which naturally avoids most secrets. If extending the script to read diffs, add a PAT regex filter.

## Known Limitations

1. **Memory entries**: Hermes stores memory via the `memory` tool (not as files). The current script shows 0 memory entries because state_meta doesn't expose them. To properly display memories, extend the script to use the Hermes memory API instead of SQLite queries.

2. **False positives in issues**: `git log --grep='fix\|bug'` catches commits where the author uses "fix" as an adjective or includes "bug" in a feature description. Consider filtering to case-insensitive only standalone "fix:" or "bug:" patterns.

3. **Cross-project linking**: The current implementation only reports per-project issues independently. Cross-project bugs (e.g., WC26Nami depends on WC26 data schema) require manual `references/` annotations or a dependency manifest.

## Frontend Cards

| Card | Purpose | JS Function |
|------|---------|-------------|
| Agent Identity | SOUL.md sections summary + version | `data.soul_md` |
| Persistent Memory | Recent sessions + memory keys | `data.dashboard_status.memory + .recent_sessions` |
| Task History | Git commits + cron outputs timeline | `data.dashboard_status.task_history` |
| Cross-Project Issues | Fix commits + dirty repo alerts | `data.dashboard_status.cross_project_issues` |

## Cron Setup

```bash
# Copy script (NOT symlink — cron rejects symlinks outside scripts dir)
cp /path/to/dashboard-status.py ~/.hermes/scripts/dashboard-status.py

# Create cron job via Hermes cron tool
# Schedule: 0 */6 * * *  (every 6 hours)
# Script: dashboard-status.py
# Deliver: local
```
