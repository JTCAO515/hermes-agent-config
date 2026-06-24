# Brain-to-Plan Pipeline

从创意发散到可执行迭代规划的完整工作流。适用于 VP-Hermes 类产品功能规划。

## Pipeline 概览

```
Brainstorming (3视角15功能) → Priority排序TOP 5 → Grill 压力测试 → PLAN.md + ADRs → Batch实现
```

## 详细步骤

### Step 1: Brainstorming（发散）

使用 brainstorming skill 的 A/B 模式：
- **PM 视角** — 业务价值、增长、商业化（5 个）
- **Designer 视角** — 体验升级、交互、视觉（5 个）
- **Engineer 视角** — 技术能力、性能、扩展（5 个）

每视角需要包含：名称 + 描述 + 用户价值 + 实现成本。

### Step 2: 优先级排序（收敛）

跨视角排序后输出 TOP 5，排序依据：
1. 战略对齐 — 是否匹配产品定位
2. 用户影响 — 多少用户受益、提升有多大
3. 技术可行性 — 现有架构能否支撑
4. 差异化 — 竞品有没有、用户能不能感知

同时标注「不推荐现在做」的功能，说明原因。

### Step 3: Grill 压力测试

用 grill-with-docs 或 decision-mapping skill 对计划进行压力测试。
针对每个 Batch 问 3-5 个「尖锐问题」：

- 冷启动场景下用户看到什么？
- 数据来源可靠吗？缺字段容错怎么做？
- MVP 范围怎么切？不做什么？
- 并行依赖关系：Batch A 是否等 Batch B？

### Step 4: 写 PLAN.md

项目根目录的 PLAN.md 包含：
- 总体策略（一句话方向）
- 分 Batch 详情：目标 / 范围 / 不做 / 工时 / 版本 / 依赖
- 开发顺序图（ASCII 依赖图）
- 验证门禁清单

### Step 5: 写 ADRs

每个关键决策一个独立的 ADR 文件：`docs/adr/000N-title.md`
ADR 结构：Context → Decision → Consequences

哪些需要 ADR：架构变更、数据存储策略、外部依赖、MVP 范围切分。

### Step 6: 按 Batch 执行

从依赖树最底层的 Batch 开始实现。完成后更新版本号 → git push → 验证部署。

## 注意事项

- 「要文字版的」 — 用户偏好文字版规划，不要炫技格式
- 每 Batch 独立可部署、可验证
- 不要在 PLAN.md 中写具体代码实现（那是 IMPLEMENT.md 的内容）
