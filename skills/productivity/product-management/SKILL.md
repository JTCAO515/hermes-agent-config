---
name: product-management
version: 1.2.0
description: |
  Product management documentation suite. Structured templates for competitive
  analysis, consulting reports, brainstorming, PRDs, user story mapping,
  executive reports, product launch docs, and product development handoff documents.
  One class-level skill with labeled subsections covering the full product
  documentation lifecycle.
triggers:
  - "竞品分析"
  - "竞争分析"
  - "competitor"
  - "咨询报告"
  - "研报"
  - "SWOT"
  - "行业分析"
  - "脑暴"
  - "brainstorm"
  - "写PRD"
  - "产品需求"
  - "功能规格"
  - "用户故事"
  - "user story"
  - "故事地图"
  - "需求拆分"
  - "epic"
  - "对标"
  - "差异化"
  - "市场定位"
  - "产品说明书"
  - "产品说明"
  - "汇报文档"
  - "去汇报"
  - "产品介绍"
  - "product spec"
  - "product specification"
  - "executive reporting"
  - "立项"
  - "立项评审"
  - "WC26的方式"
  - "产品启动文档"
  - "三件套"
  - "产品拆解"
  - "迭代方向"
  - "项目目标"
  - "产品开发设计"
  - "开发设计文档"
  - "内部功能"
  - "内部功能开发"
  - "内部功能开发工作流"
  - "技术交付说明"
  - "研发负责人视角"
  - "研发视角"
  - "PM产品说明"
  - "先写pm"
  - "手把手交付"
  - "手把手文档"
  - "代码编写SOP"
  - "Coding SOP"
  - "外包交付"
  - "外包文档"
  - "给其他人开发"
  - "交给别人做"
  - "handoff"
  - "开发设计说明"
mutating: false
---

# Product Management Documentation Suite

> Umbrella skill absorbing: `competitive-analysis`, `consulting-report`, `brainstorm`, `prd-generator`, `user-story-mapping` (archived 2026-06-02).

Eight product management artifact templates. Each is a labeled subsection — use the relevant one based on what you need to produce.

**v1.3.0:** New Section J — Internal Feature Development Workflow (内部功能开发工作流), a two-document approach for adding features to an existing product: PM Requirements Doc → Tech Delivery Doc → Implement. Captures the "先写PM产品说明 → 从研发负责人角度写技术交付说明" pattern.

---

## Section A: Competitive Analysis

Structured comparison of competitors across features, pricing, positioning, and GTM strategy.

### Framework

| Dimension | Us | Competitor A | Competitor B | Gap/Opportunity |
|-----------|-----|-------------|-------------|-----------------|
| Core features | | | | |
| Pricing | | | | |
| Channels | | | | |
| Brand | | | | |

### 6 Perspectives

1. **Competitive Matrix:** Feature completeness (X) × Price/Positioning (Y)
2. **Feature Comparison:** Core features with /⚠️/❌ ratings
3. **Pricing Comparison:** Basic/Pro/Enterprise tiers
4. **GTM Strategy:** Channels, content, community, sales
5. **Differentiation Opportunity:** What competitors can't do but we can
6. **Threat Assessment:** Where competitors might attack

---

## Section B: Consulting Report

Full consulting-grade research report with structured sections.

### Report Structure

1. **Executive Summary** (1-2 pages) — Core findings and recommendations
2. **Background & Methodology** — Scope, data sources
3. **Market Analysis** — Size, trends, drivers
4. **Competitive Landscape** — Major players, share, differentiation
5. **SWOT Analysis** — Strengths/Weaknesses/Opportunities/Threats
6. **Strategic Recommendations** — Short-term (0-6m) / Mid-term (6-18m) / Long-term
7. **Appendix** — Data sources, methodology docs

### Output

Markdown → convertible to docx/pdf. Each strategic recommendation includes: objective / actions / KPIs / timeline.

---

## Section C: Structured Brainstorming

Divergence → Convergence → Refinement for creative idea generation.

### Phase 1: Divergence (no judgment, only generate)

Select framework by problem type:

