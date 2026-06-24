# Product Plan Example: 国标麻将决策助手 (PLAN.md)

> This is a reference file capturing the full 19-section PLAN.md structure from a real session.
> Use it as a template for future product plan documents.

## Session Context

- **User**: 猪猪微
- **Request**: "像之前TXPOKERASSIST一样写的详细" — write a product plan as detailed as the TXPokerAssist one
- **Project**: General Mahjong Assist (国标麻将决策助手)
- **Output file**: `PLAN.md` (23KB, 19 sections)

## Section-by-Section Detail

### 1. Project Vision

```
# [Project Name] — 产品规划 v0.1

## 1. 项目愿景

**一句话**：[core pitch — decision copilot, not calculator]

**不是**：[what it is NOT]

**核心价值主张**：
- Decision explainable: every recommendation with mathematical basis
- Info transparent: show all visible tiles, remaining counts, expected values
- Offline local: no data upload, privacy preserved
```

### 2. Domain Complexity vs Reference

```
## 2. 领域核心复杂度（vs [Reference Project]）

| Dimension | [Reference] | [This Project] | Impact |
|---|---|---|---|
| Player count | 2–10 flexible | Fixed 4 | Dimension fixed |
| Card/tile pool | 52 cards | 136 tiles (34×4) | 2.6× enumeration space |
| Decision granularity | 4 stages | Continuous 13 rounds | Higher sequential complexity |
| Info structure | Hidden + community | Hidden hand + open discards | More complex partial info |
| Scoring | Continuous (pot odds) | Discrete (番数制, 8-88) | Non-linear strategy |

Key differences:
1. [diff 1]
2. [diff 2]
3. [diff 3]
```

Always contrast against a familiar system (TXPokerAssist for poker tools). Use a structured table, not prose.

### 3. Core Decision Points

```
## 3. 核心决策点（N 类）

| Decision | Trigger | Goal | Model | MVP |
|---|---|---|---|---|
| **A. [Name]** | [When] | [What] | [How] | P0 ✅ |
| **B. [Name]** | [When] | [What] | [How] | P1 |
```

List all decisions the system must support. Mark current status (✅/❌) for each.

### 4. Target Users

```
## 4. 目标用户

| User segment | Pain point | Priority |
|---|---|---|
| [Primary] | [Core pain] | P0 ⭐ |
| [Secondary] | [Secondary pain] | P1 |
```

Keep it to 3-5 segments max. Each must have a distinct, verifiable pain point.

### 5. Feature Framework

```
## 5. 功能框架

### 5.1 Core Features (P0)
| Feature | Description | Status |
|---|---|---|
| [Feature] | [Description] | ✅ / Pending |

### 5.2 Enhancement Features (P1)
| Feature | Description | Priority |
|---|---|---|
| [Feature] | [Description] | P1 ⭐ |

### 5.3 Advanced Features (P2)
| Feature | Description | Priority |
|---|---|---|
| [Feature] | [Description] | P2 |
```

### 6. Feature Progress (if applicable)

```
## 6. 番种实现进度 / Feature Completion

| Category | Total | Done | Gap |
|---|---|---|---|
| [Category] | N | M | [list gaps] |
| **Total** | **81** | **76** | **5** |
```

Include a table of remaining gaps with difficulty + implementation plan.

### 7. Data Model

```
## 7. 数据模型

### 7.1 Core Entity
```
[Entity] {
  fields...
}
```

### 7.2 Request/Response Schema
```
[Request] {
  fields...
}

[Response] {
  fields...
}
```

Include full JSON schemas for all core entities. Not "similar to X" — actual field names and types.

### 8. Algorithm Architecture

```
## 8. 算法架构

### 8.1 Module Dependency Graph
```
[A] → [B] → [C]
  ↘    ↓
    [D]
```

### 8.2 [Algorithm 1]
```
def algorithm(...):
    # Step 1: ...
    # Step 2: ...
```

Include pseudocode for all non-trivial algorithms. Focus on the key insight, not boilerplate.

### 9. API Design

