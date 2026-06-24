---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Plans

Three levels of planning documents, each serving a different purpose:

| Document | Level | Audience | When |
|----------|-------|----------|------|
| **Product Plan** (`PLAN.md`) | Product/strategy | User + developer | Start of project or major phase |
| **Iteration Plan** (`docs/ITERATION_PLAN.md`) | Phased roadmap | Developer (self) | After product plan, before building |
| **Implementation Plan** | Feature/task | Implementer (agent) | Before each feature build |

All three follow the same discipline: **make the next step obvious.** If someone has to guess, the plan is incomplete.

---

## Product Plan Documents (`PLAN.md`)

### Overview

The product plan answers **what we're building, why, for whom, and how**. It's the strategic north star — written before any code, revisited at major phase transitions.

### When to Write

- Brand new project (before any code)
- Major pivot or phase change (Phase 1→Phase 2)
- User says "先做个规划" / "写个产品规划" / "像 TXPokerAssist 一样详细"

### Standard Structure (19 sections)

| # | Section | Purpose |
|---|---------|---------|
| 1 | **Project Vision** | One-sentence positioning + core value proposition + what it is NOT |
| 2 | **Domain Complexity** | Compare vs known reference (TXPokerAssist, related tools) — structured table |
| 3 | **Core Decision Points** | Grid: decision type, trigger, goal, mathematical model, MVP phase |
| 4 | **Target Users** | User segments with pain points + priority (P0/P1) |
| 5 | **Feature Framework** | P0 (core) → P1 (enhancement) → P2 (advanced), each with status |
| 6 | **Feature Progress** | Current completion status (e.g. 76/81 番种) with gap table |
| 7 | **Data Model** | JSON Schemas for all core data structures |
| 8 | **Algorithm Architecture** | Module dependency graph + pseudocode for key algorithms |
| 9 | **API Design** | Endpoint table + request/response examples |
| 10 | **Frontend Design** | ASCII wireframe + interaction details + responsive requirements |
| 11 | **Tech Stack** | Table: layer → choice → rationale; dependency analysis |
| 12 | **Iteration Roadmap** | Phased iteration list with status (✅/planned) |
| 13 | **ADR (Architecture Decision Records)** | Key decisions with context, rationale, trade-offs |
| 14 | **Non-goals** | Explicit "Phase X won't touch this" with reasoning |
| 15 | **Acceptance Criteria** | Quantifiable pass/fail checks for MVP + next phase |
| 16 | **Known Risks & Mitigations** | Probability × impact matrix + mitigation strategy |
| 17 | **Competitive Analysis** | What exists, how this differs |
| 18 | **Quick Start** | One-line commands to run + test + deploy |
| 19 | **Appendix** | Reference tables, taxonomy, glossary |

### Writing Heuristics

- **Compare vs known reference** — When explaining domain complexity, always contrast against a familiar system (TXPokerAssist → Mahjong). Use a structured table, not prose.
- **Explicit non-goals** — "What we are NOT" is as important as "what we are". List Phase 2 before Phase 1.
- **Decision points first** — Before describing implementation, enumerate the core decisions the system must support (e.g. 5 types for mahjong, 4 stages for poker).
- **Save as `PLAN.md`** in project root.

**Reference file**: `references/product-plan-example.md` — full 19-section PLAN.md for General Mahjong Assist.

---

## Iteration Plan Documents (`docs/ITERATION_PLAN.md`)

### Overview

The iteration plan translates the product plan into **specific, actionable iterations**. Each iteration has a clear goal, exact file changes, test counts, and acceptance criteria.

### When to Write

- After PLAN.md is approved
- Before starting a new Phase
- User says "先做出具体迭代计划"

### Standard Structure

#### Header: Current Baseline

```
| Metric | Value |
|--------|-------|
| Tests  | 197   |
| Features | 76/81 番种 |
| Decision engines | A✅ B✅ C✅ D✅ E❌ |
```

#### Iteration Table (each iteration)

```
### Iter 00X: [Name]

**Goal**: One-sentence objective.

**File changes**:

| File | Change | Complexity |
|------|--------|:----------:|
| `path/to/file.py` | Description of change | ⭐/⭐⭐/⭐⭐⭐ |
| `tests/test_new.py` | New test file (+N tests) | ⭐⭐ |

**Algorithm/model** (if applicable):
Pseudocode for the core logic.

**API changes** (if applicable):
```
{
  "new_field": "description of what changed"
}
```

**Test checklist** (at least N items):
1. ...
N. ...

**Acceptance criteria**:
- N tests pass
- API returns new_field
- Total tests: OLD + N
```

#### Priority Matrix

| Iter | Value | Cost | Risk | Priority |
|------|-------|------|------|:---------:|
| 007  | High  | Med  | Low  | **P0 ⭐** |

#### Recommended Execution Order

ASCII arrow graph showing dependencies and parallel paths:
```
007 → 008 → 009 → 010
         ↓
        011 (parallel)
```

### Writing Heuristics

- **Each iteration must have acceptance criteria with exact test counts**: "197 + 15 = **212 tests**". Never vague "more tests".
- **File changes must be exact paths**, not "modify the game engine".
- **Algorithm/model section**: include pseudocode for any non-trivial logic. Don't assume the implementer knows the algorithm.
- **Priority matrix**: Value × Cost × Risk with clear P0/P1/P2 labels.
- **Recommended order**: ASCII graph showing dependencies. Identify parallelizable iterations.
- **Save as `docs/ITERATION_PLAN.md`** under project root.

---

## Implementation Plans (original skill)

### Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

## Appendix: Plan Mode (no-exec mode)

> Absorbed from standalone `plan` skill (2026-06-02). Use when the user explicitly asks for a plan without execution.

### Core Behavior

For this turn, planning only:
- Do not implement code.
- Do not edit project files except the plan markdown file.
- Do not run mutating terminal commands, commit, push, or perform external actions.
- You may inspect the repo or other context with read-only commands/tools when needed.

### Save Location

Save plans under `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md` (relative to active workspace).

### Interaction Style

- If the request is clear enough, write the plan directly.
- If no explicit instruction accompanies `/plan`, infer the task from current conversation context.
- If genuinely underspecified, ask a brief clarifying question instead of guessing.
- After saving, reply briefly with what you planned and the saved path.
