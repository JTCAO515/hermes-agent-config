# Android Compose 编译错误目录

从 VisePanda-Android v0.1.0 构建修复中整理的常见编译错误及修复。

---

## 1. `Redeclaration: MapData`

**症状**: `e: City.kt:96:12 Redeclaration: MapData` 和 `e: Trip.kt:35:12 Redeclaration: MapData`

**原因**: 同一 package（`space.jtcao.visepanda.data.model`）下两个文件都定义了 `data class MapData`，但字段不同（City.kt 的 MapData 是 lat/lng/zoom/pois；Trip.kt 的 MapData 是 cities: List<MapMarker>）。

**修复**: 将 Trip.kt 中的共享模型（`MapMarker`, `MapApiResponse`, `AppConfig`, `MapCenter`）移到独立文件 `ApiModels.kt`，Trip.kt 只保留 `Trip` data class。

---

## 2. `Unresolved reference: PullToRefreshBox`

**症状**: 多个文件报 `Unresolved reference: PullToRefreshBox`，即使 import 写了。

**原因**: `PullToRefreshBox` 需要 Compose Material 3 **1.3.0+**，Compose BOM 2024.02.00 捆绑的是 Material 3 ~1.2.x，该 API 不存在。

**修复**: 
- 方案 A：升级 BOM 到 `2024.09.00+`
- 方案 B（推荐 MVP）：替换为 `Box` + `IconButton(Icons.Default.Refresh)` 手动触发刷新

`@OptIn(ExperimentalMaterial3Api::class)` 注解也必须同步移除或添加。

**搜索模式**:
```kotlin
// 查找所有 PullToRefreshBox 使用
// 替换为 Box(modifier = Modifier.fillMaxSize())
// 移除 isRefreshing / onRefresh 参数
// 移除或添加 @OptIn
// 移除 import PullToRefreshBox
```

---

## 3. `@Composable invocations can only happen from the context of a @Composable function`

**症状**: `e: MarkdownText.kt:131:48 @Composable invocations can only happen from the context of a @Composable function`

**原因**: `withStyle(SpanStyle(color = MaterialTheme.colorScheme.primary))` 中的 `MaterialTheme.colorScheme` 是 `@Composable` 访问器，但被调用位置在 `private fun AnnotatedString.Builder.appendInlineStyled()` 中——这是一个**非** `@Composable` 函数。

`buildAnnotatedString { }` 的 lambda **不是** @Composable 上下文。

**修复**: 在 `@Composable` 函数中提取所有颜色为 `val` 参数，传给非 Composable 助手函数：
```kotlin
@Composable
fun MarkdownText(text: String) {
    val primaryColor = MaterialTheme.colorScheme.primary
    val primaryAlpha = primaryColor.copy(alpha = 0.1f)
    val annotatedString = buildAnnotatedString {
        parseInlineMarkdown(line, primaryColor, primaryAlpha) // 传参而非内部访问 MaterialTheme
    }
}

private fun AnnotatedString.Builder.parseInlineMarkdown(
    text: String, primaryColor: Color, primaryAlpha: Color  // 参数化
)
```

---

## 4. `Expecting a top level declaration` + `imports are only allowed in the beginning of file`

**症状**: 整个文件的每一行（包括 `package` 声明）都报这个错，几十行相同错误。

**原因**: 文件被 `read_file()` 工具输出的行号前缀 `     1|     1|` 污染。文件开头变成了 `     1|     1|package space.jtcao...`，Kotlin 编译器无法解析。

**修复**: 
```bash
# 从 git 恢复干净版本，重新应用修改
git show <good-commit>:app/src/main/java/.../File.kt > /tmp/File_fixed.kt
# 然后追加需要的修改
sed -i '/^import .../a import ...' /tmp/File_fixed.kt
cp /tmp/File_fixed.kt app/src/main/java/.../File.kt
```

**预防**: 永远不要直接 `write_file(path, read_file(path)['content'])`，因为 content 包含行号前缀。改用 `patch` 工具或从 git 恢复。

---

## 5. `Conflicting import, imported name 'MapMarker' is ambiguous`

**症状**: `e: MapScreen.kt:31:41 Conflicting import, imported name 'MapMarker' is ambiguous`

**原因**: 同一文件中有两行相同的 `import space.jtcao.visepanda.data.model.MapMarker`（一行是 sed 添加的重复）。

**修复**: 
```bash
# 检查重复
grep -n "import.*MapMarker" File.kt
# 移除多余行
```

---

## 6. `Overload resolution ambiguity: append()`

**症状**: `e: MarkdownText.kt:42:25 Overload resolution ambiguity: append(text: AnnotatedString) / append(text: String) / ...`

**原因**: `append(parseInlineMarkdown(content))` 中 `parseInlineMarkdown` 返回 `AnnotatedString.Builder`，然后传给 `append()` 时 Kotlin 不知道该调用哪个重载。

**修复**: 改变设计——不在 `append()` 内再调用另一个 builder，而是让解析函数直接在 `this`（AnnotatedString.Builder）上修改：
```kotlin
// 错误:
private fun parseInlineMarkdown(text: String): AnnotatedString.Builder { ... }
append(parseInlineMarkdown(content))

// 正确:
private fun AnnotatedString.Builder.appendInlineStyled(text: String) { ... }
appendInlineStyled(content)  // 直接在 this 上修改，不返回 new builder
```

---

## 7. `Type mismatch: inferred type is NavController but NavHostController was expected`

