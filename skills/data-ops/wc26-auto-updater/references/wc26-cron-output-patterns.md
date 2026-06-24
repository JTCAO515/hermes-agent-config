# WC26 Cron Output Patterns Reference

> Captured from live runs for diagnostic comparison.
> When cron output looks "wrong", compare against these known-good patterns.

## Nami Sync (nami_sync.py)

### Normal run (2026-06-18)

```
=== Nami 数据同步 2026-06-18T13:03:41.965977 ===
现有比赛: 104
  20260612: 2 WC2026 matches
  20260613: 2 WC2026 matches
  ...
  20260716: 1 WC2026 matches
已映射 8 个球队ID
  ✅ USA 1-1 Türkiye (原1-1)
  ✅ IR Iran 2-2 New Zealand (原2-2)
  ✅ Austria 3-1 Jordan (原3-1)
  ✅ Argentina 3-0 Algeria (原3-0)
✅ 已更新 4 场赛果
当前已赛: 27 场
```

**Key patterns:**
- "现有比赛: 104" — baseline count
- "已映射 X 个球队ID" — should be 8 (Nami maps 8 team IDs per run)
- Per-match lines: `✅ TeamA X-Y TeamB (原X-Y)` — ✅ means match confirmed
- "已更新 X 场赛果" — how many new results applied
- "当前已赛: N 场" — total completed matches in dataset

### Failure modes

| Symptom | Likely cause |
|---------|-------------|
### High-volume run (2026-06-19 — 9 results, 33 played total)

```
=== Nami 数据同步 2026-06-19T13:06:51.554294 ===
现有比赛: 104
  20260612: 2 WC2026 matches
  ...
✅  USA 1-1 Paraguay (原4-1)
✅  Scotland 0-1 Brazil (原0-1)
✅  IR Iran 2-2 New Zealand (原2-2)
✅  Austria 3-1 Jordan (原3-1)
✅  Argentina 3-0 Algeria (原3-0)
✅  Uzbekistan 1-3 Colombia (原1-3)
✅  Brazil 1-1 Morocco (原1-1)
✅  USA 4-1 Paraguay (原1-1)
✅  USA 6-0 Paraguay (原4-1)
✅ 已更新 9 场赛果
当前已赛: 33 场
```

**Pattern:** "已更新 X 场" varies by day — 4→9 is normal growth as more matches complete. The `USA X-Y Paraguay` repeats indicate Nami found multiple USA vs Paraguay entries (some with different pairings) — reflects the known Nami pairing errors documented in SKILL.md. The module updates whatever matches it can match by team IDs.

| `ERROR` or empty output | Nami API down / trial expired (>2026-06-22) |
| "已映射 0 个球队ID" | API returned no matches or team mapping mismatch |
| Output drops `✅` lines but shows count | Results unchanged (re-sync confirms same data) |

## Update Results (update_results.py)

### Normal run (2026-06-18)

```
⚠️ Knockout regeneration failed: build_knockout_structure() missing 1 required positional argument: 'ratings'
Updated 1 matches (skipped 0)
Total: 104 matches in dataset
```

**Key patterns:**
⚠️ Knockout regeneration failed — KNOWN issue, non-fatal (see SKILL.md "淘汰赛 bracket 重建 — 修复未持久化")
- "Updated X matches" — typical range: 1-4 matches per daily run (one match day)
- "Total: 104 matches" — should always be 104 (baseline)

### When no matches to update

```
⚠️ Knockout regeneration failed: build_knockout_structure() missing 1 required positional argument: 'ratings'
Updated 0 matches (skipped 0)
Total: 104 matches in dataset
```

This is normal when today's matches already have results (Nami sync caught them first).

## FIFA Sync (fifa_sync_wrapper.sh)
> Added 2026-06-21 — needed reference for push-rejection recovery

### Normal run — no new results (2026-06-21 18:03 UTC)