| Problem Type | Framework |
|-------------|-----------|
| Product features | SCAMPER (Substitute/Combine/Adapt/Modify/Put to other use/Eliminate/Rearrange) |
| Market strategy | 4P+AI (Product/Price/Place/Promotion + Tech) |
| Content ideas | 6 Angles (Pain/Emotion/Counter-intuitive/Data/Story/Comparison) |
| UX optimization | User journey (Before/During/After × Touchpoints) |
| Business model | Canvas 9-box |

**Rule:** Minimum 3 ideas per angle. Feasibility is Phase 2's problem.

### Phase 2: Convergence (filter + rank)

Use 2x2 matrix:
- Y-axis: Impact (High/Low)
- X-axis: Difficulty (Easy/Hard)

Prioritize: High Impact + Easy → **Top priority**

### Phase 3: Refinement (top 3-5)

For each selected idea:
- One-sentence description
- Why it was chosen
- Next step (what to validate)

---

## Section D: PRD Generator

Product Requirements Document with full structure.

### Sections

1. **Meta info:** Version / Author / Date / Status
2. **Problem Definition:** User pain → Opportunity quantification → Solution hypothesis
3. **User Personas:** Role / Scenario / Pain points / Expectations
4. **Functional Specs:** Priority P0-P3 / Feature description / Interaction flow / Edge cases
5. **Non-functional Requirements:** Performance / Security / Compatibility
6. **Acceptance Criteria:** Given-When-Then format
7. **Success Metrics:** KPIs / OKRs
8. **Risks & Dependencies:** Technical / Business / Compliance

### Domain Adaptation

- Cross-border/SaaS: Auto-inject compliance checks, multi-language, currency
- Travel: Auto-inject seasonality, customer segments, supply chain
- Hardware: Auto-inject 3C certification, supply chain, BOM

---

## Section E: User Story Mapping

From user journey to Epic → Feature → User Story breakdown.

### Flow

1. **Define Persona**
2. **Draw Journey Map** — Stages → Activities → Tasks
3. **Decompose to Epics** (grouped by stage)
4. **Each Epic → Features** (by activity)
5. **Each Feature → User Stories** (As a... I want... So that...)

### Output Template

```markdown
Epic: [Name] (Priority P0-P3)
├── Feature 1: [Name]
│   ├── US-01: As a [role], I want [feature], so that [value]
│   │   Acceptance: Given/When/Then
│   └── US-02: ...
└── Feature 2: ...
```

### Priority Rules

- **P0:** Product unusable without it → MVP must-have
- **P1:** Significantly affects core experience → V1.0
- **P2:** Nice to have → V1.1
- **P3:** Long-term vision → Backlog

---

## Section G: Executive Report (汇报文稿)

Narrative-driven product report for **executive presentations, project approval reviews, and stakeholder alignment meetings**. Unlike the Product Spec (Section F — comprehensive reference), the Executive Report is a **persuasive narrative** that tells the full story in a logical arc: vision → market → solution → execution → success.

### When to Write

- User says "做成一份完整的汇报，可以直接拿去用的汇报"
- User says "从资深产品经理的角度去思考怎么写"
- Project approval / funding review / board presentation
- Cross-team launch kickoff

### How It Differs from Product Spec

| Dimension | Product Spec (Section F) | Executive Report (Section G) |
|-----------|------------------------|------------------------------|
| Reader | Engineers, PMs, cross-functional | Executives, investors, stakeholders |
| Tone | Descriptive, reference-like | Persuasive, narrative-driven |
| Structure | 14 flat chapters, any order | 10 progressive chapters, ordered arc |
| Data density | High (tables, schemas, specs) | Medium (summary tables, key metrics) |
| Emotional arc | None | Problem → Solution → Confidence |
| Call to action | None (reference document) | Yes: "approved / next step" |

### 10-Chapter Narrative Structure

