# SSE ChatViewModel Pattern (Android Compose)

> Chat SSE 流式收集的 ViewModel 架构模式。
> 核心：Token → accumulate, Split → flush, Done → finalize。

## State 定义

```kotlin
data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isStreaming: Boolean = false,
    val currentStreamText: String = "",      // 正在生成的文本
    val currentImages: List<ChatImage> = emptyList(),
    val currentFaqs: List<ChatFaq> = emptyList(),
    val error: String? = null
)
```

## ViewModel 核心循环

```kotlin
class ChatViewModel : ViewModel() {
    private val repository = ChatRepository()
    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private var streamJob: Job? = null
    private var accumulatedText = ""
    private var accumulatedImages = mutableListOf<ChatImage>()

    fun sendMessage(text: String, city: String? = null) {
        // 1. 添加用户消息到 state
        val userMsg = ChatMessage(role = "user", content = text)
        _uiState.value = _uiState.value.copy(
            messages = _uiState.value.messages + userMsg
        )

        // 2. 准备流式
        accumulatedText = ""
        accumulatedImages.clear()
        _uiState.value = _uiState.value.copy(isStreaming = true)

        // 3. 启动 SSE 收集
        streamJob = viewModelScope.launch {
            repository.streamChat(allMessages, city)
                .catch { e ->
                    _uiState.value = _uiState.value.copy(isStreaming = false, error = e.message)
                }
                .collect { event -> handleEvent(event) }
        }
    }

    private fun handleEvent(event: ChatEvent) {
        when (event) {
            is ChatEvent.Token -> {
                accumulatedText += event.text
                _uiState.value = _uiState.value.copy(currentStreamText = accumulatedText)
            }
            is ChatEvent.Split -> flushAccumulated(isSplit = true)
            is ChatEvent.Image -> accumulatedImages.add(...)
            is ChatEvent.Done -> { flushAccumulated(false); _uiState.value = _uiState.value.copy(isStreaming = false) }
            is ChatEvent.Error -> _uiState.value = _uiState.value.copy(isStreaming = false, error = event.message)
        }
    }

    private fun flushAccumulated(isSplit: Boolean) {
        if (accumulatedText.isNotEmpty() || accumulatedImages.isNotEmpty()) {
            val msg = ChatMessage(role = "assistant", content = accumulatedText, images = accumulatedImages.toList())
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + msg,
                currentStreamText = "",
                currentImages = emptyList()
            )
            accumulatedText = ""
            accumulatedImages.clear()
        }
    }

    fun stopStreaming() { streamJob?.cancel(); flushAccumulated(false); _uiState.value = _uiState.value.copy(isStreaming = false) }
    fun clearChat() { streamJob?.cancel(); _uiState.value = ChatUiState(); accumulatedText = ""; accumulatedImages.clear() }
}
```

## UI 端消费

```kotlin
@Composable
fun ChatScreen(viewModel: ChatViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsState()
    val listState = rememberLazyListState()

    // 自动滚动到底部
    val itemCount = uiState.messages.size + if (uiState.isStreaming) 1 else 0
    LaunchedEffect(itemCount) {
        if (itemCount > 0) listState.animateScrollToItem(itemCount - 1)
    }

    LazyColumn(state = listState, ...) {
        // 已完成的助手消息
        items(uiState.messages) { msg -> MessageBubble(msg) }

        // 流式中的消息（实时显示 accumulated text）
        if (uiState.isStreaming && uiState.currentStreamText.isNotEmpty()) {
            item { StreamBubble(text = uiState.currentStreamText) }
        }

        // 加载状态（刚请求还没收到 token）
        if (uiState.isStreaming && uiState.currentStreamText.isEmpty()) {
            item { Box { Text("thinking...") } }
        }
    }
}
```

## 关键点
1. **Split vs Done**: `event: split` 是段落分隔（创建多条消息），`event: done` 是流结束（finalize）
2. **Stop button**: 取消 streamJob 后必须 flush 已累积的内容
3. **currentStreamText**: 实时状态→UI 实时渲染，不需要额外 debounce
4. **auto-scroll**: `LaunchedEffect(itemCount)` 监听消息数变化自动滚动
