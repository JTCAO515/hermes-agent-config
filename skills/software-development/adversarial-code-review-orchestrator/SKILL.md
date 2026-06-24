---
name: adversarial-code-review-orchestrator
description: "异构多模型对抗式代码审查编排器。三阶段流水线：Reason→Route→Refine。模拟三个基座大模型（Backend/Security、Frontend/UX、Product/Business QA）独立审查后交叉验证。"
version: 1.0.0
author: Hermes Agent
tags: [code-review, adversarial, multi-model, security, architecture, quality]
---

# 异构多模型对抗式代码审查

> **哲学**：单一模型的顺从性幻觉是代码审查的最大敌人。通过"物理多模型路由 + 交叉验证"暴露致命缺陷。

## 适用场景

- 高风险的代码合并（金融、安全、底层算法）
- 新功能模块第一次提交
- 架构重构或重大变更
- 你刚写完自己觉得"挺完美"的代码（这种最危险）

## 三阶段流水线

### Phase 1: Reason-then-Select（智能分发）

收到代码后，**不要立即审查**。先推理：

1. **代码意图分析**：这段代码的核心业务逻辑是什么？技术栈？
2. **专家子集选择**：动态决定需要调用哪些模型视角
3. **上下文依赖检查**：是否需要额外信息（API 文档、DB Schema）？

### Phase 2: Heterogeneous Model Routing（异构模型独立扫描）

模拟以下三个认知偏好的模型视角，**独立**给出诊断意见：

#### 🔴 模型 A — Backend/Security

**人格设定**：见过无数线上 P0 故障的后端总监。所有未经验证的外部输入都是恶意攻击。

**审查焦点**：
- SOLID 原则违反
- 并发安全（竞态条件、死锁）
- 内存泄漏、资源未释放
- SQL 注入、NoSQL 注入
- 越权访问、权限校验缺失
- 分布式事务、数据一致性
- 异常处理（网络/IO/超时）
- 输入验证（所有源头）

**输出风格**：每句都直指具体行号和代码路径。

#### 🟠 模型 B — Frontend/UX

**人格设定**：被奇葩用户输入折磨过的前端老兵。极度反感脆弱的 DOM 操作和不安全的 API 调用。

**审查焦点**：
- 渲染性能（重排/重绘）
- 状态管理合理性
- XSS/CSRF 防护
- 边界 UI 表现（空状态、错误态、极限值）
- 无障碍（A11y）
- 响应式兼容性
- API 调用安全（token 暴露、请求拦截）

#### 🟡 模型 C — Product/Business QA

**人格设定**：总是因边缘场景给用户赔礼道歉的产品经理。不关心代码多优雅，只关心出错时系统会不会死锁或丢数据。

**审查焦点**：
- 业务逻辑死胡同
- 异常流处理缺失
- 用户体验降级方案
- 偏离需求 Spec
- 数据完整性（部分写入、重复提交）
- 回滚/补偿机制
- 用户误操作防护

### Phase 3: Consensus & Arbitration（共识裁决）

作为 **Chief Architect** 执行仲裁：

#### 置信度分级

| 级别 | 条件 | 动作 |
|------|------|------|
| 🔴 **Critical** | ≥2 个模型共识 或 涉及严重安全/架构缺陷 | **必须阻断**，提供修复代码 |
| 🟡 **Warning** | 特定条件下成立的风险 | 建议重构或补充防御 |
| 🟢 **Nitpick** | 仅 1 个模型提出，审美或过度设计 | **直接丢弃，不展示** |

#### 争议焦点复盘

如果两个模型的意见冲突（如：前端说接口慢是后端问题，后端反驳是前端请求不合理），由 Chief Architect 结合代码给出最终定论。

## 输出格式

```text
══════════════════════════════════════════
  [VERDICT] ALLOW / ALLOW_WITH_CONDITIONS / DENY
══════════════════════════════════════════

📊 Executive Summary
  代码健康度: 7/10
  核心结论: (一句话)

🔴 Top Risks (Critical — 必须修复)
  [CRITICAL] file.py:42
    问题: (描述)
    修复: (方案或代码)

🟡 Warnings (Warning — 建议修复)
  [HIGH] file.py:88
    问题: (描述)

🔄 Debate Focus (争议复盘)
  模型A 认为... 但 模型C 指出... 最终结论: ...

💾 Refactored Snippet
  (仅 Critical 级别提供 diff 或重写代码)
```

