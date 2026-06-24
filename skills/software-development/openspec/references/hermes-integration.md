# OpenSpec CLI 实操指南（Hermes Agent 专用）

> OpenSpec `/opsx:propose` 是 IDE 内嵌斜杠命令，在 Hermes 聊天界面中不可用。
> 本文档记录通过 CLI 在 Hermes 中使用 OpenSpec 的完整流程。

## 环境

| 项 | 值 |
|----|-----|
| 版本 | v1.3.1 |
| 路径 | `~/.npm-global/bin/openspec` |
| Node | v22.22.2 |
| 项目 | `vise-panda-2`（已 `openspec init --tools claude`） |

## 创建提案全流程

```bash
# 1. 进入项目
cd /home/ubuntu/projects/vise-panda-2

# 2. 创建变更目录
openspec new change "feature-name"
# → openspec/changes/feature-name/.openspec.yaml

# 3. 创建规范文件
mkdir -p openspec/changes/feature-name/specs/capability/
touch openspec/changes/feature-name/proposal.md
touch openspec/changes/feature-name/design.md
touch openspec/changes/feature-name/specs/capability/spec.md
touch openspec/changes/feature-name/tasks.md

# 4. 写入内容（见 SKILL.md 模板）
# ...

# 5. 验证
openspec validate feature-name
# 持续修正直到输出 "Change 'feature-name' is valid"

# 6. 归档（实现完成后）
openspec archive feature-name
```

## `openspec validate` 常见错误及修复

### Error: "Change must have at least one delta"
**原因**：`specs/` 目录结构不对，或没有符合格式的 spec.md。

**修复**：
```
# ❌ 错误结构
specs/README.md

# ✅ 正确结构
specs/capability-name/spec.md
```

### Error: "missing requirement text"
**原因**：`### Requirement: Name` 后面没有正文描述。

**修复**：
```markdown
### Requirement: Feature Name
The system SHALL do something...  # ← 必须有这一行正文
```

### Error: "must contain SHALL or MUST"
**原因**：Requirement 正文缺少 SHALL/MUST 关键词。

**修复**：在描述中加入 "SHALL" 或 "MUST"。

### Error: "No requirement entries parsed"
**原因**：`## ADDED Requirements` 后面没有 `### Requirement:` 标题。

### Error: "Why section" (openspec change show)
**原因**：spec.md 缺少 `## ADDED Requirements` 节头。

## 模板速记

### spec.md 模板
```markdown
## ADDED Requirements

### Requirement: Feature Name
The system SHALL provide [function] that [behavior].

#### Scenario: Scenario name
- **WHEN** [trigger condition]
- **THEN** [expected outcome]
```

### proposal.md 模板
```markdown
# Feature Title

## Why
[为什么做]

## What
[做什么]

## What NOT
[不做什么]
```

### design.md 模板
```markdown
# Design: Feature Title

## Tech Stack
| Item | Choice | Reason |

## Architecture
[数据流/架构图]

## Performance
[考虑]
```

### tasks.md 模板
```markdown
# Tasks

## Phase 1: Backend
- [ ] Task 1
- [ ] Task 2

## Phase 2: Frontend
- [ ] Task 3

## Files Changed
| File | Change |
```

## 注意事项

- `openspec validate` 只检查格式，不检查语义正确性
- 提案阶段不写任何代码，只产出文档
- 归档后变更移到 `openspec/changes/archive/`，主 `specs/` 会更新
- 匿名统计通过 `export OPENSPEC_TELEMETRY=0` 关闭
