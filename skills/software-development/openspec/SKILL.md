---
name: openspec
description: OpenSpec 规格驱动开发（Spec-Driven Development）框架。安装、配置、初始化、使用全流程。触发词：openspec / 规格驱动 / SDD / opsx
---

# OpenSpec 技能

## 概述

[OpenSpec](https://github.com/Fission-AI/OpenSpec) 是一个轻量级规格驱动开发（SDD）框架，专为 AI 编程助手设计。通过在写代码前先生成规格文档，确保目标和方案对齐。

## 安装

```bash
# 全局安装
npm install -g @fission-ai/openspec

# 验证
openspec --version
```

**位置**：安装到 `~/.npm-global/bin/openspec`（Node v22.22.2，PATH 已配置在 `~/.bashrc` 中）。

## 初始化

```bash
cd your-project
openspec init --tools claude    # 需要指定 AI 工具，否则报错
```

创建 `openspec/` 目录 + `specs/` 主规格 + `changes/` 活动变更。

## Hermes 工作流（CLI 模式）

`/opsx:propose` / `/opsx:apply` 是 IDE 内嵌 AI（Cursor/Claude Code）的**聊天斜杠命令**。在 Hermes Agent 中它们**不可用**，需要通过 CLI 手动创建和处理。

### CLI 命令参考

```bash
openspec init [options] [path]           # 初始化（需 --tools）
openspec new change <name>               # 创建新变更目录（核心入口）
openspec validate <change>               # 验证变更完整性
openspec change show <change> [--json]   # 查看变更详情
openspec list [options]                  # 列出变更/规格
openspec view                            # 交互式仪表盘
openspec archive <change-name>           # 归档已完成变更
openspec update                          # 更新配置
openspec config                          # 查看/修改配置
openspec status [change]                 # 显示完成状态
```

### 完整提案流程

**① 创建变更骨架**
```bash
openspec new change "feature-name"
# → 创建 openspec/changes/feature-name/.openspec.yaml
#   （注意：只有 .openspec.yaml，文件需要手动创建）
```

**② 手动创建以下文件**
```
openspec/changes/feature-name/
├── proposal.md               # 为什么做、做什么、不做什么
├── design.md                 # 技术选型、架构、数据流
├── specs/
│   └── <capability-name>/
│       └── spec.md           # 需求规格（注意目录层级！）
└── tasks.md                  # 实现步骤清单
```

**③ 填写 spec.md（必须通过 `openspec validate` 检查）**

模板格式：
```markdown
## ADDED Requirements

### Requirement: Feature Name
Description text containing SHALL or MUST keyword.

#### Scenario: Scenario name
- **WHEN** condition
- **THEN** expected outcome (use SHALL/MUST if appropriate)
```

**验证强制规则：**
1. 文件路径必须是 `specs/{capability}/spec.md` — `specs/README.md` **不通过**
2. 节头必须是 `## ADDED/MODIFIED/REMOVED/RENAMED Requirements`
3. 每条需求 `### Requirement:` 正文必须含 **SHALL** 或 **MUST** 关键词
4. 每个 Scenario 必须是 `#### Scenario:` + `- **WHEN**` / `- **THEN**` 子弹列表（不是代码块 \`\`\`）
5. 至少一个 `specs/{capability}/spec.md` 文件

**常见踩坑：**

| 错误写法 | 修正 |
|----------|------|
| `openspec propose "xx"` → `unknown command` | CLI 没 propose，用 `new change` + 手动文件 |
| Scenario 写在 ``` 代码块里 | 改为 `- **WHEN**` / `- **THEN**` 子弹列表 |
| 缺少 SHALL/MUST | 正文加 "The system SHALL..." |
| specs/ 放 README.md | 放到 `specs/cap/spec.md` |
| 无 Scenario 块 | 每个 requirement 至少一个 Scenario |

**④ 验证**
```bash
openspec validate <change-name>
# 持续修正直到输出 "Change 'x' is valid"
```

**⑤ 实现** — 按 tasks.md 逐步实现，每项完成打 `[x]`

**⑥ 归档**
```bash
openspec archive <change-name>
# 移到 openspec/changes/archive/YYYY-MM-DD-<name>/
```

## 文件结构

```
project/
├── openspec/
│   ├── changes/                    # 活动变更
│   │   └── <feature>/
│   │       ├── .openspec.yaml     # 自动生成
│   │       ├── proposal.md
│   │       ├── design.md
│   │       ├── specs/
│   │       │   └── <cap>/
│   │       │       └── spec.md
│   │       └── tasks.md
│   ├── specs/                     # 主规格（init 创建）
│   └── changes/archive/           # 已归档
```

## 参考文件

- `references/hermes-integration.md` — 完整 CLI 提案流程实操指南
- `references/python-fstring-js-braces.md` — Python 3.11 f-string + JavaScript 花括号冲突（在 Python 后端嵌入 JS 代码时参考）