## 严格约束

- **绝对禁止**："赋能、抓手、闭环、链路、综上所述、至关重要"——一个词都不许出现
- **绝对禁止**："这段代码整体不错，但是..."、"作为一个AI模型..."
- **每段批评必须有具体函数名或逻辑分支**，空洞的泛泛之谈直接删掉
- **必须找出至少一个优化点**，不许给自己写的代码满分

## 多轮审查反馈循环（Review Feedback Loop）

当审查发现被修复后，**必须回读验证**。本实践源于 TXPokerAssist v4.0→v4.1 的真实数据：

| 轮次 | 操作 | GLM findings | DeepSeek findings |
|------|------|:------------:|:-----------------:|
| 原始审查 | 首次运行 | 40 | 10 |
| v4.0 修复 | 修 20+ 问题后重审 | **33** (↓7) | **19** (↑9) |
| v4.1 修复 | 再修 26 问题 | 审查完成 | 审查完成 |

**核心观察：**
- 修复后的第二次审查**不是**简单地数量下降 —— GLM 从 40 降到 33（共识问题少了），但 DeepSeek 从 10 **升到** 19（发现了新问题）
- 原因：模型在不同时间/上下文下对同一代码的审查视角不同。第一次遗漏的问题在第二次被捕获
- 结论：**坏消息不是「修复后还有问题」，而是「修了一轮就不再审了」**

### 标准流程

1. **V0 审查** — 运行 `--rounds all` 获取基线
2. **V0 修复** — 按 CRITICAL→HIGH→MEDIUM→LOW 修复
3. **V1 审查** — 运行 `--summary-only` 确认修复 + 检查新发现
4. **V1 修复** — 修复新发现的问题
5. **循环** — 直到关键问题数为 0 或收敛
6. **产出** — 每个循环一个 git tag（v4.0, v4.1, ...）

### 收敛判断

问题收敛的判据：
1. 连续两轮审查中无新 CRITICAL/HIGH 发现
2. 剩余发现均为 MEDIUM/LOW（已知未修复项）
3. ROADMAP 中已无 HIGH 项

满足以上条件时，审查期结束，进入功能迭代期。

## 与现有审查工具的区别

| 维度 | requesting-code-review | adversarial-code-review-orchestrator |
|------|----------------------|--------------------------------------|
| 视角 | 单代理独立审查 | 三模型对抗交叉验证 |
| 焦点 | pre-commit 质量门禁 | 架构缺陷 + 安全 + 业务逻辑盲区 |
| 输出 | pass/fail 判定 | 分级风险 + 争议复盘 + 修复代码 |
| 适用 | 日常提交 | 高风险合并 / 首次审查 / 重构 |

## 实际脚本 vs SKILL.md 差异

本 skill 描述的 3 模型人格化流程（Backend/Security、Frontend/UX、Product QA）是"理想设计"。实际实现的 `adversarial_review.py` 采用 **批次化 2 模型架构**：

| 维度 | 设计 | 实现 |
|------|------|------|
| 模型数量 | 3（人格化） | 2（GLM 5.1 + DeepSeek V4 Flash） |
| 文件组织 | 按专家视角跨文件 | 按文件分组为批次（每批 2-3 文件） |
| 路由逻辑 | 文件→专家子集 | 全量发送给两个模型，独立评审 |

两种方式各有优劣。**批次化方案的参考实现参见 `references/batch-review-pattern.md`**。

## Post-Deployment Hotfix Pattern

审查不能捕获所有 bug — 有些问题只在生产环境触发。TXPokerAssist v4.1 后修复的 pot=0 ZeroDivisionError 就是典型：

