---
name: user-story-mapping
description: >
  用户故事地图。从用户旅程出发，结构化拆分Epic→Feature→User Story。
  触发词：用户故事/user story/故事地图/backlog/需求拆分/epic。
version: 1.0.0
---

# 用户故事地图

## 流程
1. **确定用户角色** (Persona)
2. **绘制用户旅程** (Journey Map): 阶段 → 活动 → 任务
3. **分解为 Epic** (按阶段分组)
4. **每个 Epic 拆 Feature** (按活动)
5. **每个 Feature 拆 User Story** (As a... I want... So that...)

## 输出模板
```
Epic: [名称] (优先级 P0-P3)
├── Feature 1: [名称]
│   ├── US-01: As a [角色], I want [功能], so that [价值]
│   │   验收: Given/When/Then
│   └── US-02: ...
└── Feature 2: ...
```

## 优先级规则
- P0: 没有它产品不可用 → MVP必须
- P1: 显著影响核心体验 → V1.0
- P2: 锦上添花 → V1.1
- P3: 远期愿景 → Backlog
