# Scaffold + FAB + BottomNav (Chat CTA pattern)

> 在 4-tab 底部导航中，用 FAB 突出 Chat 入口的 Material 3 模式。

## 核心结构

```kotlin
Scaffold(
    containerColor = Background,
    bottomBar = {
        VpBottomNav(
            selectedTab = selectedTab,
            onTabSelected = { selectedTab = it }
        )
    },
    floatingActionButton = {
        // Chat FAB — 仅在非 Chat tab 时显示
        if (selectedTab != BottomNavTab.CHAT) {
            Box(
                modifier = Modifier
                    .padding(bottom = 8.dp)
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(Gold)  // 品牌金色
                    .clickable { selectedTab = BottomNavTab.CHAT },
                contentAlignment = Alignment.Center
            ) {
                Text(text = "\uD83D\uDCAC", fontSize = 18.sp)  // 聊天气泡emoji
            }
        }
    },
    floatingActionButtonPosition = FabPosition.Center  // 居中显示
) { innerPadding ->
    when (selectedTab) {
        BottomNavTab.HOME -> HomeScreen(modifier = contentModifier)
        BottomNavTab.CHAT -> ChatScreen(modifier = contentModifier)
        // ...
    }
}
```

## 要点

| 属性 | 值 | 理由 |
|------|-----|------|
| `FabPosition.Center` | 居中在底部导航上方 | 视觉上像"悬停"在导航栏中间 |
| 显示条件 | `selectedTab != CHAT` | Chat tab 时隐藏，避免重复 |
| 尺寸 | 48dp | 比标准 FAB(56dp) 小，不遮挡导航标签 |
| 颜色 | `Gold` (品牌色) | 从导航栏中跳脱出来 |
| 图标 | emoji / icon | 轻量，不需要额外 icon asset |

## 导航模式

使用 `mutableStateOf(BottomNavTab)` 而非 NavHost:
- 简单 4-tab 场景不需要 Navigation Compose 的 back stack
- 每个 tab 独立维护状态（remember + ViewModel）
- 切换时不会丢失 tab 内状态（如 Chat 对话历史）

## 何时应该用 NavHost

当以下任一条件满足时，切换到 Navigation Compose:
- 有深层嵌套页面（Home → CityDetail → Itinerary）
- 需要 back stack 支持
- 需要 deep link 支持
