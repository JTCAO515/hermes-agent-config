# ViseBits Patterns — React Bits Adaptation for Vanilla JS

Session: 2026-06-23, VP-Hermes-Web (VisePanda China Travel SPA)

## Context

Adapted 5 React Bits components to a vanilla HTML/CSS/JS project (Python WSGI backend, no framework). Source: reactbits.dev. All components written as standalone ES6 classes in a single file with no external dependencies.

## Component Implementations

### 1. AuroraHero (Canvas Background)

```javascript
class AuroraHero {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.beams = [];   // { x, y, vx, vy, width, speed, opacity, hue, sat, phase }
    this.time = 0;
    this.resize();
    this.initBeams();
    window.addEventListener('resize', () => this.resize());
    this.animate();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width * devicePixelRatio;
    this.canvas.height = rect.height * devicePixelRatio;
    this.ctx.scale(devicePixelRatio, devicePixelRatio);
    this.w = rect.width;
    this.h = rect.height;
  }

  initBeams() {
    this.beams = [];
    const count = 8 + Math.floor(this.w / 200);
    for (let i = 0; i < count; i++) {
      this.beams.push({
        x: Math.random() * this.w, y: this.h * (0.2 + Math.random() * 0.6),
        vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.3,
        width: 30 + Math.random() * 80, speed: 0.3 + Math.random() * 0.7,
        opacity: 0.03 + Math.random() * 0.08, hue: 200 + Math.random() * 40,
        sat: 60 + Math.random() * 30, phase: Math.random() * Math.PI * 2,
      });
    }
  }

  animate() {
    this.time += 0.008;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.w, this.h);
    // Draw each beam as radial gradient ellipse + light rays
    for (const b of this.beams) {
      const x = b.x + Math.sin(this.time * b.speed + b.phase) * 60;
      const y = b.y + Math.cos(this.time * b.speed * 0.7 + b.phase) * 40;
      const w = b.width + Math.sin(this.time * 0.3 + b.phase) * 20;
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, w);
      gradient.addColorStop(0, `hsla(${b.hue}, ${b.sat}%, 60%, ${b.opacity * 2})`);
      gradient.addColorStop(0.4, `hsla(${b.hue + 10}, ${b.sat - 10}%, 55%, ${b.opacity})`);
      gradient.addColorStop(1, `hsla(${b.hue + 20}, ${b.sat}%, 50%, 0)`);
      ctx.beginPath(); ctx.fillStyle = gradient;
      ctx.ellipse(x, y, w, w * 0.3, Math.sin(this.time * 0.1 + b.phase) * 0.5, 0, Math.PI * 2);
      ctx.fill();
      // Light rays
      // ... 5-8 rays per beam, drawn as lines fading to transparent
      // Wrap-around at edges
      b.x += b.vx; b.y += b.vy;
    }
    requestAnimationFrame(() => this.animate());
  }
}
```

**Key patterns**: reset on resize, dpr-aware canvas, beams wrap around edges, overlapped radial gradients create aurora layering effect.

### 2. TiltedCard (3D Hover)

```javascript
class TiltedCard {
  constructor(element, options = {}) {
    this.element = element;
    this.options = { maxTilt: 8, perspective: 1000, scale: 1.02, speed: 300, glare: true, ...options };
    element.classList.add('vise-tilt');
    this.isMobile = window.matchMedia('(pointer: coarse)').matches;
    if (this.isMobile) return;
    // Wrap content in .vise-tilt-inner div
    // Add .vise-tilt-glow and .vise-tilt-shine divs for glare
  }
  onMouseMove(e) {
    const rect = this.element.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    const rotateX = ((y - rect.height/2) / (rect.height/2)) * -this.options.maxTilt;
    const rotateY = ((x - rect.width/2) / (rect.width/2)) * this.options.maxTilt;
    this.element.style.transform = `
      perspective(${this.options.perspective}px)
      rotateX(${rotateX}deg) rotateY(${rotateY}deg)
      scale3d(${this.options.scale}, ${this.options.scale}, ${this.options.scale})
    `;
    // Update --mouse-x / --mouse-y for glow
  }
  onMouseLeave() {
    this.element.style.transform = '';
    this.element.style.transition = `transform ${this.options.speed}ms ease`;
    setTimeout(() => { this.element.style.transition = ''; }, this.options.speed);
  }
}
```

**CSS**:
```css
.vise-tilt { transform-style: preserve-3d; will-change: transform; }
.vise-tilt-inner { transform-style: preserve-3d; pointer-events: none; }
.vise-tilt-glow {
  position: absolute; inset: 0; pointer-events: none; opacity: 0;
  transition: opacity 0.3s ease;
  background: radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(14, 165, 233, 0.15) 0%, transparent 60%);
}
.vise-tilt:hover .vise-tilt-glow { opacity: 1; }
```

**Key patterns**: CSS preserve-3d for perspective children, pointer-events: none on inner & glow, animation reset with transition timeout.

### 3. SpotlightCard (Radial Glow)

```javascript
class SpotlightCard {
  constructor(element) {
    element.classList.add('vise-spotlight');
    // Add .vise-spotlight-border div
  }
  onMouseMove(e) {
    const rect = this.element.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    this.element.style.setProperty('--mouse-x', x + '%');
    this.element.style.setProperty('--mouse-y', y + '%');
  }
}
```

