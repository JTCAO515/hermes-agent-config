---
name: android-native-development
description: Build native Android apps with Kotlin + Jetpack Compose — project skeleton, Gradle config, Compose UI, Navigation, Retrofit API layer, SSE streaming, osmdroid maps, CI/CD with GitHub Actions. 触发词：Android/安卓/Kotlin/Compose/APK/原生App
version: 1.0.0
---

# Android Native App Development (Kotlin + Jetpack Compose)

> 从零开始构建原生 Android 应用的完整流程。适用于替换 PWA/TWA 套壳为真正原生体验的场景。

---

## 用户沟通信号 (vp-hermes 用户模式)

此用户的沟通方式有鲜明特征，所有工作节奏应遵循以下规则：

### 速度与节奏
- **"下一步" / "继续"** — 不要停下来问"选哪个"。默认执行计划中的下一项。如果多任务并行，全都启动。
- **"两个一起写"** — 明确要求并行。立即将独立任务拆分执行，不要等一个完成再开始下一个。
- **连续说"下一步"** — 每次做完只给 1-2 行状态 + 下一步，不要长篇总结。

### 直接交付
- **"直接传文件给我"** — 不要告诉他怎么获取，直接把文件传过去或搭好下载通道。
- **异常**: 微信发文件失败时 → 搭 HTTP 下载通道，给出链接。不要反复重试放弃。

### 汇报格式
- 简短：`P#: 功能名 ✅` 格式，列出关键文件变更
- 不要 verbose 分析过程（除非用户问"为什么卡住了"）
- 不要等确认，交付即完成

### 当用户反馈"粗糙"时
- 问具体方向（品牌感/动画/空态/阴影/字体）
- 不要自己列一堆选项让用户选，给出优先级建议即可

---

## 核心原则

1. **先 PM 规划，再写代码** — 写完整产品规划文档（愿景→功能→技术选型→屏幕映射→API契约→工作量），用户确认后再逐模块实施
2. **设计先行（design-first）** — 编码前先用 sketch skill 出 2-3 个 HTML mockup 视觉方案对比，再用 figma-generate-library 建设计系统 + figma-generate-design 画页面。用户确认设计方向后再编码。避免"代码写一半发现方向不对"。
3. **设计系统模块独立** — 设计 tokens (Color/Type/Spacing/Shape) 和组件 (Button/Chip/Card/BottomNav) 放在独立 `core/designsystem` 模块中，与 Material 默认主题解耦，方便 iOS 对齐。
2. **单 Activity 架构** — 一个 `MainActivity` + Jetpack Compose navigation
3. **MVVM 模式** — Screen → ViewModel → Repository → API/DB
4. **Gradle Kotlin DSL** — 所有构建脚本用 `.kts`，用 Version Catalog (`libs.versions.toml`) 管理依赖
5. **Material 3 + 品牌色** — Compose Material 3 主题，映射 Web 项目的设计系统
6. **GitHub Actions CI/CD** — 云端编译 APK，不依赖本地 Android Studio

---

## 从中国大陆构建 (China-specific)

腾讯云/阿里云服务器从 `services.gradle.org` 和 `repo1.maven.org` 下载超时是常见问题。需要配置国内镜像。

### Gradle 发行版下载

Gradle Wrapper 下载 `gradle-*-bin.zip` 时默认从 `services.gradle.org`，中国大陆网络超时严重。

```kotlin
// gradle/wrapper/gradle-wrapper.properties — 改用腾讯云镜像
distributionUrl=https\\://mirrors.tencent.com/gradle/gradle-8.5-bin.zip
```

**手动离线缓存 (兜底方案):**
```bash
# 1. 用 curl 从腾讯/华为镜像下载
curl -L --connect-timeout 10 --max-time 120 \
  "https://mirrors.tencent.com/gradle/gradle-8.5-bin.zip" \
  -o /tmp/gradle-8.5-bin.zip

# 2. 放入 Gradle wrapper cache
HASH=$(python3 -c "
import hashlib
url = 'https://services.gradle.org/distributions/gradle-8.5-bin.zip'
h = hashlib.md5(url.encode()).hexdigest()
import math
chars = '0123456789abcdefghijklmnopqrstuvwxyz'
n = int(h, 16)
result = ''
while n > 0:
    result = chars[n % 36] + result
    n //= 36
print(result)
")
mkdir -p ~/.gradle/wrapper/dists/gradle-8.5-bin/$HASH/
cp /tmp/gradle-8.5-bin.zip ~/.gradle/wrapper/dists/gradle-8.5-bin/$HASH/
rm -f ~/.gradle/wrapper/dists/gradle-8.5-bin/$HASH/*.lck ~/.gradle/wrapper/dists/gradle-8.5-bin/$HASH/*.part
```

### Maven 依赖镜像

```kotlin
// settings.gradle.kts — 添加国内 Maven 镜像
dependencyResolutionManagement {
    @Suppress("UnstableApiUsage")
    repositories {
        google()                           // 无需镜像
        maven { url = uri("https://maven.aliyun.com/repository/public") }
        maven { url = uri("https://jitpack.io") }  // 如需要
        mavenCentral()
    }
}
```

### 可用国内镜像源

| 源 | Gradle 发行版 | Maven 依赖 |
|----|-------------|-----------|
| 腾讯云 | `mirrors.tencent.com/gradle/` | 无专用 Maven 镜像 |
| 阿里云 | `mirrors.aliyun.com/gradle/` | `maven.aliyun.com/repository/public` |
| 华为云 | `mirrors.huaweicloud.com/gradle/` | `repo.huaweicloud.com/repository/maven/` |

**注意**: 修改 `distributionUrl` 后，Gradle wrapper 的 cache hash 会变化（基于完整 URL 的 MD5→base36），所以需要重新计算 hash 或删掉旧的 `.lck/.part` 文件。

