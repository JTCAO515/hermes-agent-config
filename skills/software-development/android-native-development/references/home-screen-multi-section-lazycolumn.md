# HomeScreen Multi-Section LazyColumn Pattern

> 适用于 Home/Tab 首页的 scrollable 多区块布局
> 从 VisePanda Native v1.0 (方案C 浅色东方) 中提取

---

## 结构概览

```
LazyColumn
├── item { HeroSection }          — 品牌V图标 + Headline + Subtitle + CTA
├── item { SectionHeader }        — "Featured Cities" + "See all"
├── item { FeaturedCitiesRow }    — LazyRow 横向城市卡片
├── item { SectionHeader }        — "Inspiration"
├── item { InspirationGrid }      — 竖排双卡片
├── item { SectionHeader }        — "Travel Essentials"
├── item { EssentialsGrid }       — 3×2 网格
└── item { Spacer(24.dp) }       — 底部安全空间
```

## 关键模式

### 1. Local Mock Data

```kotlin
private val featuredCities = listOf(
    CityData("Beijing", "Capital of China", listOf("Culture", "History")),
    // ...
)

private data class CityData(
    val name: String,
    val description: String,
    val tags: List<String>
)
```

**原则:** Mock data 类型是 `private` + 与 Screen composable 同文件。只在 `app/` 模块中使用。
如果数据需要跨页面共享，才抽到 `core:common` 模块。

### 2. SectionHeader

```kotlin
@Composable
private fun SectionHeader(
    title: String,
    actionText: String? = "See all"
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(start = 24.dp, end = 24.dp, top = 8.dp, bottom = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = title, style = MaterialTheme.typography.headlineMedium, color = TextPrimary)
        if (actionText != null) {
            Text(text = actionText, style = MaterialTheme.typography.bodyMedium, color = Gold)
        }
    }
}
```

**原则:** SectionHeader 是 `private` composable（只在 HomeScreen 用到）。如果多个 Screen 都需要，抽到 `core/designsystem/components/`。

### 3. Horizontal LazyRow with fixed width items

```kotlin
LazyRow(
    modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp),
    horizontalArrangement = Arrangement.spacedBy(12.dp)
) {
    items(cities) { city ->
        VpCityCard(
            onClick = { /* navigate */ },
            modifier = Modifier.width(200.dp),
            height = 220
        )
    }
}
```

**要点:**
- `LazyRow` 放在 `LazyColumn` 的 `item {}` 内（嵌套 Lazy）
- 项目使用 `Modifier.width()` 固定宽度，而非 `fillMaxWidth`
- 间距用 `Arrangement.spacedBy()` 而非手动加 padding

### 4. Chunked Grid (Essentials 3×2)

```kotlin
essentials.chunked(3).forEach { row ->
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        row.forEach { item ->
            EssentialTile(item = item, modifier = Modifier.weight(1f))
        }
        // Fill remaining space if last row has < 3 items
        if (row.size < 3) {
            repeat(3 - row.size) { Spacer(modifier = Modifier.weight(1f)) }
        }
    }
}
```

**要点:**
- `List.chunked(n)` 将长列表分为 n 元素一组
- 每行用 `Modifier.weight(1f)` 均分宽度
- 末行补齐用 `Spacer.weight()` 占位

### 5. Aspect Ratio Tiles

```kotlin
Card(
    onClick = { ... },
    modifier = modifier,  // weight(1f) from parent
    shape = RoundedCornerShape(12.dp),
) {
    Column(
        modifier = Modifier.fillMaxWidth().aspectRatio(1f).padding(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = item.icon, fontSize = 28.sp)
        Spacer(modifier = Modifier.height(6.dp))
        Text(text = item.label, style = MaterialTheme.typography.labelLarge, color = TextSecondary)
    }
}
```

`aspectRatio(1f)` 确保卡片始终为正方形，无需硬编码高度。

### 6. Hero Section with Brand Icon

```kotlin
Box(
    modifier = Modifier.size(56.dp).clip(CircleShape).background(Gold),
    contentAlignment = Alignment.Center
) {
    Text(text = "V", color = Color.White, fontSize = 24.sp, fontWeight = Bold)
}
```

**要点:** 品牌图标是 `CircleShape` + `Box` 居中文字，不需要导入任何图片资源。
如需实际图标，用 `Seedream` 生成 SVG 后放入 `app/src/main/res/drawable/`。

### 7. Inspiration Card (Row Layout)

```kotlin
Card(onClick = { ... }, shape = RoundedCornerShape(12.dp)) {
    Row(modifier = Modifier.fillMaxWidth().padding(20.dp), verticalAlignment = Center) {
        Box(modifier = Modifier.size(48.dp).clip(RoundedCornerShape(12.dp)).background(GoldLight.copy(alpha = 0.3f)),
            contentAlignment = Center) {
            Text(text = item.icon, fontSize = 22.sp)
        }
        Spacer(modifier = Modifier.width(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(text = item.title, style = MaterialTheme.typography.headlineMedium, color = TextPrimary)
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = item.description, style = MaterialTheme.typography.bodyMedium, color = TextSecondary, maxLines = 2)
        }
    }
}
```

---

## 完整代码参考

实际实现参见 `visepanda-native/app/src/main/java/com/visepanda/hermes/ui/home/HomeScreen.kt` (12KB, ~350行)
GitHub: `github.com/JTCAO515/visepanda-native/blob/master/app/src/main/java/com/visepanda/hermes/ui/home/HomeScreen.kt`
