# Parallel Feature Development Workflow (vp-hermes pattern)

> 当用户有多个功能待做时，默认并行而非串行。

## 用户信号

用户说:
- "两个一起写" / "都做" / "全写" → 并行执行
- "下一步" × N → 不要每个做完都问，直接执行队列
- "继续" → 默认取剩余任务中的最高优先级执行，不问

## 执行原则

1. **队列思维**: 用户说"下一步"时，不是问"选哪个"，而是默认执行计划中的下一个
2. **批量提交**: 多个独立页面可一次写完、一次编译、一次提交（减少对话来回）
3. **独立文件优先**: 并行写不互相依赖的文件（如 CityDetailScreen + ChatScreen 可同时写，因为它们只依赖 core:designsystem）
4. **串行依赖**: 只有当一个文件需要另一个文件的结果时才串行（如 ChatViewModel 需要 ChatMessage model 先定义）

## 本地执行方法

```python
# 文件多时，用一次 execute_code 调用 write_file 批量写
from hermes_tools import write_file

# 并行写多个独立文件
files = {
    "path/to/Screen1.kt": content1,
    "path/to/Screen2.kt": content2,
}
for path, content in files.items():
    write_file(path, content)
```

## 编译验证节奏

多文件写完 → 一次 `./gradlew assembleDebug` 验证 → 修编译错误 → 再验证 → git commit

如果编译错误多，按顺序修：
1. 缺失的 import（最常见）
2. 类型不匹配
3. 未解析的引用（通常是缺少 data class 或 import）

## 适用条件

| 条件 | 并行 | 串行 |
|------|------|------|
| 文件互不依赖 | ✅ | ❌ 浪费来回 |
| 文件 A 依赖文件 B 的结果 | ❌ B 写完后才写 A | ✅ |
| 用户不耐烦（多次说"继续"） | ✅ 减少等待 | ❌ 增加来回 |
| 用户第一次接触 | ⚠️ 先确认方向再并行 | ✅ 逐个确认 |