```toml
[versions]
agp = "8.2.2"
kotlin = "1.9.22"
composeBom = "2024.02.00"
composeCompiler = "1.5.10"
navigationCompose = "2.7.7"
retrofit = "2.9.0"
okhttp = "4.12.0"
kotlinxSerialization = "1.6.3"
coil = "2.6.0"
osmdroid = "6.1.18"
datastore = "1.0.0"

[libraries]
# Compose BOM — 不指定版本号，由 BOM 统一管理
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-ui = { group = "androidx.compose.ui", name = "ui" }
androidx-ui-graphics = { group = "androidx.compose.ui", name = "ui-graphics" }
androidx-material3 = { group = "androidx.compose.material3", name = "material3" }
androidx-material-icons-extended = { group = "androidx.compose.material", name = "material-icons-extended" }
androidx-navigation-compose = { group = "androidx.navigation", name = "navigation-compose", version.ref = "navigationCompose" }

# Networking
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
okhttp = { group = "com.squareup.okhttp3", name = "okhttp", version.ref = "okhttp" }
okhttp-logging = { group = "com.squareup.okhttp3", name = "logging-interceptor" }
kotlinx-serialization-json = { group = "org.jetbrains.kotlinx", name = "kotlinx-serialization-json" }
retrofit-kotlinx-serialization = { group = "com.jakewharton.retrofit", name = "retrofit2-kotlinx-serialization-converter", version = "1.0.0" }

# Image loading
coil-compose = { group = "io.coil-kt", name = "coil-compose" }
coil-gif = { group = "io.coil-kt", name = "coil-gif" }

# Map
osmdroid-android = { group = "org.osmdroid", name = "osmdroid-android" }

# Local storage
androidx-datastore-preferences = { group = "androidx.datastore", name = "datastore-preferences" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
```

---

## 项目结构 (多模块架构)

对于品牌定制 App，建议使用多模块架构将设计系统、网络层、公共模型解耦：

```
ProjectName/
├── build.gradle.kts              # Root: plugins { android-application(apply=false), kotlin-android(apply=false) }
├── settings.gradle.kts           # include(":app", ":core:designsystem", ":core:network", ":core:common")
├── gradle.properties             # android.useAndroidX=true, kotlin.code.style=official
├── gradle/libs.versions.toml     # 版本目录（可选，多模块时推荐）
├── local.properties              # sdk.dir=/path/to/android-sdk（本地开发，不提交）
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/visepanda/hermes/
│       │   ├── MainActivity.kt            # 单 Activity + Compose
│       │   └── VisePandaApp.kt            # Application
│       └── res/
│           ├── values/         (strings.xml, themes.xml)
│           └── drawable/       (ic_launcher_*.xml)
├── core/designsystem/           # 设计系统独立模块
│   ├── build.gradle.kts
│   └── src/main/java/com/visepanda/designsystem/
│       ├── Color.kt            # 品牌色板
│       ├── Type.kt             # 字体系统（8级字形）
│       ├── Theme.kt            # MaterialTheme 组装
│       ├── Spacing.kt          # 间距刻度
│       ├── Shape.kt            # 圆角系统
│       └── components/
│           ├── VpButton.kt     # 品牌按钮（Gold/Secondary/Ghost）
│           ├── VpChip.kt       # 标签（Gold/JadeGreen/JadeGrey）
│           ├── VpCard.kt       # 卡片（CityCard/TripCard）
│           ├── VpBottomNav.kt  # 底部导航
│           └── VpShimmer.kt    # 骨架屏
├── core/network/                # 网络层独立模块
│   ├── build.gradle.kts
│   └── src/main/java/com/visepanda/network/
│       ├── ApiConfig.kt        # BASE_URL + 端点定义
│       ├── ApiService.kt       # REST + SSE 调用
│       ├── HttpClientProvider.kt  # OkHttp 单例
│       └── sse/SseClient.kt    # SSE 协议解析
├── core/common/                 # 公共模型
│   ├── build.gradle.kts
│   └── src/main/java/com/visepanda/common/
│       ├── UiState.kt          # sealed class: Loading/Success/Empty/Error
│       └── AppError.kt         # sealed class: Network/Server/Parse/EmptyData/Unknown
└── .github/workflows/build.yml
```

**为什么推荐多模块:**
- `core/designsystem` 是纯展示层，不依赖网络/数据模块，可独立预览
- `core/network` 不依赖 Compose，View层变化不影响网络层
- iOS 阶段可复用 designsystem 的 token 定义（Color/Type/Spacing/Shape），不是 copy 截图
- 构建速度：单一模块变更不会触发全部重编

---

## 关键配置模式

### settings.gradle.kts

```kotlin
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
```

**⚠️ Pitfall**: 必须用 `dependencyResolutionManagement`（Kotlin DSL），不是 `dependencyResolution`（Groovy DSL 旧写法）。

### app/build.gradle.kts — Compose

```kotlin
android {
    buildFeatures { compose = true }
    composeOptions {
        kotlinCompilerExtensionVersion = libs.versions.composeCompiler.get()
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.material3)
    // ...
}
```

### app/build.gradle.kts — signingConfigs

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("../android.keystore")
            storePassword = "..."
            keyAlias = "..."
            keyPassword = "..."
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

**⚠️ Pitfall**: `signingConfigs.create()` 必须在 `android {}` 作用域内的 `signingConfigs {}` 块中，不能在 `buildTypes.release {}` 闭包内创建。AGP 8.x 不允许在 buildTypes 内动态创建 signing config。

### PullToRefreshBox (Material 3)

```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(viewModel: HomeViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsState()

    PullToRefreshBox(
        isRefreshing = uiState is HomeUiState.Loading,
        onRefresh = { viewModel.loadCities() },
        modifier = Modifier.fillMaxSize()
    ) {
        when (val state = uiState) {
            is HomeUiState.Loading -> LoadingContent()
            is HomeUiState.Success -> HomeContent(state.cities)
            is HomeUiState.Error -> ErrorContent(state.message)
        }
    }
}
```

**⚠️ Pitfall**: `PullToRefreshBox` 是 `ExperimentalMaterial3Api`，需要 `@OptIn` 注解。
**⚠️ 版本坑**: `PullToRefreshBox` 需要 Compose Material 3 **1.3.0+**（对应 Compose BOM **2024.09.00+**）。
使用 BOM 2024.02.00 时 Material 3 为 ~1.2.x，`PullToRefreshBox` **根本不存在**，编译报 `Unresolved reference: PullToRefreshBox`。
解决方案：
- **升级 BOM**: 将 `composeBom` 升到 `2024.09.00+`（推荐，但可能引入其他 breaking change）
- **替换为 Box + 手动刷新按钮**: 移除 PullToRefreshBox wrapper，改为 Box + IconButton(Icons.Default.Refresh) 手动触发 viewModel.load()

### 零依赖 Markdown 渲染 (AnnotatedString)

Android Compose 中渲染 **bold**, *italic*, `code`, ### header, - list, [link] 等 Markdown 语法。不引入外部库，纯 `buildAnnotatedString`。

**参考:** `references/markdown-text-composable.md` — 完整代码示例

