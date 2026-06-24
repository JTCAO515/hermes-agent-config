---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### ⚠️ CRITICAL: read_file() Line-Number Corruption

When debugging Android/Kotlin projects, NEVER use the content of `read_file()` as input to `write_file()` — the returned content includes line-number prefixes (`     1|package ...`) that corrupt the file when written back.

**The problem:**
```python
# ❌ WRONG — corrupts the file
r = read_file("SomeActivity.kt")
write_file("SomeActivity.kt", r["content"])  # writes "     1|package ..." 
```

**Symptoms of corruption:**
- Build error: `Unresolved reference: onStartChat` even though you added the parameter
- File shows `     1|     1|package` at the start
- Git diff shows massive deletions/insertions (e.g., "+313 -75" for a small change)

**Correct approach — use native Python I/O inside execute_code:**

```python
def fix_file(path, callback):
    with open(path, "r") as f:
        content = f.read()
    result = callback(content)
    with open(path, "w") as f:
        f.write(result)

# Then use it:
fix_file("/path/to/file.kt", lambda c: c.replace("old", "new"))
```

Or use the `patch` tool with unique surrounding context:
```python
patch(mode="replace", 
      old_string="onClick = { onCityClick(\"all\") }",
      new_string="onClick = { onViewAllCities() }",
      path="/path/to/file.kt")
```

**Prevention:**
- For targeted changes: prefer `patch` tool over `read_file`+`write_file`
- For bulk rewrites: use `write_file` with fresh content you construct directly
- Never pipe `read_file["content"]` into `write_file` without stripping line numbers first
- After any such operation, verify first few bytes: `head -1 file.kt` should NOT show `     1|`

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Framework-Specific Pitfalls

These are known bug patterns that look like mysterious 500 errors or wrong behavior but have a specific root cause. **Always check these before deep-diving into custom logic.**

### Android/GitHub Actions Build Debugging

**Symptom:** GitHub Actions `assembleRelease` workflow fails at `:app:compileReleaseKotlin` step. Build log shows "Compilation error. See log for more details" but no obvious error in the tail.

**Method — Extract Kotlin errors from GitHub Actions logs:**

```bash
# 1. Find run IDs
curl -s -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?per_page=5" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f\"#{r['run_number']} | {r['id']} | {r['status']} | {r['head_commit']['message'][:60]}\") for r in d.get('workflow_runs',[])]"

# 2. Download and extract logs
RUN_ID="<run_id>"
curl -L -s -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs" \
  -o /tmp/gh_logs.zip
cd /tmp && rm -rf gl && mkdir gl && cd gl
unzip -q ../gh_logs.zip

# 3. Find Kotlin errors (grep for .kt: lines)
grep "\.kt:" build/*.txt | grep -i "error\|unresolved\|type mismatch" | head -20

# 4. Focus on first error — Kotlin stops at first compilation error
```

**Iterative fix loop (Kotlin: one error at a time):**
- Kotlin's compiler stops at the first batch of errors. Fix ALL errors from one build, then push and re-trigger.
- Common categories:
  - **Too many arguments for constructor** — data class was simplified (e.g., MapMarker lost `vibe`/`days`/`nameCn` fields). Fix call sites or keep fields.
  - **Unresolved reference** — missing import, undefined function/parameter in nested composable scope, or field doesn't exist on the model
  - **Type mismatch** — often caused by OkHttp API changes (`MediaType.parse()` → `"text/json".toMediaType()`)
  - **Missing toRequestBody** — replace `*` wildcard imports with specific ones

**Key Kotlin import rules (OkHttp):**
```kotlin
// ❌ OLD — wildcard import masks missing symbols
import okhttp3.*

// ✅ NEW — explicit imports for what you actually use
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Callback
import okhttp3.Call
import okhttp3.Response
// Also need: okio.BufferedSource (for exhausted()/readUtf8Line())
```

**Nested composable parameter trap:**
When a composable function has a private helper function (`private fun CityDetailContent(...)`), extra parameters (like `onStartChat`) must be EXPLICITLY passed:
```kotlin
// CityDetailScreen has onStartChat
CityDetailScreen(cityName, onBack, onStartChat) {
    // But CityDetailContent is a separate function — it CANNOT see onStartChat
    CityDetailContent(uiState)  // ❌ onStartChat not available here
}

// Fix — pass it explicitly:
CityDetailContent(onStartChat = onStartChat, uiState = uiState)
private fun CityDetailContent(onStartChat: (String) -> Unit = {}, uiState: ...)
```

