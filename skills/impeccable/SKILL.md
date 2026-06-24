# Impeccable – Production-Grade Frontend Design Skill

**Source:** [sbakaus/impeccable – skill definition](https://github.com/pbakaus/impeccable/blob/main/skill/SKILL.src.md)

## Overview

A design skill for AI that generates production‑ready frontend interfaces (websites, dashboards, app UI, components, forms, etc.). Covers UX review, visual hierarchy, typography, color, motion, accessibility, responsive behaviour, theming, anti‑patterns, and design systems. Invoked for tasks like `craft`, `shape`, `audit`, `polish`, `animate`, `colorize`, etc.

> *"Designs and iterates production-grade frontend interfaces. Real working code, committed design choices, exceptional craft."*

---

## Setup (Mandatory Steps)

1. **Run context script** once per session (`node {{scripts_path}}/context.mjs`). If output says `NO_PRODUCT_MD`, stop and follow `reference/init.md`.
2. **Read sub‑command reference** if user invoked a sub‑command (e.g., `craft`, `audit`). Required file: `reference/<command>.md`.
3. **Familiarise with existing design system** – read at least one CSS / tokens / theme / component file. Never reinvent what’s already there unless UX wins.
4. **Read the matching register reference**:
   - **Brand register** (`reference/brand.md`) – for marketing, landing pages, portfolios (design IS the product).
   - **Product register** (`reference/product.md`) – for app UI, admin, dashboards (design SERVES the product).
   - Choose by: task cue, surface in focus, or `register` field in `PRODUCT.md`.
5. **For brand‑new projects** (no existing brand colors) → run `node {{scripts_path}}/palette.mjs` to get a seed colour and compose the palette in OKLCH. Skip if committed brand colours exist.

---

## Design Guidance

### General Rules

- **Produce ready‑to‑ship, production‑grade code** – no prototypes or starting points unless user asks.
- **No shortcuts** – complete implementation (beautiful, responsive, fast, precise, bug‑free, on‑brand).
- **Battle‑test everything** using browser screenshots, computer use, etc.

---

### Color

> *"Body text must hit ≥4.5:1 against its background; large text (≥18px or bold ≥14px) needs ≥3:1. Placeholder text needs the same 4.5:1, not the muted-gray default."*

- Gray text on a coloured background → use a darker shade of the background’s own hue or a transparency of the text colour.
- Common failure: muted gray body text on a tinted near‑white. Bump toward ink if contrast is close.

### Typography

- **Line length**: cap at 65–75ch for body text.
- **Font pairing**: don’t pair two similar fonts. Use contrast axis (serif + sans) or one family in multiple weights.
- **Hero/display heading ceiling**: `clamp()` max ≤ 6rem (~96px).
- **Display heading letter‑spacing floor**: ≥ -0.04em (tighter makes letters touch; often -0.02 to -0.03em is better).
- Use `text-wrap: balance` on h1–h3; `text-wrap: pretty` on long prose.

### Layout

- **Vary spacing for rhythm** – don’t use uniform gaps.
- **Cards**: use only when they are the best affordance. Nested cards are always wrong.
- **Flexbox for 1D, Grid for 2D**. Default to `flex-wrap` when simpler.
- **Responsive grids**: `repeat(auto-fit, minmax(280px, 1fr))`.
- **Semantic z‑index scale**: dropdown → sticky → modal‑backdrop → modal → toast → tooltip. Never arbitrary values like 9999.

### Motion

> *"Motion should be intentional, and not be an afterthought. Consider it as part of the build."*

- **Don’t animate CSS layout properties** unless truly needed.
- **Ease‑out curves** (exponential: quart/quint/expo). No bounce, no elastic.
- Use libraries for advanced needs: motion, GSAP, anime.js, Lenis.
- **Reduced motion**: every animation needs `@media (prefers-reduced-motion: reduce)` alternative – typically crossfade or instant transition.
- **Staggering is legitimate**; the tell is a uniform reflex (identical entrance on every section). Each reveal should fit what it reveals.
- **Reveal animations must enhance an already‑visible default** – don’t gate content on a class‑triggered transition (transitions pause on hidden tabs / headless renderers).
- **Premium materials**: blur, backdrop-filter, clip‑path, mask, shadow/glow – use when they improve the effect and stay smooth.

### Interaction

> *"Dropdowns rendered with `position: absolute` inside an `overflow: hidden` or `overflow: auto` container will be clipped. Use the native `<dialog>` element, a portal library, or `position: fixed` with dynamic positioning."*

- **Focus indicators**: strong, high‑contrast `:focus-visible` ring (not outline: none). Use `outline-offset` for clarity.
- **Hover states**: not optional. Interactive elements need a clear style change.

### Accessibility

- **Skip‑to‑content** link (first focusable element). Not optional.
- **All images** need meaningful `alt`. Decorative → `alt=""`.
- **Forms**: every `<input>` needs a `<label>`; use `aria-describedby` for errors/hints.
- **Interactive elements**: `role`, `aria‑*`, keyboard handlers, `tabindex` as needed.
- **Semantic H

[... summary truncated for context management ...]