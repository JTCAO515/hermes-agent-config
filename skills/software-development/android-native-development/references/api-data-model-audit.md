# API 数据模型审计：App 编译通过但无数据显示

> 应用编译通过、安装运行，但页面空白/无数据/卡在 Loading。
> 根因通常是 Kotlin 数据模型与后端 API 实际返回的 JSON 不一致。

---

## 审计流程

### Step 1 — 确认后端活着

```bash
curl -sL -w "HTTP %{http_code}" API_ENDPOINT | head -c 500
```

检查：
- HTTP 状态码 200？（307 需要 `-L` 跟随跳转）
- 返回的是 JSON 不是 HTML？
- 如果 5xx → 后端挂了，不是 App 问题

### Step 2 — 抓取 API 真实响应，对比 Kotlin 模型

对每个 API 端点，抓取完整 JSON 并对比 `@Serializable` 数据类：

| 检查项 | 工具 |
|--------|------|
| API 返回格式 | `curl -sL API_URL \| python3 -c "import json;d=json.load(sys.stdin);print(list(d.keys()))"` |
| Kotlin 模型字段 | 读 `@SerialName` 注解 |

**常见不匹配模式：**

- **List vs Dict** — API 返回 `{"cities": {"beijing": {...}}}` 但 Kotlin 期待 `List<City>`
- **字段名不同** — API 的 `name_en` 但模型写的 `@SerialName("name")`
- **嵌套层级不同** — API 返回 `{"city": {...}}` 但模型直接是 `CityDetail`
- **文件为空** — Kotlin data class 文件存在但只有 package 声明，再无其他内容（如 ToolItem.kt）

### Step 3 — 检查 @SerialName 注解是否匹配

```kotlin
// 注意 API 字段名和 @SerialName 必须完全一致
@Serializable
data class CityDetail(
    @SerialName("name_en") val nameEn: String = "",    // API 字段是 "name_en"
    @SerialName("name_cn") val nameCn: String = "",    // API 字段是 "name_cn"
)
```

### Step 4 — 检查 Repository 层的数据解析方式

App 使用两种 API 调用方式：

**方式 A: kotlinx.serialization 自动反序列化**
```kotlin
val response = URL("$BASE_URL/api/xxx").readText()
val data = json.decodeFromString<MyModel>(response)
```
→ 如果 JSON 顶层 key 与模型不匹配抛出 `JsonDecodingException`
→ `ignoreUnknownKeys = true` 容忍多余字段，但**缺失必需字段**仍然报错

**方式 B: 手动 kotlinx.serialization.json 逐字段解析**
```kotlin
val root = json.parseToJsonElement(response).jsonObject
val citiesObj = root["cities"]?.jsonObject
// 然后手动构建 City 对象
```
→ JSON 字段类型错误不会自动暴露（如 array 用 `jsonPrimitive?.content` 读取会拿 null）
→ 检查每个字段的读取方式是否匹配 JSON 的实际类型

### Step 5 — 检查 ViewModel 状态管理

常见无声失败：
- `MutableStateFlow` 初始化为 `Loading`，API 失败后没有 emit `Error`
- `catch {}` 空吞异常
- collect 后的 UI 状态更新遗漏了某些分支

---

## 典型调试场景

### 场景 1：ToolItem.kt 为空文件

**症状**: Tools 页面显示 Loading 或空白。
**根因**: `data/model/ToolItem.kt` 只有 `package` 声明，`ToolsRepository` 调用 `json.decodeFromString<List<ToolItem>>()` 时找不到 `@Serializable` 类 → 崩溃。
**修复**: 创建 ToolItem 数据类：
```kotlin
@Serializable
data class ToolItem(
    @SerialName("name") val name: String,
    @SerialName("description") val description: String,
    @SerialName("icon") val icon: String = ""
)
```

### 场景 2：API 返回 dict 但代码期待 array

**症状**: `/api/tools` 返回 `{"tools": {"packing":"...", "pricing":"..."}}`，Repository 写的是 `decodeFromString<List<ToolItem>>()`。
**根因**: JSON 顶层不是数组，无法反序列化为 `List<T>`。
**修复**: 用手动解析：
```kotlin
val root = json.parseToJsonElement(response).jsonObject
val toolsObj = root["tools"]?.jsonObject ?: return emptyList()
toolsObj.entries.map { (name, element) ->
    ToolEntry(name = name, description = element.jsonPrimitive.content)
}
```

### 场景 3：/api/map 返回 dict of dicts 但代码期待 array

**症状**: 地图空白无标记。`root["cities"]?.jsonArray` 返回 null。
**根因**: API 返回 JSON 对象（键值对），不是 JSON 数组。
**修复**: 改用 `?.jsonObject?.entries.map { ... }`。

### 场景 4：后端 import 缺失导致 API 返回错误

**症状**: 聊天功能无法使用，API 返回 `{"error": "name 're' is not defined"}`。
**根因**: Python 后端在函数内使用了 `re` 模块，但 `import re` 在另一个函数的作用域内无法共享。
**修复**: 将 `import re` 提到文件顶部。

### 场景 5：手动解析遗漏字段

**症状**: 城市列表不显示 highlights。
**根因**: `CityRepository` 手动构建 `City` 对象时 `highlights` 字段没有被 fill。
**修复**: 
```kotlin
highlights = obj["highlights"]?.jsonArray?.map {
    it.jsonPrimitive.content
} ?: emptyList()
```

---

## 审计速查表

| 症状 | 根因模式 | 检查位置 |
|------|----------|----------|
| 页面停在 Loading | API 异常 / ViewModel 未 emit Error | Repository / catch block |
| 页面空白 / 无数据 | 数据模型不匹配 → 崩溃被 silent catch | @SerialName / JSON vs Model |
| 某些字段不显示 | 手动解析遗漏 / @SerialName 不对 | Repository 字段映射 |
| 聊天没反应 | 后端 `import` 缺失 / API 5xx | 直接 curl 端点 |
| 地图空 | API dict/array 类型不匹配 | MapRepository |

---

## 预防

1. **每次新建 data class 后，立即用真实 API 响应验证** — 在服务器上 curl endpoints，手动对比字段
2. **ToolItem.kt 等"简单"文件最容易忘** — 跑完 CI 构建后马上检查这些文件是否有内容
3. **Repository 层优先用手动解析**（`jsonObject.entries.map`）而不是 `decodeFromString`
4. **后端 bug（import 等）和前端 bug 分开排查** — 先 `curl` 确认后端正常，再怀疑 App 代码
