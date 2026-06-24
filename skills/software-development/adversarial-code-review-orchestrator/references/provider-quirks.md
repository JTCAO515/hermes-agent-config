# 代码审查 API 提供者异常行为记录

## DeepSeek V4

### reasoning_content 替代 content

**问题**：DeepSeek V4 系列（包括 `deepseek-v4-flash` 和 `deepseek-v4-pro`）是推理模型。当系统要求输出结构化 JSON 时，模型把全部分析写入 `reasoning_content` 字段，而 `content` 字段保持空字符串 `""`。

**API 响应结构**：
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "",                      // ← 空！
      "reasoning_content": "我们分析代码..."  // ← 分析在这里
    }
  }]
}
```

**影响**：标准 OpenAI API 客户端通常只读 `content`，导致误报"空响应"。

**解决方案**：
1. 读取时 fallback：`msg.get("content", "") or msg.get("reasoning_content", "")`
2. 两步法：第一步让模型自由推理 → 提取 reasoning_content → 第二步让模型将推理转为 JSON
3. 在 system prompt 中加入 `CRITICAL: Output ONLY raw JSON. No thinking, no reasoning.` 但推理模型可能会忽略此指令

**性能**：DeepSeek V4 Flash 处理 26K chars 代码约 40-66s，比 GLM 5.1 快 3-4 倍。两步法（推理+转换）总耗时约 80-120s。

### max_tokens 参数

DeepSeek 使用 `max_tokens`（OpenAI 标准），`max_completion_tokens` 不被识别。GLM 5.1 两者都支持但更兼容 `max_tokens`。

---

## GLM 5.1（智谱 AI）

### 超长 prompt 空响应

**问题**：当 user prompt 超过约 20K chars 时，GLM 5.1 返回空 content（0 chars），http code 200。原因不明（可能是内部超时或截断）。

**表现**：10K chars → 工作正常（170-434s，8 findings），26K chars → 空响应

**解决方案**：将代码拆分为 <=15K chars 的批次发送。

**性能**：10K chars 约 170s，26K chars 约 434s（但空响应后重试也无效）。比 DeepSeek 慢约 3-4 倍，但审查质量更高。

### JSON 输出一致性

GLM 5.1 比 DeepSeek 更可靠地遵循"输出 JSON"指令。batch 1 直接返回了有效 JSON，而 DeepSeek 需要两步法才能提取 JSON。

### 非确定性结果

**同一个代码文件，在模型端没有代码变更的情况下，两次运行返回不同数量的发现。** 实测结果：

| 运行 | 批次 1-4 总数 |
|------|--------------|
| 第一次 | 40 findings |
| 第二次（修复后代码重跑） | 33 findings |

差异原因推测：
- temperature=0.2 的随机性
- 批次间上下文差异（前一批次结果不影响当前批次）
- 模型负载/版本漂移

**处理建议**：对 GLM 的审查结果做"二次确认"——CRITICAL/HIGH 级别的问题如果只有一个模型报告，降低一档严重度评估。共识（双模型均发现）的问题优先修复。

---

## GPT 5.5 (NUWA Flux)

**已知问题**：NUWA Flux API 可能返回 403 Forbidden（密钥过期或配额用完）。建议配置 fallback：先试 NUWAFLUX_API_KEY，失败后切到 OPENAI_API_KEY 或 DEEPSEEK_API_KEY。

---

## 通用技巧

### 批次大小

| Prompt 大小 | GLM 5.1 | DeepSeek V4 Flash |
|------------|---------|-------------------|
| 10K chars | 170s ✅ | 40s ✅ |
| 26K chars | 空响应 ❌ | 66s ✅（两步法 120s） |
| >30K chars | 空响应 ❌ | 空响应 ❌ |

建议每批 10-15K chars，2-3 个文件。

### JSON 提取优先级

```python
def extract_json(text):
    # 1. 代码块 ```json ... ```
    # 2. 全文 json.loads
    # 3. 首 { 到末 } 截取
    # 4. 失败 → 第二步调用：让模型将推理转为 JSON
```
