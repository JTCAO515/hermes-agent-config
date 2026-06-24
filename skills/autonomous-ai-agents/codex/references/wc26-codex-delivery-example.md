# WC26 Edge Lab — Codex Delivery Prompt Example

> **Purpose:** This is the complete delivery prompt used to hand off the WC26 Edge Lab project to Codex CLI for a full rewrite. It demonstrates the "Crafting Delivery Prompts" pattern documented in the `codex` skill.

**Project:** WC26 Edge Lab — 2026 FIFA World Cup prediction & decision platform  
**Target Agent:** Codex CLI (`codex exec --full-auto "prompt"`)  
**Input Size:** ~13KB  
**Result:** v9.0.1 rewrite completed autonomously

---

## 1. Repository

- **GitHub:** `https://github.com/JTCAO515/WC26-Main.git`
- **Live:** `https://worldcup.jtcao.space/`
- **Current version:** v8.0.1
- **Default branch:** `master` (NOT `main`)

> ⚠️ Git push: `https_proxy=http://127.0.0.1:10809 git push origin master`

---

## 2. Product Strategy

### 2.1 Vision

**把专业博彩团队的建模能力，打包成一个普通人也能用的世界杯决策实验室。**

不是"预测黑箱"——而是把模型的思考过程打开：预期进球怎么算的、市场赔率隐含了什么、此时的推荐值是多少、为什么。

### 2.2 Target Users

| Segment | Pain Point | Current Alternative |
|---------|-----------|-------------------|
| 足球数据分析爱好者 | 想用量化方法验证判断，但不会写泊松模型 | Excel表格、手动算xG、零散不可复现 |
| 轻度竞猜用户 | 凭感觉下注，没有系统性的价值判断 | 只看赔率、跟大V、凭直觉 |
| 体育数据学习者 | 想学习预测建模，缺可交互的教学工具 | 读论文太理论、看博主分析不够系统 |

### 2.3 Core Value Proposition

| Dimension | Before | After |
|-----------|--------|-------|
| Match analysis | 看赔率+看阵容+凭经验 | 模型概率 vs 市场概率，量化Edge |
| Recommendation | 主观"这场有戏" | Edge × 置信度 × 数据新鲜度 → 推荐值 0-100 |
| History verification | 凭记忆回顾 | 可复现的回测 + Brier Score 客观评估 |
| Parameter tuning | 拍脑袋换模型 | 面板调参，重新跑就能对比 |

### 2.4 Explicit Trade-offs (不做什么)

- ❌ 不做实时推送/通知
- ❌ 不做用户系统/登录/历史
- ❌ 不做自动数据爬取（现有管道不动）
- ❌ 不接入真实下注平台（法律风险）
- ❌ 不做移动端 App（PWA 就够了）
- ❌ 不要引入任何 Python 第三方依赖（Vercel 冷启动必须快）

---

## 3. Current Capabilities

### 3.1 Models & Algorithms

| Capability | Description |
|-----------|-------------|
| 独立泊松模型 | Per-team attack/defense rating → WDL probabilities |
| 双变量泊松模型 | With shared_lambda for draw correlation |
| Odds de-vig | Remove market margin from Polymarket/The Odds API |
| Recommendation engine | Edge × Confidence × Data freshness → score 0-100 + label |
| Timegate | Data leakage prevention — timestamps block future info leak |
| Backtest engine | Per-checkpoint replay → Brier Score → leak audit |
| Monte Carlo simulation | 2000+ tournament runs → probability distributions |

### 3.2 Data Sources

| Source | Type | Frequency |
|--------|------|-----------|
| FIFA API | Real match results | Every 2h (via proxy :10809) |
| The Odds API | Live betting odds | Every 30min (direct) |
| Polymarket | Prediction market data | Static archive (2.2B volume) |
| wc2026_matches.json | 104 match database | Static (manual update) |
| wc2026_teams.json | 48 team ratings | Static |

### 3.3 Backend APIs (全部保留，不改)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check + version |
| `GET /api/version` | Version info (single source: version.py) |
| `GET /api/wc/predict` | Full prediction report for all matches |
| `GET /api/wc/recent-results` | Latest match results from FIFA data |
| `GET /api/wc/data-consistency` | Data integrity check |
| `GET /api/wc/standings` | Group stage standings |
| `GET /api/wc/knockout` | Knockout bracket + probability tree |
| `GET /api/wc/backtest` | Backtest results + model health metrics |

---

## 4. Frontend Requirements (per page)

### 4.1 Overview (首页)

**Purpose:** 用户的第一屏。先看全局健康度，再决定要不要深入。

**Must display:**
- Top nav: 品牌 logo + "WC26 Edge Lab" + 版本号角标
- Summary bar: 模型类型 / Brier WDL / Brier O/U 2.5 / 数据质量
- Quick stats: 已赛场次 / 总场次 / 最近更新
- 入口卡片矩阵: Standings / Knockout / Predictions / Simulation / Schedule / Comparison
- 状态栏: 最近同步时间、数据新鲜度指示

