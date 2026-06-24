/**
 * TripRepository.kt — DataStore Preferences CRUD pattern for Android (Kotlin)
 *
 * Use this pattern when you need simple local persistence WITHOUT Room DB.
 * Good for: saved trips, user preferences, cache of API data.
 * Not good for: complex queries, relational data, large datasets (>100KB).
 *
 * KEY PATTERNS:
 * 1. DataStore extension via `preferencesDataStore` delegate
 * 2. JSON serialization of complex objects into a single string key
 * 3. Flow-based read, suspend write
 * 4. UUID-based ID generation for new items
 */

// ── DataStore setup (extension property) ──
private val Context.tripsDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "app_data_store"
)

class TripRepository(private val context: Context) {

    companion object {
        private val ITEMS_KEY = stringPreferencesKey("saved_items")
    }

    private val json = Json { 
        ignoreUnknownKeys = true 
        isLenient = true       // tolerate trailing commas
        encodeDefaults = true   // include null/default values in serialized JSON
    }

    // ── READ (returns Flow<List<T>>) ──
    fun getAllItems(): Flow<List<MyItem>> {
        return context.appDataStore.data.map { prefs ->
            try {
                json.decodeFromString<List<MyItem>>(prefs[ITEMS_KEY] ?: "[]")
            } catch (e: Exception) {
                emptyList()
            }
        }
    }

    // ── CREATE / UPDATE ──
    suspend fun saveItem(item: MyItem) {
        context.appDataStore.edit { prefs ->
            val items = try {
                json.decodeFromString<MutableList<MyItem>>(prefs[ITEMS_KEY] ?: "[]")
            } catch (e: Exception) {
                mutableListOf()
            }
            val idx = items.indexOfFirst { it.id == item.id }
            if (idx >= 0) {
                items[idx] = item.copy(updatedAt = System.currentTimeMillis())
            } else {
                items.add(item.copy(
                    id = if (item.id.isBlank()) UUID.randomUUID().toString() else item.id,
                    createdAt = System.currentTimeMillis(),
                    updatedAt = System.currentTimeMillis()
                ))
            }
            prefs[ITEMS_KEY] = json.encodeToString(items)
        }
    }

    // ── DELETE ──
    suspend fun deleteItem(itemId: String) {
        context.appDataStore.edit { prefs ->
            val items = try {
                json.decodeFromString<MutableList<MyItem>>(prefs[ITEMS_KEY] ?: "[]")
            } catch (e: Exception) {
                mutableListOf()
            }
            items.removeAll { it.id == itemId }
            prefs[ITEMS_KEY] = json.encodeToString(items)
        }
    }

    // ── DELETE ALL ──
    suspend fun clearAll() {
        context.appDataStore.edit { prefs ->
            prefs.remove(ITEMS_KEY)
        }
    }
}

// ── Example model (using kotlinx.serialization) ──
@Serializable
data class MyItem(
    @SerialName("id") val id: String = "",
    @SerialName("title") val title: String = "",
    @SerialName("content") val content: String = "",
    @SerialName("created_at") val createdAt: Long = System.currentTimeMillis(),
    @SerialName("updated_at") val updatedAt: Long = System.currentTimeMillis()
)
