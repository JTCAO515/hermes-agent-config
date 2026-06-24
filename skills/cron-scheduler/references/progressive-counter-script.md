# Progressive Counter Script Pattern

A reusable cron pattern for jobs that need to track **progressive state** (e.g., day counters, sequence numbers, tiered milestones) across executions.

## Problem

Standard cron jobs are stateless — each run is independent. But some tasks need to know "what iteration are we on":
- 30-day interview (Day → Week → Theme)
- N-week habit tracker
- Escalating retry/reminder sequence
- Rotating prompt templates (different questions each day)

## Solution

A Python tracking script placed in `~/.hermes/scripts/` that:
1. Reads a counter file (`~/.hermes/cron/counter-<name>.txt`)
2. Increments / computes the next state
3. Writes the updated state back
4. Outputs variables that get **injected into the cron prompt**

## Contract

```
cron (scheduled)
  └── tracking-script.py ← no arguments, deterministic
        └── reads:  ~/.hermes/cron/counter-<name>.txt
        └── writes: same file (incremented state)
        └── stdout: KEY=VALUE (one per line)
              ↓ injected into prompt
              ↓ agent uses {{KEY}} references
```

## Script Template

```python
#!/usr/bin/env python3
import os

COUNTER = os.path.expanduser("~/.hermes/cron/counter-<name>.txt")

def main():
    os.makedirs(os.path.dirname(COUNTER), exist_ok=True)

    if os.path.exists(COUNTER):
        with open(COUNTER) as f:
            try:
                n = int(f.read().strip())
            except ValueError:
                n = 0
        n = min(n + 1, MAX_VALUE)
    else:
        n = 1  # or 0, depending on first-run semantics

    with open(COUNTER, "w") as f:
        f.write(str(n))

    # Output variables for prompt injection
    print(f"COUNTER={n}")
    print(f"PHASE={compute_phase(n)}")
    ...

if __name__ == "__main__":
    main()
```

## Rules

- Script path is **relative to `~/.hermes/scripts/`** — use just the filename, not absolute path
- Must NOT reset the counter — the agent resets by `echo 0 > ~/.hermes/cron/counter-<name>.txt`
- Output goes to stdout — each line `KEY=VALUE` becomes a variable in the prompt
- Variables are referenced in the prompt as `{{KEY}}` — the `{{VALUE}}` format from the script output
- First-run logic handles the case where counter file doesn't exist yet
- Max value cap (e.g., 30 for a 30-day program) to prevent overflow

## Verification

```bash
# Test the script
python3 ~/.hermes/scripts/<name>.py

# Check counter
cat ~/.hermes/cron/counter-<name>.txt

# Reset
echo 0 > ~/.hermes/cron/counter-<name>.txt

# Manual trigger
hermes cron run --job-id <job-id>
```

## Example: 30-Day Interview

See `self-cognition` skill reference `references/cron-progressive-interview.md` for a complete implementation.
