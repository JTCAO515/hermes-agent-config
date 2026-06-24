---
name: cron-scheduler
version: 1.0.0
description: |
  Schedule management with staggering, quiet hours, and wake-up override.
  Validates schedules, prevents collisions, and gates delivery during quiet hours.
triggers:
  - "schedule a job"
  - "cron"
  - "quiet hours"
  - "what jobs are running"
tools:
  - search
  - get_page
  - put_page
mutating: true
---

# Cron Scheduler

> **Convention:** See `skills/conventions/test-before-bulk.md` — test every cron job on 3-5 items first.

## Contract

This skill guarantees:
- Schedule staggering: max 1 job per 5-minute slot, no collisions
- Quiet hours gating: timezone-aware, with user-awake override
- Thin job prompts: jobs say "Read skills/X/SKILL.md and run it" (no inline 3000-word prompts)
- Idempotency: jobs can run twice without duplicate side effects
- Results saved as reports: `reports/{job-name}/{YYYY-MM-DD-HHMM}.md`

## Phases

1. **Define job.** Name, schedule (cron expression), skill to run, timeout.
2. **Validate schedule.** Check no collision with existing jobs (5-minute offset rule).
   - Slots: :05, :10, :15, :20, :25, :30, :35, :40, :45, :50
   - If collision detected, suggest the next available slot
3. **Check quiet hours.** Default: 11 PM - 8 AM local time.
   - Override: user-awake flag (if user is active, quiet hours suspended)
   - During quiet hours: save output to held queue
   - Morning contact releases the backlog
4. **Register with host scheduler.** OpenClaw cron, Railway cron, crontab, or process manager. **Each registered entry should execute via Minions, not `agentTurn`.** See `skills/conventions/cron-via-minions.md` for the rewrite pattern (PGLite uses `--follow`, Postgres uses fire-and-forget + `--idempotency-key` on the cycle slot). GBrain's v0.11.0 migration auto-rewrites entries for built-in handlers; host-specific handlers need a code-level registration per `docs/guides/plugin-handlers.md`.
5. **Write thin prompt.** Job prompt is one line: "Read skills/{name}/SKILL.md and run it."

## Idempotency Requirement

Every cron job MUST be idempotent:
- Running the same job twice produces the same result (no duplicate pages, no duplicate timeline entries)
- Use checkpoint state files to track progress and resume interrupted runs
- Check for existing output before creating new output

## Output Format

Job configuration saved. Report: "Job '{name}' scheduled at {cron expression}. Next run: {time}."

## Cron-Driven Dashboard Status Aggregation

A reusable pattern for using cron to periodically collect system state, memory, task history, and cross-project issues, then serve them through a dashboard API.

### Architecture

```
cron (every 6h)
  └── dashboard-status.py
        ├── Reads: git logs (fix/bug commits, dirty repos)
        ├── Reads: Hermes session DB (state.db → recent sessions)
        ├── Reads: cron output dirs (task history)
        ├── Reads: error logs
        ├── Scrubs: PAT tokens, API keys from output
        └── Writes: ~/.hermes/data/dashboard/status.json
                          │
dashboard frontend        │
  └── fetch('/api/hermes/all')
        └── hermes-api.py reads cached JSON
```

### Implementation Pattern

1. **Script** (`dashboard-status.py`): A Python script that:
   - Iterates `~/projects/` for git repos → reads recent fix/bug commits + dirty status
   - Queries `~/.hermes/state.db` (SQLite) for recent sessions
   - Reads cron job output directories for task history
   - Scrubs sensitive data (PAT tokens, API keys) before writing
   - Writes structured JSON to cache directory

2. **Cache location**: `~/.hermes/data/dashboard/status.json` (inside Hermes data dir, not in project dir)

3. **API layer**: `hermes-api.py` reads this cache and includes it in the dashboard `/all` endpoint

4. **Frontend**: Dashboard renders cards from the cached data (Memory, Task History, Cross-Project Issues)

5. **Cron schedule**: `0 */6 * * *` (every 6 hours) — balances freshness vs. server load

### Key Collector Functions

```python
def get_cross_project_issues():
    """Find fix/bug commits + dirty repos across all projects"""
    
def get_task_history():
    """Recent git commits + cron output files"""
    
def get_recent_sessions():
    """Last N sessions from state.db"""
```

### Verification

```bash
# Test the script
python3 ~/.hermes/scripts/dashboard-status.py

# Verify cache was written
cat ~/.hermes/data/dashboard/status.json | python3 -m json.tool | head -20
```

See `references/dashboard-status-aggregation.md` for full implementation with data scrubbing and error handling.

## Script-Level Pitfalls

### Broken Pipe on stdout (scripts that print status lines)

When a cron job uses a `script` that prints status lines to stdout (e.g. `interview-tracker.py`), the cron pipeline may close its read-end before the script finishes writing. Python then raises `RuntimeError: [Errno 32] Broken pipe` — this terminates the **entire** job, including the Agent step that runs after the script.

**Fix:** Add `signal.signal(signal.SIGPIPE, signal.SIG_DFL)` at the top of the script, right after imports. This restores default SIGPIPE behavior (silent exit instead of exception), so the script exits cleanly if the pipe closes early.

```python
import os
import signal

signal.signal(signal.SIGPIPE, signal.SIG_DFL)
```

**Verification:** Test the script piped through `head` to simulate early pipe closure:

```bash
python3 script.py | head -3   # should exit 0, not raise BrokenPipeError
```

### urllib response context manager gotcha

When building a `_urlopen_with_retry` helper, do NOT use `with ... as resp: return resp`. The `with` block calls `__exit__` when the function returns, closing the response and causing `"I/O operation on closed file"` in the caller.

