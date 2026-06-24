# AMap (Gaode) JS API v2.0 Integration

Reference for integrating AMap/Gaode Maps (高德地图) into web SPAs with Leaflet fallback.

## Architecture (Dual-Engine)

```
Client (browser) → /api/config → backend checks AMAP_KEY + AMAP_SECURITY_CODE env vars
                                         ↓
                    use_amap: true? ──→ Load AMap JS API dynamically from CDN
                    use_amap: false? ──→ Load Leaflet from CDN (fallback)
```

Both engines produce the same UX: full China map + city markers with click-to-detail.

## Backend Setup

### Vercel Environment Variables

| Variable | Value |
|----------|-------|
| `AMAP_KEY` | Your Web JS API key from console.amap.com |
| `AMAP_SECURITY_CODE` | The "安全密钥" (securityJsCode) from the same application |

### API Endpoint (`/api/config`)

Returns client-safe config. The frontend fetches this to decide which engine to use.

```python
def _handle_config(start_response):
    amap_key = os.environ.get("AMAP_KEY", "")
    amap_security = os.environ.get("AMAP_SECURITY_CODE", "")
    use_amap = bool(amap_key and amap_security)
    return _json(start_response, {
        "amap_key": amap_key if use_amap else "",
        "amap_security_code": amap_security if use_amap else "",
        "use_amap": use_amap,
        "version": "3.0.5",
    })
```

### Key & Security Code

When creating a key on console.amap.com:
- **Service type**: Web端(JS API) — NOT Web服务 (which is for server-side REST API)
- **Domain whitelist**: yourdomain.com (e.g., vise-panda-2.vercel.app)
- **Security code** (安全密钥): used alongside the key for AMap JS API v2.x

## Frontend Integration

### Step 1: Fetch config and decide engine

```javascript
function initMap() {
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;
    if (mapInitialized && mapInstance) {
      mapInstance.invalidateSize();
      return;
    }

    fetch('/api/config').then(r => r.json()).then(config => {
      if (config.use_amap && config.amap_key && config.amap_security_code) {
        initAMap(config.amap_key, config.amap_security_code);
      } else {
        initLeafletMap();
      }
    }).catch(() => {
      initLeafletMap(); // fallback
    });
}
```

### Step 2: AMap initialization with security code

**Critical**: `window._AMapSecurityConfig` must be set BEFORE loading the AMap script.

```javascript
function initAMap(apiKey, securityCode) {
    const canvas = document.getElementById('map-canvas');
    if (!canvas) return;

    // MUST be set BEFORE loading the API script
    window._AMapSecurityConfig = {
      securityJsCode: securityCode || '',
    };

    const script = document.createElement('script');
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${apiKey}`;
    script.onload = () => {
      if (typeof AMap === 'undefined') return;
      const map = new AMap.Map('map-canvas', {
        zoom: 4,
        center: [104.0, 35.0],
        mapStyle: 'amap://styles/darkblue',  // dark theme
      });
      mapInstance = map;

      // Now plot markers from your data
      fetch('/api/map').then(r => r.json()).then(data => {
        const cities = data.cities || {};
        Object.keys(cities).forEach(key => {
          const c = cities[key];
          if (!c.lat || !c.lng) return;
          const marker = new AMap.Marker({
            position: [c.lng, c.lat],
            title: key,
          });
          marker.on('click', () => showCityDetail(key));
          map.add(marker);
        });
      });

      mapInitialized = true;
    };
    document.head.appendChild(script);
}
```

### Step 3: Leaflet fallback (open source, no API key)

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
    mapInitialized = true;
}
```

## AMap vs Leaflet Comparison

| Feature | AMap (Gaode) | Leaflet (CartoDB) |
|---------|--------------|-------------------|
| China data accuracy | ★★★★★ Exact POIs, roads | ★★★ OSM data, less precise |
| API key required | Yes (Web JS API + security code) | No (free tile servers) |
| Dark theme | `mapStyle: 'amap://styles/darkblue'` | CartoDB dark_all tiles |
| Marker clustering | Built-in via AMap.Plugin | Requires Leaflet.markercluster |
| Geolocation | AMap.Geolocation plugin | Leaflet locate control |
| Satellite tiles | Built-in via `layers: [new AMap.TileLayer.Satellite()]` | Requires 3rd party tile URL |

## AMap MapStyles

| Style Value | Description |
|-------------|-------------|
| `amap://styles/darkblue` | Dark theme with blue accents |
| `amap://styles/light` | Light/clean style |
| `amap://styles/fresh` | Fresh green style |
| `amap://styles/grey` | Gray/modern style |
| `amap://styles/macaron` | Pastel style |

## Pitfalls

1. **Script loading order**: `_AMapSecurityConfig` MUST be set before `<script src="...webapi.amap.com...">` loads. If reversed, security validation fails silently and no map renders.
2. **Lng/Lat order**: AMap uses `[lng, lat]` convention (GeoJSON standard). Leaflet uses `[lat, lng]`. Always double-check coordinate order.
3. **Zoom levels**: AMap max zoom is typically 18 (vs Leaflet's 19). Don't set `maxZoom: 19` in AMap.
4. **Marker labels**: AMap `label.offset` uses `new AMap.Pixel(-15, -15)` (absolute pixels). Leaflet uses `iconAnchor: [16, 16]` (relative to icon size).
5. **Domain whitelist**: AMap key must have the deployment domain whitelisted in the console. For local dev, you might need `127.0.0.1` added (though many keys work without it during dev).
6. **Vercel deployment**: The env vars must be redeployed after setting (click Redeploy on the deployment page, the commit push alone won't pick them up).