要点:
- 支持：**bold** / *italic* / `code` / ### H / - list / [link] / --- hr
- 不支持：表格、代码高亮、嵌套列表、图片（Chat 场景 90% 够用）
- 需要扩展时：加一个 `when` 分支 + `withStyle(SpanStyle(...))` 即可

### SSE ChatViewModel 模式

### SSE ChatViewModel 模式

Chat SSE 流式收集的标准 ViewModel 架构。Token 累积 → Split 刷新 → Done 关闭。

**参考:** `references/chat-viewmodel-sse-pattern.md` — 完整代码

状态设计:
- `currentStreamText` — 实时流式文本（UI 用 `collectAsState()` 实时渲染）
- `currentImages` / `currentFaqs` — 流式中的图片/FAQ
- `isStreaming` — 控制 Send/Stop 按钮切换

自动滚动: `LaunchedEffect(itemCount) { listState.animateScrollToItem(itemCount - 1) }`

### 模板文件

`templates/app-build.gradle.kts` — 项目快速启动骨架（含 Compose/Navigation/Retrofit/Coil/osmdroid/DataStore，`{{placeholder}}` 替换即可）

### API Map-to-List 转换 (API 返回 `{cities: {name: {...}}}` 而非数组)

当后端 API 返回 JSON 对象键值对而非数组时，用 `kotlinx.serialization.json` 手动解析：

```kotlin
suspend fun getCities(): List<City> {
    val response = URL("$BASE_URL/api/cities").readText()
    val root = Json.parseToJsonElement(response).jsonObject
    val citiesObj = root["cities"]?.jsonObject ?: return emptyList()
    return citiesObj.entries.map { (name, element) ->
        val obj = element.jsonObject
        City(
            name = name,
            nameCn = obj["name_cn"]?.jsonPrimitive?.content ?: "",
            vibe = obj["vibe"]?.jsonPrimitive?.content ?: "",
            // ... 逐字段映射
        )
    }
}
```

优点：零额外依赖，不依赖 Retrofit converter。用 `ignoreUnknownKeys = true` 避免 schema 不匹配。

### DataStore 本地持久化 (替代 Room DB for MVP)

保存 JSON 序列化的数据到 DataStore Preferences（单 key）：

```kotlin
private val Context.tripsDataStore: DataStore<Preferences> by preferencesDataStore(name = "app_data")

class TripRepository(private val context: Context) {
    companion object {
        private val KEY = stringPreferencesKey("saved_trips")
    }
    private val json = Json { ignoreUnknownKeys = true }

    fun getAllTrips(): Flow<List<Trip>> {
        return context.tripsDataStore.data.map { prefs ->
            val raw = prefs[KEY] ?: "[]"
            json.decodeFromString(raw) // 返回空列表而非崩溃
        }
    }

    suspend fun saveTrip(trip: Trip) {
        context.tripsDataStore.edit { prefs ->
            val trips = json.decodeFromString<MutableList<Trip>>(prefs[KEY] ?: "[]")
            trips.add(trip)
            prefs[KEY] = json.encodeToString(trips)
        }
    }
}
```

**优于 Room 的理由（MVP 阶段）：** 无需写 DAO/Database/Entity，零 SQL 知识，<20 行代码实现 CRUD。数据量小（<100 条行程）时性能无差异。

---

## 主题映射 (Web CSS → Compose Material 3)

| Web CSS Token | Compose Color | 用途 |
|---------------|---------------|------|
| `#F5A623` / `#E8912E` | `PandaAmber` / `PandaAmberDark` | Primary |
| `#4CAF50` / `#388E3C` | `BambooGreen` / `BambooGreenDark` | Secondary |
| `#E53935` / `#C62828` | `ChinaRed` / `ChinaRedDark` | Tertiary/Error |
| `#0E0B14` / `#1A1525` | `DarkBg` / `DarkSurface` | Background (Dark) |
| `#F5F0EB` / `#FFFFFF` | `LightBg` / `LightSurface` | Background (Light) |
| `#EDE7F6` / `#9E9E9E` | `DarkTextPrimary` / `DarkTextSecondary` | 文字 (Dark) |
| `#1A1525` / `#666666` | `LightTextPrimary` / `LightTextSecondary` | 文字 (Light) |

---

## 底部导航 (5 Tab)

```kotlin
enum class BottomNavItem(val route: String, val label: String, val icon: ImageVector) {
    HOME("home", "Home", Icons.Default.Home),
    CHAT("chat", "Chat", Icons.Default.Chat),
    MAP("map", "Map", Icons.Default.Map),
    TRIPS("trips", "Trips", Icons.Default.ListAlt),
    TOOLS("tools", "Tools", Icons.Default.Build);
}
```

**要点:**
- 用 `currentBackStackEntryAsState()` 获取当前路由
- 只在主路由（`bottomBarRoutes`）显示 BottomBar，详情页隐藏
- 导航用 `popUpTo(HOME) { saveState = true }` + `launchSingleTop = true` + `restoreState = true` 保持 back stack 干净
- 对于简单 4-tab 场景（无深层导航），可用 `mutableStateOf(BottomNavTab)` + `when {}` 代替 NavHost，状态保持更简单

**Chat FAB 模式:** 在 4-tab 底部导航中用一个金色 FAB 突出 Chat 入口。参考 `references/scaffold-fab-bottomnav.md`。

---

## SSE 流式聊天 (Android 无原生 EventSource)

Android 没有浏览器的 `EventSource` API，需要自建：

```kotlin
class SseClient(private val okHttpClient: OkHttpClient) {
    fun streamChat(requestBody: RequestBody): Flow<ChatEvent> = callbackFlow {
        val request = Request.Builder()
            .url("$BASE_URL/api/chat")
            .post(requestBody)
            .build()

        okHttpClient.newCall(request).enqueue(object : Callback {
            override fun onResponse(call: Call, response: Response) {
                val source = response.body?.source() ?: return
                while (!source.exhausted()) {
                    val line = source.readUtf8Line() ?: break
                    when {
                        line.startsWith("data: ") -> {
                            val data = line.removePrefix("data: ")
                            trySend(parseChatEvent(data))
                        }
                    }
                }
                trySend(ChatEvent.Done)
                close()
            }
        })
        awaitClose { /* cancel call */ }
    }
}
```

**MVC fallback**: 如果 SSE 实现有困难，先用 POST blocking call 获取完整 JSON 回复，UI 一次性渲染。优先级：活板先跑 > 流式后期优化。

---

## Launcher 图标生成 (从 PNG → Android Adaptive Icon)