```
## 9. API 设计

| Endpoint | Method | Function | Input | Output | Status |
|---|---|---|---|---|---|
| /api/health | GET | Health check | — | {status} | ✅ |

### 9.1 Request Example
```json
{
  "hand": [0, 1, 2, ...]
}
```

### 9.2 Response Example
```json
{
  "result": {...}
}
```

Include actual request/response examples with realistic data.

### 10. Frontend Design

```
## 10. 前端设计

### 10.1 Page Layout (ASCII)
```
┌──────────────────────────────────────────┐
│  Header                                  │
├──────────────────────────────────────────┤
│  ┌─ Section 1 ─────────────────────────┐ │
│  │  Content                             │ │
│  └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### 10.2 Interaction Details
- Click → action
- Long press → action
- Responsive breakpoints

Include an ASCII wireframe for the main page. Layout should be precise enough that someone could implement from it.

### 11. Tech Stack

```
## 11. 技术栈

| Layer | Choice | Rationale |
|---|---|---|
| Backend | FastAPI | Async + auto docs + type hints |
| Algorithm | Pure Python stdlib | Zero external deps |
| Frontend | HTML + CSS + JS | Zero dep, lightweight |
| Deploy | Vercel WSGI | Proven (world-cup-edge-lab pattern) |

### 11.1 Dependency Analysis
```
requirements.txt:
- fastapi
- uvicorn[standard]
```

### 12. Iteration Roadmap

```
## 12. 迭代路线图

### Phase 1: [Name] ✅ Completed
| Iter | Content | Status |
|---|---|---|
| 001 | [Content] | ✅ |
| 002 | [Content] | ✅ |

### Phase 2: [Name] (Current → Next)
| Iter | Content | Priority |
|---|---|---|
| 007 | [Content] | P0 ⭐ |
| 008 | [Content] | P1 |
```

### 13. ADRs

```
## 13. 关键工程决策

### ADR-001: [Title]

- **Decision**: [What was chosen]
- **Rationale**: [Why]
- **Trade-offs**: [What was given up]
- **Impact**: [Measurable effect]
```

Include 3-5 key decisions. Each should have clear context, decision, and trade-offs.

### 14. Non-goals

```
## 14. 非目标（Phase 2 不碰）

| Feature | Reason | V2 candidate |
|---|---|---|
| [Feature] | [Why not now] | ✅ / ❌ |
```

Explicit "we won't build this now" — prevents scope creep.

### 15. Acceptance Criteria

```
## 15. 验收标准

### MVP Acceptance
| Criteria | Method | Status |
|---|---|---|
| [Criterion] | [How to verify] | ✅ |

### Phase 2 Acceptance
| Criteria | Method |
|---|---|
| [Criterion] | [How to verify] |
```

Each criterion must be quantifiable and verifiable.

### 16. Known Risks & Mitigations

```
## 16. 已知风险与缓解

| Risk | Prob | Impact | Mitigation |
|---|---|---|---|
| [Risk] | Med | High | [Strategy] |
```

### 17. Competitive Analysis

```
## 17. 竞争分析

| Product | Position | Difference |
|---|---|---|
| [Product] | [Positioning] | [Key difference] |
```

### 18. Quick Start

```
## 18. 快速开始

```bash
cd ~/projects/[project]
pip install -r requirements.txt
bash start.sh   # → http://localhost:PORT
pytest -q       # N tests
```
```

### 19. Appendix

```
## 19. 附录：[Topic]

[Reference table, taxonomy, glossary]
```

## Formatting Rules

1. **Tables everywhere** — structured data belongs in tables, not prose
2. **Code blocks for schemas** — JSON, not natural language
3. **ASCII for layouts** — wireframes, not descriptions
4. **Status badges** — ✅ / ❌ / P0 / P1 everywhere
5. **No filler** — every section must earn its place

## Key Opening Decision

When the user says "写一个产品规划" / "像 TXPokerAssist 一样详细":

1. Read the TXPokerAssist ITERATION_LOG.md or world-cup-edge-lab PLAN.md for format reference
2. Investigate the current project state (search_files, git log, test count)
3. Write PLAN.md with all 19 sections, adapting the template to the specific project
4. If the user then asks for iteration plan, offer to write ITERATION_PLAN.md immediately
