# Product Launch Document Suite — Example: VisePanda v3.0.1

> This document annotates how the WC26-style three-document suite was applied to VisePanda v3.0.1, a different product type (AI travel planner vs sports prediction). Use as a structural reference, not a template to copy verbatim.

## Context

- **Product**: VisePanda — AI China Travel Platform
- **Previous version**: v2.x (FastAPI + Supabase + GLM-5.1, 124 iterations)
- **Target version**: v3.0.1 (WSGI + stdlib + DeepSeek V4 Flash, complete rewrite)
- **User directive**: "先从资深产品经理的角度做详细产品介绍，迭代方向，项目目标。可以参考wc26的方式和格式"

## The Three Documents

### 1. PRD_PRODUCT_ANALYSIS.md (~19KB)

Saved to: `/home/ubuntu/projects/vise-panda-2/PRD_PRODUCT_ANALYSIS.md`

**Structure used:**
```
## 一、产品战略画布
### 1. 愿景 — "让每个想来中国的外国人像跟本地朋友聊天一样"
### 2. 目标市场 — 4 segments (in-China foreigners, outbound planners, expats, domestic)
### 3. 成本定位 — v2 vs v3 comparison table (architecture/LLM/DB/deps)
### 4. 价值主张 — Before/After table
### 5. 明确的取舍 — ❌ no auth, no real-time API, no map (MVP); ✅ AI chat, 33-city KB, tools, panda UI
### 6. 关键指标 — conversation success rate, KB hit rate, Lighthouse score
### 7. 增长策略 — Product-Led Growth via chat screenshots
### 8. 核心能力 — Existing 33-city KB, LLM integration, panda branding
### 9. 护城河 — KB×LLM fusion, curated China data, panda brand recognition

## 二、竞品分析 — vs ChatGPT/TripAdvisor/小红书/Lonely Planet

## 三、v3.0 回顾与 v3.0.1 重构动因
- What v2 got right (retainable assets)
- What went wrong (why rewrite is necessary)
- Reconstruction principles

## 四、v3.0.1 迭代路线图 — 3 Phases × 15 rounds

## 五、技术架构 — ASCII diagram

## 六、MVP 交付清单 — Table

## 七、机会-解决方案树

## 八、与 WC26 的架构对比
```

**Key differences from WC26's PRD:**
- WC26 focused on math model explainability; VisePanda focuses on AI conversation + knowledge base
- Added "v3.0 回顾与重构动因" section — necessary because this is a rewrite, not a greenfield project
- Added "与 WC26 的架构对比" — useful when user wants consistency across projects
- Token/estimation table was replaced with a more detailed iteration roadmap

### 2. PLAN.md (~6KB)

Saved to: `/home/ubuntu/projects/vise-panda-2/PLAN.md`

**Structure used:**
```
# PLAN.md — VisePanda v3.0.1 迭代路线图

## Current Project Status (table: version, lines, LLM, deps, DB, etc.)

## Tech Stack (code block)

## Completed Iterations (v2.x era — retained assets)

## v3.0.1 Iteration Plan
- Phase 1 (Rounds 1-6): 骨架搭建 — WSGI/frontend/chat/KB/tools/ship
- Phase 2 (Rounds 7-11): 体验打磨 — animation/responsive/multi-turn/light-theme/perf
- Phase 3 (Rounds 12-15): 深度增强 — persistence/map/share/smart features

## Retained vs Rewritten Assets (table)

## Verification Criteria (table by iteration phase)
```

### 3. README.md (~4KB)

Saved to: `/home/ubuntu/projects/vise-panda-2/README.md`

**Structure used:**
```
# VisePanda · v3.0.1

> One-liner

## Latest Version (feature table)

## Tech Stack

## Frontend Features (tab table)

## Quick Start (code block)

## API Endpoints (table)

## Data Sources (table)

## Project Structure (tree)

## Iteration Roadmap (link to PLAN.md)

## vs v2.x Changes (comparison table)
```

## When to Adapt This Pattern

| Scenario | Adapt | Don't Adapt |
|----------|-------|-------------|
| Greenfield project | Full 3-document suite, smaller PLAN.md | Skip the "v2→v3" comparison sections |
| Major version rewrite | Full 3-document suite + "retrospective" section | Skip only if the rewrite is trivial |
| **Feature addition to existing product** | **Single planning document (Strategy Canvas style) — see auth system example: feature scope, why, architecture, data model, API design, UI flow, iteration plan, risks, success criteria** | Don't skip docs entirely. User wants PM planning **before every feature**, not just new products. |
| User says "参考WC26" | Full 3-document suite, add architecture comparison table | Don't skip the explicit comparison — user wants cross-project consistency |
| Bug-fix iteration | None of these | Use PRD or Release Notes instead |

## Common Pitfalls

- ❌ **Writing docs that are too long** — PRD ~15-20KB, PLAN ~5-8KB, README ~3-5KB. If exceeding, tighten.
- ❌ **Writing all three in the same tone** — PRD is strategic, PLAN is tactical, README is promotional. Different voices.
- ❌ **Skipping the "not doing" list** — This is the most important signal of strategic thinking. Without it, the doc reads as naive.
- ❌ **No numbers** — "lots of cities" vs "33 cities with curated data". Quantify everything you can.
- ❌ **Starting to code before the user reviews the docs** — Present the docs first, wait for "开干" (like user said). The docs set direction; coding without direction review risks rework.
