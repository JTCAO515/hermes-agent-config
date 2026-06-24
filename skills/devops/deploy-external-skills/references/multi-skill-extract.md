# Multi-Skill Repo Extraction Techniques

Field notes from bulk-extracting skills from repositories with many SKILL.md files.

## phuryn/pm-skills (68 skills)

**Repo structure:** Plugins organized by PM domain, each with `skills/<name>/SKILL.md`.
```
pm-product-discovery/skills/brainstorm-ideas-existing/SKILL.md
pm-product-discovery/skills/identify-assumptions-new/SKILL.md
pm-execution/skills/create-prd/SKILL.md
...
```

**Extraction command:**
```bash
git clone --depth 1 https://github.com/phuryn/pm-skills.git ~/projects/pm-skills
cd ~/projects/pm-skills
find . -name 'SKILL.md' -type f | while read f; do
  name=$(grep '^name: ' "$f" | head -1 | sed 's/name: //' | tr -d '[:space:]')
  [ -z "$name" ] && name=$(basename "$(dirname "$f")")
  mkdir -p ~/.hermes/skills/"$name"
  cp "$f" ~/.hermes/skills/"$name"/SKILL.md
done
```

**Notes:**
- All SKILL.md files had standard Hermes frontmatter (`name:`, `description:`)
- No modifications needed — direct copy works
- 68 skills across 9 plugin directories

## ljg-skills (16 skills)

**Repo structure:** Each skill in its own subdirectory at repo root.
```
ljg-card/SKILL.md
ljg-plain/SKILL.md
ljg-learn/SKILL.md
...
```

**Extraction:**
```bash
# Fetch each SKILL.md from raw GitHub URL
for skill in card plain learn writes book paper qa rank think word invest read travel present roundtable skill-map; do
  mkdir -p ~/.hermes/skills/ljg-$skill
  curl -sL "https://raw.githubusercontent.com/lijigang/ljg-skills/main/ljg-$skill/SKILL.md" \
    > ~/.hermes/skills/ljg-$skill/SKILL.md
done
```

**Notes:**
- Can use HTTP fetch instead of git clone for speed
- Skill names are predictable (`ljg-<name>`)

## Egonex-AI/Understand-Anything (8 skills)

**Repo structure:** Skills in `understand-anything-plugin/skills/`.
```
understand/SKILL.md
understand-chat/SKILL.md
understand-dashboard/SKILL.md
...
```

**Extraction:**
```bash
git clone --depth 1 https://github.com/Egonex-AI/Understand-Anything.git ~/projects/Understand-Anything
cd ~/projects/Understand-Anything/understand-anything-plugin/skills
for d in */; do
  name=$(basename "$d")
  mkdir -p ~/.hermes/skills/"$name"
  cp "$d/SKILL.md" ~/.hermes/skills/"$name"/SKILL.md
done
```

**Notes:**
- Has native Hermes support via `install.sh hermes` — but the script only copies SKILL.md files anyway
- Full functionality needs Node.js 22+ and pnpm for the analysis engine
- ⚠️ The skills reference bundled scripts in `languages/`, `frameworks/`, `locales/` subdirectories — those are NOT copied and won't work without the full plugin checkout. For Hermes, these skills serve as documentation/reference only unless the full plugin is also cloned.

## pm-skills nuance

The pm-skills repo has 68 skills spread across 9 plugin directories:
```
pm-product-discovery/skills/<name>/SKILL.md      (13 skills)
pm-product-strategy/skills/<name>/SKILL.md        (12 skills)
pm-execution/skills/<name>/SKILL.md               (16 skills)
pm-market-research/skills/<name>/SKILL.md          (7 skills)
pm-go-to-market/skills/<name>/SKILL.md             (5 skills)
pm-marketing-growth/skills/<name>/SKILL.md         (5 skills)
pm-data-analytics/skills/<name>/SKILL.md           (5 skills)
pm-ai-shipping/skills/<name>/SKILL.md              (3 skills)
pm-toolkit/skills/<name>/SKILL.md                  (2 skills)
```

All 68 use standard Hermes frontmatter. The `name:` field in each SKILL.md matches the directory name, but the script below uses the frontmatter as the primary name source. No modifications needed — direct copy works.

## Figma MCP Official Skills (9 skills)

**Source:** `https://github.com/figma/mcp-server-guide` → `skills/` directory

**Skills installed:**
- `figma-use` — Plugin API write operations (create/edit nodes, variables, auto-layout)
- `figma-use-figjam` — FigJam whiteboard operations
- `figma-use-slides` — Figma Slides presentations
- `figma-code-connect` — Figma component → code snippet mapping
- `figma-create-new-file` — New blank Figma file creation
- `figma-generate-diagram` — Mermaid → FigJam diagram generation
- `figma-generate-design` — Code → Figma screen/view building
- `figma-generate-library` — Design system library construction
- `figma-swiftui` — SwiftUI ↔ Figma bidirectional translation

**Installation:**
```bash
# Download repo
cd /tmp && curl -sL "https://github.com/figma/mcp-server-guide/archive/refs/heads/main.zip" -o figma-skills.zip
unzip -q figma-skills.zip

# Install all 9 skills
for d in mcp-server-guide-main/skills/figma-*/; do
  name=$(basename "$d")
  mkdir -p ~/.hermes/skills/"$name"
  cp -r "$d"/* ~/.hermes/skills/"$name"/
done
```

**Notes:**
- Each skill has `SKILL.md` + `references/` directory — full copy (`cp -r`) preserves references
- Frontmatter is properly formatted (`name:`, `description:`, `disable-model-invocation: false`)
- All skills reference each other via relative paths (`../figma-use/SKILL.md`) — install ALL or note cross-references may break
- Figma MCP server connection (separate from skills) needed for actual tools: `mcp.json` → `{"figma": {"type": "http", "url": "https://mcp.figma.com/mcp"}}`
- Require Figma account with Dev/Full seat for meaningful use (rate limits: 6 calls/month for Starter, unlimited for Pro/Org/Enterprise)
- ⚠️ 9 skills at once is a lot of context — only load the specific ones needed for the current task
- Strategy: This repo is a **docs/guide repo** containing skills, not a pure skill repo. The `skills/` directory is the target; ignore root-level files

## 君言 (ljg-skills) — 16 skills

Same repo as above. Separated for clarity.

## General Pattern

Most multi-skill repos follow one of two structures:

1. **Flat:** `skills/<name>/SKILL.md` — extract by scanning `find . -name 'SKILL.md'`
2. **Nested by category:** `<category>/skills/<name>/SKILL.md` — same extraction works

**Name fallback:** If `grep '^name: '` returns empty, use `basename "$(dirname "$f")"` as the skill directory name.

**SKILL.md compatibility check:** Always spot-check one file for proper frontmatter. Claude Code skills sometimes omit the `---` frontmatter delimiters or use different fields — those need manual conversion.
