# Nested API Response Handling (CityDetailResponse pattern)

> 后端 API 返回 `{city: {nested fields...}}` 时，Kotlinx Serialization 的解析策略。

---

## 问题

VisePanda API 返回格式：

```json
GET /api/cities/beijing
{
  "city": {
    "name_cn": "北京",
    "food": [
      {"name_en": "Peking Duck", "must_try": true, ...}
    ],
    "hotels": {
      "budget": {"range": "$20-40", ...},
      "mid": {"range": "$50-100", ...}
    },
    "tips": [{"en": "Transport", "tip": "..."}],
    "estimate": {"budget_daily": "$30-50", ...}
  }
}
```

Kotlin `@Serializable` 数据类需要匹配这个嵌套结构。

## 两层包装模式

```kotlin
// 第一层：API 响应
@Serializable
data class CityDetailResponse(
    @SerialName("city") val city: CityDetail
)

// 第二层：实际数据（包含 City 的所有字段 + 扩展字段）
@Serializable
data class CityDetail(
    @SerialName("name_cn") val nameCn: String = "",
    @SerialName("food") val food: List<FoodItem> = emptyList(),
    @SerialName("hotels") val hotels: HotelData = HotelData(),
    @SerialName("tips") val tips: List<TipItem> = emptyList(),
    @SerialName("estimate") val estimate: PriceEstimate = PriceEstimate(),
    // ... 所有 City 字段也需要重复
)

// 同名的简化版 City（用于列表展示，不包含嵌套数据）
@Serializable
data class City(
    @SerialName("name_cn") val nameCn: String = "",
    @SerialName("vibe") val vibe: String = "",
    // ... 只有列表需要的字段
)
```

## Repository 解析

```kotlin
suspend fun getCityDetail(city: String): CityDetail {
    val response = URL("$BASE_URL/api/cities/$city").readText()
    val wrapper = json.decodeFromString<CityDetailResponse>(response)
    return wrapper.city  // 取出真正的数据
}
```

## 为什么不用单一 `City` 类

如果 CityDetail 继承 City，kotlinx.serialization 在反序列化嵌套 `{city: {...}}` 时会把外层 `{city: ...}` 也包含进来。两层包装 + ignoreUnknownKeys 是最干净的方案。

## 适用场景

- API 返回 `{data: {...}}` 或 `{result: {...}}` 包装
- 列表和详情使用不同的字段集合（列表轻量，详情完整）
- 列表用 map/object 键值对而非数组时（`/api/cities` vs `/api/cities/:id`）
