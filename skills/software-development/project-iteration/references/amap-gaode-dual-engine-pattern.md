# AMap (Gaode) + Leaflet Dual Map Engine Pattern

## Overview

China-facing web apps need accurate Chinese map data. **AMap (Gaode Maps)** provides superior China data vs OpenStreetMap/Leaflet. This pattern implements a **dual engine**: AMap when API key exists, Leaflet fallback otherwise.

## Architecture

```
Frontend                   Backend (Vercel WSGI)
  │                           │
  ├─ fetch /api/config ──────→  reads AMAP_KEY from env
  │                           │
  ├─ use_amap=true ──────────→  dynamically load AMap JS SDK
  │                           │    → init with dark style
  │                           │    → plot markers from /api/map
  │                           │
  └─ use_amap=false ─────────→  use Leaflet (CartoDB Dark tiles)
                                → plot same markers
```

## Key Types: Web端(JS API) vs Web服务

When creating an AMap application, choose **Web端(JS API)** — this is the browser SDK that loads interactive maps (`AMap.Map`, markers, controls). Not to be confused with **Web服务** (server-side REST API for geocoding/routing, which has different key management).

## AMap JS API v2.0 Security (Critical)

AMap v2.0+ requires TWO credentials:

| Credential | Environment Variable | Purpose |
|------------|-------------------|---------|
| **API Key** | `AMAP_KEY` | Identifies your app to the AMap service |
| **Security JS Code** (安全密钥) | `AMAP_SECURITY_CODE` | Prevents unauthorized use of the key on other domains |

The security code must be set **before** loading the AMap JS SDK:

```javascript
// MUST be set BEFORE loading https://webapi.amap.com/maps?v=2.0&key=...
window._AMapSecurityConfig = {
  securityJsCode: 'your-security-code-here',
};
```

⚠️ **Without the security code, AMap v2.0 will refuse to initialize** (error in console about missing security config).

## Backend Setup

### 1. Config API endpoint (`api/index.py`)

```python
def _handle_config(start_response):
    amap_key = os.environ.get("AMAP_KEY", "")
    amap_security = os.environ.get("AMAP_SECURITY_CODE", "")
    # Both key AND security code required to activate AMap
    use_amap = bool(amap_key and amap_security)
    return _json(start_response, {
        "amap_key": amap_key if use_amap else "",
        "amap_security_code": amap_security if use_amap else "",
        "use_amap": use_amap,
        "version": "3.0.3",
    })
```

### 2. Map data API endpoint (`api/index.py`)

Returns all city coordinates from MAP_DATA dictionary:

```python
def _handle_map(start_response):
    cities = _load_json(DATA_DIR / "cities.json") or {}
    result = {}
    for name in cities:
        if name in MAP_DATA:
            m = MAP_DATA[name]
            result[name] = {"lat": m["lat"], "lng": m["lng"]}
    return _json(start_response, {"cities": result})
```

### 3. Environment variable (Vercel)

Set `AMAP_KEY` in Vercel Dashboard → Settings → Environment Variables.

## Frontend: AMap Init

### Dynamic Script Loading (with Security Code)

```javascript
function initAMap(apiKey, securityCode) {
    // Step 1: Set security config BEFORE loading the SDK
    window._AMapSecurityConfig = {
        securityJsCode: securityCode || '',
    };

    // Step 2: Dynamically load the SDK
    const script = document.createElement('script');
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${apiKey}`;
    script.onload = () => {
        // Step 3: Initialize map (ONLY inside onload)
        const map = new AMap.Map('map-canvas', {
            zoom: 4,
            center: [104.0, 35.0],
            mapStyle: 'amap://styles/darkblue',
        });
        // Add markers, events...
    };
    document.head.appendChild(script);
}
```

### Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| API version | `v=2.0` | Latest AMap Web JS API |
| Dark style | `amap://styles/darkblue` | Fits dark UI themes |
| China center | `[104.0, 35.0]` | Approximate center of China |
| Default zoom | `4` | Country-level view |
| API endpoint | `https://webapi.amap.com/maps?v=2.0&key=${key}` | CDN |

