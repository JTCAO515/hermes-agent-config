# Design System Wiki Structure

> Created: 2026-06-23 | Project: VP-Hermes-Web
> Location: `docs/uiux/`

## 10-Section Wiki Template

```
docs/uiux/
├── README.md              ← Index with directory and quick links
├── design-principles.md   ← Core design philosophy (5 max)
├── design-tokens.md       ← Colors, typography, spacing, shadows, radii
├── navigation.md          ← Tab bars, topbar, bottom nav, view switching
├── interactions.md        ← Transitions, loading states, gestures, performance
├── responsive.md          ← Breakpoints, mobile/desktop layout rules
├── accessibility.md       ← Semantics, focus, color contrast, reduced motion
├── translation-ui.md      ← (if app has translation) UI specs for translation panels
├── visebits.md            ← (if app has animations) Animation component specs
├── assets.md              ← Logos, icons, imagery rules
├── components/
│   ├── README.md          ← Component index
│   ├── button.md          ← Button variants
│   ├── city-card.md       ← Card component
│   ├── input.md           ← Form inputs
│   └── ...
```

## When to Create

- Starting a new frontend project
- Re-platforming from one visual system to another
- Before bringing on additional developers
- When the project's DESIGN.md grows past 200 lines

## First Principles

1. **Single source of truth** — design tokens should reference the actual CSS custom properties (e.g., `--brand: #0ea5e9`), not duplicate values
2. **Make it scannable** — use tables for tokens, diagrams for layouts, code snippets for implementation
3. **Tie to real files** — note which CSS/JS files implement each section
4. **Keep it updated** — when CSS changes, update the wiki
