# Adversarial Dual-Model Code Review

Run two different LLMs against the same codebase independently, then cross-reference findings. Catches blind spots that any single model misses.

## When to Use

- After a feature or bug-fix PR, when quality is critical (finance, security, poker math)
- Before merging code with non-trivial mathematical correctness requirements
- When the stakes are high enough to warrant ~2× review cost

## Protocol

### Step 1 — Pick two models with different strengths

Choose models from different families or training regimes:

| Pair | Why |
|------|-----|
| GLM 5.1 + GPT 5.5 | GLM is strong on math/logic correctness; GPT is strong on security/edge cases |
| Claude 4 + GPT 5.5 | Different training distributions → different blind spots |
| DeepSeek + GPT | DeepSeek strong on reasoning chains; GPT strong on safety |

Avoid using two versions of the same model family (e.g., GPT 4o + GPT 5.0) — they share too much training data to catch orthogonal issues.

### Step 2 — Assign adversarial framing

Each review gets the same code but framed differently:

```
Reviewer A: "You are an adversarial auditor. Your job is to find ANY scenario
where this code produces wrong results. Assume the author is smart but has
blind spots in [domain]. Be harsh. Score each dimension."

Reviewer B: "You are an independent code reviewer with deep expertise in
[domain]. Your job is to evaluate correctness, security, performance, and
maintainability. Flag anything that would cause production issues."
```

### Step 3 — Cross-reference results

Build a 2×2 matrix:

```
                | Reviewer A caught | Reviewer A missed
Reviewer B caught | Consensus fix    | A's blind spot
Reviewer B missed | B's blind spot   | Both missed (worst case)
```

**A items in "Consensus fix"** → fix these first (both models agree = high confidence).
**Single-model catches** → investigate: could be noise, or could be the deeper catch.
**Both missed** → this is where domain expertise is needed.

### Step 4 — Score each dimension

Score on a consistent scale (e.g., -2 to +2 or 0-10) across:

| Dimension | What to check |
|-----------|---------------|
| A. Math/Correctness | Formulas, edge cases, invariants, floating-point |
| B. Logic/Completeness | Branch coverage, missing cases, early returns |
| C. Security | Injection, secrets, DoS, input validation |
| D. Performance | Algorithmic complexity, N+1, I/O patterns |
| E. Maintainability | Naming, dead code, docstring accuracy |
| F. Production-readiness | Error handling, logging, idempotency |

### Step 5 — Validate critical findings with concrete tests

For any "CRITICAL" finding, write a minimal reproducer first:

```python
# Before fixing, confirm the bug exists
assert old_code(input) != expected, "Bug should produce wrong output"
```

Then fix, then prove the fix works:

```python
assert fixed_code(input) == expected, "Fix should produce correct output"
```

## Case Study: TXPokerAssist

**Context:** A Texas Hold'em equity calculator and EV decision engine (~1,000 lines).

**Models used:** GLM 5.1 + GPT 5.5

**Results:**

| Category | GLM 5.1 caught | GPT 5.5 caught | Both caught |
|----------|---------------|---------------|-------------|
| CRITICAL | 2 | 2 | 2 |
| HIGH | 3 | 4 | 2 |
| MEDIUM | 2 | 3 | 1 |
| **Total** | **7** | **9** | **5** |

**Cross-reference findings:**
- **Both CRITICAL (fix first):** EV formula Win$=pot+call (should be pot), Monte Carlo pairwise win stats in multi-way pots
- **GPT-only:** Card encoding produces sparse values (range 2-62 not 0-51, breaks future index tables), `compare_hands` zip comparison doesn't check kicker list length, time_ms hardcoded to 0
- **GLM-only:** Dead `PRIMES` array never used, `lose_rate` float precision edge case
- **Neither caught:** HTML/CSS layout edge cases on narrow screens

**Verdict cross-reference validity:** 5/5 consensus-CRITICAL items were genuine bugs. 0 false positives among consensus items. ~40% of single-model findings were either noise or minor.

## Pitfalls