| # | Chapter | Purpose | One-liner to sell it |
|---|---------|---------|---------------------|
| 1 | **执行摘要** | 3-minute read for busy execs | "This is what we built, this is where we are, this is what we need." |
| 2 | **产品愿景** | Why this exists, what we stand for | "We're not building a tool, we're building a decision-making partner." |
| 3 | **市场洞察** | Who needs this and why now | "200M players, 92% complain about the same thing, no one solves it right." |
| 4 | **产品设计方案** | What we're actually building | "5 decision types, 3-tier feature pyramid, this is how the user interacts." |
| 5 | **技术实现路径** | How it works under the hood | "Pure Python, zero external deps, 221 tests, runs in browser." |
| 6 | **迭代路线图** | Where we've been + where we're going | "Phase 1 done in 2 weeks. Phase 2 is 6 more iterations. We know the path." |
| 7 | **成功标准** | How we measure "done" and "winning" | "81/81 fans, 247+ tests, 15s time-to-analysis, public URL." |
| 8 | **商业价值** | Cost, revenue potential, ROI | "¥50/year ops cost. Revenue optional. Impact is the goal right now." |
| 9 | **风险评估** | What could go wrong | "Vercel cold start. Fan value drift. User input friction. All mitigated." |
| 10 | **下一步行动** | What needs to happen now | "This week: defense engine. Next: fan completion. You decide scope." |

### Writing Heuristics

- **每一章回答一个"汇报时被问到的问题"**: Don't pre-answer questions no one asked. Each chapter maps to a question a reviewer would naturally ask.
- **前三页定生死**: 执行摘要必须让读者在3分钟内理解"这是什么、为什么做、做到哪了、要什么"。前三页不过，后面不用看。
- **"为什么不做"比"做什么"重要**: Include a clear "not doing" list in the vision chapter. Shows strategic discipline.
- **数字带单位，时间带日期**: Not "lots of tests" but "221 tests (197 old + 24 new)". Not "soon" but "2026-06-10".
- **风险要诚实**: Executives spot whitewashed risk sections instantly. Include probability × impact × mitigation explicitly.
- **结尾必须带明确的"下一步":** 报告结束时读者应该知道他们需要做什么决定（批准/否决/投资更多/等结果）。

### Output

Save as `REPORT.md` in project root. Keep at ~30-40KB, 10 chapters, readable in 15 minutes cover-to-cover.

**Reference file**: `references/executive-report-example.md` — full 10-chapter REPORT.md for General Mahjong Assist (28.6KB).

---

## Section H: Product Launch Document Suite (产品启动文档三件套)

Structured product documentation that precedes building. Used when the user says "先做详细产品介绍，迭代方向，项目目标" or "参考WC26的方式和格式".

**Available workflows:**
- **Standard (document-first):** Write strategy docs, then code. The original Section H below.
- **Design-First (recommended for visual/consumer products):** Run design exploration (taste-skill → sketch → Figma) BEFORE writing strategy docs, so the PRD is grounded in an actual visual direction. See sub-section H.1 below.

### H.1: Design-First Product Planning (设计驱动产品规划)

Use when the user says "用设计skill" or "make it look good" or the product is consumer-facing/visual. The core insight: **don't write a vision document in the abstract — design first, then document what you designed.**

#### When to Use Design-First vs Standard

| Signal | Use Design-First | Use Standard |
|--------|-----------------|-------------|
| User says "运用已部署的设计skills" | ✅ Yes | ❌ No |
| Consumer-facing app (travel, lifestyle, social) | ✅ Yes — visual design IS the product | ❌ No |
| B2B tool / internal / API-first | ❌ Overkill | ✅ Right approach |
| Product has a named design direction ("东方奢雅", "Linear-style") | ✅ Yes — document the design language | ❌ No |
| User explicitly says "参考WC26的方式" | ❌ They want the standard 3-doc suite | ✅ Yes |
| Repeated rewrite / user frustrated with visual quality | ✅ Yes — design was the problem | ❌ No |

#### The 4-Phase Workflow

```
Phase 0: DESIGN READ (taste-skill)         ────  30min
Phase 1: VISUAL DIRECTION (sketch)          ────  1-2h
Phase 2: DESIGN SYSTEM (Figma)              ────  1-2h
Phase 3: PRODUCT DOCS (this Section H)      ────  1-2h
Phase 4: CODE                               ────  per PLAN.md
```

#### Reference

See `references/design-first-workflow.md` for a full worked example with VisePanda Native v2.0.

---

### When to Write Section H

- User says '先从产品经理的角度做产品介绍、迭代方向、项目目标'
- User says '参考WC26的方式和格式' — signals they want the three-document suite
- User says '还是一样的，先写pm产品规划文档' — **every feature, even small ones**
- Starting a new project or major version
- Before any Phase 1 coding begins — document-first, code-second