### Adaptive Icon 尺寸 (正确)

Android 自适应图标使用 108dp 作为基准尺寸，foreground + background 两层叠加：

| Density | Scale | Foreground px | Background |
|---------|-------|--------------|------------|
| mdpi | 1x | 108×108 | 矢量/纯色 |
| hdpi | 1.5x | 162×162 | 同上 |
| xhdpi | 2x | 216×216 | 同上 |
| xxhdpi | 3x | 324×324 | 同上 |
| xxxhdpi | 4x | 432×432 | 同上 |

```python
# ✅ 正确 — Adaptive icon foreground sizes (108dp base)
from PIL import Image
img = Image.open("source-1024x1024.jpg").convert("RGB")

sizes = {
    "mipmap-mdpi": 108,
    "mipmap-hdpi": 162,
    "mipmap-xhdpi": 216,
    "mipmap-xxhdpi": 324,
    "mipmap-xxxhdpi": 432,
}
for folder, px in sizes.items():
    resized = img.resize((px, px), Image.LANCZOS)
    resized.save(f"app/src/main/res/{folder}/ic_launcher_foreground.png", "PNG")
```

### Adaptive Icon XML

```xml
<!-- app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- Background: 纯色或矢量 -->
    <background android:drawable="@drawable/ic_launcher_background"/>
    <!-- Foreground: 从 PNG 生成的 mipmap 资源 -->
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
```

### Background vector (纯金色)

```xml
<!-- app/src/main/res/drawable/ic_launcher_background.xml -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#FFC9A96E" android:pathData="M0,0h108v108H0z"/>
</vector>
```

### ⚠️ 常见坑 (旧模式 vs 自适应)

- **旧模式尺寸 (pre-API 26)** 使用 48/72/96/144/192px 作为 launcher icon — 这**不适合**自适应图标
- **自适应图标 foreground 必须 108dp base** — 对应上面表格的 px 值
- **background 可以选择纯色或矢量** — 纯色最简单（Android 会用 `fillColor` 填充裁剪区域）
- Adaptive icon XML 放在 `mipmap-anydpi-v26/` — **必须**放在这个目录下，API 26+ 设备才会使用
- 旧设备 fallback: 如果没有 `mipmap-anydpi-v26`，系统 fallback 到 `mipmap-hdpi/ic_launcher.png`（旧式 icon，非自适应）
- PNG mode: source 图片如果是 RGBA 半透明，先 `convert('RGB')` 再保存，否则 mipmap PNG 可能有黑色底色

---

### osmdroid MapView 集成

`AndroidView` 嵌入 osmdroid 的传统 View 到 Compose + 自定义标记图标 + API 不可用的 fallback 坐标。

**参考:** `references/osmdroid-map-integration.md`


**参考:** `references/parallel-feature-workflow.md` — 多功能并行开发的节奏和原则

### SSE 事件格式对齐

后端（Python）与 Android SseClient 之间的 SSE 事件格式不一致是常见集成问题。后端通常用旧格式 `{"token": "text"}`，Android 解析器期待 `{"type": "token", "content": "text"}`。

**解决: 后端发双格式（新旧并存），Android 端优先解析新格式，fallback 到旧格式。**

**参考:** `references/backend-sse-format-alignment.md` — 完整格式对照表 + 修复步骤 + 诊断方法

## HomeScreen 多区块 LazyColumn 实现

首页（Home Tab）的完整 scrollable 区块布局模式，含 Hero/Featured Cities/Inspiration Essentials 以及 SectionHeader 复用组件。

**参考:** `references/home-screen-multi-section-lazycolumn.md`

### API Data Model Audit

当 App 编译通过但在真机上空白/无数据时，先审计数据模型与 API 实际返回是否一致。

**五个步骤**: 确认后端活着 → 抓 API 真机响应 → 逐字段对比 @SerialName → 检查 Repository 解析方式 → 检查 ViewModel 状态

**参考**: `references/api-data-model-audit.md` — 5 个典型调试场景 + 速查表

### Nested API Response

后端返回 `{city: {food: [...], hotels: {...}}}` 时，用 `CityDetailResponse { val city: CityDetail }` 两层包装。

**参考:** `references/android-auth-flow.md` — email+password auth gate: Splash→Auth→Main token flow, SharedPreferences, org.json pitfalls

## Building APK — Three Approaches (Ranked)

当用户需要编译 APK 但环境受限时，按以下优先级尝试：

### 1️⃣ Windows 命令行 (gradlew.bat) — 最快本地方案

用户已有 Android Studio 安装（含 JDK 17 + Android SDK）但界面操作有困难时：

```bash
# 在 vp-hermes\android 目录打开 cmd 或 PowerShell
gradlew.bat assembleDebug
```

**⚠️ 常见坑 — Android Studio 代理弹窗阻止 Gradle 同步**

症状：打开项目后弹出 "Proxy Authentication" 弹窗，点 Cancel 后工具栏菜单全部灰色（Build/Sync 不可点）。

原因：系统开了全局代理（如 Xray/Clash 等），Android Studio 检测到代理设置，试图通过代理连接 Google Maven，弹窗要求输入代理凭证。

修复：
```
① Cancel 弹窗
② File → Settings → Appearance & Behavior → System Settings → HTTP Proxy
③ 选 "No proxy" → OK
④ 若找不到菜单路径 → 按两次 Shift 搜索 "proxy" → 点 "HTTP Proxy"
⑤ File → Sync Project with Gradle Files（或右下角 "Sync Now" 蓝色条）
```

**⚠️ 注意**：Gradle 同步完成前，Build 菜单和锤子图标（🔨）都是灰色的，这不是界面问题，是 Gradle 没就绪。同步完成前不要尝试找 Build 按钮。

**⚠️ ZIP 下载丢失 gradle-wrapper.jar**：从 GitHub 网页下载 ZIP 时，`gradle/wrapper/gradle-wrapper.jar` 可能不完整。确认该文件存在：
```
ls vp-hermes\android\gradle\wrapper\
# 应该有: gradle-wrapper.jar, gradle-wrapper.properties
# 如果没有，从 GitHub raw 重新下载
```

### 2️⃣ GitHub Actions CI — 零本地依赖

仓库已配好 workflow，推到 GitHub 自动编译。但需注意：
- Build 日志需要 GitHub repo 的 **Actions 读取权限**（默认公开仓库可读）
- 如果 PAT 权限不足（403 on logs），直接在浏览器打开 GitHub repo → Actions tab 查看日志
- 每次 commit/push 触发，约 2-3 分钟完成

