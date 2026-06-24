# 批次化双模型代码审查模式

## 适用场景

当代码库较大（多个文件、数千行代码）且需要多模型交叉验证时，批次化双模型审查比 3 模型人格化设计更实用：

- 单次 prompt 超 15K chars 会导致 GLM 空响应
- 两个模型已经能提供足够的视角差异
- 批次化允许增量运行和断点续查

## 批次定义

每个批次包含 2-3 个功能相关的文件（按模块分组）：

```python
BATCHES = [
    {"name": "card-hand-eval",  "files": ["card.py", "hand_evaluator.py", "__init__.py"],
     "focus": "卡牌编码、解码、校验、5牌/7牌评估、Kicker 逻辑"},
    {"name": "equity-ranges-state", "files": ["equity_calculator.py", "ranges.py", "state_manager.py"],
     "focus": "蒙特卡洛胜率模拟、whole-pot 统计、对手范围系统"},
    {"name": "decision-gt",     "files": ["decision_engine.py", "game_theory.py"],
     "focus": "EV 决策模型、博弈分析引擎、意图逆向、决策树"},
    {"name": "api-cli",         "files": ["api.py", "main.py"],
     "focus": "FastAPI Web API、CLI 入口、输入校验、错误处理"},
]
```

## 提示词设计

### System Prompt

关键：显式要求仅输出 JSON，不给模型"思考后包装"的空间：

```
You are an adversarial code reviewer.
CRITICAL: Output ONLY raw JSON. No markdown, no code blocks, no explanation, no thinking.
Output format:
{"findings": [{"severity": "CRITICAL|HIGH|MEDIUM|LOW", "file": "...", "line": 0, "title": "...", "description": "...", "suggestion": "..."}], "batch_score": "0-10", "summary": "..."}
Focus areas:
- Math correctness
- Logic errors
- Security issues
- Performance problems
- Code quality
```

### User Prompt

```
Focus: {focus_for_this_batch}

Review these files:

```python
# File: {name} ({chars} chars, {lines} lines)
{content}
```

---
...

``` ...
```

## 响应解析

### DeepSeek 推理模型特殊处理

DeepSeek V4 Flash/Pro 作为推理模型，可能将分析内容写入 `reasoning_content` 而非 `content`：

```python
reply = parsed["choices"][0]["message"].get("content", "")
reasoning = parsed["choices"][0]["message"].get("reasoning_content", "")
text = reply or reasoning
```

如果 `content` 为空但有 `reasoning_content`，采用两步法：
1. 从 `reasoning_content` 提取 JSON（先代码块 → 全文 → 首{到末}）
2. 若失败，发起第二次调用要求"将分析转为 JSON"

### JSON 提取优先级

```python
def _extract_json(text):
    # 1. ```json``` 代码块
    # 2. 全文 json.loads
    # 3. 首 { 到末 } 截取
```

## 汇总与交叉对比

### 注意：`merge()` 函数设计约束

```python
def merge(findings_list: list) -> list:
    # 接受 list of lists（每个内层 list 是一个批次的结果）
    # 不接受扁平 list of dicts！
    for findings in findings_list:       # ← 期望是 list
        if not isinstance(findings, list):
            continue                     # ← dict 被直接跳过！
```

**`generate_summary()` 中不能直接传扁平 findings 给 `merge()`**。正确做法：

```python
# 错误：all_findings 是扁平 list of dicts
all_findings = sort_by_severity(merge(all_findings))  # 全部被跳过 → 0 findings

# 正确：inline dedup
seen = set()
unique = []
for f in all_findings:
    key = (f.get("file", ""), f.get("title", ""))
    if key not in seen:
        seen.add(key)
        unique.append(f)
all_findings = sort_by_severity(unique)
```

### 交叉对比算法

对两个模型的 findings 按 `(文件, 标题)` 去重后取交集和差集：

```python
consensus = glm_only & ds_only  # 双模型一致认为的问题
glm_only = glm_all - ds_all     # 仅 GLM 发现
ds_only = ds_all - glm_all      # 仅 DeepSeek 发现
```

经验：双模型共识近乎为零（0 个共识是正常现象）。各自的发现来自不同的审查视角，互为补充。

### 非确定性

**同一模型在同一代码上，不同运行返回不同数量的发现**（实测 GLM 5.1 先后产出 40 vs 33 个发现）。原因：
- 模型自身的随机性（temperature=0.2）
- 批次间上下文差异（前一批次的 API 响应不共享）
- 模型版本与负载

**应关注已修复的问题数量，而非未修复的计数。**

## `--summary-only` 模式

```bash
python adversarial_review.py --summary-only
```

- 不调用任何 API
- 从 `reports/review_*.json` 读取已有结果
- 支持 `--p0-only` 限制只显示 CRITICAL/HIGH
- 适用于：跑完一批次后复查、比较修复前后的发现数

## 已知局限

1. **range 校验**：API 请求中 `ranges` 列表长度必须等于 `players-1`，但缺乏 Pydantic 校验器（仅在运行时检查索引越界）
2. **board 大小**：德州扑克的公共牌必须为 0、3、4、5 张（1、2 张非法），但 `max_length=5` 的 Pydantic 字段未约束具体有效值
3. **evaluate_7 输入**：传入少于 5 张总牌时降级为 HIGH_CARD，但下游 `compare_hands` 对 kicker 长度不一致会抛异常（已修复为 `sorted(..., reverse=True)`）
4. **EV 公式**：加注 EV 公式中 `raise_amount` 为总投入额（含跟注），不应再加 `to_call`
