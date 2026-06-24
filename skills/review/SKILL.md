---
name: review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

# Review

Two-axis review of the diff between `HEAD` and a fixed point the user supplies.

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

The issue tracker should have been provided to you — run `/setup-matt-pocock-skills` if `docs/agents/issue-tracker.md` is missing.

## Process

### 1. Pin the fixed point
Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. Don't be opinionated; pass it through. If they didn't specify one, ask: "Review against what — a branch, a commit, or `main`?" Don't proceed until you have it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

### 2. Identify the spec source
Look for the originating spec, in this order:
- Issue/PR references (e.g., `#123`, `Closes #45`)
- `docs/agents/issue-tracker.md` (from setup skill)
- `docs/`, `specs/`, `.scratch/`

### 3. Identify the standards sources
Anything in the repo that documents how code should be written. Common locations:
- `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CONTEXT.md`, `CONTEXT-MAP.md`
- `docs/adr/`, `.editorconfig`, `eslint.config.*`, `biome.json`, `prettier.config.*`
- `tsconfig.json`, `STYLE.md`, `STANDARDS.md`, `STYLEGUIDE.md`, `docs/`

### 4. Spawn both sub-agents in parallel
Standards sub-agent reads all standards sources and reviews code against them.
Spec sub-agent reads the spec/issue and reviews whether the code matches what was asked.

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate
Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings — the two axes are deliberately separate so the user can see them independently.

End with a one-line summary: total findings per axis, and the worst single issue (if any) flagged.

## Why two axes
A change can pass one axis and fail the other. Reporting them separately stops one axis from masking the other.