### 3️⃣ VPS 命令行构建 — 最低优先级

VPS 内存通常不足：
- Android 编译需要 4-8GB 空闲内存（dexing 阶段）
- 腾讯云/阿里云 3-4GB 实例在运行其他服务后不足
- 从中国大陆下载 Gradle/Maven 依赖超时

**只有在前两个方案都不可行时才考虑。**

### GitHub Actions CI/CD

```yaml
name: Build APK
on:
  push: { branches: [master, main] }
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { java-version: 17, distribution: temurin }
      - run: chmod +x gradlew
      - uses: actions/cache@v4
        with:
          path: ~/.gradle/caches
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*') }}
      - run: ./gradlew assembleRelease --no-daemon
      - uses: actions/upload-artifact@v4
        with:
          name: APK
          path: app/build/outputs/apk/release/*.apk
```

---

## GitHub 仓库创建 (PAT)

```bash
# PAT 需预先设到环境变量（~/.bashrc）
export GH_TOKEN="ghp_..."

# 创建仓库
curl -X POST -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/user/repos" \
  -d '{"name":"RepoName","private":false}'

# 推送
git remote add origin git@github.com:JTCAO515/RepoName.git
git push -u origin master
```

**Pitfall**: GH_TOKEN 可能在 shell 环境中不存在 → 需手动 `export` 或写入 `~/.bashrc`。GitHub API 有时返回 401 即使 token 有效（环境变量未传递）。

### Artifact 下载超时（腾讯云）

从腾讯云服务器下载 GitHub Actions 构建产物（~2MB APK zip）**持续超时**，curl 到 60-70% 后卡死。这不是大小问题，是腾讯云到 GitHub artifact CDN 的回程限速。

**参考**: `references/gha-artifact-download.md` — 详细现象、三种解决方案

**推荐方案**: 浏览器直接打开 GitHub Actions 页面下载 artifact，不走服务器中转。

### Android GHA 调试节奏（多轮修复模式）

当通过 GitHub Actions 调试 Kotlin 编译错误时，每次迭代需要：

```bash
1. 看 GHA 日志        → curl API / grep 关键错误行
2. 本地修复           → patch / write_file
3. git commit + push  → 触发新构建
4. 等待 1-2 分钟      → （Gradle 下载 + 编译）
5. 回到步骤 1
```

**每次迭代约 2-3 分钟**。5 轮修复大约需要 10-15 分钟。

**效率技巧**:
- 只修复第一个根因错误（后续错误通常是连带的）
- 使用 `for i in $(seq 1 20); do sleep 15; ... done` 轮询等待
- 用 `grep -E "error|FAILURE|Unresolved"` 快速定位新错误

---

## UI Polish — Shadows, Glassmorphism, Entry Animations, Shimmer

> 用户的 App 从\"功能完整\"到\"视觉精美\"需要这层打磨。以下模式经 vp-hermes 项目验证有效。

### Warm Colored Shadows (暖调阴影)

Material 3 默认阴影是中性灰色 (`Color(0x1A2D2D2D)`)，用金色/棕色替代以对齐品牌色板：

```kotlin
// ✅ 暖调阴影 — 对齐浅色东方的金色色板
private val ShadowWarmLight = Color(0x0DC9A96E)   // 极浅金
private val ShadowWarmMedium = Color(0x1AC9A96E)  // 中浅金
private val ShadowWarmDeep = Color(0x30C9A96E)    // 深金

// 在 Card shadow() 中应用
.shadow(
    elevation = animElevation,
    shape = shape,
    ambientColor = ShadowWarmLight,
    spotColor = ShadowWarmMedium
)
```

**效果：** 中性灰阴影→冷感/通用；金棕色阴影→暖感/品牌统一。对于有明确品牌色板（金/褐/暖白）的 App，暖调阴影是低成本高感知的改良。

### Glassmorphism Card (磨砂玻璃卡片)

实现伪磨砂玻璃效果需要两层叠加：

```kotlin
// Glass colors in Color.kt
val GlassWhite = Color(0xCCFFFFFF)        // frosted glass white
val GlassWarm = Color(0xDDF5F0E8)         // frosted glass warm
val GlassGold = Color(0x22C9A96E)         // subtle gold glass overlay

// 使用方式 — 两层布局叠加
Card(
    onClick = onClick,
    colors = CardDefaults.cardColors(containerColor = Color.Transparent)
) {
    Box(modifier = Modifier.fillMaxSize().background(GlassGold))   // 底层：金色辉光
    Box(modifier = Modifier.fillMaxSize().background(GlassWarm))  // 顶层：暖白半透
    content()                                                       // 实际内容
}
```

**⚠️ Pitfall:** `Card {}` 的 content lambda 是 `ColumnScope`，没有 `matchParentSize()`。内部 Box 必须用 `Modifier.fillMaxSize()` 而非 `matchParentSize()`。
**⚠️ Pitfall:** 在 `Box {}`（非 Card）内部，可用 `Modifier.matchParentSize()`，这是 `BoxScope` 的成员。

### Entry Animation Wrapper (入场动画)

所有列表/网格项应用 stagger 动画，使页面加载时元素逐项淡入滑入：

```kotlin
@Composable
fun VpEnterAnimation(
    visible: Boolean = true,
    index: Int = 0,
    staggerDelay: Int = 60,
    content: @Composable () -> Unit
) {
    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(animationSpec = tween(400, delayMillis = index * staggerDelay)) +
                slideInVertically(
                    animationSpec = tween(400, delayMillis = index * staggerDelay),
                    initialOffsetY = { it / 3 }
                )
    ) { content() }
}
```

**推荐参数：** LazyRow/LazyGrid: `staggerDelay = 50-60`；垂直列表: `60-80`；短列表（<5项）: `80-100`。

### Press Animation Pattern (按压动效)

所有交互式卡片应有统一的按压反馈 — 缩放 + 阴影联动：

```kotlin
val interactionSource = remember { MutableInteractionSource() }
val isPressed by interactionSource.collectIsPressedAsState()

val animScale by animateFloatAsState(
    targetValue = if (isPressed) 0.97f else 1f, animationSpec = tween(200), label = "scale"
)
val animElevation by animateDpAsState(
    targetValue = if (isPressed) 2.dp else elevation, animationSpec = tween(200), label = "elevation"
)

Card(
    onClick = onClick,
    modifier = modifier.scale(animScale).shadow(elevation = animElevation, shape = shape, ...),
    elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),  // 必须 0dp
    interactionSource = interactionSource
) { content() }
```