### The Three Documents

| Document | Purpose | Structure |
|----------|---------|-----------|
| **`PRD_PRODUCT_ANALYSIS.md`** | Strategic analysis — the "why" | Strategy Canvas → Competitive Analysis → SWOT/Reconstruction Analysis → Roadmap → Tech Architecture → Opportunity Tree → Delivery Checklist |
| **`PLAN.md`** | Iteration roadmap — the "how" | Current status → Tech stack → Completed iterations → Upcoming phases by round → Verification criteria |
| **`README.md`** | Product intro — the "what" | One-liner → Feature table → Tech stack → Features → Quick start → API → Project structure → Change summary |

### Writing Heuristics

- **Each section answers a question a reviewer would naturally ask** — don't pre-answer questions no one asked
- **Trade-offs show strategic discipline** — a "not doing" list is as important as a "doing" list
- **Numbers have units, time has dates** — not "lots of tests" but "221 tests"
- **Include a current-vs-new comparison table** for major version rewrites
- **Save all three to project root** — `PRD_PRODUCT_ANALYSIS.md`, `PLAN.md`, `README.md`

### Reference

See `references/product-launch-suite-example.md` for an annotated walkthrough based on VisePanda v3.0.1.

---

## Section I: Product Development Design Document (产品开发设计文档 — 手把手交付)

> **New in v1.2.0.** Single comprehensive document for handoff to external developers who will build from scratch. Follows the AI+ Coding SOP 6-step framework.

**When to use this section instead of Section H:**

