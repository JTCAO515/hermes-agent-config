# WC26 — Daily Auto-Update Cronjob

> Setup in v3.4. Runs daily at 13:00 UTC (afternoon) and/or 23:30 UTC (end-of-day).
> Two-stage pipeline: real scores from Nami API → simulation for upcoming match days → cross-project sync → push.

## Cronjob Configuration

- **Name:** WC26 每日赛果自动更新
- **Schedule:** `30 13 * * *` (13:30 UTC afternoon run) + `30 23 * * *` (23:30 UTC end-of-day)
- **Hermes cron handler:** Uses Hermes Agent cron system (see `~/.hermes/config.yaml` cron entries)
- **Workdir:** `/home/ubuntu/projects/WC26-Nami` (source of truth)
- **Git companion repo:** `/home/ubuntu/projects/WC26-Main` (git repo, origin `git@github.com:JTCAO515/WC26-Main.git`)
- **Stale static copy:** `/home/ubuntu/projects/world-cup-project/updated/world-cup-edge-lab/data/` (NOT a git repo — file copy only, no push)

## Two-Stage Update Pipeline

### Stage 1 — Real scores from Nami API (`data/nami_sync.py`)

```bash
cd /home/ubuntu/projects/WC26-Nami
python3 data/nami_sync.py
```
Fetches completed matches from Nami API (`match/live/history`), overwrites local `wc2026_matches.json` with real results.
On success it reports "已更新 X 场赛果" and the "当前已赛: N 场" count.

### Stage 2 — Simulation for next day (`data/update_results.py`)

```bash
python3 data/update_results.py
```
Simulates results for matches past kickoff with no result yet (bivariate Poisson model).

### Stage 3 — Cross-project sync (two targets)

```bash
# Target 1 — Git companion repo (WC26-Main, main edge-lab project)
cp /home/ubuntu/projects/WC26-Nami/data/wc2026_matches.json \
   /home/ubuntu/projects/WC26-Main/data/wc2026_matches.json

# Target 2 — Stale static copy (no git, file-only archive)
cp /home/ubuntu/projects/WC26-Nami/data/wc2026_matches.json \
   /home/ubuntu/projects/world-cup-project/updated/world-cup-edge-lab/data/wc2026_matches.json
```

### Stage 4 — Push both repos (only git repos)

```bash
# Push WC26-Nami (default branch: master) — add only changed data files
cd /home/ubuntu/projects/WC26-Nami
git add data/nami_team_map.json data/update_log.json data/wc2026_matches.json
git commit -m "每日数据更新 $(date +%Y-%m-%d): 纳米数据真实赛果 + 模拟更新"
git push origin master

# Push WC26-Main companion repo (default branch: master)
cd /home/ubuntu/projects/WC26-Main
git add data/wc2026_matches.json
git commit -m "每日数据更新 $(date +%Y-%m-%d): 同步WC26-Nami最新赛果数据"
git push origin master
```

> ⚠️ **Both repos use `master` as default branch, NOT `main`.** `git push origin main` will fail with "src refspec main does not match any".
> 
> ✅ Prefer specific file adds over `git add -A` to avoid accidental commits of pycache, temp files, or test outputs.

## How `update_results.py` Works

1. Loads `data/wc2026_matches.json`
2. Finds matches where `kickoff < now` AND no result exists
3. For each match: simulates result using bivariate Poisson model with random variation (±15%)
4. Writes result as `{"team_a_goals": X, "team_b_goals": Y}` to the match object
5. ~~Attempts to regenerate knockout bracket if any group matches changed~~ ⚠️ **Currently broken.** See Known Issues below.
6. Writes update log to `data/update_log.json`

## What It Does NOT Do

- Does NOT pre-simulate future matches (only past kickoff with no result)
- Does NOT overwrite existing results (unless `--force` flag)
- Does NOT update real-world scores (Nami sync covers that in Stage 1)
- Knockout bracket regeneration is currently broken (see Known Issues)

## Known Issues

### 1. Knockout regeneration failure

```
⚠️ Knockout regeneration failed: build_knockout_structure() missing 1 required positional argument: 'ratings'
```

`update_results.py` calls `build_knockout_structure()` but the function now requires a `ratings` parameter that wasn't there in earlier versions. The knockout bracket is therefore **not automatically rebuilt** after group-stage results change. This means:

- Pre-set knockout pairings may become inaccurate if group standings change
- The error is non-fatal (returns exit 0, still updates the 1 simulated match)
- **Fix needed:** Pass team ratings data to `build_knockout_structure()` in `update_results.py`. Or disable the knockout call until the ratings dict is available.

### 2. Both repos use `master` branch

- WC26-Nami remote: `https://github.com/JTCAO515/WC26-Nami.git` → default branch `master`
- WC26-Main remote: `git@github.com:JTCAO515/WC26-Main.git` → default branch `master`
- The stale copy at `world-cup-project/updated/world-cup-edge-lab/` is NOT a git repo — file copy only, no push.
- Do NOT use `git push origin main` — it will fail.

### 3. Nami API trial expiry

Nami API is on a ~7-day trial (~2026-06-22). After expiry, Stage 1 (nami_sync.py) will fail. The system should fall back to only running Stage 2 (update_results.py) for simulation.

## Logging

- `data/update_log.json` — records each update batch with timestamp and count
- Both `nami_sync.py` and `update_results.py` print summary stats on completion

## Manual Run (full pipeline)

```bash
cd /home/ubuntu/projects/WC26-Nami

# Stage 1 — Real scores from Nami API
python3 data/nami_sync.py || echo "Nami sync failed (API may be down)"

# Stage 2 — Simulation for next day
python3 data/update_results.py

# Stage 3 — Push WC26-Nami
git add data/nami_team_map.json data/update_log.json data/wc2026_matches.json
git commit -m "每日数据更新 $(date +%Y-%m-%d): 纳米数据同步 + 模拟更新"
git push origin master

# Stage 4 — Cross-project sync (two targets)
cp data/wc2026_matches.json /home/ubuntu/projects/WC26-Main/data/wc2026_matches.json
cp data/wc2026_matches.json /home/ubuntu/projects/world-cup-project/updated/world-cup-edge-lab/data/wc2026_matches.json

# Stage 5 — Push WC26-Main companion repo
cd /home/ubuntu/projects/WC26-Main
git add data/wc2026_matches.json
git commit -m "每日数据更新 $(date +%Y-%m-%d): 同步WC26-Nami最新赛果数据"
git push origin master
```

> Both repos push to `master` not `main`.