**关键细节：** Card 的 `elevation` 必须设为 `0.dp`，因为阴影完全交给外层 `Modifier.shadow()` 控制，避免冲突。

### Shimmer Loading (骨架屏)

每个页面（Home/Explore/Trips）都应有独立的 shimmer loading composable。

**每个页面至少需要：** 1) Hero/header shimmer  2) 内容区域 shimmer（匹配实际布局结构）  3) 加载完成后过渡到内容（`LaunchedEffect + delay(400-800ms)` 避免闪烁）。

### 入口动画 + Shimmer 完整生命周期

```
[延迟 400-800ms]                   [加载完成]
    ↓                                   ↓
Shimmer skeleton  →  VpEnterAnimation(stagger) → 内容渲染
    ↑                                   ↑
 isLoading=true                     isLoading=false
```

**细节：** 切换 Tab（如 Trips 的 Recent/Saved）时重置 `isLoading = true`，给用户每次切换的"新鲜感"。

---

## 开发顺序 (设计先行推荐)

```
Phase 0 — Product Planning (PRD_PRODUCT_ANALYSIS.md + PLAN.md)
Phase 1 — 🎨 Sketch Mockup (sketch skill, 2-3 HTML variants, browser_vision comparison)
Phase 2 — 🎨 Figma Design System (figma-generate-library + figma-generate-design)
  ├─ Color/Typography/Spacing/Shape tokens
  ├─ Core Components (Button/Chip/Card/BottomNav)
  └─ 5 key screens (Home/Explore/Chat/CityDetail/Trips)
Phase 3 — Project Skeleton + Design System Module
  ├─ Gradle config + module structure
  ├─ core/designsystem (Color/Type/Theme/Spacing/Shape + Components)
  └─ core/network + core/common
Phase 4 — Navigation Shell + Bottom Bar
Phase 5 — Home + Explore
Phase 6 — City Detail
Phase 7 — Chat Screen (SSE streaming)
Phase 8 — Trips + Tools
Phase 9 — Backend Fix + Model Switch
Phase 10 — Final Build + Validation APK
```

**关键原则:** 用户非技术背景，用 sketch/figma 先出视觉方向，确认后再开始编码。避免"代码写一半发现方向不对"的返工成本。

---

## 陷阱

### ❌ `MediaType.parse()` → `toMediaTypeOrNull()`（OkHttp 4.x 断变更）

**症状：**
```
e: SseClient.kt:19:64 Using 'parse(String): MediaType?' is an error. moved to extension function
```

**根因：** OkHttp 4.x 中将 `MediaType.parse()` 移到了扩展函数。旧式调用 `okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json"), body)` 编译报错。

**修复：**
```kotlin
// 1. 添加 import
import okhttp3.MediaType.Companion.toMediaTypeOrNull

// 2. 替换调用
// ❌ 旧式
.post(okhttp3.RequestBody.create(okhttp3.MediaType.parse("application/json"), body))
// ✅ 新式
.post(okhttp3.RequestBody.create("application/json".toMediaTypeOrNull(), body))
```

**预防：** vp-hermes 项目用的 OkHttp 4.12.0 已废弃此 API。新建项目时直接用扩展函数写法。

### ❌ Gradle 发行版从中国大陆下载超时

Gradle wrapper 连接 `services.gradle.org` 从腾讯云/阿里云服务器会读超时。需要：
- 改 `distributionUrl` 为国内镜像（见上方"从中国大陆构建"章节）
- 或手动下载 zip 放入 Gradle wrapper cache（含 hash 计算）
- 或先试一次 curl 看是否通，不通立刻切镜像

### Pill 形状按钮用 `RoundedCornerShape(percent = 50)`

```kotlin
// ✅ Correct — 无论按钮高度怎么变，始终是圆形
shape = RoundedCornerShape(percent = 50),

// ❌ Avoid — 硬编码大 dp 值，如果按钮高度变化会变成胶囊而非满圆
shape = RoundedCornerShape(9999.dp),
```

`percent = 50` 自动适应按钮/容器的实际尺寸，不需要预先知道高度。Android Compose 1.5+ 支持。

Kotlin DSL (`settings.gradle.kts`) 必须用 `dependencyResolutionManagement`，不是 `dependencyResolution`（Groovy DSL 旧写法）。写错编译报错。

### ❌ dependencyResolutionManagement repositories 放错位置

`repositories` 块必须放在 `dependencyResolutionManagement {}` 内部，而不是外部顶层。正确：
```kotlin
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
```

### ❌ signingConfigs.create() 位置错误
必须在 `android { signingConfigs { create("release"){...} } }` 块中，不能放在 `buildTypes.release{}` 闭包内。

### ❌ GH_TOKEN 环境变量缺失
GitHub API 调用报 401 → 可能是 shell 未加载 `~/.bashrc`，手动 `export GH_TOKEN="..."`。

### ❌ Gradle Wrapper 无执行权限
`gradlew` 文件必须 `chmod +x`（GitHub Actions 需要 `run: chmod +x gradlew`）。

### ❌ 字体文件放错模块（多模块项目常见）

**症状:** 字体 `.ttf` 文件放在 `app/src/main/res/font/`，但 `Type.kt` 在 `core:designsystem` 模块中引用 `R.font.dm_sans_regular`。编译报 `Unresolved reference: R.font.dm_sans_regular` 或字体不生效。

**根因:** 每个 Android 模块有独立的 `R` 类。`core:designsystem` 的 `R.font.xxx` 解析的是 `core/designsystem/src/main/res/font/` 目录下的资源，不是 app 模块的。

**修复:** 字体文件放在**引用它们的模块**的资源目录下：
```bash
# ✅ 正确 — Type.kt 在 designsystem 模块，字体也放 designsystem
cp /path/to/fonts/*.ttf core/designsystem/src/main/res/font/

# ❌ 错误 — 放 app 模块对 designsystem 不可见
cp /path/to/fonts/*.ttf app/src/main/res/font/
```

**预防:** 创建 `Type.kt` 时，先确认字体文件的 `res/font/` 目录在哪个模块，保持一致。多模块项目中，`R.font.xxx` 引用必须和字体文件在同一个 module。

### ❌ matchParentSize() 在 Card {} 中报 Unresolved reference

**症状:** `Card { Box(modifier = Modifier.matchParentSize().background(...)) }` 编译报 `Unresolved reference: matchParentSize`。

