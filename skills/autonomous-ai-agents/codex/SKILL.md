---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing

Requires the codex CLI and a git repository.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI auth configured: either `OPENAI_API_KEY` or Codex OAuth credentials
  from the Codex CLI login flow
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

For Hermes itself, `model.provider: openai-codex` uses Hermes-managed Codex
OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. For the
standalone Codex CLI, a valid CLI OAuth session may live under
`~/.codex/auth.json`; do not treat a missing `OPENAI_API_KEY` alone as proof
that Codex auth is missing.

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |
| `--sandbox danger-full-access` | No Codex sandbox; useful when the host service context breaks bubblewrap |

## Hermes Gateway Caveat

When invoking the Codex CLI from a Hermes gateway/service context (for example,
Telegram-driven agent sessions), Codex `workspace-write` sandboxing may fail even
when the same command works in the user's interactive shell. A typical symptom is
bubblewrap/user-namespace errors such as `setting up uid map: Permission denied`
or `loopback: Failed RTM_NEWADDR: Operation not permitted`.

In that context, prefer:

```
codex exec --sandbox danger-full-access "<task>"
```

Use process boundaries as the safety layer instead: explicit `workdir`, clean git
status before launch, narrow task prompts, `git diff` review, targeted tests, and
human/agent confirmation before committing broad changes.

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work

---

## Crafting Delivery Prompts (for Full Rewrites)

When delegating a full rewrite/rebuild to Codex, the prompt itself is the most critical artifact. A bad prompt produces expensive wrong code. A good prompt lets Codex work autonomously for extended periods.

### Structure

Every delivery prompt should contain these sections in order:

| Section | What to include |
|---------|----------------|
| **Repository** | Exact GitHub URL, live URL, current version, default branch, git push quirks (proxy, branch name) |
| **Product Strategy** | Vision (one sentence), target users with pain points, before/after value proposition, explicit trade-offs (what NOT to do) |
| **Current Capabilities** | All models, algorithms, data sources, API endpoints (exact paths that must be preserved) |
| **Detailed Requirements** | Per page/feature: purpose, must-display items, interaction patterns, edge cases |
| **Architecture Spec** | Proposed directory structure, data flow diagram, component breakdown |
| **Design System** | Color palette (hex values), typography, spacing, component library, interaction patterns |
| **Do NOT Touch** | Explicit list of files/directories Codex must NOT modify (with reasons) |
| **Technical Constraints** | Dependency limits, deployment platform limits, test requirements, git config |
| **Deliverables** | Checkable completion criteria (test pass, deployable, push target) |

### Key Pitfalls

- **Don't say "rewrite this" without saying what to preserve** — Codex will happily delete working data pipelines. Use a "Do NOT Touch" section.
- **Private repos need auth context** — tell Codex the repo is private and how to read/write (PAT from `~/.git-credentials`, `--noproxy '*'` for curl, proxy config for git push)
- **Design system must be concrete** — don't say "dark theme with good colors", say hex values (`#0f1117` background, `#5e6ad2` primary)
- **Per-page specs must include purpose** — Codex needs to know WHY a feature exists, not just WHAT to display, or it simplifies away the real value
- **Branch name matters** — if the repo uses `master` not `main`, say it explicitly. Codex defaults to `main`
- **Proxy config must be explicit** — `https_proxy=http://127.0.0.1:10809` for git push, `--noproxy '*'` for curl/GitHub API
- **Precision matters — don't include sibling projects** — Only include the repos and scope the user asked for. Adding companion/sibling repos ("also rewrite the Nami version") expands scope without authorization. Codex treats everything in the prompt as in-scope.
- **Product depth > technical build** — Lead with WHY (product strategy, user needs, value proposition) before HOW (architecture, tech stack). Codex builds better when it understands the product context — don't start with directory trees.
- **Verify if the work was already done** — Before writing a rewrite/handoff prompt, check if the repo already has the rewrite committed. Use the commits endpoint (`GET /repos/{o}/{r}/commits?sha={branch}`) to check for recent "feat: rewrite" or version-bump commits.

### When to use this pattern

- Full rewrite/rebuild of a project
- Migrating from one tech stack to another
- Building a new feature set that requires deep product context
- Handoff to a different AI agent for autonomous execution

### Reference Example

See `references/wc26-codex-delivery-example.md` for a complete, 13KB delivery prompt that was used to hand off the WC26 Edge Lab project to Codex CLI for a full rewrite. It covers all 10 sections above and was structured for autonomous execution.