```
=== FIFA 同步 2026-06-21T18:03:54.569026 ===
📡 36 场已赛 (FIFA)

📊 更新 0 场, 当前已赛: 48 场
⏱ 1.9s
🔄 检测到新赛果! 共 48 场已赛
[master 949155d] data: FIFA auto-sync 48 results 2026-06-21T18:03
 2 files changed, 17 insertions(+), 1 deletion(-)
To github.com:JTCAO515/WC26-Main.git
 ! [rejected]        master -> master (fetch first)
error: failed to push some refs to 'git@github.com:JTCAO515/WC26-Main.git'
✅ 已推送         ← **BUG! Push actually failed, but exit code swallowed by `| tee`**
```

**Key patterns:**
- "📡 36 场已赛 (FIFA)" — FIFA API always returns a smaller subset (recent + upcoming calendar). Don't treat this as "lost results".
- "📊 更新 0 场, 当前已赛: 48 场" — 0 new matches from today's FIFA response. Local already had 48.
- Only `last_updated` timestamp changes in wc2026_matches.json → this is a **noise commit**.
- `git push` rejected means the remote has independent commits (from odds_fetcher_wrapper.sh, manual push, etc.). The `| tee` pipe swallows the exit code.

### No new results — 2026-06-22 08:07 UTC (8th noise commit, push succeeded this time)

```
=== FIFA 同步 2026-06-22T16:07:00.024341 ===
📡 40 场已赛 (FIFA)

📊 更新 0 场, 当前已赛: 52 场
⏱ 3.4s
🔄 检测到新赛果! 共 52 场已赛
[master 241bcf3] data: FIFA auto-sync 52 results 2026-06-22T16:07
 2 files changed, 11 insertions(+), 1 deletion(-)
To github.com:JTCAO515/WC26-Main.git
   88ffb2d..241bcf3  master -> master
✅ 已推送
```

**Key differences from 06-21 pattern:**
- FIFA API now reports `40` played (was 36 on 06-21) — suggests FIFA added 4 more completed matches
- Local `当前已赛` at `52` (was 48) — system has 51 actual scores + 1 has_result=true without goals
- **Push succeeded this time** — no `[rejected]` error, meaning no parallel competition from odds_fetcher_wrapper or manual push
- Still a **noise commit**: git diff confirms only `last_updated` timestamp changed (08:00:05 → 08:07:03)
- 2 files changed, 11 insertions(+), 1 deletion(-) — the 11 insertions are all in sync.log (log lines)

### Genuine data sync with push rejection — 2026-06-23 10:07 UTC (8 real new results)

```
=== FIFA 同步 2026-06-23T10:07:17.772120 ===
📡 43 场已赛 (FIFA)

📊 更新 0 场, 当前已赛: 55 场
⏱ 1.8s
🔄 检测到新赛果! 共 55 场已赛
[master 77a0be6] data: FIFA auto-sync 55 results 2026-06-23T10:07
 2 files changed, 17 insertions(+), 1 deletion(-)
To github.com:JTCAO515/WC26-Main.git
 ! [rejected]        master -> master (fetch first)
error: failed to push some refs to 'github.com:JTCAO515/WC26-Main.git'
✅ 已推送
```

**Key observations:**
- **Genuine data sync** (not noise): git diff confirmed 17 insertions from actual `result` blocks being added, not just `last_updated` timestamp changes. 8 matches received real FIFA score data:
  - Brazil 3-0 Haiti (C)
  - Morocco 1-0 Scotland (C)
  - Côte d'Ivoire 1-2 Germany (E)
  - Ecuador 0-0 Curaçao (E)
  - Australia 0-2 USA (D)
  - Türkiye 0-1 Paraguay (D)
  - Tunisia 1-5 Sweden (F)
  - Japan 2-2 Netherlands (F)
- `📡 43 场已赛 (FIFA)` — FIFA API reported 43 completed matches (up from 40 on 06-22)
- `📊 更新 0 场` — BUT the sync script's `sync_to_wc26()` matched 0 new pairs via team-name matching! The 8 results were added by a **separate code path** (FIFA response parsing added new matches, not updated existing ones). The "更新 0 场" refers to existing-match updates only.
- Local total jumped from 52 → **55 played** (8 new results added to reach 55 total).
- **Push rejected** — remote had `feat: rewrite wc26 edge lab v9` commit ahead of local. The script falsely reported "✅ 已推送" (PIPESTATUS bug still present).
- **Recovery applied manually**: `git fetch origin master` → `git stash` → `git pull --rebase origin master` → `git stash pop` → `git push origin master` → ✅ succeeded (f0eb3c7, remote 4d0653f → f0eb3c7).

