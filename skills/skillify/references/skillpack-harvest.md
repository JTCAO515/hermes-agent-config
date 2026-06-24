# Skillpack Harvest — Lift Skills Upstream

> Absorbed from standalone `skillpack-harvest` skill (2026-06-02).

## Purpose

Lift a proven skill from a host repo (e.g. OpenClaw fork) back into gbrain's bundle so other clients can scaffold it.

## Preconditions

1. Skill is mature (used in production, recent routing-eval cases pass)
2. Skill is generalizable (strip-test: replace fork-specific names)
3. User owns the gbrain checkout

## Workflow

### Phase 1 — Plan
Ask user: slug name, host repo path, whether paired source files come along.

### Phase 2 — Dry Run
```bash
gbrain skillpack harvest <slug> --from <host-repo-root> --dry-run
```

### Phase 3 — Genericization Checklist
- Fork-specific names → generic phrasing
- Real entities → placeholders
- Fork-specific conventions → references
- Triggers array generalizes
- routing-eval.jsonl examples scrubbed
- Code comments checked

### Phase 4 — Real Harvest
```bash
gbrain skillpack harvest <slug> --from <host-repo-root>
```

### Phase 5 — Verify
```bash
bun test test/skills-conformance.test.ts
gbrain skillpack check --strict
gbrain skillpack list
```

## Anti-Patterns

- ❌ Skipping the dry-run
- ❌ Harvesting a skill still in flux
- ❌ Moving files instead of copying (harvest = copy)
- ❌ Harvesting batch (multiple skills at once)
