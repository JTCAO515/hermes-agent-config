# Skill Creator — SKILL.md Template Generator

> Absorbed from standalone `skill-creator` skill (2026-06-02). Use this as Phase 1 reference when creating a new SKILL.md.

## Frontmatter Template

```yaml
---
name: {skill-name}
version: 1.0.0
description: |
  {One paragraph describing what the skill does and when to use it.}
triggers:
  - "{trigger phrase 1}"
  - "{trigger phrase 2}"
tools:
  - {tool1}
  - {tool2}
mutating: {true|false}
---
```

## Required Body Sections

- **Contract** — What this skill guarantees (3-5 bullet points)
- **Phases** — Numbered workflow steps
- **Output Format** — What good output looks like
- **Anti-Patterns** — What NOT to do (3-5 items)

## MECE Check

Before creating, verify no existing skill covers the same triggers. Check:
- `skills_list` output for description overlap
- Manifest and resolver for trigger phrase collisions
