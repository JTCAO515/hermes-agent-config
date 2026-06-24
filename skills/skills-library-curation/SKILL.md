---
name: skills-library-curation
description: |
  Manage, find, install, organize, deduplicate, and create scenario
  recommendations for a large skills library. Use when the user asks you to
  "organize skills", "merge skill guides", "install missing skills",
  "deduplicate skills", "categorize skills", "create skill combinations",
  or "review the skill library". Covers the end-to-end lifecycle of
  curating a collection of 100+ skills across multiple ecosystems (Hermes
  native, npx skills ecosystem, GitHub raw).
triggers:
  - "organize skills"
  - "merge skill guide"
  - "install missing skills"
  - "deduplicate skills"
  - "categorize|classify skills"
  - "skill combo|combination|scenario"
  - "review skill library"
  - "curate skills"
  - "skill gardening"
  - "clean up skills"
  - "整理技能"
  - "skills 去重"
  - "skills 分类"
---

# Skills Library Curation

## Contract

This skill guarantees a systematic approach to:
1. Comparing skill lists across ecosystems (Hermes/npx/GitHub raw)
2. Finding and installing missing skills from any accessible source
3. Categorizing a skill list by functional domain (design, finance, AI, etc.)
4. Detecting and documenting overlaps/duplicates between skills
5. Creating usage-scenario combo recommendations

## Phases

### Phase 0: Inventory

Always start with the full installed list:

```bash
hermes skills list
# or via Hermes: skills_list tool
```

If the user provides a reference guide from another ecosystem (e.g. SKILLS_GUIDE.md from npx skills), extract the named skills and compare.

### Phase 1: Find missing skills

Two sources for finding skills:

**Source A — npx skills ecosystem (recommended first):**
```bash
npx skills find "<skill-name>"
```
Parses output for `owner/repo@skill` format → `skills.sh/<owner>/<repo>/<skill>` page → derive GitHub raw URL.

**Source B — direct GitHub raw URL search:**
```
https://raw.githubusercontent.com/<owner>/<repo>/main/SKILL.md
https://raw.githubusercontent.com/<owner>/<repo>/main/skills/<skill>/SKILL.md
```

Common proven sources:
- `mattpocock/skills` — most engineering/productivity skills
- `op7418/humanizer-zh` — Chinese text humanizer
- `davila7/claude-code-templates` — gh-fix-ci and other dev skills
- `anthropics/skills` — internal-comms and other official Anthropic skills

**Pitfall:** Many skills in npx ecosystem do NOT have publicly accessible GitHub repos (e.g. `hyperframes`, `motion-graphics`, `gsap-*`, `yeet`). In that case, record the gap and offer alternatives.

### Phase 2: Install missing skills

**Preferred method** — direct download (avoids `hermes skills install` hanging):

```bash
mkdir -p ~/.hermes/skills/<skill-name>
curl -s --noproxy '*' "<raw-SKILL.md-url>" > ~/.hermes/skills/<skill-name>/SKILL.md
```

**Fallback** — official Hermes installer (may hang behind some proxies):

```bash
hermes skills install "<url>" --name <name> --yes
```

**Pitfall:** If `hermes skills install` hangs indefinitely, the SKILL.md was still fetched but install didn't complete. Cancel and use the direct download method instead.

**Git push failure:** If `git clone`/`git push` fails (no disk space, network blocked), use the GitHub REST API to create files directly. See `references/install-workarounds.md` → "When Git Clone Fails".

**Verification:**
```bash
ls ~/.hermes/skills/<name>/SKILL.md
wc -c ~/.hermes/skills/<name>/SKILL.md
```

### Phase 3: Categorize

Use keyword-based classification to bucket skills by functional domain. Default category buckets:

| Category | Keywords |
|----------|----------|
| 设计与前端 | design, figma, ui, ux, sketch, css, html, frontend, motion, animation, gsap, pixel, ascii, excalidraw, p5js, web-design, claude-design, drawio |
| 写作与内容 | writing, humanizer, article, editor, fragment, beat, shape, grammar, release-notes, internal-comms |
| 金融与投资 | model, finance, bond, swap, option, equity, portfolio, lbo, dcf, merger, comps, accrual, recon, earnings, valuation, pitch, cim, deal, stock, futu, macro, rates |
| 编程与开发 | tdd, test, debug, diagnose, codereview, python, typescript, git, github, pr, refactor, architect, prototype, coding, workflow |
| 产品与商业 | product, prd, user-stories, feature, roadmap, north-star, metrics, analytics, cohort, pricing, gtm, competitive, business-model |
| AI/ML | llm, dspy, vllm, llama, unsloth, axolotl, fine-tun, rag, swarm, image-generation, qwen-voice |
| DevOps | deploy, vercel, cloud, remote-desktop, pwa, android, xray, cron, webhook |
| 前端框架 | vue, react, nuxt, vitepress, vite, pinia, vueuse, unocss, turborepo |
| 工具集成 | notion, linear, airtable, obsidian, docx, xlsx, powerpoint, maps, spotify |
| 搜索与研究 | search, arxiv, tavily, wiki, blogwatcher, perplexity, agent-reach |
| 教练与沟通 | coach, qingsheng, relationship, hinge, sage, self-cognition |
| 认知与学习 | structured-thinking, ljg, strategic-reading, teach, knowledge-extractor |

Unmatched skills go into a "misc/未分类" bucket. That's fine — better unclassified than force-fit.

### Phase 4: Deduplicate

Look for these common overlap patterns:

1. **Same approach, two names**: `tdd` vs `test-driven-development`, `planning` vs `planning-with-files`
2. **Different ecosystem, same job**: `design-taste-frontend` vs `frontend-design` vs `ui-ux-pro-max`
3. **Umbrella absorbs sub-variants**: `hindsight` absorbs `hindsight-architect/local/cloud/...`
4. **Built-in tool supersedes skill**: browser tools > `web-access/playwright/webapp-testing`
5. **Prototype install vs mature install**: check if both are actually installed or one was never installed

For each overlap found, decide: **keep one, alias, or document as alternatives** — never delete without user confirmation.

### Phase 5: Create scenario recommendations

Build "combo sets" for common user scenarios. Structure:

```
### 🧑‍💻 [Scenario Emoji + Name]
```
skill-A → skill-B → skill-C → skill-D
```

Brief rationale for why this sequence works (1-2 lines).
```

Common scenarios to cover:
- 日常开发 (grill → decision-mapping → planning → tdd/diagnose → review → verification)
- 新项目启动 (design-taste-frontend → sketch → figma → create-prd → to-issues → coding-workflow)
- 写作 (writing-fragments → writing-beats → writing-shape → humanizer)
- 金融建模 (deal-workflow → cim-builder → dcf-model/lbo-model → pitch-deck)
- 产品设计 (brainstorming → assumptions-prioritization → user-stories → create-prd → sprint-plan)
- CI 故障 (gh-fix-ci + diagnose)
- AI 微调 (dspy → axolotl/unsloth → evaluating-llms-harness)
- 数据分析 (data-analysis + sql-queries + show-widget)

## Output Format

Deliverable: one merged guide document (`SKILLS_GUIDE_MERGED.md`) containing:

```
# Skills Guide — Merged

## 新装技能
- 从参考指南新装的技能清单

## 分类目录（去重后）
- 按功能组组织的表格/列表
- 每组包含技能名称、用途、去重说明

## 去重说明
- 保留 vs 合并/替代的映射表

## 使用场景搭配
- 8-12 个常见场景的组合推荐
```

## Anti-Patterns

- ❌ Installing missing skills before understanding the full inventory
- ❌ Keyword-only classification without manual review (keyword hits produce false positives)
- ❌ Deleting overlapping skills without user confirmation
- ❌ Creating wide flat lists instead of grouped categories
- ❌ Skipping the "not found" documentation for unavailable skills
- ❌ Assuming npx skills ecosystem skills are installable into Hermes (many are not)