**Wrong:**
```python
def _urlopen_with_retry(req):
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp  # ❌ — closed on return
    except:
        return None
```

**Right — return the raw response, let the caller own the context:**
```python
def _urlopen_with_retry(req):
    try:
        return urllib.request.urlopen(req, timeout=15)  # ✅ — caller wraps in `with`
    except:
        return None

# Caller:
resp = _urlopen_with_retry(req)
if resp:
    with resp:  # caller owns the context
        data = resp.read()
```

### PAT / git-credentials drift (watchdog scripts)

The password vault and `~/.git-credentials` are separate stores that can fall out of sync. The vault records the current PAT; `git-credentials` holds whatever was written last. When a cron script reads PAT from `git-credentials` and the vault has been updated, the script silently uses an expired token.

**Fix:** After updating PAT in the vault, always sync `git-credentials`: `sed -i 's/OLD_TOKEN/NEW_TOKEN/g' ~/.git-credentials`. Add a cron health check that warns if vault and git-credentials differ.

When a watchdog script calls `get_commit_detail()` for each new commit, the diff Accept header request (`application/vnd.github.v3.diff`) is slow — especially for commits with 10+ files. If 5+ new commits are detected, the script can timeout at 30s.

**Fix:** Fetch full detail (with diff summaries) only for the 1-2 most recent commits. Use a `commit_index` counter:

```python
commit_index = 0
for c in data:
    if commit_index < 2:
        detail = get_commit_detail(c["sha"], repo)  # full detail with diff
    else:
        # just the commit message, no detail
    commit_index += 1
    if c["sha"] == last_sha: break
```

## Watchdog Script Patterns

Two reusable no_agent=True script patterns for periodic monitoring:

### 1. GitHub Repo Watchdog

Monitor GitHub repos via the Commits API, extracting version info from project files (CHANGELOG.md, build.gradle, package.json, pyproject.toml), and reporting **detailed change content** — including file-level +N/-N stats AND diff summaries (actual code changes extracted from patches).

See `references/github-repo-watchdog.md` for the full template, version extraction strategies, and output format.

### 2. External Service Status Watchdog

Monitor third-party service status pages (statuspage.io, etc.) for outage → recovery transitions. Polls the JSON API, tracks state in a state file, and only alerts when status changes (e.g., `major_outage` → `operational`).

See `references/external-status-watchdog.md` for the full template, proxy handling, and CRITICAL: must unset http_proxy for global services.

### Key Requirements for Watchdog Scripts

1. **Network-aware proxy strategy** — The approach depends on your server's network:
   - **Unfiltered networks** (non-China VPS): Strip all proxy env vars at startup (`os.environ.pop("http_proxy", None)` etc.)
   - **China VPS / restricted networks**: Default to Xray proxy (`127.0.0.1:10809`) for GitHub API, with automatic fallback to direct if proxy fails. GitHub API has intermittent SSL reset from China, even on public endpoints. See `references/github-repo-watchdog.md` → "Proxy Strategy for Restricted Networks" for the full pattern.

2. **Decide whether commit detail is worth the risk** — From restricted networks, the commit detail endpoint (`/repos/{owner}/{repo}/commits/{sha}` with diff Accept header) frequently SSL-resets. Two strategies:
   - **Reliable but less detail**: Skip `get_commit_detail()`, use only the commit list data (SHA, message, author, date). The commit list endpoint is more reliable.
   - **Full detail with fallback**: Call commit detail for 1-2 commits only, with aggressive retry (2 attempts × 10s) and `except: pass` — if it fails, skip gracefully.

3. **Version from CHANGELOG.md** — extract version from `## vX.Y.Z` header pattern: `re.search(r"^##\\s+(v?\\d+\\.\\d+\\.\\d+\\w*)", content, re.MULTILINE)`

4. **Add retry logic for all API calls** — Python urllib connection reuse causes SSL reset on subsequent requests to the same host. Add: 2 retries with 1s backoff, proxy↔direct fallback, and `Connection: close` header.

5. **PAT from git-credentials: validate freshness** — `git-credentials` can fall out of sync with the password vault. Scripts that read PAT from `~/.git-credentials` should check periodically against vault (`python3 ~/.hermes/scripts/vault.py get GitHub`).

### Use Cases
- Monitor your own repos for new commits between cron runs
- Monitor PR activity, release branches, or docs repos
- Combine with multi-repo monitoring (2–3 repos per script) for a single consolidated report

### Cron Setup
```bash
# no_agent=True — script output goes directly to delivery channel
cronjob action=create \
  schedule="every 2h" \
  script="monitor-my-repo.py" \
  no_agent=true \
  name="My Repo Watchdog" \
  deliver="weixin"
```

## Anti-Patterns

- Scheduling jobs at the same minute (:00 for everything)
- Inline 3000-word prompts in cron jobs (use skill file references)
- Running cron jobs without testing on 3-5 items first
- Jobs that produce different output on re-run (not idempotent)
- Sending notifications during quiet hours (save to held queue instead)
- **Creating symlinks in ~/.hermes/scripts/** — the cronjob tool validates that the script resolves to a file inside `~/.hermes/scripts/`. Symlinks that `realpath` to paths outside this directory will be rejected with "Script path escapes the scripts directory". Use `cp` (not `ln -s`) to place the script there, or write it in place directly.
- **PM2 script path mismatch** — When a PM2 process references a script, it uses the `cwd` where `pm2 start` was originally called, not the script's actual file path. If PM2 errors with `can't open file '/wrong/dir/script.py'`, the process was started from a different directory. Fix: `pm2 delete <name>` → `cd /actual/project/dir` → `pm2 start script.py --name <name>`