- **Confirmation bias** — If both models flag the same thing, it's high-confidence, but check they're giving the same *reason*. Two wrong reasons ≠ one right fix.
- **Model-specific hallucination** — A model may fabricate a "bug" that doesn't exist (e.g., claiming a function is unused when it's imported elsewhere). Cross-reference with actual code.
- **Surface vs depth** — A model that writes a long fluent review may have shallow analysis. A model that writes a terse, specific review often caught more. Verbosity ≠ thoroughness.
- **Session cost** — 2× model calls = 2× token cost. Use for high-stakes reviews only.
- **Consensus ≠ completeness** — Both models can share the same blind spot (e.g., both missed HTML/CSS issues because they're "code" focused, not "UI" focused). Add domain-specific reviewers for multi-layer stacks.

---

## Phase 2: Systematic Fix Pipeline

After the review produces a prioritized issue list, execute fixes as a **sequential pipeline** — not a random walk.

### Step 6 — Prioritize by consensus × severity

| Tier | Criteria | Action |
|------|----------|--------|
| **P0** | Both models: CRITICAL | Fix **now**. These are real bugs with high confidence. |
| **P1** | One model: CRITICAL + other: HIGH/MEDIUM | Fix after P0. Investigate first — ~60% are real, ~40% are noise. |
| **P2** | One model: HIGH, other agrees it's real | Fix after P1. Lower urgency, lower risk. |
| **P3** | One model: MEDIUM/LOW | Optionally fix. Dead code, naming, docstring drift. |

**Validation rule:** Run the full test suite after fixing each tier. If tests fail, identify which specific fix broke them — don't batch-and-hope.

### Step 7 — Fix in priority order

**For each fix tier (P0 → P1 → P2 → P3):**

```
For each issue:
  1. Read the relevant code (not just the diff — full context)
  2. Write a regression test that proves the bug exists (RED)
  3. Implement the fix — change ONE thing at a time
  4. Run the regression test (GREEN)
  5. Run the full test suite — zero regressions
  6. Commit with issue reference in message
```

**Never batch multiple issue fixes in one commit** across tiers. P0 gets its own commit, P1 gets its own, etc. This makes `git bisect` clean and rollbacks safe.

### Step 8 — Prioritization gotchas

**The order rule is strict:**
1. **Math correctness** first. If the fundamental formula is wrong, all downstream logic is suspect. Fixing performance before accuracy is cargo-culting.
2. **Statistical correctness** second. If your Monte Carlo / aggregation is biased, every confidence interval is wrong.
3. **Missing features** third. Don't polish a car missing its engine.
4. **Performance** fourth. Don't optimize wrong math.
5. **Code quality / dead code** last. Deletions can't cause regressions.

### Step 9 — Cross-validate after fixing

After the fix pipeline completes, run the adversarial review **again** on the fixed code. One full cycle of review → fix → re-review catches ~90% of issues. Two cycles catches ~99%.

### Step 10 — Commit discipline

```
commit 1: "P0 — [module]: fix [specific bug]"
commit 2: "P1 — [module]: fix [specific bug]"
commit 3: "P2 — [module]: fix [specific bug]"
```

Each commit message should name the specific bug, not just the category ("fix bugs" is unhelpful). This structure makes release notes write themselves.

---

## Case Study Extension: TXPokerAssist Fix Pipeline

**Session structure:** 6 todos, executed in strict priority order:

| Tier | Issues | Commits | Tests before | Tests after | Time |
|------|--------|---------|-------------|-------------|------|
| P0 | EV formula, whole-pot MC, opponent ranges | 1 commit (3 issues) | 27/27 | 27/27 | ~15min |
| P1 | parallel MC, time_ms, compare_hands, cleanup | 1 commit | 27/27 | 27/27 | ~10min |

**Key insight:** P0 fixes changed the mathematical output of every calculation. Running tests after P0 confirmed the new output was *different but still correct* (equity ranges shifted but assertions held). If you'd fixed performance first, you'd have optimized wrong code.

**Performance before/after P1 fix:**
- 10,000 sims serial: 4.0s → 10,000 sims parallel: 1.1s (3.6x improvement)
- But this improvement would have been meaningless without correct math first.

**Lessons:**
1. Math first, stats second, features third, performance fourth — always
2. Test suite that uses loose assertions (e.g., "equity > 0.75") survives refactors better than hardcoded expected values
3. Fixing in priority order means each commit is self-verifying — no "oops, that broke something I fixed earlier"