| Signal | Use Section H (产品启动三件套) | Use Section I (开发设计文档) |
|--------|------------------------------|------------------------------|
| Internal team building | ✅ Yes — 3 docs for ongoing iteration | ❌ No |
| External developers / outsourcing | ❌ No | ✅ Yes — single comprehensive handoff |
| User says "交给其他人开发"/"给外包做" | ❌ No | ✅ Yes |
| User references a Coding SOP / methodology | ❌ No | ✅ Yes |
| Need to include full design specs (tokens, API contracts) | ❌ No (PRD is strategic) | ✅ Yes (soup-to-nuts) |
| Developers will rewrite from scratch | ❌ No (waste — they'd redo your docs) | ✅ Yes (all info in one doc) |

### The AI+ Coding SOP 6-Step Framework

This section maps to the AI+ Coding SOP ("AI+ Coding SOP指南"):

```
SOP Step 1: 需求编写     →  Section I, §1-3 (产品定义 + 用户分析 + PRD)
SOP Step 2: 产品/UI设计  →  Section I, §4 (设计方向与体验指南)
SOP Step 3: 技术设计     →  Section I, §5 (技术架构指引)
SOP Step 4: 代码编写     →  Section I, §6 (迭代路线图)
SOP Step 5: 功能测试     →  Section I, §7 (测试策略)
SOP Step 6: 工程归档     →  Section I, §8 (交付标准)
```

### Template Structure

Save as `PRODUCT_HANDOFF.md` in project root. Target size: 25-35KB.

#### §1 产品定义与战略

- **一句话定义** — What is this product, in one compelling sentence
- **核心价值主张** — Table: dimension / description (target user, user state, core value, differentiation, emotional promise)
- **竞争格局** — Table: competitor / type / strength / weakness / VisePanda opportunity
- **战略取舍** — Table: ✅ list (what we do) vs ❌ list (what we don't do). Shows strategic discipline
- **核心能力与护城河** — Table: capability / build-or-buy / explanation. Followed by moat analysis

#### §2 用户与市场分析

- **用户画像** — 2-3 persona tables (who they are, motivation, pain point, use scenario, what they care about)
- **用户旅程图** — ASCII flow showing the 7-step arc from discovery → download → first open → browse → plan → manage → revisit
- **情感曲线设计** — Table: stage / user state / design goal / key experience point. Maps emotional state to UX treatment

#### §3 产品需求规格 (PRD)

- **功能全景表** — Table: priority (P0/P1/P2) / module / feature / description. Sort by priority, not module
  - P0 = MVP must-have. P1 = v1.0 core. P2 = future iteration
- **非功能需求** — Table: category / requirement / acceptance criteria
- **页面树 (完整版)** — ASCII tree of all screens, sub-elements, and navigation flows. Every CTA and transition documented
- **核心交互流程** — ASCII flow of the 2-3 main user paths (main journey, city-driven path, etc.)

**Heuristic:** The PRD section must be complete enough that a developer can implement without asking "what does this button do?"

#### §4 设计方向与体验指南

- **设计语言** — One-liner positioning (e.g., "Oriental Luxury — dark, restrained, gold-accented premium")
- **灵感参考** — Who/what the design references (e.g., "柏悦/安缦 for warmth, Linear for dark system")
- **三要素配置** — VISUAL_DENSITY / DESIGN_VARIANCE / MOTION_INTENSITY (each 1-10)
- **设计原则** — 5-10 hard rules that cannot be violated (e.g., "留白大于填充", "金色不泛滥")
- **色板系统** — Code block with hex values for Surface / Accent / Secondary / Neutral, each with usage notes
- **字体系统** — Table: role / size / weight / line height / tracking / use
- **间距/圆角/阴影系统** — Tables with dp values and use cases
- **关键交互动效规范** — Table: interaction / animation / parameters (duration, easing)

**Heuristic:** Give developers the design tokens they need to implement — hex codes, dp values, ms timings. Any abstract adjective without a numeric spec is a liability.

#### §5 技术架构指引

- **架构概览** — ASCII architecture diagram (UI layer → ViewModel → Domain → Data → Network)
- **技术选型建议** — Table: decision / recommended choice / rationale
- **API 接口规范** — REST endpoints (method, path, purpose) + key JSON data structures with fields and types
- **统一 UiState 设计** — Code block showing sealed class pattern
- **状态处理规范** — Table: state (Loading/Empty/Error/Network Poor) / visual treatment / animation / behavior

**Heuristic:** Do NOT prescribe exact libraries unless there's a strong reason. Give guidance with options, not commands. The developer owns implementation.

#### §6 迭代路线图

- **阶段总览** — Table: Phase / duration / what gets done. Total estimated duration
- **迭代详情 (per Phase)** — For each phase:
  - **目标**: One-line what this phase achieves
  - **交付物**: Checkbox list of specific outputs
  - **验证门禁**: Checkbox list of passing criteria (compile, screenshot, E2E)
- **P2+ 功能清单** — Table of post-MVP features with estimated effort

**Heuristic:** Each phase must end with a clear "done" signal (a verification gate, not "developer says it's ready"). Phases should be independently ship-able — the app should compile and show progress after each phase.

#### §7 测试策略

- **测试层次** — Table: level / scope / tool / owner
- **关键测试场景** — Table: # / scenario / steps / expected result. Cover the 5-8 most important paths
- **人工验收清单** — Checkbox list for PM/QA to verify at the end of each phase

#### §8 交付标准与工程归档

- **交付物清单** — Table: deliverable / description / owner
- **编码规范** — Bullet list of project-specific conventions (naming, comments, formatting)
- **代码审查清单** — Table: check item / standard
- **版本号约定** — Table: version range / meaning (what's complete at that version)

#### §9 附录：关键决策记录

- **ADRs** — 5-10 Architecture Decision Records, each in the format:
  - **标题**: Decision being made
  - **决定**: What we chose
  - **理由**: Why we chose it
  - **被放弃的方案**: What we considered but rejected, and why

### Section I Writing Heuristics

- **写给开发者看的，不是写给老板看的** — 语气是"你要知道这些才能开始做"，不是"为什么这个产品有价值"
- **每个数字都有单位** — 30ms/字, 24dp 圆角, 200ms 动效. 不是"很快"、"大圆角"
- **每个设计决策都有数值** — 设计师可以给 hex code 和 dp，不要只说"暗色调"
- **ADRs 比章节正文更重要** — 附录里那些"为什么选这个"的决策记录，是开发者最需要的上下文
- **不引用已有代码** — 开发者从零开始，他们不需要知道之前代码长什么样
- **每个 Phase 的验证门禁要具体** — "编译通过"是 OK 的，"单元测试覆盖"要量化

### Execution Workflow (文档→代码的执行模式)

写完 PRODUCT_HANDOFF.md 后，按以下顺序执行：

1. **先写 PLAN.md** — 将文档中的迭代路线图拆分为具体 Phase，每个 Phase 含交付物 + 验证门禁
2. **Phase 0：后端基础设施** — 数据库 Schema + 框架骨架 + 认证系统 + 种子数据。这是所有依赖的基础
3. **Phase 1：API 层** — 所有业务接口。完成前端可依赖的完整 API
4. **Phase 2-N：并行执行** — 前端/客户端各模块可拆分为并行子任务（如 Android + Web Admin 同步开发）
5. **Final Phase：集成·测试·部署** — 串行收尾

**关键约束:**
- Phase 0 必须串行（基础不牢，上层全废）
- Phase 1+ 之后尽量并行（硬件不冲突就可并行）
- 每个 Phase 结束必须有验证门禁，不通过不进下一个

**模板:** 见 `templates/backend-scaffold-fastapi.md` — 后端从零搭建的标准结构与文件清单。

### Pitfalls

- ❌ 把 Section I 写成 Section G（执行汇报）— 读者不同，语气不同
- ❌ 引用已有的代码实现 — 开发者从零开始，会困惑
- ❌ 写"这个功能在之前的版本里已经做了" — 失效信息
- ❌ 设计 token 只写概念不写数值 — "金色调" vs "#C9A96E" 是 0 和 1 的差距
- ❌ 给开发者像 Section H 一样的三文件套餐（PRD+PLAN+README）— 对方会分散查阅，反而失去整体感
- ❌ 一个 Phase 写 30 个交付物 — 每个 Phase 应有 5-8 个明确的交付物
- ❌ 引用已有的代码实现 — 开发者从零开始，引用旧代码只会造成困惑
- ❌ 保存旧代码 / 旧数据库 — 用户说"从零开始"时，必须清理干净或新建仓库，不能复用

### Reference

See `references/vise-panda-android-handoff.md` — full worked example for VisePanda Android App (31.7KB, 9 chapters, AI+ Coding SOP framework).

**Templates:**\n- `templates/backend-scaffold-fastapi.md` — standard backend scaffold from scratch (FastAPI + PostgreSQL + JWT Auth + seed data)\n\n---\n\n## Section J: Internal Feature Development Workflow (内部功能开发工作流)\n\n> **New in v1.3.0.** Two-document approach for adding features to an EXISTING product. PM Requirements Doc → Tech Delivery Doc → Implement. Captures the \"先写PM产品说明 → 从研发负责人角度写技术交付说明\" pattern.\n\n**When to use this section (vs Section H or I):**\n\n| Signal | Use Section H (新项目启动) | Use Section I (外包交付) | Use Section J (内部功能) |\n|--------|--------------------------|------------------------|------------------------|\n| New product / major rewrite | ✅ Yes | ❌ No | ❌ No |\n| Handoff to external developers | ❌ No | ✅ Yes | ❌ No |\n| Adding feature to existing product | ❌ Overkill (too heavy) | ❌ No | ✅ Yes |\n| User says \"先写pm产品说明\" then \"再写技术交付说明\" | ❌ No | ❌ No | ✅ Yes — this is the signature pattern |\n| Existing codebase, no rewrite | ❌ No | ❌ No | ✅ Yes |\n| User says \"参考WC26的方式\" | ✅ Yes (3-doc suite) | ❌ No | ❌ No |\n\n### The Two-Document Workflow\n\n```\nStep 1: PM Product Document (PRD_USER_SYSTEM.md)  ─── PM视角\n    ↓ 用户确认方向后\nStep 2: Tech Delivery Document (TECH_USER_SYSTEM.md)  ─── 研发负责人视角\n    ↓ 对齐后\nStep 3: Implement per TECH doc's iteration plan\n```\n\nBoth documents go into a `docs/` directory at the project root (not project root itself, to avoid cluttering the codebase).\n\n---\n\n### Document 1: PM Product Requirements Doc (PRD_xxx.md)\n\n**File name:** `docs/PRD_<FEATURE>.md`\n**Reader:** Product Manager / Stakeholders / Engineering Lead\n**Tone:** Business-first, user-centric, strategic\n\n#### Sections\n\n1. **需求概述** — One-sentence summary, current-vs-target comparison table, user stories (As a... I want... So that...)\n2. **角色与权限模型** — Table: role / access scope / typical scenario. Permission matrix (✅/❌).\n3. **功能需求** — Login page / Auth state UI / Feature gating / Persistence / Admin panel. Each with sub-sections.\n4. **非功能需求** — Security / UX / Data (with Vercel limitations noted)\n5. **明确不做的** — What's explicitly out of scope for this iteration\n\n#### Writing Heuristics\n\n- **用户故事先行** — 每个功能点前先写用户故事（As a... I want... So that...），确保需求是从用户出发的\n- **\"不做\"列表体现战略自律** — 把\"这个迭代不做什么\"写清楚，比\"做了什么\"更重要\n- **角色权限表要完整** — 每个角色能做什么、不能做什么，一个表格说清楚\n- **承认已知限制** — 如 Vercel 冷启动会重置 SQLite，要在文档里标注\"MVP 阶段接受此限制\"\n\n---\n\n### Document 2: Tech Delivery Doc (TECH_xxx.md)\n\n**File name:** `docs/TECH_<FEATURE>.md`\n**Reader:** Engineering Lead / Developers\n**Tone:** Engineering-first, implementation-focused, precise\n\n#### Sections\n\n1. **架构变更** — ASCII architecture diagram showing before-vs-after changes. File-level diff (new/modified/deleted)\n2. **数据库 Schema** — SQL DDL for new tables. Exact column types, constraints, indexes\n3. **API 详细设计** — Request/Response JSON examples for every new endpoint. Method, path, auth, role headers\n4. **前端实现方案** — Code structure (module/class spec), state management pattern, UI component map\n5. **实现顺序（迭代计划）** — Iter 1 → Iter N, each with checkbox tasks and estimated hours\n6. **文件变更清单** — Table: file / action (add/modify/delete) / description\n7. **风险与边界条件** — Table: risk / probability / impact / mitigation\n\n#### Writing Heuristics\n\n- **写给工程师看的** — 语气是\"你需要知道这些才能开始编码\"，不是\"为什么做\"\n- **API 要有完整示例** — 每个请求/响应给 JSON 示例，不要只写\"见文档\"\n- **SQL DDL 要可直接运行** — `CREATE TABLE` 写完整，带 NOT NULL / DEFAULT / 索引\n- **前端给出代码骨架** — 关键模块的 class/function 签名，不是全量代码\n- **每个 Iter 有预估工时** — 让用户知道大概需要多少时间\n- **风险部分必须诚实** — 枚举已知限制（如 Vercel SQLite 重置），给出 MVP 接受条件\n- **参考具体的已有代码** — 因为是对已有项目加功能，可以引用现有文件里的代码段（\"参考 auth.py 中的 handle_login 模式\"）\n\n---\n\n### Pitfalls\n\n- ❌ **Section J ≠ Section H 的简化版** — H 是面向新项目的三文件套餐（战略层），J 是面向已有项目的两文件工作流（功能层）。读者不同、结构不同\n- ❌ **Tech doc 写成 PRD** — Tech doc 要有 SQL DDL、API 示例、代码骨架。只写\"用户故事\"和\"功能描述\"是 PM 的事\n- ❌ **PM doc 写得像技术说明书** — PM doc 面向业务决策，不要写技术细节（SQL 表结构、API 参数等留给 Tech doc）\n- ❌ **文件放错位置** — PM doc + Tech doc 放 `docs/` 目录下，不是项目根目录，项目根目录留 PLAN/PRD_PRODUCT_ANALYSIS/README\n- ❌ **跳过用户确认直接写 Tech doc** — PM doc 写完后必须让用户确认方向，再写 Tech doc。用户说\"先写PM产品说明\"之后，等他的反馈再进入 Tech doc\n\n### Common Feature Recipes (Section J addenda)\n\n- **Password Reset (MVP)**: See `references/password-reset-flow.md` — email-less token pattern for MVP stage, with production upgrade path. Covers DB schema, backend API code, frontend UX flow, and known pitfalls."