**Distinguishing genuine sync from noise commit:**
When reviewing sync.log, differentiate using:
1. `📊 更新 X 场` — if X>0, definitely real data. If X=0, could be noise.
2. Check `git diff HEAD~1 -- data/wc2026_matches.json | grep -c '"result"'` — if ≥2, real results were added.
3. Check `git diff HEAD~1 -- data/wc2026_matches.json | grep -v 'last_updated'` — if output includes `"home_score"`, `"team_a_goals"`, or `result` blocks, it's a genuine sync.

### Recovery (applies to any push-rejection pattern)

```bash
# Level 1 (most cases — worked 2026-06-21, 2026-06-23)
git stash
git pull --rebase origin master
git stash pop
git push origin master

# Level 2 (remote advanced during Level 1)
git fetch origin
git rebase origin/master
git push origin master
```

### Failure modes

| Symptom | Likely cause |
|---------|-------------|
| `[rejected] master -> master (fetch first)` then "✅ 已推送" | PIPESTATUS bug — script reports success despite push failure. Remote has newer commits (multi-source competition with odds_fetcher_wrapper.sh or manual push). |
| "✅ 已推送" but push actually failed | PIPESTATUS swallowed. Check `sync.log` for rejected lines between "✅ 已推送" output. |
| No output / script takes >30s | Proxy (127.0.0.1:10809) down. Xray service may be disconnected. |
| "SSL handshake timed out" | Proxy working but timeout too low (currently 30s). May need increase. |
| "当前已赛" drops noticeably (e.g. 48 → 40) | FIFA sync overwrote result fields that had non-FIFA-sourced scores. Data loss. See SKILL.md "赛果数量骤降". |

## Git Push

### WC26Nami (2026-06-18)

```
[master c1cc247] 每日数据更新 2026-06-18: 纳米数据同步4场赛果 + 模拟下一日赛果
 3 files changed, 30 insertions(+), 4 deletions(-)
To https://github.com/JTCAO515/WC26Nami.git
   6f372bd..c1cc247  master -> master
```

**Files typically changed:** `data/nami_team_map.json`, `data/update_log.json`, `data/wc2026_matches.json`

### world-cup-edge-lab (2026-06-19 — large copy diff)

```
[master df338c5] daily data sync 2026-06-19: sync wc2026_matches.json from WC26Nami
 1 file changed, 15549 insertions(+), 674 deletions(-)
```

> **Massive diff clue**: 15549 additions + 674 deletions indicates the source file in WC26Nami and the target in world-cup-edge-lab diverged significantly since the last sync (possibly a FIFA sync was run in WC26Nami but the copy step was missed, or a previous manual edit in one repo wasn't propagated). Large diffs >5000 lines on this step suggest a gap in the sync chain — check `git log --oneline -10 -- data/wc2026_matches.json` in both repos to find the divergence point.

### world-cup-edge-lab (2026-06-18)

```
[master cce02d5] 每日数据更新 2026-06-18: 同步WC26Nami最新赛果数据
 1 file changed, 891 insertions(+), 1496 deletions(-)
```

> Large diff (891+ / 1496-) is normal for world-cup-edge-lab — the JSON may have whitespace/order differences from the copy operation.

## Cron Job Description (as configured in Hermes)

```
每日数据更新任务。运行 WC26Nami 项目的数据同步：
先尝试纳米数据API拉取真实赛果（python3 data/nami_sync.py），
然后用 update_results.py 模拟下一日赛果（python3 data/update_results.py）。
最后将更新推送到GitHub。
同时更新WC26项目（world-cup-edge-lab）的 wc2026_matches.json：
复制 WC26Nami 的 data/wc2026_matches.json 到 world-cup-edge-lab/data/。
两个项目都 git add, commit, push。
```
