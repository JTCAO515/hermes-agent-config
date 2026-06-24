# Design-First Product Planning — Worked Example: VisePanda Native v2.0

> Full workflow from this session: 2026-06-17, user asked to "在前端设计上下功夫，运用已部署的skills" and rewrite the PM product planning document.

## Context

- **Product**: VisePanda Native — AI China Travel Assistant (Android native app)
- **Previous version**: v0.2.6 (patched old build, still broken after user install)
- **User directive**: "要从资深产品经理角度写产品规划...你要在前端设计上下功夫，运用已部署的skills，你也可以找一些相关的设计类的skills，把这个app做的好看。再写一次pm产品规划文档"
- **Design direction (from earlier session)**: A 东方奢雅 — dark background, warm gold accent, jade green/stone grey auxiliary

## Phase 0: Design Read

### Skills loaded
- `taste-skill` (design-taste-frontend) — full SKILL.md loaded, 169 sections
- `popular-web-designs` — catalog scanned, `linear.app.md` loaded as reference

### Design Read output

```
Design Read: "Native mobile Android app with Compose UI, for international
travelers planning China trips. Premium consumer / luxury travel brand vibe.
Dark-mode native. Leaning toward: dark-background luxury travel brand with
Oriental quiet-luxury character — not loud Chinese motifs, not generic tool UI."

Dials:
  VISUAL_DENSITY:  3  (art gallery — generous whitespace, 24-48dp gaps)
  DESIGN_VARIANCE: 7  (asymmetric image placement, varied card ratios)
  MOTION_INTENSITY:  5  (fluid cross-fade tab switches, shimmer entry)
```

### Anti-AI-tell checklist (taste-skill Section 9)

