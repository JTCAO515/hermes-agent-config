---
name: planning
description: "文件式任务规划 — 每次任务前先写PLAN.md，再执行。planning with file，planning以后走文件"
version: 1.0.0
triggers:
  - planning
  - 规划
  - 计划
  - 写计划
  - plan
  - 做规划
---

# Planning — 文件式任务规划

## 核心原则

**一切规划走文件，不输出纯文字规划。**

每次开始新任务或复杂功能前：
1. 创建 `PLAN.md`（项目根目录 或 `.hermes/plans/`）
2. 按模板填充
3. 用户确认后执行
4. 执行过程中持续更新 PLAN.md

## 模板

### 标准模板（日常任务用）

```markdown
# PLAN.md

## Task
<!-- 一句话：做什么 -->

## Context
<!-- 为什么做、成功标准是什么 -->

## Approach
<!-- 怎么做、关键方案选择 -->

## Milestones
- [ ] M1: xxx | verify: `命令`
- [ ] M2: xxx | verify: `命令`
- [ ] Final: all pass | verify: `命令`

## Scope
In scope:
-
Out of scope:
-

## Open questions
-
```

### 简短模板（快速任务用）

```markdown
# PLAN.md

**Goal:** 一句话

**Steps:**
1. [ ] step1 | verify: xxx
2. [ ] step2 | verify: xxx
3. [ ] final | verify: xxx
```

## 存储位置

优先项目根目录 `PLAN.md`。如果项目已有 `PLAN.md`，追加到末尾而不是覆盖。

如果当前不在项目目录，存到 `.hermes/plans/`。

## 执行纪律

- 每个 milestone 完成后标记 `[x]` 并更新 PLAN.md
- 卡住时在 PLAN.md 追加 Open questions 而不是跳过
- 任务完成后 PLAN.md 保留在项目中（历史记录）
