---
name: briefing
description: Compile daily briefing with meeting context, active deals, and citation tracking
triggers:
  - "daily briefing"
  - "morning briefing"
  - "汇报"
  - "what's the status"
  - "项目状态"
  - "what's happening today"
  - "今日汇报"
  - "status update"
tools:
  - search
  - query
  - get_page
  - list_pages
  - get_timeline
  - session_search
  - cronjob
  - read_file
  - terminal
  - skill_view
mutating: false
---

# Briefing Skill

Compile a daily briefing from brain context.

> **Filing rule:** When the briefing creates or updates brain pages,
> follow `skills/_brain-filing-rules.md`.

## Contract

- Every fact in the briefing includes an inline `[Source: slug, updated DATE]` citation.
- Meeting participants are resolved against the brain; gaps are explicitly flagged.
- Active deals and action items include deadlines and recency context.
- The briefing is read-only: no brain pages are created or modified unless the user explicitly requests it.
- Stale alerts surface pages relevant to today's context, not just all stale pages.

## Environment Detection

Two paths exist. **Prefer gbrain if available; fall back to multi-source path if gbrain commands fail or don't exist.**

| Environment | Detection | Approach |
|---|---|---|
| gbrain available | `which gbrain` succeeds | Full gbrain path below |
| No gbrain (Hermes Agent w/o brain) | `gbrain` not found or commands fail | Multi-source path (Phase 0b) |

### Phase 0b — Multi-source status compilation (no gbrain)

When gbrain is unavailable, compile status across projects using available tools:

