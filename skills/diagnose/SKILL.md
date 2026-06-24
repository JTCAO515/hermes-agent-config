---
name: diagnose
description: A structured, 6-phase debugging loop for hard bugs and performance regressions. Use when a user reports a bug, says something is broken/failing, or describes a performance regression.
---

# Diagnose — Disciplined Debugging Loop

**"Reproduce → minimise → hypothesise → instrument → fix → regression-test"**

## Phase 1 — Build a Feedback Loop

> **"This is the skill. Everything else is mechanical."**

Spend disproportionate effort here. Be aggressive, creative, refuse to give up.

- **Goal:** A fast, deterministic, agent-runnable pass/fail signal.
- **Tools (try in order):** `git bisect run`, `scripts/hitl-loop.template.sh`
- **Iterate on the loop itself** – treat it as a product.
- **Non-deterministic bugs:** Raise reproduction rate (e.g., loop 100×, parallelise, add stress, inject sleeps).
- **If you genuinely cannot build a loop:** Stop. List what you tried. Ask user for access to reproducing environment, ARTIFACT (HAR, log dump, core dump, screen recording with timestamps), or permission to add temporary production instrumentation. **Do not proceed** to hypothesise without a loop.

## Phase 2 — Reproduce

Run the loop. Watch the bug appear. **Confirm:** The bug is observable. Do not proceed until you reproduce it.

## Phase 3 — Hypothesise

> **"3–5 ranked hypotheses before testing any of them."**

- Single-hypothesis generation anchors on the first plausible idea.
- Each hypothesis must be **falsifiable** – state the prediction it makes.
- **Format:** "If `<cause>` is the cause, then `<change>` will make the bug disappear / will make it worse."
- **Show the ranked list to the user before testing.** They often have domain knowledge that re-ranks instantly.

## Phase 4 — Instrument

> **"Change one variable at a time."**

- Each probe maps to a specific prediction from Phase 3.
- **Tool preference (order):** `console.log` (fast) → debugger → breakpoint → binary search.
- **Tag every debug log** with a unique prefix: `[DEBUG-a4f2]`. Cleanup becomes a single `grep`.
- **Perf branch:** For performance regressions, logs are usually wrong. Instead: establish a baseline (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

## Phase 5 — Fix + Regression Test

Write the regression test **before the fix** – but only if there is a **correct seam** for it.

- **Correct seam:** The test exercises the real bug pattern as it occurs at the call site.
- **If no correct seam exists:** That itself is the finding. Note it – the architecture is preventing bug lock-down.
- If a correct seam exists: 1. Write the test. 2. See it fail. 3. Apply the fix. 4. See the test pass.

## Phase 6 — Cleanup + Post-mortem

Required before declaring done:
- Remove all `[DEBUG-...]` tags (grep for them).
- Remove all extra instrumentation.
- Remove temporary test code and console logs.

> **"Then ask: what would have prevented this bug?"** If the answer involves architectural change (no good test seam, tangled callers, hidden coupling), hand off to `/improve-codebase-architecture`.
