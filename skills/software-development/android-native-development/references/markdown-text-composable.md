# Zero-Dependency MarkdownText Composable

> Android Compose 中零外部依赖的 Markdown 渲染方案。
> 用 `buildAnnotatedString` 实现，支持 **bold**, *italic*, `code`, ### header, - list, [link](url), --- hr。

## 完整代码

```kotlin
@Composable
fun MarkdownText(text: String, modifier: Modifier = Modifier) {
    val annotatedString = buildAnnotatedString {
        val lines = text.split("\n")
        lines.forEachIndexed { index, line ->
            when {
                // ### Header
                line.matches(Regex("^#{1,3}\\s.*")) -> {
                    val content = line.replace(Regex("^#{1,3}\\s"), "")
                    withStyle(SpanStyle(fontWeight = FontWeight.Bold,
                        fontSize = MaterialTheme.typography.titleMedium.fontSize)) {
                        append(parseInlineMarkdown(content))
                    }
                    if (index < lines.lastIndex) append("\n\n")
                }
                // - list item
                line.matches(Regex("^-\\s.*")) -> {
                    val content = line.replace(Regex("^-\\s"), "")
                    append("  •  ")
                    append(parseInlineMarkdown(content))
                    if (index < lines.lastIndex) append("\n")
                }
                // --- horizontal rule
                line.matches(Regex("^-{3,}$")) -> append("─".repeat(20) + "\n")
                // Empty line = paragraph break
                line.isBlank() -> { if (index > 0 && index < lines.lastIndex) append("\n") }
                // Regular paragraph
                else -> {
                    append(parseInlineMarkdown(line))
                    if (index < lines.lastIndex && lines[index + 1].isNotBlank()) append("\n")
                }
            }
        }
    }
    Text(text = annotatedString, style = MaterialTheme.typography.bodyMedium, modifier = modifier)
}

// Inline patterns: **bold**, *italic*, `code`, [text](url)
private fun buildAnnotatedString.parseInlineMarkdown(text: String): buildAnnotatedString {
    val pattern = Regex("""(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`(.+?)`)|(\[(.+?)\]\((.+?)\))""")
    var lastIndex = 0
    pattern.findAll(text).forEach { match ->
        if (match.range.first > lastIndex) append(text.substring(lastIndex, match.range.first))
        when {
            match.groupValues[1].isNotEmpty() -> withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { append(match.groupValues[2]) }
            match.groupValues[3].isNotEmpty() -> withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { append(match.groupValues[4]) }
            match.groupValues[5].isNotEmpty() -> withStyle(SpanStyle(color = MaterialTheme.colorScheme.primary, background = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f))) { append(match.groupValues[6]) }
            match.groupValues[7].isNotEmpty() -> withStyle(SpanStyle(color = MaterialTheme.colorScheme.primary, textDecoration = TextDecoration.Underline)) { append(match.groupValues[8]) }
        }
        lastIndex = match.range.last + 1
    }
    if (lastIndex < text.length) append(text.substring(lastIndex))
    return this
}
```

## 为什么不用第三方库

| 方案 | 问题 |
|:----|:-----|
| `compose-richtext` | 大而全但依赖多，API 不稳定 |
| `compose-markdown` | 社区库维护不活跃 |
| WebView 渲染 | 用户明确拒绝 WebView |
| `AnnotatedString` | ✅ 零依赖，完全可定制，Compose 原生 |

## 限制
- 不支持：表格、代码高亮、嵌套列表、图片
- Chat 场景足够（90% 的 AI 回复只需要 bold/italic/code/list）
- 需要扩展时，加到 `parseInlineMarkdown` 的 `when` 分支即可