**根因:** `Card {}` 的 content lambda 是 `ColumnScope`，没有 `matchParentSize()` 方法。`matchParentSize()` 只在 `BoxScope` 和 `RowScope` 中可用。

**修复:** 
```kotlin
// ❌ Card 内容 lambda 是 ColumnScope
Card { 
    Box(modifier = Modifier.matchParentSize().background(Gold))  // 编译错
}

// ✅ 用 fillMaxSize 替代
Card {
    Box(modifier = Modifier.fillMaxSize().background(Gold))  // 正确
}

// ✅ Box 内可以安全用 matchParentSize
Box {
    Box(modifier = Modifier.matchParentSize().background(Gold))  // 正确
}
```

### ❌ Modifier.let {} 不能用在 .then() 链中

**症状:** `Modifier.then(if (cond) Modifier.let { ... } else Modifier.background(...))` 报 `Type mismatch: inferred type is Any but Modifier was expected`。

**根因:** `Modifier.let {}` 返回 lambda 的最后一行表达式，它的类型是 `Unit`（如果最后一行是表达式语句）。`then()` 要求返回值是 `Modifier`。

**修复:** 不要用 `let` 做条件分支。改用 `if-else` 表达式或单独处理：
```kotlin
// ❌ 错误
.then(if (onClick != null) Modifier.let { /* handled elsewhere */ }
      else Modifier.background(Gold))

// ✅ 正确 — 完全分开的两个分支
if (onClick != null) {
    Card(onClick = onClick, ...) { content() }
} else {
    Box(modifier = modifier.background(Gold)) { content() }
}
```

### ❌ `./gradlew clean assembleDebug` shell 解析错误

**症状:** 运行 `./gradlew clean assembleDebug` 后只执行了 `clean`，输出 `assembleDebug: not found`。

**根因:** shell 将 `clean` 和 `assembleDebug` 解析为两个独立的命令（某些 shell 环境下 `&&` 被吞掉或分号风格导致）。

**修复:** 务必分两步执行：
```bash
./gradlew clean    # 先 clean
./gradlew assembleDebug  # 再单独构建
# 或
./gradlew clean && ./gradlew assembleDebug
```

**预防:** 避免 `./gradlew <task1> <task2>` 格式，用 `&&` 或分步执行。Gradle 的 multi-task 语法在特定 shell 环境（如 tool sandbox 中）不可靠。

### ❌ Design Token 改名/删除导致所有组件文件编译失败

**症状:** 在 `Color.kt` 中改名或删除某个颜色 token（如 `SurfaceDefault` → `Surface`），编译报 `Unresolved reference: SurfaceDefault` 遍布所有组件文件（VpBottomNav.kt, VpCard.kt, VpChip.kt, VpShimmer.kt 等）。

**根因:** 组件文件直接 `import com.visepanda.designsystem.SurfaceDefault` 并在内部引用。Color.kt 中的 token 名被删除后，所有 import 和 usage 全部断裂。

**修复步骤:**
```bash
# 1. 找出所有引用旧 token 的文件
grep -r "SurfaceDefault" core/designsystem/src/main/java/com/visepanda/designsystem/components/
# → 列出所有受影响的文件

# 2. 批量替换（每个文件独立操作）
sed -i 's/SurfaceDefault/Surface/g' core/designsystem/src/main/java/com/visepanda/designsystem/components/VpBottomNav.kt
# （对所有受害文件重复）

# 3. 验证：搜索是否还有残留
grep -r "SurfaceDefault" core/designsystem/ --include="*.kt"
```

**预防:**
- 设计系统 token 名在首次定稿后尽量不改名，只改值（hex color）不改标识符
- 若必须改名，先 `grep -r "旧名" --include="*.kt"` 确认影响范围再做
- 把 token 名视为公共 API，改名相当于 breaking change
- 更稳的方案：`Color.kt` 中保留旧名作为 `typealias`，标记 `@Deprecated`：
  ```kotlin
  @Deprecated("Use Surface instead", ReplaceWith("Surface"))
  val SurfaceDefault = Surface
  ```

### ❌ MaterialTheme.colorScheme 在非 @Composable 上下文中
`MaterialTheme.colorScheme.primary` / `.onSurface` 等是 `@Composable` 访问器，只能在 `@Composable` 函数中调用。
`buildAnnotatedString { }` 的 lambda **不是** `@Composable` 上下文。
如果在 `withStyle(SpanStyle(color = MaterialTheme.colorScheme.primary))` 中调用 → 报 `@Composable invocations can only happen from the context of a @Composable function`。

**修复**: 在 `@Composable` 函数中提取颜色为 `val`，作为参数传给非 Composable 助手函数：
```kotlin
@Composable
fun MarkdownText(text: String) {
    val primaryColor = MaterialTheme.colorScheme.primary     // ← 在 @Composable 中提取
    val annotatedString = buildAnnotatedString {
        appendInlineStyled(line, primaryColor)               // ← 作为参数传递
    }
}

private fun AnnotatedString.Builder.appendInlineStyled(
    text: String, primaryColor: Color                         // ← 参数化，不直接访问 MaterialTheme
) {
    withStyle(SpanStyle(color = primaryColor)) {              // ← 安全
        append(text)
    }
}
```

### ❌ 同名 data class 冲突（MapData 等）
当两个 Model 文件定义相同名字的 data class（如 `City.kt` 和 `Trip.kt` 都定义 `MapData`，但字段不同），Kotlin 编译报 `Redeclaration: MapData`。

**最佳实践**: 用不同文件名/类名避免冲突：
- `City.kt` 中的 MapData（lat/lng/zoom/pois）→ 保留原名或重命名为 `CityMapData`
- `Trip.kt` 中的 MapData（cities: List<MapMarker>）→ 移到独立文件 `ApiModels.kt`，重命名 `MapApiResponse`
- 文件级命名空间（同一 package）下所有顶层声明必须全局唯一

### ❌ Python write_file 写入 Kotlin 源码中的 `\\n` 转义

**症状:** 使用 Python 的 `write_file()` 写入 Kotlin 源码时，字符串中的 `\\n`（如 `\"Welcome\\nYour AI Travel Companion\"`）会被 Python 解释器**转换为实际换行符**，导致 Kotlin 编译报错：

## 使用已签名 APK 的本地构建 vs GitHub Actions

对于本地开发/调试场景，用 `assembleDebug`（Android SDK 自动签 debug 证书）即可，不需要配置 signingConfigs。Release APK 才需要签名配置。

**GitHub Actions workflow 避免 release 签名问题：** 只构建 `assembleDebug`，不构建 `assembleRelease`（除非在 repo secrets 中配置了签名密钥环境变量）。