### Adding Markers

```javascript
const marker = new AMap.Marker({
    position: [lng, lat],  // Note: [lng, lat] not [lat, lng]!
    title: "City Name",
    label: { content: "🐼", offset: new AMap.Pixel(-15, -15) },
});
marker.on('click', () => showMapDetail(cityKey));
map.add(marker);
```

**⚠️ Pitfall:** AMap uses `[lng, lat]` order. Leaflet uses `[lat, lng]`. Don't mix them up.

## Frontend: Leaflet Fallback

```javascript
function initLeafletMap() {
    mapInstance = L.map('map-canvas', {
        center: [35.0, 108.0],
        zoom: 4,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
    }).addTo(mapInstance);
    plotMarkers();
}
```

## Frontend: Auto-Detection

```javascript
function initMap() {
    if (mapInitialized && mapInstance) {
        mapInstance.invalidateSize();  // Reflow after tab switch
        return;
    }
    fetch('/api/config')
        .then(r => r.json())
        .then(config => {
            // Require BOTH key AND security code
            if (config.use_amap && config.amap_key && config.amap_security_code) {
                initAMap(config.amap_key, config.amap_security_code);
            } else {
                initLeafletMap();
            }
        })
        .catch(() => initLeafletMap());  // Fallback on error
}
```

## Configuration Steps (for the user)

To enable AMap:

1. **Register** at [console.amap.com](https://console.amap.com) → Create application
2. **Get Key** → Choose **Web端(JS API)** (NOT Web服务)
3. **Whitelist domain** → Security settings → add Vercel domain (e.g., `vise-panda-2.vercel.app`)
4. **Get Security Code** → In the same app, find the **安全密钥** (security JS code) field — it's separate from the API key
5. **Deploy** → Set both env vars in Vercel Dashboard → Redeploy

### Environment Variables (Vercel)

| Variable | Example Value | Notes |
|----------|---------------|-------|
| `AMAP_KEY` | `479e4513dd...` | Public API key — safe to serve to frontend |
| `AMAP_SECURITY_CODE` | `f5fcaf4b8c...` | Must NOT be hardcoded in source; serve via /api/config |

> ⚠️ **Both are required.** If only `AMAP_KEY` is set without `AMAP_SECURITY_CODE`, the backend reports `use_amap: false` and Leaflet is used. This is intentional — AMap v2.0 will fail without the security code, so we don't even try.

## Pitfalls

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Security domain not whitelisted** | Map shows "INVALID_USER_DOMAIN" error | Add domain in AMap console |
| **Missing security JS code** | Console error: security config required | Set `_AMapSecurityConfig.securityJsCode` before loading SDK |
| **Coord order confusion** | Markers in wrong country | AMap: `[lng, lat]`; Leaflet: `[lat, lng]` |
| **Script not loaded before AMap.Map()** | `AMap is not defined` | Put init inside `script.onload` |
| **Map grey after tab switch** | Map container has 0 dimensions | Call `mapInstance.invalidateSize()` after container becomes visible |
| **Missing Satellite layer** | No satellite view available | Add `layers: [new AMap.TileLayer.Satellite()]` for hybrid |
| **API key URL path** | AMap JS SDK returns 404 or stale | Always use `v=2.0` (latest stable). Old versions get removed |

## Example: VisePanda v3.0.3

Implemented in VisePanda (vise-panda-2.vercel.app):
- 36 city markers with emoji custom markers
- Three categories: Top Destinations (red), Regional Hubs (amber), Hidden Gems (green)
- City detail panel on marker click → "Plan a trip here" navigates to chat
- Dark theme throughout
- Full mobile responsive (map-wrapper respects viewport)