### 4.2 Standings (积分榜)

**Purpose:** 48队12组，小组排名与出线形势。

**Must display:**
- 小组选择器 (A-L)
- 积分榜表格: 排名/球队/场次/胜/平/负/进球/失球/净胜球/积分
- 出线区域高亮 + 每队预测出线概率
- 响应式: 桌面宽表格，移动端紧凑卡片

### 4.3 Knockout (淘汰赛)

**Purpose:** 淘汰赛对阵表 + 每轮晋级概率。

**Must display:**
- 横向 bracket 流程图
- 每个对阵显示球队名 + 晋级概率%
- 夺冠概率排行
- 已完成的比赛标记结果

### 4.4 Predictions (预测卡片列表 — 核心功能)

**Must display (per match card):**
- 头部: 主队 vs 客队 + 实际比分 (如已赛)
- xG 柱状图
- 概率面板: WDL + O/U 2.5
- 推荐值: 标签 (strong/medium/weak/watch/avoid) + Edge% + 置信度
- 时间线: 开球时间、当前状态
- 过滤器: 按日期/小组/推荐强度/比赛状态

### 4.5 Simulation (蒙特卡洛模拟)

夺冠概率柱状图 / 小组出线概率 / 参数配置 / CSV导出

### 4.6 Schedule (赛程日历)

按日期分组的完整赛程 / 今天高亮 / 小组筛选

### 4.7 Comparison (模型对比)

独立 Poisson vs 双变量 Poisson 并排对比 / Brier Score / 推荐命中率

### 4.8 参数面板 (全局浮动)

模型选择 / shared_lambda 滑块 / lineup_impact 滑块 / risk_modifier 滑块
参数变更后自动刷新所有页面 / 持久化到 localStorage

---

## 5. Architecture Spec

### Frontend

```
web/
├── index.html          # Shell: nav + container + modals
├── app.js              # Router + state manager + API client
├── components/         # Per-module components
├── styles/             # Global + component + responsive CSS
├── lib/                # API client + state + utils
├── sw.js               # Service Worker (保留)
└── manifest.json       # PWA (保留)
```

### Backend

```
api/
├── app.py              # WSGI app factory + CORS + JSON helpers
├── routes/             # Modular route handlers
├── middleware/          # CORS + auth
└── index.py            # Thin entry point
```

---

## 6. Design System

| Token | Value |
|-------|-------|
| Primary | `#5e6ad2` |
| Background | `#0f1117` / `#1a1d27` / `#242738` |
| Text | `#e8eaed` / `#9aa0a6` / `#5f6368` |
| Win | `#34a853` |
| Draw | `#fbbc04` |
| Loss | `#ea4335` |
| Font | Inter (sans), JetBrains Mono (numbers) |
| Radius | 8px / 6px / 4px |
| Spacing 4px base unit |

Components: Button / Card / Badge / ProgressBar / TabBar / Selector / Slider / Modal / Toast / Table / Tooltip

---

## 7. Do NOT Touch

| File/Folder | Reason |
|-------------|--------|
| `data/*.py`, `data/*.sh` | Data pipelines running in production |
| `data/*.json` | Data structures, frontend/backend depend on them |
| `football_predictor/scorelines.py` | Core Poisson model, verified |
| `football_predictor/backtest.py` | Backtest engine |
| `football_predictor/tournament_sim.py` | Simulation engine |
| `football_predictor/wc_api.py` | WC API logic |
| `football_predictor/timegate.py` | Data leakage defense |
| `football_predictor/recommendations.py` | Recommendation engine |
| `football_predictor/odds.py` | Odds processing |
| `football_predictor/version.py` | Single version source |
| `football_predictor/services/*.py` | Service layer with test coverage |
| `vercel.json` | Deployment config |
| `requirements.txt` | Zero-dependency declaration |
| `pyproject.toml` | Project metadata |
| Existing pytest files | Test logic (update test code if routing changes) |

---

## 8. Technical Constraints

| Constraint | Detail |
|------------|--------|
| Zero pip dependencies | Python stdlib only — serverless must cold-start instantly |
| Vercel deployment | `@vercel/python` runtime, Python 3.11, 10mb lambda |
| Git branch | `master`, not `main` |
| Git push | `https_proxy=http://127.0.0.1:10809 git push origin master` |
| Version source | Single source: `football_predictor/version.py` |
| Tests must pass | `python3 -m pytest tests -q` |

---

## 9. Deliverables

1. ✅ English-native frontend, componentized, preserves 8 tabs + parameter panel
2. ✅ Modular backend (`api/routes/`, thin `api/index.py`)
3. ✅ All existing pytest tests pass
4. ✅ Deployable to Vercel without config changes
5. ✅ Git push: `https_proxy=http://127.0.0.1:10809 git push origin master`

---

*This is an example reference document for the `codex` skill's "Crafting Delivery Prompts" pattern.*
