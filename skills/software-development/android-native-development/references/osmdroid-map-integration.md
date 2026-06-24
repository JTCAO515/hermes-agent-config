# osmdroid MapView in Jetpack Compose

> osmdroid 是 OpenStreetMap 的 Android 端实现，开源免费，无需 API Key。
> 使用 `AndroidView` 将传统 View-based 地图嵌入 Compose。

---

## 核心模式

```kotlin
@Composable
fun ChinaMapScreen() {
    var mapView by remember { mutableStateOf<MapView?>(null) }

    AndroidView(
        factory = { ctx ->
            MapView(ctx).apply {
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)

                // 定位中国中心
                controller.setZoom(4.0)
                controller.setCenter(GeoPoint(35.86, 104.19))

                // 添加标记
                cities.forEach { city ->
                    val marker = Marker(this).apply {
                        position = GeoPoint(city.lat, city.lng)
                        title = city.name
                        setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                        icon = createCityMarkerIcon(ctx)
                        setOnMarkerClickListener { _, _ ->
                            onMarkerClick(city)
                            true
                        }
                    }
                    overlays.add(marker)
                }
                mapView = this
                invalidate()
            }
        },
        modifier = Modifier.fillMaxSize()
    )
}
```

## 配置初始化

```kotlin
// 在 Composable 中，用 remember 确保只初始化一次
remember {
    Configuration.getInstance().apply {
        userAgentValue = context.packageName
        osmdroidBasePath = context.cacheDir
        osmdroidTileCache = context.cacheDir.resolve("tiles")
    }
}
```

## 自定义标记图标 (程序化绘制)

```kotlin
private fun createCityMarkerIcon(context: Context): Drawable? {
    val density = context.resources.displayMetrics
    val size = 24.dp.toInt(density)
    val bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(bitmap)
    val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    // 橙色实心圆
    paint.color = 0xFFE8912E.toInt()  // PandaAmberDark
    paint.style = Paint.Style.FILL
    canvas.drawCircle(size / 2f, size / 2f, size / 2.5f, paint)

    // 白色描边
    paint.color = android.graphics.Color.WHITE
    paint.style = Paint.Style.STROKE
    paint.strokeWidth = 2f
    canvas.drawCircle(size / 2f, size / 2f, size / 2.5f - 1f, paint)

    return BitmapDrawable(context.resources, bitmap)
}
```

## 备用坐标 (API 不可用时)

VisePanda-Android 有 34 城硬编码坐标的 `FALLBACK_CITIES` 列表。当 API 返回空或失败时，自动 fallback。

```kotlin
private val FALLBACK_CITIES = listOf(
    MapMarker("beijing", "北京", 39.9042, 116.4074, "Ancient capital", "3-5 days"),
    MapMarker("shanghai", "上海", 31.2304, 121.4737, "Modern metropolis", "3-4 days"),
    MapMarker("chengdu", "成都", 30.5728, 104.0668, "Panda & Sichuan food", "3-5 days"),
    MapMarker("guangzhou", "广州", 23.1291, 113.2644, "Canton cuisine", "2-3 days"),
    // ... 完整 34 城列表见 actual implementation
    MapMarker("tibet", "西藏", 29.6500, 91.1000, "High plateau", "5-7 days"),
)
```

## Design 考虑

- **弹窗位置**: Marker 点击后底部弹出 `CityInfoPopup`（中文名/英文名/vibe/天数/Tap to explore）
- **点击卡片**: 跳转到 `CityDetailScreen`（复用 Step 5 的详情页）
- **缩放级别**: zoom=4 显示全中国，用户可双指缩放

## 限制

- osmdroid 瓦片源 (MAPNIK) 中国区域不如高德/百度详细
- 不支持 3D 地图、实时交通
- 如果用 AMap SDK 替换：需中国开发者账号 + fastjson + 专有 SDK。MVIP 阶段 osmdroid 够用。

## Pitfalls

1. **`AndroidView` 内存泄漏**: `MapView` 需要在 Composable 离开时销毁。在 `DisposableEffect` 中调用 `mapView.onDetach()`。
2. **瓦片缓存**: `osmdroidTileCache` 默认在内部存储，如果图片瓦片太多可能膨胀。MVP 阶段可忽略。
3. **代理冲突**: `http_proxy` 环境变量可能阻塞 osmdroid 下载瓦片（腾讯云场景）。如果地图空白，检查代理。
4. **`onResume/onPause`**: MapView 是传统 View，生命周期需要手动管理。在 `AndroidView` 的 `update` lambda 中无法获取 Activity 生命周期。复杂场景建议用 `MapViewComposable` 封装。
