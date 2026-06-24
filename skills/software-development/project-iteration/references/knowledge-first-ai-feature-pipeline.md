# Knowledge-First AI Feature Pipeline

> 从 VisePanda v3.0.1 迭代模式提炼。适用于所有「AI 助手 + 领域知识库」类产品。

## 核心模式

把每一次功能迭代组织成四层流水线，自上而下推进：

```
Layer 1: DATA   → 知识数据层（JSON/Python dict）
Layer 2: INJECT → Prompt 注入层（system prompt 增强）
Layer 3: UI     → 展示交互层（卡片/列表/详情/地图）
Layer 4: PERSIST → 持久化层（localStorage/项目数据库）
```

## 四层详解

### Layer 1 — DATA（知识数据层）

**做什么**：构建/扩充领域知识的 JSON 数据结构。

```python
# 典型模式：嵌套 JSON，每层独立文件
data/
  cities.json     # 城市元数据（名称/省份/季节/天数/vibe）
  food.json       # 美食（名称/描述/价格/must_try）
  hotels.json     # 酒店（三档/价格/区域/建议）
  tips.json       # 贴士（文化/交通/安全）
  tools.json      # 工具（打包/价格/签证/语言/紧急）
```

**原则**：
- 每层独立文件，避免一个巨型 JSON 文件
- key 名保持一致（`city_name` → `food[city_name]` → `hotels[city_name]`）
- 添加 Python 一致性验证脚本（`scripts/verify-knowledge-consistency.py`）

### Layer 2 — INJECT（Prompt 注入层）

**做什么**：把知识数据注入到 LLM 的 system prompt 中。

```
用户输入城市 → detectCity() → API 检测城市名
  → _build_system_prompt() → 加载对应 JSON 数据
  → 注入结构化知识（城市信息 / 美食 / 酒店 / 贴士 / 价格估算）
  → LLM 用具体数据产生回复
```

**模式**：
- 惰性加载：仅在用户提及城市时才加载对应数据
- 结构化格式：注入数据用 Markdown 表格/列表，LLM 解析最稳
- 分块注入：城市概览 → 美食 ⭐推荐 → 酒店三档 → 贴士 → 价格估算
- 兜底：未检测到城市时只给通用旅行建议

### Layer 3 — UI（展示交互层）

**做什么**：把知识数据以可视化形式展示给用户。

```
三种展示模式（可组合）：
1. 卡片网格：cities grid / trips grid / tools grid
2. 详情模态框：food items / hotel tiers / tips list
3. 地图标注：Leaflet 暗色地图 + POI 分类标记
```

**数据流**：`API /api/cities/:city` → 返回完整数据(含 map/estimate) → 前端 renderCityDetail() → 分节展示

### Layer 4 — PERSIST（持久化层）

**做什么**：把 AI 生成的内容保存为用户可复用的资产。

```
自动保存：
  Llama 回复 → autoSaveTrip() 检测行程模式（Day N / 列表 / emoji）
    → structed Trip { id, city, title, content, days, created }
    → localStorage.setItem('vp_trips', ...)
    → save-note UI 提示 + Trips Tab 可见

手动管理：
  列表视图 → Load(恢复对话) / Share(Clipboard) / Delete
```

## 迭代节奏

```
典型一次迭代覆盖 2-3 层：
  Iter N-1: Data 层（新增城市/美食数据）
  Iter N:   Inject + UI 层（注入新数据+展示）
  Iter N+1: Persist 层（持久化新功能）
```

VisePanda v3.0.1 7 轮迭代的实际节奏：
- Iter 1: 骨架（基础架构）
- Iter 2-3: Data + Inject（知识库导入 + Prompt 增强）
- Iter 4-5: UI（体验打磨 + 响应式 + 多轮对话）
- Iter 6-7: Persist + 深度增强（行程持久化 + Leaflet 地图 + 价格估算）

## 适用场景

- AI 旅行规划（VisePanda 模式）
- AI 餐厅推荐
- AI 酒店比价
- AI 攻略/指南类应用
- 任何「大模型 + 领域知识库」组合

## Pitfalls

- ❌ 一次迭代覆盖全部 4 层 → 变更太大，commit 风险和退
- ❌ JSON 数据层不独立 → 全部内联在 API 文件 → 数据更新要改代码
- ❌ 注入数据不结构化（纯 JSON dump）→ LLM 理解差，回复质量低
- ❌ UI 层与 API 硬编码 → 新增知识类型要改前端代码
