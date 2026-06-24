/**
 * SseClient.kt — Full production SSE streaming client for Android (Kotlin + OkHttp)
 *
 * Copy-paste this as a starting point for any project needing SSE streaming in Android.
 * No external SSE libraries needed — uses OkHttp's streaming response + Kotlin Flow.
 *
 * SEVENT TYPES:
 *   event: token  → data: "text fragment"
 *   event: split  → data: {"boundary": true}
 *   event: image  → data: {"key":"..","url":"..","label":".."}
 *   event: faq    → data: {"id":"..","title":"..","icon":".."}
 *   event: done   → data: ""
 *   event: error  → data: {"message":".."}
 *
 * ADAPT FOR YOUR API: modify buildJsonBody(), parseEvent(), and BASE_URL.
 */

class SseClient(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)     // SSE streams are long-lived
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
) {
    private val json = Json { ignoreUnknownKeys = true }

    fun streamChat(
        messages: List<ChatMessage>,
        city: String?
    ): Flow<ChatEvent> = callbackFlow {
        val bodyJson = buildJsonBody(messages, city)
        val requestBody = bodyJson.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url("${ApiConfig.BASE_URL}/api/chat")
            .post(requestBody)
            .build()

        var currentCall: Call? = null

        client.newCall(request).enqueue(object : Callback {
            override fun onResponse(call: Call, response: Response) {
                currentCall = call
                val source = response.body?.source() ?: run {
                    trySend(ChatEvent.Error("Empty response body"))
                    channel.close()
                    return
                }
                var currentEvent = "message"
                try {
                    while (!source.exhausted()) {
                        val line = source.readUtf8Line() ?: break
                        when {
                            line.startsWith("event: ") ->
                                currentEvent = line.removePrefix("event: ").trim()
                            line.startsWith("data: ") ->
                                parseEvent(currentEvent, line.removePrefix("data: ").trim())
                                    ?.let { trySend(it) }
                            line.isEmpty() -> currentEvent = "message"
                        }
                    }
                } catch (e: Exception) {
                    trySend(ChatEvent.Error(e.message ?: "Stream error"))
                } finally {
                    trySend(ChatEvent.Done)
                    channel.close()
                    response.closeQuietly()
                }
            }
            override fun onFailure(call: Call, e: IOException) {
                trySend(ChatEvent.Error(e.message ?: "Network error"))
                channel.close()
            }
        })
        awaitClose { currentCall?.cancel() }
    }

    /** Non-streaming fallback */
    fun chatSync(messages: List<ChatMessage>, city: String?): String {
        val bodyJson = buildJsonBody(messages, city)
        val response = client.newCall(Request.Builder()
            .url("${ApiConfig.BASE_URL}/api/chat")
            .post(bodyJson.toString().toRequestBody("application/json".toMediaType()))
            .build()).execute()
        return response.body?.string() ?: ""
    }

    private fun buildJsonBody(messages: List<ChatMessage>, city: String?): JsonObject {
        val msgs = messages.joinToString(",") { """{"role":"${it.role}","content":"${escapeJson(it.content)}"}""" }
        val cityPart = if (city != null) ""","city":"$city"""" else ""
        return json.parseToJsonElement("""{"messages":[$msgs]$cityPart}""").jsonObject
    }

    private fun escapeJson(s: String) =
        s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")

    private fun parseEvent(eventType: String, data: String): ChatEvent? {
        if (data.isEmpty()) return null
        return when (eventType) {
            "token" -> ChatEvent.Token(data.removeSurrounding("\""))
            "split" -> ChatEvent.Split(true)
            "image" -> tryParse(data) { obj ->
                ChatEvent.Image(
                    obj["key"]?.jsonPrimitive?.content ?: "",
                    obj["url"]?.jsonPrimitive?.content ?: "",
                    obj["label"]?.jsonPrimitive?.content ?: ""
                )
            }
            "faq" -> tryParse(data) { obj ->
                ChatEvent.Faq(
                    obj["id"]?.jsonPrimitive?.content ?: "",
                    obj["title"]?.jsonPrimitive?.content ?: "",
                    obj["icon"]?.jsonPrimitive?.content ?: ""
                )
            }
            "done" -> ChatEvent.Done
            "error" -> ChatEvent.Error(
                tryParse<String>(data) { obj ->
                    obj["message"]?.jsonPrimitive?.content ?: data
                } ?: data
            )
            else -> null
        }
    }

    private inline fun <T> tryParse(data: String, block: (JsonObject) -> T): T? =
        try { block(json.parseToJsonElement(data).jsonObject) } catch (_: Exception) { null }
}
