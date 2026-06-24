# Leaflet Dark Map Integration (stdlib Vercel App)

> 在纯标准库 Vercel 应用（WSGI/Handler 模式）中，如何通过 CDN 引入第三方 Leaflet.js 地图库。从 VisePanda v3.0.1 Iter 7 提炼。

## 架构

```
CDN (unpkg) ─→ Leaflet CSS + JS ─→ 浏览器加载
                  ↓
              HTML <link> + <script> (部署前静态文件)
                  ↓
              VP.initCityMap(mapId, mapData) ─→ 地图实例化
                  ↓
          CartoDB dark_all tile layer ─→ 暗色底图
                  ↓
          城市中心标记 + POI 分类标记 ─→ 交互地图
```

## 实现步骤

### Step 1 — 加载 Leaflet（纯 CDN，零 npm）

```html
<!-- index.html head -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin>

<!-- index.html body 末尾（app.js 之前） -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin></script>
```

### Step 2 — 前后端数据流

后端 API 返回地图数据：

```python
# API /api/cities/beijing → response
{
  "map": {
    "lat": 39.9042, "lng": 116.4074, "zoom": 11,
    "pois": [
      {"name": "Forbidden City", "name_cn": "故宫", "lat": 39.9163, "lng": 116.3972, "type": "history"},
      {"name": "Great Wall", "name_cn": "长城", "lat": 40.3601, "lng": 116.0114, "type": "landmark"},
    ]
  }
}
```

前端提取数据后调用初始化函数。

### Step 3 — 前端地图初始化

```javascript
function initCityMap(mapId, mapData) {
  if (!window.L || !mapData.lat || !mapData.lng) return;

  var tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  var tileAttr = '&copy; OSM contributors, &copy; CartoDB';

  var map = window.L.map(mapId, {
    center: [mapData.lat, mapData.lng],
    zoom: mapData.zoom || 11,
    zoomControl: true,
    attributionControl: false,
  });

  window.L.tileLayer(tileUrl, { attribution: tileAttr, maxZoom: 18 }).addTo(map);

  // 城市中心标记（红色金边）
  var goldIcon = window.L.divIcon({
    className: 'map-marker-city',
    html: '<div style="background:#bc3a2c;width:16px;height:16px;border-radius:50%;border:3px solid #c9a96e;box-shadow:0 2px 8px rgba(0,0,0,.5)"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
  window.L.marker([mapData.lat, mapData.lng], { icon: goldIcon }).addTo(map);

  // POI 分类标记
  var typeColors = {
    history: '#c9a96e',
    nature: '#7dd3fc',
    food: '#bc3a2c',
    culture: '#a78bfa',
    landmark: '#f59e0b',
    modern: '#6ee7b7',
    entertainment: '#f472b6',
  };

  if (mapData.pois) {
    mapData.pois.forEach(function(poi) {
      var color = typeColors[poi.type] || '#888';
      var poiIcon = window.L.divIcon({
        className: 'map-marker-poi',
        html: '<div style="background:' + color + ';width:10px;height:10px;border-radius:50%;border:2px solid rgba(255,255,255,.6);box-shadow:0 2px 6px rgba(0,0,0,.4)"></div>',
        iconSize: [10, 10],
        iconAnchor: [5, 5],
      });
      var marker = window.L.marker([poi.lat, poi.lng], { icon: poiIcon }).addTo(map);
      marker.bindPopup('<b>' + escHtml(poi.name) + '</b>' + 
        (poi.name_cn ? '<br><span style="font-size:12px;color:#888">' + escHtml(poi.name_cn) + '</span>' : ''));
    });
  }

  setTimeout(function() { map.invalidateSize(); }, 200);
  return map;
}
```

### Step 4 — 暗色主题 CSS 覆盖

```css
.city-map{
  height:260px;
  border-radius:var(--radius-md);
  overflow:hidden;
  border:1px solid var(--border-subtle);
}
.city-map .leaflet-container{background:#0a0f17}
.city-map .leaflet-control-zoom a{background:var(--bg-elevated);color:var(--text-secondary);border-color:var(--border-default)}
.city-map .leaflet-control-zoom a:hover{background:var(--bg-hover);color:var(--text-primary)}
.city-map .leaflet-popup-content-wrapper{background:var(--bg-secondary);color:var(--text-primary);border-radius:var(--radius-md);box-shadow:var(--shadow-elevated);border:1px solid var(--border-default)}
.city-map .leaflet-popup-tip{background:var(--bg-secondary);border:1px solid var(--border-default)}
.city-map .leaflet-popup-content{margin:8px 12px;font-size:13px;line-height:1.4}
```

### Step 5 — 资源清理

```javascript
function closeCityDetail() {
  if (window._vpMaps) {
    window._vpMaps.forEach(function(m) { m.remove(); });
    window._vpMaps = [];
  }
}
```

## Pitfalls

- ❌ `map.invalidateSize()` 必须延迟调用 → Modal 动画期间容器尺寸未定 → 地图灰色
- ❌ `window.L` 必须延迟检查 → Leaflet JS 需加载完成
- ❌ 多实例必须清理 → 事件监听残留 + 内存泄漏
- ❌ Leaflet CSS 必须在 head 加载，JS 在 body 末尾 → CSS 缺失导致布局错乱
- ❌ `attributionControl: false` 在暗色模式下必须 → 白文字看不清
