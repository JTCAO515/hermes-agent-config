## Known Issues

### grill-with-docs name collision

Two skills with the same name `grill-with-docs` exist after bulk install:
- `/home/ubuntu/.hermes/skills/grill-with-docs/SKILL.md` (root level, original)
- `/home/ubuntu/.hermes/skills/software-development/grill-with-docs/SKILL.md` (subcategory, duplicate)

**Symptom:** `skill_view(name='grill-with-docs')` fails with "Ambiguous skill name: 2 skills match."
**Fix:** Load by categorized path: `skill_view(name='software-development/grill-with-docs')` or delete the duplicate.

### 4 skills with raw CDN 404 (reconstructed from web_extract)

These SKILL.md files were manually reconstructed on 2026-06-19 because `raw.githubusercontent.com` returned 404 despite files existing on GitHub:

| Skill | GitHub path | Reconstructed from |
|-------|-------------|-------------------|
| `diagnose` | `skills/engineering/diagnose/SKILL.md` | web_extract of GitHub blob page |
| `zoom-out` | `skills/engineering/zoom-out/SKILL.md` | web_extract of GitHub blob page |
| `decision-mapping` | `skills/in-progress/decision-mapping/SKILL.md` | web_extract of GitHub blob page |
| `review` | `skills/in-progress/review/SKILL.md` | web_extract of GitHub blob page |

**Verification:** If upstream changes, these reconstructed versions may be stale. Pull fresh content from GitHub blob page and re-reconstruct if issues arise.
