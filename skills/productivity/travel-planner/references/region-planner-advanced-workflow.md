# Region Planner — Advanced Data-Driven Workflow

> **Source**: User's Region Planner project methodology (Italy Lux Offline V6).
> **When to use**: For projects needing structured iteration tracking, data/UI separation, multi-city POI management, and commercial partnership infrastructure. Use the base `travel-planner` skill for simple one-off itineraries; use this workflow for production-grade multi-region planners.

## 1. Architecture Difference

| Aspect | Travel-Planner (inline) | Region Planner (data-driven) |
|--------|------------------------|------------------------------|
| Data storage | JS constants embedded in index.html | Separate JSON files loaded on demand |
| Iteration tracking | Manual changelog | Scripted (`iter.js start/done`) |
| Validation | Node syntax check only | Dedicated `validate-data.js` |
| Image management | Manual | Auto-scan via `missing-images.js` |
| Commercial features | None built-in | buildOtaLink + localStorage analytics + partner tab |

## 2. Project Structure

```
project/
├── index.html                  # Shell (minimal, loads data)
├── data/
│   ├── core.json               # cities/routes/drives
│   ├── poi.<region>.json       # Attractions (按 cityKey 分组)
│   ├── food.<region>.json      # Restaurants
│   ├── hotels.<region>.json    # Hotels
│   ├── transport.<region>.json # Intercity comparisons
│   └── partners.json           # Deep link templates + utmDefaults + partners[]
├── assets/images/
│   ├── poi_<id>.webp
│   ├── hotel_<slug(name)>.webp
│   ├── food_<slug(name)>.webp
│   └── *_sm(640w)/_md(1024w).jpg  # Responsive JPG variants
├── scripts/v6/
│   ├── iter.js                 # Iteration tracking (start/done)
│   ├── validate-data.js        # Structural validation
│   ├── missing-images.js       # Missing image scanner
│   └── generate-jpg-variants.py # JPG responsive variants
└── manifest.json / sw.js       # PWA support
```

## 3. Mandatory Iteration Workflow

Each cycle must follow EXACTLY:

```bash
# 1) Start iteration
node scripts/v6/iter.js start <id> "<title>"

# 2) Modify data/page (following on-demand loading)

# 3) Validate structural integrity
node scripts/v6/validate-data.js --allow-missing

# 4) If images were added/modified:
node scripts/v6/missing-images.js --iter <id>

# 5) Local verification
python3 -m http.server 8000

# 6) If deploying:
#    commit + deploy first
node scripts/v6/iter.js done <id> --commit <hash> --deploy <url>
```

## 4. Data Contracts

### core.json
```json
{
  "cities": [{ "key": "rome", "name": "罗马", "lat": 41.9, "lng": 12.5, "tag": "历史古都" }],
  "routes": [{ "id": "north", "name": "北意深度", "color": "#...", "cities": ["milan","venice"] }],
  "drives": [{ "from": "rome", "to": "florence", "dist": "275km", "time": "3h" }]
}
```

### poi/restaurants/hotels JSON
- Keyed by cityKey for filtering
- Each item has: `id`, `name`, `desc` (3-4 sentences), `img` (path or URL), any type-specific fields
- Hotels: `stars`, `price`, `type`, `url`
- Food: `cuisine`, `price`
- Attractions: `tag` (地标/博物馆/自然等)

## 5. Image Naming

| Type | Pattern | Format |
|------|---------|--------|
| Attraction | `poi_<id>.webp` | WebP |
| Hotel | `hotel_<slug(name)>.webp` | WebP |
| Food | `food_<slug(name)>.webp` | WebP |
| Large JPG | `*_sm(640w)/_md(1024w)` | JPG + srcset |

slug() = remove symbols, lowercase, spaces→hyphens, truncate.

## 6. SW Caching Strategy

- HTML: network-first
- /assets: cache-first
- /data: stale-while-revalidate

## 7. Commercialization Skeleton

```js
// Uniform OTA link builder
buildOtaLink(provider, product, params) // appends UTM from utmDefaults

// Analytics (localStorage)
otaImpressions / otaClicks / otaJumps

// Partner tab
// Tab with partner processes, fields, sample redirects
```

## 8. Design Spec (for consistency)

- **Layout**: 3-column (left: city list + budget | center: tabbed content | right: Leaflet map)
- **Theme**: Dark (#07070a bg, #d6b46a gold, #90d5ff blue accent)
- **Panels**: Glassmorphism rgba(255,255,255,0.05-0.08), border-radius 14-20px
- **Typography**: Serif for headings, sans-serif for body (PingFang SC / Microsoft YaHei)
- **Tabs**: 9px uppercase, letter-spacing 0.1em
- **Cards**: Image + rating + price + external link
- **Price panel**: Itemized cost breakdown (rental/fuel/toll/hotel/food/experiences)
- **Map**: Leaflet with 高德/OSM/CartoDB multi-source fallback