### ❌ GitHub Actions env vars for signing 缺失

```yaml
# 如果用 assembleRelease + signingConfigs.env.get()
# 必须在 GitHub 仓库 Settings → Secrets and variables → Actions 中设置
# SIGNING_STORE_PASSWORD / SIGNING_KEY_ALIAS / SIGNING_KEY_PASSWORD
#
# 如果没有设置 secrets，则在 build.gradle.kts 中使用 fallback 值
# storePassword = System.getenv("SIGNING_STORE_PASSWORD") ?: "dev_password"
```

**如果没有 secrets + 没有 fallback → 构建失败。** 开发阶段去掉 release build 或只 build debug。

### ❌ Python write_file 写入 Kotlin 源码中的 `\\n` 转义

**症状:** 使用 Python 的 `write_file()` 写入 Kotlin 源码时，字符串中的 `\n`（如 `"Welcome\nYour AI Travel Companion"`）会被 Python 解释器**转换为实际换行符**，导致 Kotlin 编译报错：

```
e: file:///.../HomeScreen.kt:23:28 Expecting '"'
e: file:///.../HomeScreen.kt:24:33 Expecting '"'
e: file:///.../HomeScreen.kt:25:19 Expecting an element
```

**根因:** Python 的三引号字符串中，`\n` 被解释为字面换行符，写入文件时变成了真正的两行而非 Kotlin 的 `\n` 转义序列。

**修复:**
```python
# ❌ 错误写法 — \n 会被 Python 解释为换行符
write_file("HomeScreen.kt", """
Text(text = "Welcome\nYour AI Travel Companion")
""")

# ✅ 正确写法 — 用 \u000A unicode 转义
write_file("HomeScreen.kt", """
Text(text = "Welcome\u000AYour AI Travel Companion")
""")
```

**预防:**
- Kotlin 字符串中的 `\n` 在 Python 代码里用 `\u000A` 替代
- 或 Kotlin 中使用三引号原始字符串 `"""Welcome\nYour AI Travel Companion"""`（如果 Kotlin 版本支持）
- 或先写一个临时变量 `val nl = "\n"` 然后用字符串模板 `"Welcome${nl}Your..."`（最安全但啰嗦）

### ❌ 组件硬编码暗色/亮色渐变，主题切换后视觉断裂

**症状:** 设计方向从暗色主题切换到浅色主题时，组件（如 VpCityCard）的硬编码渐变颜色（`Color(0xFF2A2A2A)` 暗色→暗色 / `Color(0xCC0A0A0A)` overlay）在新主题下视觉不协调，出现深色渐变覆盖在浅色底上的情况。

**根因:** 组件在设计系统初期为暗色主题硬编码了颜色值，之后主题色板变更但组件的局部渐变/overlay 未同步更新。

**修复步骤:**
1. `grep -r "Color(0xFF" core/designsystem/src/main/java/ --include="*.kt" | grep -v "Color.kt\|Theme.kt\|Spacing\|Shape"` — 找出组件中所有硬编码颜色
2. 逐组件分析哪些颜色应该引用 token（`Surface` / `Gold` / `JadeGrey` 等），哪些可以保留硬编码（如语音气泡、阴影色）
3. 对于暗→亮切换，城市卡片的背景渐变改为暖金渐变：
   ```kotlin
   // Old (dark theme):
   .background(Brush.verticalGradient(listOf(Color(0xFF2A2A2A), Color(0xFF1A1A1A))))
   // overlay: Color(0xCC0A0A0A)

   // New (light theme 浅色东方):
   .background(Brush.verticalGradient(listOf(Color(0xFFDCC798), Color(0xFFC9A96E))))
   // overlay: Color(0xCCC9A96E)
   ```
4. Card 文字颜色同步调整为对比色（深色底→白色字，金色底→白色字）

**预防:**
- 所有组件只引用 Color.kt 中的 token 名，不直接写 `Color(0xFF...)` 字面量
- 如果渐变必须硬编码，在 Color.kt 顶部添加注释 `// Component gradients — update when theme changes`
- 设计 token 只改值不改名的原则同样适用于组件内部使用的渐变
- 设计方向确认后（暗色/浅色），统一检查全部组件的 background/gradient/color 引用

### ❌ read_file() 工具输出含行号前缀（Hermes 工具注意事项）
`hermes_tools.read_file()` 返回的 `content` 字段包含 `     1|     1|` 行号前缀。
如果直接将 `content` 写回文件（`write_file(path, content)`），文件会被行号前缀损坏，Kotlin 编译报 `Expecting a top level declaration`（每行都是）。

**修复**: 任何时候要修改从 `read_file()` 读取的文件，必须：
1. 优先用 `patch` 工具（`mode=replace` + `old_string/new_string`）而不是 `read_file → write_file` 流程
2. 如果必须用 `read_file → write_file`，先用 `git show hash:path` 获取干净版本，再追加修改
写回后立即 `git diff` 验证文件格式正常。

### ❌ 域名重定向导致 API 全挂（HTTP 307）

当 App 在真机上 "failed to load X" 但编译通过时：

1. **用 curl 测试后端 API** — 看 HTTP 返回码
   ```bash
   curl --noproxy '*' -s -o /dev/null -w "HTTP %{http_code}\n" https://go2china.space/api/cities
   curl --noproxy '*' -s -L https://go2china.space/api/cities | head -3  # 跟重定向
   ```
2. **检查是否 307 重定向** — Vercel 或 Cloudflare 经常把裸域名重定向到 `www.` 子域名
3. **修复**: `ApiConfig.BASE_URL` 改为带 `www.` 的版本
4. **检查 OkHttp 的 followRedirects** — OkHttpClient 默认 `followRedirects(true)` 和 `followSslRedirects(true)`。如果用 `URL.readText()`（非 OkHttp），默认**不**跟重定向

### ❌ 用户说"从0开始重写"时的诊断顺序

用户（非技术背景）说"从0开始重新写"通常是**挫折信号**而非技术要求。正确顺序：

1. **先查后端** — API 返回 200？数据格式对？
2. **查域名/DNS** — 是否有 307 重定向？
3. **查网络层** — SSL 证书？安全组？代理？
4. **查数据模型** — @SerialName 与 API 字段一致？
5. **查 App 代码** — 最后才是改代码

**经验**: 大部分 Android 数据空白问题在**网络层**（域名/DNS/重定向/SSL），不在 App 代码。不要用户一说重写就开始改 Kotlin。