**CSS** (key part):
```css
.vise-spotlight::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  opacity: 0; transition: opacity 0.3s ease;
  background: radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(14, 165, 233, 0.08) 0%, transparent 40%);
  z-index: 1;
}
.vise-spotlight:hover::before { opacity: 1; }
```

**Key patterns**: pure CSS approach — the JS only sets `--mouse-x`/`--mouse-y` custom properties. The actual glow rendering happens entirely in CSS via `radial-gradient` on `::before`.

### 4. CountUp (Scroll-Triggered Counter)

```javascript
class CountUp {
  constructor(element, options = {}) {
    this.target = options.target || 0;
    this.duration = options.duration || 2000;
    this.decimals = options.decimals || 0;
    this.observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.animated) {
        this.animated = true;
        this.animate();
        this.observer.disconnect();
      }
    }, { threshold: 0.3 });
    this.observer.observe(element);
  }
  animate() {
    const start = performance.now();
    const from = 0, to = this.target;
    const tick = (now) => {
      const progress = Math.min((now - start) / this.duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out
      this.numSpan.textContent = (from + (to - from) * eased).toFixed(this.decimals);
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
}
```

**Key patterns**: IntersectionObserver with `{ threshold: 0.3 }` and `disconnect()` after first trigger; cubic ease-out `1 - pow(1-t, 3)`; `font-variant-numeric: tabular-nums` for stable digit widths.

### 5. SplashCursor (Click Particles)

```javascript
class SplashCursor {
  constructor(options = {}) {
    this.options = {
      colors: ['#0ea5e9', '#f97316', '#2d8a63', '#8b5cf6', '#ec4899', '#fbbf24'],
      particleCount: 12, lifetime: 800, size: 6, gravity: 0.05, ...options,
    };
    this.canvas = document.createElement('canvas');
    this.canvas.id = 'vise-splash-canvas';
    // Fixed position, pointer-events: none, z-index: 99999
    document.body.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.resize();
    window.addEventListener('resize', () => this.resize());
    document.addEventListener('click', (e) => this.splash(e.clientX, e.clientY));
    document.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      if (touch) this.splash(touch.clientX, touch.clientY);
    }, { passive: true });
    this.animate();
  }
  splash(x, y) {
    for (let i = 0; i < this.options.particleCount; i++) {
      const angle = (i / this.options.particleCount) * Math.PI * 2 + Math.random() * 0.5;
      const speed = 2 + Math.random() * 4;
      this.particles.push({
        x, y, vx: Math.cos(angle) * speed * (0.5 + Math.random()),
        vy: Math.sin(angle) * speed * (0.5 + Math.random()),
        size: this.options.size * (0.4 + Math.random() * 0.6),
        color: this.options.colors[Math.floor(Math.random() * this.options.colors.length)],
        alpha: 1, decay: 0.015 + Math.random() * 0.02,
        gravity: this.options.gravity,
      });
    }
  }
  animate() {
    this.ctx.clearRect(0, 0, this.w, this.h);
    this.particles = this.particles.filter(p => {
      p.x += p.vx; p.y += p.vy; p.vy += p.gravity;
      p.vx *= 0.98; p.vy *= 0.98; p.alpha -= p.decay;
      return p.alpha > 0;
    });
    for (const p of this.particles) {
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = p.alpha;
      this.ctx.fill();
      this.ctx.globalAlpha = 1;
    }
    requestAnimationFrame(() => this.animate());
  }
}
```

**Key patterns**: `pointer-events: none` on overlay canvas so clicks pass through; particles filtered by alpha (remove dead); `globalAlpha` for fade-out; gravity for downward arc.

## Integration Patterns

### Initialization (IIFE)

```javascript
(function() {
  'use strict';
  // Define all classes above...
  function init() {
    // AuroraHero on <canvas id="vise-hero-canvas">
    // CountUp on [data-vise-countup]
    // SplashCursor (singleton)
  }
  document.addEventListener('DOMContentLoaded', init);

  // MutationObserver for dynamically-added cards
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node.nodeType === 1) {
          applyCardEffects(node);
        }
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });

  window.ViseBits = { AuroraHero, TiltedCard, SpotlightCard, CountUp, SplashCursor };
})();
```

### CSS Structure

```css
/* All at class level — no id selectors for reusable effects */
.vise-tilt { ... }
.vise-spotlight { ... }
.vise-countup { ... }
#vise-splash-canvas { position: fixed; inset: 0; z-index: 99999; pointer-events: none; }
#vise-hero-canvas { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 0; }
```

### Pitfalls

1. **`pointer: coarse` media query**: Always check this for 3D tilt/spotlight effects — they feel wrong on touch devices. Disable with `if (window.matchMedia('(pointer: coarse)').matches) return;`
2. **`devicePixelRatio`**: Canvas backgrounds MUST scale for retina displays. Miss this and the canvas looks blurry on Mac/iPad.
3. **MutationObserver fire-once**: Use `data-` attribute flag (`el.dataset.viseTilted`) to prevent double-initialization when observer fires for the same element.
4. **CSS transition reset**: After mouseleave on TiltedCard, the transition must be removed after it completes, or the next hover's immediate transform won't start from current position.
5. **Canvas resize**: Always clear and re-init beams on resize. Stale beam positions cause visual jumps.
6. **Dynamic cards after initial load**: City cards loaded via API need the MutationObserver approach. A simple `DOMContentLoaded` handler won't catch them.
