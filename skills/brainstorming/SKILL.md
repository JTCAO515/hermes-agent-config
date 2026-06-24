---
name: brainstorming
description: Product ideation and planning methods. Brainstorm product ideas (existing/new), design experiments (existing/new), and set OKRs. Multi-perspective ideation from PM, Designer, and Engineer viewpoints within continuous product discovery.
---

# Brainstorming

Five brainstorming methods for product/startup work. Each is a labeled section below.

---

## A. Ideas for Existing Product

Multi-perspective ideation (PM, Designer, Engineer) for an existing product. Use when generating new feature ideas for an identified opportunity.

1. Understand the opportunity: confirm product, objective, target segment, desired outcomes.
2. Generate 5 ideas each from PM (business value), Designer (UX delight), and Engineer (technical possibilities).
3. Prioritize top 5 across all perspectives based on: strategic alignment, impact, feasibility, differentiation.
4. For each: name, description, reasoning, key assumptions to validate.

## B. Ideas for New Product

Same multi-perspective format but for a new product in initial discovery. Wider scope of ideation since no existing product constraints.

## C. Experiments for Existing Product

Design lean experiments to test assumptions for an existing product feature. Focus on: falsifiability, speed to signal, and what would constitute a "fail" threshold.

## D. Experiments for New Product

Design pretotypes (minimum viable experiments) for new product concepts. Focus on: testing demand before building, smoke tests, landing pages, and "fake door" experiments.

## E. OKRs

Brainstorm team-level OKRs aligned with company objectives.

1. Gather context (company strategy, team scope).
2. Generate three distinct, ambitious OKR sets. Each has:
   - Objective: qualitative, inspirational, time-bound.
   - 3 Key Results: measurable, ambitious (60-70% confidence), aligned.
3. Format:
   ```
   Objective: Delight new users with effortless onboarding
   Key Results:
   - CSAT >= 75% on onboarding survey
   - 66%+ onboardings completed within two days
   - Avg time-to-value <= 20 minutes
   ```
4. Key Results focus on outcomes, not outputs. Avoid "launch 5 features".

---

## F. Next: From Brainstorm to Implementation Plan

After brainstorming and prioritizing top ideas, transition to formal docs:

1. **Grill the plan** — Run `grill-with-docs` to pressure-test assumptions, identify gaps, sharpen scope boundaries. Questions to ask:
   - Cold start implications (Vercel Hobby = 10s)
   - Data availability (knowledge base fields complete?)
   - Parallel dependencies (which batches block each other?)
   - MVP scope traps (what's NOT in scope?)

2. **Write PLAN.md** — Formal iteration roadmap with:
   - Batches ordered by dependency, each with: scope, out-of-scope, est. effort, version
   - Dependency graph (batch A → B, parallel candidates)
   - Verification gates (what must pass before delivery)

3. **Write ADRs** — Architecture Decision Records for each batch's key decisions:
   - Status, Date, Context (what problem), Decision (what & why), Consequences (✅ ⚠️)
   - One ADR per architectural decision, not one per batch
   - Number sequentially from existing ADRs in `docs/adr/`

4. **Handoff** — When user approves, the plan is ready for implementation via the project's standard dev workflow (mattpocock skills or per-project workflow).