**Build time heuristic:**
- < 2 minutes → Compilation error (Kotlin stops fast)
- 3-5 minutes → Running tests or packaging
- 5+ minutes → Running successfully or stuck

### FastAPI: HTTPException swallowed by `except Exception`

**Symptom:** You raise `HTTPException(400)` for input validation, but client receives 500. Server logs show the 400 exception traceback.

**Root cause:** `HTTPException` inherits from `Exception`, so `except Exception` catches it and re-raises as 500.

**Fix:** Add `except HTTPException: raise` before `except Exception`:

```python
try:
    if invalid:
        raise HTTPException(status_code=400, detail="bad")
except HTTPException:
    raise  # Let FastAPI handle it correctly
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Detection:** Check server logs — if you see `HTTPException: 4XX: message` in traceback but client gets 500, this is the bug.

### JavaScript: Empty string `.split()` producing `['']`

**Symptom:** Backend receives `['']` instead of `[]` for an empty field.

**Root cause:** `''.split(' ')` returns `['']`, not `[]`.

**Fix:** Filter after split: `arr.split(' ').filter(x => x.trim())` or check emptiness first.

### JavaScript: Referenced-but-undefined function in template literals

**Symptom:** A tab/section renders empty or shows nothing. No visible JS error on page load — error only fires when user clicks that specific tab. The error bubbles through `.map().join('')` inside a template literal, so it hits the async catch block or gets swallowed entirely.

**Root cause:** A function called inside a template literal (`${gs(someValue)}`) was never defined (no `function gs()` anywhere in the file). The template literal throws `ReferenceError: gs is not defined` at render time, which prevents the entire `.map().join('')` from completing. The catch handler sets a generic "ERR" or "加载失败" message, masking the real bug.

**Detection — Function Audit (always run this when a section shows empty):**

```bash
# 1. List all function calls inside template literals in the render function
grep -oP '\$\{[^}]*\w+\([^}]*\}' web/app.js | grep -oP '\w+(?=\()' | sort -u

# 2. Cross-reference against defined functions
grep -oP '(function |const |let |var |window\.)\w+' web/app.js | sort -u

# 3. Find any referenced function NOT in the defined list — those are the bugs
```

Or for a quick single-file check:

```javascript
const fs = require('fs');
const js = fs.readFileSync('web/app.js', 'utf-8');
const fns = ['escHtml', 'gs', 'renderSchedule', /* ... all expected functions */];
fns.forEach(fn => {
    const defined = js.includes('function ' + fn) || js.includes(fn + ' = ') || 
                    js.includes('const ' + fn) || js.includes('window.' + fn);
    if (!defined) console.log('MISSING: ' + fn);
});
```

**Fix:** Either define the missing function or replace the call with an existing equivalent. Common pattern: `escHtml` as alias for `esc`.

**Prevention — large JS refactoring safety check (do before git push):**
1. Before modifying a large JS file, extract all function names that are called in template literals
2. After modifying, run the cross-reference check above
3. Pay special attention to functions used inside `.map().join('')` chains — any error there silently kills the entire render output
4. Remember that `0` is falsy in JS — use explicit `!= null` checks, not `||` defaults, for numeric display values

**Pitfall — "silently broken since launch":** Pre-existing bugs (like `gs` never being defined) can persist indefinitely if the affected section is rarely visited. The schedule tab was "working" (no visible error) but every match with a result would throw a runtime error. Nobody noticed because:
- The tab shows a loading message first
- If data loads slowly, users see "加载中..." and think it's still loading
- The error only fires for matches that `has_result === true`
- The `catch` block swallows the error, showing nothing useful

**Fix philosophy:** Always verify all code paths when debugging "empty section" bugs — not just the code you changed, but all code that runs in that section.

## Reference Files

- `references/frontend-loading-spinner.md` — Debugging "page stuck at loading spinner forever": JS SyntaxError, Service Worker cache trap, API hang detection, and silent template-literal errors. Use this when a SPA loads HTML but the spinner never resolves.
- `references/api-probing-methodology.md` — Reverse-engineering unknown APIs when docs are behind a login or unavailable. Systematic error-message analysis to discover auth format, param names, and endpoint structure — especially for Chinese API providers that use IP whitelisting + query-param auth.
- `references/template-literal-onclick-corruption.md` — Debugging broken HTML from template-literals-generated onclick handlers. When rendered output shows raw JavaScript source code instead of UI elements, the root cause is nested backticks in template literals. Fix with event delegation (`e.target.closest()` + `data-*` attributes).

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**