| 阶段 | 事件 |
|------|------|
| 审查 | GLM 发现 `_raise_reasoning` 有除零风险（标注为 MEDIUM） |
| 修复 | 标记为 MEDIUM 推迟到 v4.1，未立即修 |
| 上线 | 用户使用 pot=0 的输入时触发 500 |
| 热修复 | 立即加 `if pot > 0` 守卫，顺手修了另两处除零和 SPR=inf 序列化 |

**教训：** 格式化输出中的除零不容忽视——它看起来是 MEDIUM 排版问题，但在线用户真实触发时会直接 500。

### 热修复流程

1. **收到用户报错** → 先用 `fastapi.testclient` 复现（无法复现时问用户的精确输入）
2. **定位根因** → `_raise_reasoning` 中 `raise_amt/pot` 在 `pot=0` 时 ZeroDivisionError → `_ev_raise` → `analyze` → API 500
3. **修复目标** → 阻断除零链条，不修算法本身
4. **连带排查** → 搜索同类模式：所有 `f"{x/y}"`、`x / (y - z)`、`x / max(1, y)` 等
5. **修复后** → 运行完整测试 + 边缘场景扫描 + `git push`
6. **ROADMAP 标记** → 热修复的 commit 也写入下一版 ROADMAP 的修复清单

### 热修复检查清单

检查项目 `game_theory.py` 和 `decision_engine.py` 中所有除法：
- [ ] `f"{x/y}"` 格式字符串 — 加 `if y > 0` 守卫
- [ ] `x / (y + z)` 模式 — 加 `if total > 0` 守卫
- [ ] `float('inf')` 输入 API 响应体 — 用 `0.0` 或 `null` 替换
- [ ] `_calculate_spr(stack, pot)` 返回 inf — 调用处处理
- [ ] 两端同时为 0 的场景（pot=0, to_call=0, equity=0）

## Predicted Issues from Review Flow

实践中发现一个有趣现象：修复后的二次审查不是简单地数量下降。

原始 TXPokerAssist v4.0 审查：
- GLM: 40 findings → 修后 33 (↓7)
- DeepSeek: 10 findings → 修后 19 (↑9)

DeepSeek 发现反而增多了，因为它第一次没认真看（质量波动），第二次换了批次上下文后发现了新问题。

**实用建议：** 不要只看总数趋势。如果某个模型发现数上升，说明它开始覆盖之前遗漏的区域——这恰恰是审查有效的标志。如果两个模型都下降，才说明真正收敛。

## Pitfalls

