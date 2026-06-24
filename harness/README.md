# Harness Engineering — 已配置组件

> Harness Engineering = 设计 AI Agent 周围的"脚手架"：context 投喂、工具接口、规划制品、验证闭环、记忆系统、沙箱权限。

## 四个核心模板

| 模板 | 用途 | 何时用 |
|------|------|--------|
| **PLAN.md** | 任务规划制。里程碑 + 验证门禁 + 范围边界 | 任何非简单任务开始前 |
| **IMPLEMENT.md** | 实现日志。决策记录、偏离追踪、未决问题 | 执行过程中追加，不修改历史 |
| **AGENTS.md** | 项目级 Agent 指令。工具权限、编码规范、验证门禁 | 放到任意项目根目录 |
| **HARNESS_CHECKLIST.md** | 上线前审查清单。8 大维度逐项检查 | 把 Agent 交给别人用之前 |

## 使用方式

```bash
# 启动新任务
cp ~/.hermes/harness/PLAN.md ./PLAN.md
# 填写 Task / Context / Milestones / Scope

# 执行中记录
cp ~/.hermes/harness/IMPLEMENT.md ./IMPLEMENT.md
# 追加决策和偏离

# 项目初始化
cp ~/.hermes/harness/AGENTS.md ./AGENTS.md
# 填写项目规范
```

## 与现有体系的对应关系

| Harness 概念 | Hermes 对应 |
|-------------|------------|
| AGENTS.md | SOUL.md (agent 人格/规则) |
| Context delivery | Memory 系统 + 文件读写 |
| Tool permissions | SOUL.md 的 Boundaries 章节 |
| Verification loop | `coding-workflow` skill (TDD + 质量门禁) |
| Planning artifacts | PLAN.md + `structured-thinking` |
| Memory / state | Memory 工具 + skill 体系 |
| Sandboxing | 终端沙箱 / 工具白名单 |

## 核心理念

> "Every harness component exists because the model can't do it yet.
>  Document what capability improvement would make it unnecessary."

每个 harness 组件都有一个"退役条件"——记录下什么能力变强后这个组件就不再需要了。

---

*来源: [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering)*