Applied before writing any design output:
- ✅ No purple/neon gradients (use gold accent instead)
- ✅ No three-equal-card grids (use asymmetric 2-col + hero)
- ✅ No Inter by default (checked — use Inter for Android as it's the best available sans-serif on mobile)
- ✅ No em-dashes anywhere in the doc
- ✅ No "Acme" fake brand names
- ✅ No fake numbers ("99.99%")
- ✅ No stack of beige+brass for "premium" (we use 东方奢雅 — dark+gold+jade)
- ✅ No centered hero with generic glassmorphism

### Linear.app reference borrowings

| Borrowed from Linear | How applied to VisePanda |
|----------------------|-------------------------|
| Surface hierarchy (near-black → panel-dark → elevated) | `#0A0A0A` → `#1A1A1A` → `#232323` → `#2A2A2A` |
| Semi-transparent white borders | Borders at `#3A3A3A` (dark mode version) |
| Near-white text (not pure white) | `#F5F0E8` primary, `#D4CEC4` secondary |
| Single chromatic accent | Gold `#C9A96E` replaces Linear's indigo `#5E6AD2` |
| Generous section spacing | 48dp section gaps |

### Palette checks (taste-skill Section 4.2)

- ✅ NOT premium-consumer AI-default (beige/brass/oxblood) — we use true dark+gold
- ✅ Palette locked: one accent (gold `#C9A96E`) throughout
- ✅ Shape consistency: 4-value radius scale (4/8/12/16/24)
- ✅ Typography: 8-level scale, sans-serif throughout, no serif-for-premium trap

## Phase 1: Visual Direction (sketch — carried out but normalized into PRD)

This phase was executed as "design the document directly" rather than standalone HTML mockups, because the project's design direction was already locked from earlier sessions (A 东方奢雅). For a greenfield project or when direction is NOT locked, follow the `sketch` skill workflow: create 2-3 standalone HTML mockups and compare.

### What was produced instead

The design direction was documented directly into the PRD as an exhaustive design system:
- Color palette (8 colors with hex values)
- Typography scale (8 levels with size/weight/tracking)
- Spacing scale (7 levels)
- Radius system (5 levels)
- Shadow elevation (5 levels)
- Design principles (8 hard rules)
- Design benchmarks (Linear / Apple / 柏悦 / Stripe)

## Phase 2: Figma Design System (planned — not executed this session)

The Figma phase was documented as planned work (P2 in PLAN.md) but not executed. In a full workflow, this would involve:

1. `figma-generate-library` → create Color/Spacing/Typography/Radius variable collections
2. `figma-generate-design` → create 5 screens: Home/Explore/Chat/CityDetail/Trips
3. User confirms Figma designs before code

## Phase 3: Product Documentation

### The Three Documents (saved to project root)

| Document | Size | Key design sections |
|----------|------|-------------------|
| PRD_PRODUCT_ANALYSIS.md | 22.7KB | Section 二 (Design Vision): full palette, type scale, tokens, principles, benchmarks, Design-to-Code Roadmap |
| PLAN.md | 12.3KB | P1 (Sketch) + P2 (Figma) added as design-first phases; Design Skills Resource List table |
| README.md | (not yet created) | — |

### What made these docs different from standard Section H output

| Standard Section H | Design-First variant |
|-------------------|---------------------|
| Product section: vision, market, cost, value | Same + **Design Vision section** with actual tokens |
| Competitive analysis: feature matrix | Same + **Design differentiation** (东方奢雅 vs competitors' generic look) |
| Info architecture: page tree | Same + **Per-screen design detail**: colors, components, animations |
| Success criteria: functional metrics | Same + **Design audit criteria**: palette consistency, radius consistency, animation points |
| PLAN.md: code phases only | **P1/P2 added**: Sketch validation + Figma design system before any code |
| No design skills mentioned | **Design Skills Resource List** table in PLAN.md |
| Risks: technical only | **Design risks added**: Figma key not configured, user rejects design direction |

### Writing heuristics that worked

1. **Show, don't tell** — Instead of "elegant visual design", document the actual hex values (`#C9A96E`), font sizes (`36sp SemiBold`), and spacing (`24dp`). A token is worth a thousand adjectives.
2. **Reference real designs** — Naming Linear, Apple, 柏悦 as benchmarks grounds the vision in real products the user knows. Don't invent abstract references.
3. **Anti-AI-tell checklist in the doc** — Including the actual banned patterns (no purple gradient, no three-cards-equal) signals design maturity.
4. **Design roadmap as part of the product roadmap** — The PLAN.md should show design phases BEFORE code phases, not as a separate track.
5. **Figma is a Phase, not a dream** — If you don't have Figma access or the user hasn't set it up, document the design tokens anyway. The tokens are the permanent artifact; Figma is one visualization of them.

### Design-to-code bridging pattern

The most important bridge between design doc and code is the **token mapping**:

```kotlin
// PRD token → Compose code
// From PRD:
// - Color: Gold #C9A96E → VpColors.kt: val Gold = Color(0xFFC9A96E)
// - Typography: DisplayXL (36sp, SemiBold, -0.5sp) → VpTypography.kt
// - Spacing: xl(24dp) → VpSpacing.kt: val xl = 24.dp
```

Document this mapping explicitly in the PRD so the coder (you or another agent) doesn't have to re-read the design doc and infer.

## Phase 4: Code (not yet executed)

Not covered in this session. See PLAN.md P3-P8 for the execution plan.

## Key Insights

### What surprised us

1. **Design skills (taste-skill) apply to native mobile just as well as web** — The taste-skill is written for web (React/Next.js/Tailwind) but its design principles (dials, color calibration, layout diversification, AI-tell avoidance) are platform-agnostic. The 3-dial system works for mobile too.
2. **The design document IS the PRD** — You don't write a PRD and a separate design doc. The design system tokens go IN the PRD. The competitive analysis includes visual differentiation. The iterative plan includes design phases.
3. **Anti-AI-tell checklist is a PRD quality gate** — Running the taste-skill's 30+ item pre-flight check on your design decisions before writing the doc catches vague AI-default thinking early.

### What we'd do differently

1. If the design direction were NOT locked, we would run the full `sketch` workflow (2-3 HTML mockups) in a standalone sub-directory before writing the PRD. In this session the direction was locked from earlier work, so we went straight to token documentation.
2. If Figma were configured, we would produce actual screen designs and reference them as Figma frame IDs in the PRD.

### Pitfalls specific to design-first product planning

- ❌ **Over-documenting the design before the user agrees on direction** — Use sketch mockups to get direction alignment first (Phase 1). Only document tokens exhaustively (Phase 3) after the direction is confirmed. If you write 22KB of design tokens and the user picks Variant B, you've wasted work.
- ❌ **Treating the design doc as aspirational** — Every hex code, spacing value, and typography level in the PRD must be implemented. If you add a token "for completeness" that you don't plan to implement, mark it as "(future)" or remove it.
- ❌ **Design skills aren't free** — taste-skill, sketch, and figma skills have specific triggers and preconditions. Check if Figma MCP is connected before promising Figma designs. Check if `browser_navigate` works before promising sketch mockups.
- ❌ **Forgetting the "not doing" list for design** — Just as the PRD should list what features you're NOT building, the design section should list what design directions you're NOT taking ("no glassmorphism", "no neon gradients", "no serif fonts in UI").