**症状**: `e: NavGraph.kt:30:25 Type mismatch: inferred type is NavController but NavHostController was expected`

**原因**: `NavHost(navController = navController, ...)` 的 `navController` 参数类型是 `NavHostController`（`NavController` 的子类），但参数声明是 `NavController`。

**修复**: 将参数类型从 `NavController` 改为 `NavHostController`：
```kotlin
// Before
fun NavGraph(navController: NavController, ...)

// After
fun NavGraph(navController: NavHostController, ...)
```
`rememberNavController()` 返回 `NavHostController`，所以调用的地方不需要改。

---

## 8. `Property delegate must have a 'getValue' method` with `mutableStateOf`

**症状**: `e: MapScreen.kt:45:25 Property delegate must have a 'getValue(Nothing?, KProperty<*>)' method`

**原因**: `var selectedCity by remember { mutableStateOf<MapMarker?>(null) }` 中 `MapMarker` 类型无法解析（import 缺失），导致类型推断为 `Nothing?`，`by` 委托找不到合适的 `getValue`。

**修复**: 添加缺失的 `import space.jtcao.visepanda.data.model.MapMarker`。一旦类型可解析，`getValue`/`setValue` 自动生效。

---

## 9. `Cannot infer a type for this parameter` + `Unresolved reference: it`

**连带错误**: 如果某个类型（如 `MapMarker`）未解析，所有使用它的地方都会连带报错——lambda 参数类型无法推断、`it` 无法解析、`let` 内的 `@Composable` 调用被拒绝。

**根因识别**: 先找到第一个 `Unresolved reference` 错误，修复它之后其他 `Cannot infer` / `Unresolved reference: it` 错误通常会消失。不要逐个修复所有 `it` 错误。

**真实场景**: 在一个 session 中同时创建 `ChatMessage.kt` + `ChatViewModel.kt` + `ChatScreen.kt`，如果 `ChatMessage.kt` 因为 Python 语法错误没能成功创建（write_file 在错误之前已执行但不一定写入完整），会导致：
- `ChatState`、`ChatMessage.MessageType` 无法解析
- `vm.state.collectAsState()` 类型塌陷为 `State<Nothing>`（因为返回值类型不可知）
- `items(items = chatState.messages.reversed(), key = { it.id })` 中的 `it` 类型推断为 `Nothing`
- `Property delegate must have a 'getValue(Nothing?, KProperty<*>)' method` — 因为 `State<Nothing>` 找不到适用的 getValue 扩展函数

**诊断流程**: 先 `ls -la` 检查所有依赖的 data class 和 model 文件是否确实存在于磁盘上，再逐一排查编译错误。一条 'unresolved reference' 可能是多条错误的根因。

---

## 速查表

| 错误模式 | 根因 | 修复 |
|----------|------|------|
| Redeclaration | 同名 data class | 移至独立文件或重命名 |
| Unresolved reference: PullToRefreshBox | BOM < 2024.09 | 替换为 Box + refresh button |
| @Composable invocations | MaterialTheme 在非 Composable 中 | 提取颜色为参数 |
| Expecting a top level declaration | 文件被行号前缀污染 | git restore |
| Conflicting import | 重复 import 行 | 删除重复 |
| Overload ambiguity: append | 返回 builder 再传回 append | 改写为直接操作 this |
| Type mismatch: NavController | 参数类型太宽 | 改为 NavHostController |
| Property delegate / getValue | 类型未解析 | 修 import 即可 |
| Cannot infer type parameter | 连带错误 | 修第一个根因 |
| Illegal escape: `\s` / `\d` | Kotlin 字符串不认识 `\s`/`\d` | 用 `\\s`/`\\d`（双反斜杠） |
| Unresolved reference: toRequestBody | okhttp3 扩展函数需显式 import | `import okhttp3.RequestBody.Companion.toRequestBody` |
| Unresolved reference: .toMediaType() | MediaType.parse() 已废弃 | `import okhttp3.MediaType.Companion.toMediaType` + `"application/json".toMediaType()` |
| Unresolved reference: Call/Callback/Response | okhttp3.* 通配符不够 | 显式 `import okhttp3.Call` `import okhttp3.Callback` `import okhttp3.Response` |
| Cannot find parameter: name (or similar) | 传了命名参数但函数需要对象 | 检查函数签名——可能是 `saveTrip(trip: Trip)` 而非 `saveTrip(name=...)` |
| A type annotation is required | `@Composable private fun` 参数缺类型 | 必须写 `parm: Type`，不能省略类型或用 default value 代替 |
| Unresolved reference in private fun | 独立 `private fun` 不在外层函数作用域内 | `private fun` 在 Kotlin 文件中是顶层函数，不继承外层函数参数，需显式传递 |
| API returns HTTP 307 but app treats as error | 域名添加 `www.` 子域名，裸域名 307 跳转 | App 的 `ApiConfig.BASE_URL` 改为 `https://www.go2china.space`（带 www）|
| All API endpoints fail with 307 | Vercel 重定向配置或 Cloudflare SSL 强制跳转 | 先用 curl -L 跟踪重定向确认目标 URL；检查 OkHttpClient 是否 `followRedirects(true)` |
| TripsScreen EmptyTrips默认值报错 | `private fun EmptyTrips(onStartChat = onStartChat)` 缺类型注解 | 改为 `private fun EmptyTrips(onStartChat: () -> Unit)` — 有类型即可，不需要默认值 |