1. **Cron pulse** — `cronjob(action='list')` to get all scheduled jobs, their last_run_at, next_run_at, and any delivery errors.
2. **Session pulse** — `session_search()` without filters to pull most recent sessions (titles, previews, message counts). Identify active conversation threads.
3. **Project scan** — For each active project directory (~/projects/*), check:
   - `ITERATION_LOG.md` tail (last 30-50 lines) for latest iteration status
   - `PLAN.md` for roadmap completion
   - `git log --oneline -3` for recent changes
   - `git status --short` for uncommitted changes
4. **Skill pulse** — Check any relevant skills deployed or used in recent sessions via `skill_view(name)` for status.
5. **Deployment check** — For Vercel-deployed projects, `curl -sL -o /dev/null -w "%{http_code}" <url>` to confirm live.

### Output format (non-gbrain)

```
## 📋 [Day]汇报 — [date]

### ✅ 在跑任务（N个 Cron）
| 任务 | 时间 | 状态 |
|------|------|------|

### 🛠 各项目状态
**[Project A]** — [1-line summary]
- Latest: Iter N — [description] [✅/⏳/⚠️]
- Git: [clean/dirty], [deployed/not deployed]

**[Project B]** — [1-line summary]
...

### 💬 活跃会话
- [session title] ([N条消息]) — [last active time]

### ⚠️ 需关注
- [any issues: cron failures, uncommitted work, stale projects]

### 有什么要动的？
[3-5 open-ended prompts for user to pick next action]
```

## Phases

0. **Hot memory pulse (v0.32).** Before composing anything else, run:

   ```bash
   gbrain recall --since-last-run --supersessions --pending --rollup --json
   ```

   Fold the result into the briefing under a "Brain pulse" section at the top:
   1. **Contradictions resolved overnight** — the `--supersessions` output. Lead
      with these because they're new corrections to your model of the world.
   2. **Top mentions** — `top_entities` from `--rollup` (top 5 entity slugs by
      fact count in the window).
   3. **New facts since last briefing** — group the `facts` array under each
      entity from the rollup; include `kind`, `notability`, and `confidence`.
   4. **Pending consolidation footer** — when `pending_consolidation_count > 0`,
      note `N facts await dream-cycle consolidation` so the operator can decide
      whether to run `gbrain dream` before reading further.

   The `--since-last-run` flag advances `~/.gbrain/recall-cursors/<source>.json`
   so the next briefing picks up exactly where this one left off. If you're
   running this as a cron job, pass `--source <slug>` or set `GBRAIN_SOURCE`
   explicitly — cron doesn't start in your repo-root cwd, so dotfile resolution
   may miss the right source. Thin-client installs (`gbrain init --mcp-only`)
   route through the remote brain transparently.

1. **Today's meetings.** For each meeting on the calendar:
   - Search gbrain for each participant by name
   - Read their pages from gbrain for compiled_truth context
   - Summarize: who they are, recent timeline, relationship to you
2. **Active deals.** List deal pages in gbrain filtered to active status:
   - Deadlines approaching in the next 7 days
   - Recent timeline entries (last 7 days)
3. **Time-sensitive threads.** Open items from timeline entries:
   - Items with deadlines in the next 48 hours
   - Follow-ups that are overdue
4. **Recent changes.** Pages updated in the last 24 hours:
   - What changed and why (read timeline entries from gbrain)
5. **People in play.** List person pages in gbrain sorted by recency:
   - Updated in last 7 days
   - Have high activity (many recent timeline entries)
6. **Stale alerts.** From gbrain health check:
   - Pages flagged as stale that are relevant to today's meetings

## GBrain-Native Context Loading

Before generating any briefing, load context from gbrain systematically.

### Before a meeting

For every attendee on the calendar invite:
- `gbrain search "<attendee name>"` -- find their brain page
- `gbrain get <slug>` -- load compiled truth, recent timeline, relationship context
- If no page exists, note the gap ("No brain page for Sarah Chen -- consider enrichment")

### Before an email reply

Before drafting or triaging any email:
- `gbrain search "<sender name>"` -- load sender context
- Read their compiled truth to understand who they are, what they care about, and
  your relationship history. This turns a cold reply into an informed one.

### Daily briefing queries

Run these queries to populate the briefing sections:
- `gbrain query "active deals status"` -- deal pipeline snapshot
- `gbrain query "meetings this week"` -- recent meeting pages with insights
- `gbrain query "pending commitments follow-ups"` -- open threads and action items
- `gbrain search --type person --sort updated --limit 10` -- people in play

## Output Format

```
DAILY BRIEFING -- [date]
========================

MEETINGS TODAY
- [time] [meeting name]
  Participants: [name] (slug: people/name, [key context])

ACTIVE DEALS
- [deal name] -- [status], deadline: [date]
  Recent: [latest timeline entry]

ACTION ITEMS
- [item] -- due [date], related to [slug]

RECENT CHANGES (24h)
- [slug] -- [what changed]

PEOPLE IN PLAY
- [name] -- [why they're active]
```

## Back-Linking During Briefing

If the briefing creates or updates any brain pages (e.g., new meeting prep
pages, updated entity pages), the back-linking iron law applies: every entity
mentioned must have a back-link from their page. See `skills/_brain-filing-rules.md`.

## Citation in Briefings

When presenting facts from brain pages, include inline citations:
- "Jane is CTO of Acme [Source: people/jane-doe, updated 2026-04-01]"
- This lets the user trace any claim back to the brain page and assess freshness

## Anti-Patterns

- **Briefing without brain queries.** Never generate a briefing from memory alone; always query gbrain for current data.
- **Uncited facts.** Every claim must include `[Source: slug, updated DATE]`. A fact without a citation is unverifiable.
- **Stale context presented as current.** If a page hasn't been updated in 30+ days, flag the staleness explicitly rather than presenting it as fresh.
- **Modifying brain pages unprompted.** The briefing is read-only by default. Do not create or update pages unless the user explicitly requests it.
- **Ignoring coverage gaps.** When a meeting participant has no brain page, say so. Silence about gaps hides ignorance.

## Tools Used

- Search gbrain by name (query)
- Read a page from gbrain (get_page)
- List pages in gbrain by type (list_pages)
- Check gbrain health (get_health)
- View timeline entries in gbrain (get_timeline)

## References

- `references/session-timeline-reconstruction.md` — Technique for reconstructing multi-day project timelines from session_search history. Use when user asks "汇总过去N天的项目/迭代" or any historical work summary.
- `references/multi-source-status-example.md` — Concrete walkthrough of the multi-source compilation workflow from a real "汇报" session (2026-06-14). Exact commands, data sources, and thinking process for the Phase 0b path.
