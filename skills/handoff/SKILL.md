---
name: handoff
description: 项目交接文档（HANDOFF.md）标准化模板。用于记录项目快照，方便后续恢复或交接给其他AI。
---

# Handoff.md — 项目交接文档规范

## 用途

当项目迭代暂停、切换主力项目、或需要让另一个AI/人接手时，产出 `HANDOFF.md` 作为完整项目快照。**不是CHANGELOG，不是PLAN——是"给我看这个文件就能继续干活"的文档。**

## 触发条件

- 用户说"写handoff"或"写交接文档"
- 用户说"暂停这个项目，切到别的"
- 用户说"把这个项目交接给xxx"
- 项目长期搁置前

## 模板结构

每个 HANDOFF.md 必须包含以下12个节（按顺序），根据项目实际情况填充：

```
# [项目名称] v[版本号] — Handoff Document

> **Last Updated:** [日期]
> **Status:** [✅/🔄/⏸️] + 状态说明
> **Repo:** [仓库SSH/HTTPS地址]
> **Live URL:** [生产环境地址]
> **Agent Memory Key:** [Hermes记忆中的关键词，用于session_search]

---

## 1. Product Overview
一句话+一段话说明产品是什么、解决了什么问题、目标用户是谁。

## 2. Architecture
架构图（ASCII art 或文字描述）+ 关键设计决策表（决定/选择/原因）

## 3. Current State
当前完成的功能清单（按模块/阶段分类，✅/🔄/❌标记）+ 已知问题/坑点

## 4. File Structure
项目目录树，标注每个文件的作用

## 5. API / Interface
所有API端点或对外接口（方法、路径、说明、参数）

## 6. Key Config
环境变量、配置文件、第三方服务凭据（不含敏感值）

## 7. Core Logic / Data Flow
核心逻辑流程、数据处理链路、关键算法

## 8. Frontend / UI Component Map
前端页面/组件结构图

## 9. Dependencies
技术栈、外部依赖、版本号

## 10. Next Steps
待办事项（标注优先级：🔴🟡🟢）

## 11. Troubleshooting
常见问题清单（问题→原因→解决方案）

## 12. References
相关文档链接、skill名称、设计参考

---

*End of Handoff.*
```

## 编写原则

1. **自包含** — 不需要再看其他文件也能理解项目全貌
2. **最新状态** — 不是规划，是当前真实状态
3. **含坑点** — 已知问题、踩过的坑、配置陷阱必须写明
4. **可恢复** — 给另一个AI看后能直接继续开发
5. **版本号** — 标注当前版本，每次写handoff时更新

## 续写项目（恢复流程）

当用户说"继续写[项目名]"或"恢复[项目名]"时，按以下步骤恢复：

### 恢复 Step 1 — 读 HANDOFF.md
- 先找到并读取项目根目录的 `HANDOFF.md`
- 理解产品定位、架构、当前状态、已知坑点

### 恢复 Step 2 — 验证真实状态（文档 vs 现实）
HANDOFF.md 是"上次暂停时的快照"，恢复时必须验证以下维度：
- **Git 状态**：`git log --oneline -3` + `git status` — 确认最新代码
- **部署状态**：`curl` 线上域名 / `curl` Vercel 原始域名 — 确认是否活着
- **API 可用性**：调用 `/api/health` 或 `/api/version` — 确认后端响应
- **数据完整性**：检查关键 JSON 是否损坏、必要字段是否为空
- **关键配置**：验证环境变量是否配置（如 LLM API Key）
- **自动化任务**：`cronjob list` — 确认 Cron 是否仍在运行

如果发现 HANDOFF.md 中声称"已配置"或"已部署"但实际缺失，需向用户报告差异。

### 恢复 Step 3 — 理解后提问
- 在提出优化方向前，先基于扫描结果给用户 2-4 个候选方向
- 每个方向标注优先级（🔴/🟡/🟢）和执行路径
- 让用户选方向，不替用户决定

## 写完后必做

HANDOFF.md 写完后，**必须执行以下四个步骤**才算完成暂停/交接：

