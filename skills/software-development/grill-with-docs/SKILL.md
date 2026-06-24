---
name: grill-with-docs
description: 压力测试方案 vs 项目领域模型。面试式对话，锐化术语，更新 CONTEXT.md 和 ADR。触发词：grill / 压力测试方案 / 领域建模 / 术语对齐 / context / ADR
---
# grill-with-docs

从 Matt Pocock 的 `/grill-me` + `/grill-with-docs` 技能改编。  
核心思想：**先把方案和已有文档对齐，再动手写代码。**

## 触发条件

用户说以下内容时加载：
- "grill 一下这个方案"
- "压力测试我的计划"
- "帮我理清领域术语"
- "建 CONTEXT.md"
- "写 ADR"
- "领域建模"
- "对齐文档"

## 工作流

### Phase 1: 面试式深度拷问

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

**关键纪律：**
- 一次只问一个问题，等回答再继续
- 如果能通过探索代码库回答问题，不要问用户
- 不要假想用户已确认 — 每步都要确认

### Phase 2: 文档发现

在代码库探索中寻找已有文档：

```
/
├── CONTEXT.md          # 领域术语表
├── CONTEXT-MAP.md      # 多上下文指引（有则说明多 bounded context）
├── docs/
│   └── adr/
│       ├── 0001-xxx.md
│       └── 0002-yyy.md
```

如果项目根有 `CONTEXT-MAP.md`，说明有多个 bounded context，按 map 指引找到各 context 的文档。

**创建规则：** 懒创建 — 只有真正有内容可写时才创建文件。

### Phase 3: 术语锐化 (Ubiquitous Language)

#### 3a — 挑战已有术语表
当用户用的术语和 `CONTEXT.md` 中已有的不一致时，立即指出：
> "你的术语表里 'cancellation' 定义为 X，但你刚才说的好像是 Y — 到底是哪个？"

#### 3b — 锐化模糊语言
当用户使用模糊或 overloaded 术语，提出精确规范术语：
> "你说的 'account' — 是指 Customer 还是 User？这是两个不同概念。"

#### 3c — 具体场景测试
当讨论领域关系时，构造具体边界场景来压力测试：
> "如果一个 Order 有 5 个 LineItem，其中 3 个已发货、1 个取消、1 个待处理 — partial cancellation 在你的模型里怎么表示？"

#### 3d — 交叉验证代码
当用户陈述某个行为时，检查代码是否同意：
> "你的代码 cancel 的是整个 Order，但你刚才说支持 partial cancellation — 哪个是对的？"

#### 3e — 即时更新 CONTEXT.md
每个术语决议后立刻更新 `CONTEXT.md`。不批量积攒。

**`CONTEXT.md` 的边界：**
- ✅ 术语定义（glossary）
- ❌ 实现细节
- ❌ 规格说明
- ❌ 草稿笔记
- ❌ 实现决策

### Phase 4: ADR (可选)

只在**同时满足以下三个条件**时才写 ADR：

1. **难逆转** — 事后改的代价很大
2. **无上下文则令人费解** — 未来的人会问"为什么这么搞？"
3. **真的有取舍** — 存在真正替代方案并选了其一

三条缺一则跳过 ADR。

**ADR 格式：**
```markdown
# {编号}-{标题}

## 状态
提议 / 已接受 / 已废弃

## 背景
为什么要做这个决策？

## 决策
我们决定做什么？怎么做的？

## 理由
为什么选这个方案？其他方案是什么？为什么不选它们？
```

## 实战示例

### 拷问话术库

```
Q: "你说要支持多个 Tenant — 每个 Tenant 的数据是完全隔离的，
    还是共享 Database 但用 tenant_id 区分？我推荐后者作为起点，
    你怎么看？"

Q: "你说的 'User' 在系统里是一个人还是一个 Account？
    如果一个人可以属于多个 Organization，User 和 Organization
    的关系是 N:N, 还是 N:1?"

Q: "你的代码里 Order 有个 status 字段，取值是 pending/confirmed/shipped。
    但你刚才提到 'cancelled' — 这是新状态，还是业务逻辑上的
    从 pending 转换过去？"
```

### CONTEXT.md 输出示例

```markdown
# 术语表

## User
系统中的自然人。一个人一个 User。

## Organization
一组 User 组成的租户。一个 User 可以属于多个 Organization。

## Order
一次购物请求。属于一个 Organization 和 一个 User。
状态: pending → confirmed → shipped
```

### ADR 输出示例

```markdown
# 0001-事件溯源订单

## 状态
已接受

## 背景
订单状态变化复杂，需要审计追踪。

## 决策
使用事件溯源（Event Sourcing）存储订单流。

## 理由
- 需要完整审计日志
- 需要能回放到任意历史状态做分析
- 替代方案：传统 CRUD + audit_log 表 — audit 和业务逻辑分离易不同步
```

## 约束
- 不要一次问多个问题
- 不要替用户做假设
- 术语必须精确到代码级
- CONTEXT.md 只含术语，不含实现