- **循环自比（circular self-reference）**：当预测/推荐系统的"市场赔率"和"模型预测"来自同一引擎时，所有推荐结果呈现虚假一致性。WC26 v4.0 中，`daily_picks.py` 的 EV 全部锁定在 +5.1%、评级统一 C — 根因是模型赔率由系统自身的 bivariate Poisson 生成 + 统一 5% 抽水，循环自比导致无差异化。**破解方法**：构建独立市场赔率模型（ELO+公众偏好+差异化抽水），让 market_odds 和 model_probs 来自两个不共享参数的引擎。审查时检查"对比的另一半数据来源是否独立于数据生成方"。
- **代码太长**：分段发送（每批 2-3 文件，~15K chars），否则被截断或模型返回空响应
- **模型响应非 JSON**：用正则提取 `{...}` 块，二次校验。DeepSeek 推理模型把内容放 `reasoning_content` 而非 `content`，参见 `references/provider-quirks.md`
- **`merge()` 函数设计约束**：接受 `list of lists`（每批一个内层 list），不接受扁平 `list of dicts`。如果 `generate_summary` 直接传扁平 findings 给 `merge()`，所有条目因 `isinstance(findings, list) == False` 被跳过 → 汇总显示为 0。**修复方法**：在汇总时用 inline dedup（`seen = set(); unique = [f for f in all_findings if not (key in seen or seen.add(key))]`）代替 `merge()`。
- **`--summary-only` 模式可用**：`python adversarial_review.py --summary-only` 读取已有 JSON 结果文件（`reports/review_*.json`）生成汇总+交叉对比，不调用 API。适合快速复查。确保结果文件存在（运行完整审查一次后）。
- **empty findings ≠ 没缺陷**：模型可能偷懒，需要显式要求"至少找出一个优化点"
- **意见冲突是好信号**：说明该问题有深度，需要人工介入
- **不要跳过 Nitpick 过滤**：单模型噪音会淹没真正的问题
- **非确定性警告**：同一批次同一模型的审查结果在不同运行中可能不同（GLM 在同一代码上先后产出 40 vs 33 个发现，DeepSeek 从 10 → 19 个）。应关注"已修复"而非"计数归零"。
- **单模型模拟多视角的局限性**：当没有多模型 API Key（delegation 未配置）时，只能用一个模型模拟三个专家视角（Backend/Frontend/QA）。这比真正的多模型交叉验证弱很多——单个模型的自洽性幻觉无法被另一个模型打破。**对策**：(1) 审查时先明确声明这是单模型审查，标注置信度 (2) 用探针脚本验证审查发现，不要只依赖审查报告 (3) 优先为 delegation 配置至少两个不同 providers 的 API Key
- **fold_equity 误用模式**：一个常见的审查发现是「把 break-even 值当成实际值传入公式」。典型例子：计算 raise EV 时，先把 `_required_fold_equity()` 求出的**盈亏平衡点**弃牌率作为 `fold_equity` 参数传入 `_ev_raise()`，导致 EV 永远 ≈ 0。正确做法：用另一个参数（如从对手画像估算的 33%）作为 actual FE，保留 break-even FE 仅用于"所需弃牌率"显示。审查脚本需要显式检查调用链中的参数语义。
- **IndexError + wheel detection**：当牌面有 A 时，添加 A=1 作为 wheel 检测会使 rank 集合比原始集合多一个元素。如果外层循环遍历 wheel-set 而内层代码仍然访问原始 rank-set 的边界索引，会导致 IndexError。审查时重点检查「两个不同大小集合的循环边界是否对齐」。
- **多对手 fold_equity**：单对手弃牌率和多对手联合弃牌率有本质区别（联合概率 = 乘积）。如果 EV 公式假设单对手而实际是多对手场景，弃牌率被高估。审查时应检查 `fold_equity` 的使用处是否有 `num_opponents` 参数。
- **格式化输出除零风险**：EV/博弈分析代码常在格式化字符串中计算比值（如 raise_amt/pot 或 action.amount/pot）。当 pot=0 时，ZeroDivisionError 在字符串格式化时引发。审查时检查所有 f"{x/y}" 格式的字符串是否有分母保护。
- **SPR=inf 导致 JSON 序列化失败**：当 pot=0 时，SPR 计算为 float('inf')。直接填入 API 响应体后 JSON 序列化报 Out of range float，浏览器收到空响应。修复：输出时 spr if spr != inf else 0.0。审查时检查响应体中有无 inf/-inf/NaN 未被处理。
- **Python WSGI wsgi.input bytes/str 兼容性**：在 Vercel/Gunicorn 生产环境中 `environ["wsgi.input"].read(length)` 返回 bytes（有 `.decode("utf-8")` 方法），但用 `StringIO` 做 WSGI 测试时返回 str（无 `.decode()`）。修复：`if isinstance(raw, bytes): raw = raw.decode("utf-8")`。审查 API 的 `_read_post_json` 类函数时检查是否兼容两种类型。
- **checkbox?.checked !== false 陷阱**：`element?.checked` 在 element 不存在时返回 `undefined`。`undefined !== false` 求值为 `true`，导致"checkbox 不存在"被当作"已勾选"。审查时检查 checkbox 相关逻辑的默认值意图：`(element?.checked ?? true)` 显式声明默认值。

## 参考文件

- `references/provider-quirks.md` — 各 LLM 提供者（DeepSeek / GLM / GPT）在代码审查场景中的异常行为记录
- `references/batch-review-pattern.md` — 批次化 2 模型审查的实际实现模式：批次定义、汇总逻辑、交叉对比算法
- `references/frontend-security-checklist.md` — 前端 XSS 防护、DOM 性能优化、AbortController、0||陷阱 的检查清单和修复模式
- `references/data-accuracy-probes.md` — 数学/数据模块探针编写：赔率验证、EV/Kelly 边界、策略差异化、API 数据完整性、资金边界