### Step 1 — 同步到 GitHub
- 执行 `git add HANDOFF.md && git commit -m "[version]: Handoff document" && git push`
- 如果项目包含大量静态资源（图片等），push 可能因体积大而超时：
  - 使用 `GIT_SSH_COMMAND="ssh -o ServerAliveInterval=120" git push origin main` 保持长连接
  - 或后台运行并告诉用户正在推送
- 确保远程仓库（GitHub/GitLab）上的 HANDOFF.md 与本地一致
- 这样其他设备/平台可以随时 clone 或 pull 获取最新项目快照

### Step 2 — 生成文字摘要发用户
- 将 HANDOFF.md 核心内容压缩为一段文字版摘要，发给用户
- 摘要应包含：项目名+版本、一句话定位、当前状态（⏸️/✅）、关键功能清单、下一步待办（仅🔴🟡级别）
- 格式简洁，方便用户口述、笔记、截图保存

### Step 3 — 更新记忆
- 将项目的记忆条目标记为 ⏸️ 已暂停（替换原有条目）
- 清理旧的项目详情记忆（如具体版本号、图片下载记录等），只保留「项目路径 + 恢复方式」
- 恢复方式统一写成：「恢复时发送 HANDOFF.md 即可」

### Step 4 — 清理代码库
- 删除因失败尝试留下的空/损坏文件（如下载中断的 29B 占位文件）
- 确保工作树干净：`git status` 只显示有意提交的变更

## Codex CLI Handoff Prompt — 面向代码Agent的交付文档

### 用途

当用户说"给Codex一个prompt"、"交付给Codex来重写"、"写一个给AI的prompt"时，产出 **prompt-for-codex.md**。它不是HANDOFF.md（项目状态快照），而是一份**让另一个AI Agent直接开始编码的完整brief**——包含产品战略、用户画像、功能规格、设计系统、技术约束、不可动边界。

### 与HANDOFF.md的区别

| 维度 | HANDOFF.md | prompt-for-codex.md |
|------|-----------|-------------------|
| 读者 | 人类/任何AI接手 | Codex CLI / Claude Code 等编码Agent |
| 目的 | "理解项目现状" | "直接开始编码" |
| 内容重点 | 当前状态、已知坑点、下一步 | 产品战略、功能规格、设计约束、技术边界 |
| 语言 | 中文（面向用户和中文AI） | 英文（Codex CLI等编码agent更擅长英文指令） |
| 格式 | Markdown文档 | 自包含的Markdown，可直接喂给CLI |

### 模板结构

```
# [Project Name] — Full Rewrite Brief for Codex CLI

## 1. Repository
GitHub URL, live URL, current version, default branch, push instructions

## 2. Product Strategy
Vision, target users, value proposition, explicit trade-offs (what NOT to do)

## 3. Product Capabilities
Current system capabilities: models, algorithms, data sources, API endpoints (all must be preserved)

## 4. Feature Requirements
Per-page/modal specs — purpose, must-display, design notes, interaction patterns

## 5. Architecture
Frontend + backend architecture diagrams, data flow, file structure for the rewrite

## 6. Design System
Color palette, typography, spacing, component library, interaction patterns

## 7. Do NOT Touch (硬边界)
Explicit list of files/modules that must not be modified, with reasons

## 8. Test Requirements
Which tests must pass, what to update if routes change

## 9. Success Criteria
How to verify the rewrite is complete

## 10. Deliverables
Checklist of what must be done before marking complete
```

### 编写原则

1. **产品深度优先** — 用户纠正过：「将产品规划和需求和能力写清楚」。不要只写技术架构，要把以下三块写透：
   - **产品规划（Product Strategy）**：产品Vision一句话、目标用户细分类表（痛点+当前替代方案）、核心价值主张（Before/After对比）、明确的取舍边界（不做什么、为什么）
   - **需求（Requirements）**：每个页面/模块的Purpose+Must Display列表+Design notes。不是列功能名，而是描述用户进入这个页面看到什么、能做什么
   - **能力（Capabilities）**：当前系统的算法能力、数据源、API端点——Codex需要知道现有系统的能力边界才能正确重写
   写完后检查：「如果Codex只读这个prompt、不看项目代码，能写出正确的产品吗？」

