---
name: vanilla-animation-integration
version: 1.0.0
description: |
  Add animated UI components from third-party libraries (React Bits, etc.)
  to vanilla JS / non-framework projects. Covers component selection, JS+CSS
  extraction, encapsulation, dynamic-content integration, touch-device handling,
  and performance considerations.
triggers:
  - "add animation"
  - "react bits"
  - "vanilla js animation"
  - "component adaptation"
  - "animated ui"
tools:
  - terminal
  - write_file
  - patch
mutating: true
---

# Vanilla Animation Integration

> Adding third-party animated UI components to vanilla JS projects

## Overview

Many animated UI component libraries (React Bits, Magic UI, etc.) offer **vanilla JS + CSS** variants alongside their React versions. These can be directly adapted into non-React projects.

## Workflow

### 1. Browse & Select

Scan the target library for components that fit the project's visual style and functional needs. Categorize by use case:

| Category | Examples | Fits |
|----------|----------|------|
| Backgrounds | Aurora, Beams, Particles, Silk | Hero sections |
| Cards | Tilted Card, Spotlight Card, Reflective Card | Destination/city cards |
| Text | Split Text, Count Up, Gradient Text | Headlines, stats |
| Navigation | Dock, Pill Nav, Staggered Menu | App nav |
| Interactive | Splash Cursor, Magnet, Click Spark | Global cursor effects |

### 2. Prefer JS+CSS Variant

Always check if the library offers a plain JS+CSS version (no framework dependency):
- React Bits: 4 flavors per component — JS+CSS, TS+CSS, JS+Tailwind, TS+Tailwind
- Pick **JS+CSS** for vanilla projects

### 3. Component Encapsulation Pattern

Each component should be a **self-contained class** in a single file:

```javascript
class ComponentName {
  constructor(element, options = {}) {
    // Store element and options
    // Apply CSS class
    // Set up event listeners
    // Handle touch devices
  }
  
  onMouseMove(e) { /* ... */ }
  onMouseLeave(e) { /* ... */ }
  destroy() { /* Cleanup */ }
}
```

**Key conventions:**
- CSS class prefix: `vise-` (or project-specific prefix)
- Touch devices: `window.matchMedia('(pointer: coarse)').matches` → skip heavy hover effects
- Performance: Use `requestAnimationFrame` for canvas, `will-change` for animations
- No external dependencies

### 4. CSS Structure

Create a companion CSS file with:
- Component-specific styles
- Transition/animation definitions
- Keyframe animations
- `@media (prefers-reduced-motion)` support

```css
.vise-component {
  /* Base styles */
}

.vise-component:hover {
  /* Hover enhancements */
}
```

### 5. Dynamic Content Integration

For dynamically loaded elements (e.g., city cards fetched via API), use **MutationObserver**:

```javascript
const observer = new MutationObserver((mutations) => {
  for (const m of mutations) {
    for (const node of m.addedNodes) {
      if (node.nodeType === 1) {
        applyEffects(node);
      }
    }
  }
});
observer.observe(document.body, { childList: true, subtree: true });
```

### 6. Performance Considerations

| Technique | Why |
|-----------|-----|
| `requestAnimationFrame` | Smooth canvas/JS animations |
| `transform` + `opacity` only | GPU-accelerated, no layout thrash |
| `will-change` on hover elements | Hint browser for optimization |
| `devicePixelRatio` scaling | Sharp canvas on Retina |
| Limit Canvas pixel ops | Reduce draw calls |
| Touch device detection | Skip heavy 3D transforms on mobile |

## Class Template

```javascript
(function() {
  'use strict';

  class MyEffect {
    constructor(element, options = {}) {
      this.element = element;
      this.options = { /* defaults */, ...options };
      this.isMobile = window.matchMedia('(pointer: coarse)').matches;
      if (this.isMobile) return;
      this.bind();
    }
    
    bind() {
      this.boundHandler = this.onEvent.bind(this);
      this.element.addEventListener('mousemove', this.boundHandler);
    }
    
    onEvent(e) { /* ... */ }
    
    destroy() {
      this.element.removeEventListener('mousemove', this.boundHandler);
    }
  }

  // Auto-init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Dynamic card effects
  const observer = new MutationObserver(/* ... */);
  observer.observe(document.body, { childList: true, subtree: true });
})();
```

## Avoid

- Adding React/framework just for animations
- Large animation libraries for simple hover effects
- Full-page canvas effects on every viewport (hero only)
- Animations that interfere with user interaction (pointer-events: none)

## See Also

- `cron-scheduler` skill: `references/github-repo-watchdog.md` for repo monitoring
- `references/visebits-components.md` — full implementation details for the 5 VP-Hermes-Web animation components
- `references/design-system-wiki.md` — template for setting up a project UI/UX design wiki
