# Skillpack Health Check

> Absorbed from standalone `skillpack-check` skill (2026-06-02).

## Command

```bash
gbrain skillpack-check
```

Returns JSON with:
- `healthy` (bool) — true if no action needed
- `summary` (string) — one-line summary
- `actions` (string[]) — remediation commands to run
- `doctor` — `gbrain doctor --fast --json` output
- `migrations` — applied/pending/partial counts

## Exit Codes

- `0` — healthy
- `1` — action needed (read `actions[]`)
- `2` — could not determine (binary crash, investigate)

## When to Run

- **Daily cron**: `gbrain skillpack-check --quiet` (exit code only)
- **On demand**: for full JSON when debugging
- **After container restart**: bootstrap health check

## Common Actions

| Action | What it means |
|--------|--------------|
| `gbrain apply-migrations --yes` | Migration pending or half-finished |
| `gbrain embed --stale` | Embeddings are stale |
| `gbrain check-backlinks --fix` | Dead links or missing back-links |