2. **边界精确** — 用户纠正过「不需要wc26nami项目」（排除不相关的兄弟项目）。在prompt中必须把「要改什么」和「别碰什么」都列清楚。每一条Do NOT Touch都要给理由（测试逻辑不动、框架依赖不动、数据管道不动）。

3. **自包含+0歧义** — Codex CLI不会追问。prompt里漏掉一个功能，它就不会实现。每个页面、每个API、每个约束都要写全。不要假设Codex了解你的项目。

4. **技术约束显式化** — Vercel部署、零pip依赖、代理配置、Git分支名、推送命令——这些Codex不知道的本地环境约束必须逐条写清楚。

5. **英文写作** — 面向Codex CLI的prompt用英文。产品名、专有名词、API路径保持原样即可。

6. **不做过度设计** — 不要写「未来可能XXX」的路线图。只聚焦当前重写的范围。

7. **交付标准明确** — 要有Success Criteria节，包含可验证的条目（测试全绿、API响应200、响应式验证等）。

## 衍生模式：AGENT_MEMORY.md — AI Agent 用户/项目入职文档

### 用途

当用户说"给别的AI agent写一个我的memory"或"为其他agent写一个项目介绍"时，产出 **AGENT_MEMORY_<Project>.md**。它不是项目状态快照（那是 HANDOFF.md 的职责），而是一份**面向其他AI Agent的入职文档**——帮助新agent在几分钟内理解这个项目的用户、产品、架构和工作风格，零返工地开始干活。

### HANDOFF.md vs AGENT_MEMORY.md

| 维度 | HANDOFF.md | AGENT_MEMORY.md |
|------|-----------|----------------|
| **定位** | 项目状态快照 | AI Agent 入职指南 |
| **读者** | 人类/另一个AI接手项目 | 另一个AI Agent第一次接触这个项目和用户 |
| **内容重点** | 当前功能、API、坑点、下一步 | 用户画像、沟通模式、项目拓扑、设计约定 |
| **更新频率** | 每次暂停/交接时 | 用户画像或项目架构有重大变化时 |
| **保存位置** | 项目根目录 `HANDOFF.md` | 项目根目录 `AGENT_MEMORY_<Project>.md` |

### 模板结构

```
# [项目名] 用户记忆 — 给其他 AI Agent
> 一句话产品简介 | 最后更新：[日期]

## 用户画像 — 技术/业务背景、沟通风格、工作节奏偏好、语言偏好
## 项目拓扑 — 每个子系统一张表（GitHub/在线地址/技术栈/功能/部署）
## 设计约定 — 界面语言、视觉风格、PM文档规约、版本号管理
## 已知边界 — 待办/问题/部署限制
## 沟通模式 — 用户习惯的指令风格、回复模式
```

### 编写原则
1. **以用户为中心** — 不是讲项目功能，而是讲"怎么和这个用户合作这个项目"
2. **自包含且简洁** — 新AI看这份文件+读HANDOFF.md就能直接上手
3. **沟通模式必须写** — 极简指令/信任判断/频繁确认等模式，最能加速新AI上手
4. 保存到项目根目录，不push到GitHub（除非用户要求）——这是AI之间的上下文文档

## 与相关文件的区别

| 文件 | vs HANDOFF.md | vs AGENT_MEMORY.md |
|------|---------------|--------------------|
| CHANGELOG.md | 记录"改了什么" | 不相关 |
| PLAN.md | 规划"下一步做什么" | 不相关 |
| README.md | 给人类看的产品介绍 | 给AI看的用户入职指南 |
| PRD | 产品战略 | 不相关 |
| AGENT_MEMORY.md | 项目状态快照 | 用户+项目入职指南（本skill） |

## 参考文件

- `references/visepanda-handoff-example.md` — VisePanda 项目交接示例 (v3.0.1)
- `references/wc26-resume-example.md` — WC26 续写项目恢复流程示例（含验证差异的实际记录）
- `references/agent-memory-visepanda-example.md` — VisePanda AGENT_MEMORY 示例（面向其他AI的入职文档）
- `references/codex-handoff-wc26-example.md` — WC26 交付Codex CLI的prompt示例（含产品战略+设计系统+技术约束）
