# 2026-06-21 — Memory Dream Mode 真实巡检流程

## 背景

`memory-dream-mode.py` 脚本原有实现仅为占位（写入静态 JSON），不做任何真实文件检查。此文档记录如何**手动验证**和**增强检查**记忆健康。

## 真实记忆存储位置

| 文件 | 作用 | 格式 |
|------|------|------|
| `~/.hermes/memories/MEMORY.md` | 系统记忆（环境/规则/项目/工具） | `§` 分隔的条目 |
| `~/.hermes/memories/USER.md` | 用户画像 | `§` 分隔的条目 |
| `~/.hermes/config.yaml` | 容量限制 | `memory.memory_char_limit` / `memory.user_char_limit` |

## 手动检查步骤

### 1. 查容量限制（必须从 config.yaml 读，不是代码默认值）

```bash
grep -A5 "memory:" ~/.hermes/config.yaml
```

返回示例：
```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 4400    # ← 实际值，非代码默认 2200
  user_char_limit: 2750      # ← 实际值，非代码默认 1375
```

### 2. 查文件大小

```bash
wc -c ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md
```

### 3. 统计条目数

用 Python 按 `§` 分割：
```python
raw = open("~/.hermes/memories/MEMORY.md").read()
entries = [e.strip() for e in raw.replace("§", "\nDELIM\n").split("\nDELIM\n") if e.strip()]
print(f"{len(entries)} entries, {len(raw)} chars")
```

### 4. 检查重复

比较前 60 字符前缀看是否有潜在重复。

### 5. 检查任务进度残留

持久记忆不应含：`Day `, `cron`, `已完Day`, `每晚` 等任务跟踪内容。

## 容量门限

| 指标 | 阈值 | 操作 |
|------|------|------|
| usage_pct > 85% | ⚠️ 告警 | 建议压缩 |
| usage_pct > 95% | 🚨 紧急 | 必须立即压缩 |
| usage_pct = 100% | ❌ 拒绝写入 | 新记忆会失败 |

## 压缩检查清单

- [ ] 是否已在 config.yaml 查阅真实的 `memory_char_limit` / `user_char_limit`？
- [ ] 是否直接检查了 `~/.hermes/memories/MEMORY.md` 和 `USER.md` 的内容？
- [ ] 是否排除了任务进度条目（Day X、cron 等）？
- [ ] 是否标注了【→推理】链让每条记忆可关联？
