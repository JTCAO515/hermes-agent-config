# ViseBits — 5 Animation Components for VP-Hermes-Web

> Created: 2026-06-23 | Project: VP-Hermes-Web (go2china.space)
> Source: Adapted from reactbits.dev patterns

## Files

| File | Description |
|------|-------------|
| `web/visebits.js` | All 5 components in IIFE |
| `web/visebits.css` | Component styles |
| `web/index.html` | Hero section + stats grid |
| `web/app.js` | MutationObserver integration |

## Components

### 1. AuroraHero (aurora beams background)
- Canvas-based animated light rays
- Auto-resizes to parent container
- Uses devicePixelRatio for Retina
- `new AuroraHero(canvasElement)`

### 2. TiltedCard (3D perspective tilt)
- `maxTilt: 8°`, `perspective: 1000px`, scale 1.02
- Wraps content in `.vise-tilt-inner`
- Optional glare + shine layers
- Disabled on touch devices

### 3. SpotlightCard (radial glow)
- Radial gradient follows mouse position
- CSS custom properties `--mouse-x`, `--mouse-y`
- Disabled on touch devices

### 4. CountUp (scroll-triggered counter)
- HTML: `<div data-vise-countup="36" data-vise-duration="2000" data-vise-suffix="+">`
- IntersectionObserver → scroll into view → animate
- Ease-out cubic timing

### 5. SplashCursor (click particles)
- Fixed canvas overlay, `pointer-events: none`, `z-index: 99999`
- 12 particles per click, 800ms lifetime
- 7 colors from brand palette
- Gravity + decay physics

## Integration Points

| Effect | Applied to | Method |
|--------|-----------|--------|
| Aurora | `#vise-hero-canvas` | Auto-init on DOMContentLoaded |
| Tilted + Spotlight | `.city-card` | MutationObserver on body |
| Count Up | `[data-vise-countup]` | Auto-init on DOMContentLoaded |
| Splash | Global click | Auto-init (singleton flag) |

## Key Decisions
- Vanilla JS IIFE to avoid polluting global scope
- Touch device check via `matchMedia('(pointer: coarse)')` — tilt/spotlight disabled on mobile
- MutationObserver picks up dynamically loaded cards — no need to modify app.js
- Canvas components use `devicePixelRatio` for sharp rendering
