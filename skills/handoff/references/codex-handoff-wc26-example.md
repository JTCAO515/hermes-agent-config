# WC26 Edge Lab — Full Rewrite Brief for Codex CLI

> Example of a comprehensive Codex CLI handoff prompt with full product strategy, requirements, and capabilities sections.
> See the `handoff` skill's "Codex CLI Handoff Prompt" section for the template.

## 1. Repository

- **GitHub:** `https://github.com/JTCAO515/WC26-Main.git`
- **Live:** `https://worldcup.jtcao.space/`
- **Current version:** v8.0.1
- **Default branch:** `master` (NOT `main`)

> ⚠️ Git push: `https_proxy=http://127.0.0.1:10809 git push origin master`

---

## 2. Product Strategy

### 2.1 Vision

把专业博彩团队的建模能力，打包成一个普通人也能用的世界杯决策实验室。

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

### 2.4 Trade-offs (不做什么)

- ❌ 不做实时推送/通知
- ❌ 不做用户系统/登录/历史
- ❌ 不做自动数据爬取（现有管道不动）
- ❌ 不接入真实下注平台（法律风险）
- ❌ 不做移动端 App（PWA 就够了）
- ❌ 不要引入任何 Python 第三方依赖（Vercel 冷启动必须快）

---

## 3. Product Capabilities

### 3.1 Models & Algorithms

| Capability | Description |
|-----------|-------------|
| 独立泊松模型 | Per-team attack/defense rating → WDL probabilities |
| 双变量泊松模型 | With shared_lambda for draw correlation |
| Odds de-vig | Remove market margin from Polymarket/The Odds API |
| Recommendation engine | Edge × Confidence × Data freshness → score 0-100 + label |
| Timegate | Data leakage prevention via timestamps |
| Backtest engine | Per-checkpoint replay → Brier Score → leak audit |
| Monte Carlo simulation | 2000+ tournament runs → probability distributions |

### 3.2 API Endpoints (全部保留)

`GET /api/health` `GET /api/version` `GET /api/wc/predict` `GET /api/wc/recent-results` `GET /api/wc/data-consistency` `GET /api/wc/standings` `GET /api/wc/knockout` `GET /api/wc/backtest`

---

## 4. Frontend Requirements (每页详细规格)

### 4.1 Overview (首页)
Purpose: 用户的第一屏。看全局健康度，再决定是否深入。

Must display:
- Top nav: logo + "WC26 Edge Lab" + version badge
- Summary bar: model type, Brier WDL, Brier O/U 2.5, data quality
- Quick stats: matches played / total / last update
- Entry card matrix (6 cards linking to each tab)
- Status bar: last sync time, data freshness

### 4.2 Standings (积分榜)
48 team, 12 group ranking table with knockout zone highlighting, promotion probability per team.

### 4.3 Knockout (淘汰赛)
Horizontal bracket flow (32→16→8→4→Final+3rd), win probability %, champion probability, progress indicator.

### 4.4 Predictions (预测)
Per match card: xG bar, WDL + O/U 2.5 probability panel, recommendation (strong/medium/weak/watch/avoid), Edge %, confidence, filters by date/group/recommendation.

### 4.5-4.8 Simulation / Schedule / Comparison / Parameter Panel
Full specs — see original prompt-for-codex.md.

---

## 5. Technical Architecture

### Frontend
```
web/
├── index.html          # Shell
├── components/         # overview.js, standings.js, knockout.js, predictions.js, simulation.js, schedule.js, comparison.js, params-panel.js
├── styles/
│   ├── app.css
│   ├── components.css
│   └── responsive.css
├── lib/
│   ├── api.js          # API client
│   ├── state.js        # Pub/sub state manager
│   └── utils.js        # Formatting helpers
└── sw.js / manifest.json
```

### Backend
```
api/
├── app.py              # WSGI app factory
├── routes/             # health.py, version.py, wc.py
├── middleware/          # cors.py, auth.py
└── index.py            # Thin entry (1 line)
```

---

## 6. Design System

- Theme: Dark mode (Linear-inspired), Primary: `#5e6ad2`, Background: `#0f1117`, Font: Inter / JetBrains Mono
- Components: Button, Card, Badge, Progress bar, Tab bar, Selector, Slider, Modal, Toast, Table, Tooltip
- Interactions: Instant tab switching, debounced API (300ms), skeleton loading, hover states on all interactive elements

---

## 7. Do NOT Touch

| Area | Reason |
|------|--------|
| `data/*.py` `data/*.sh` | 数据管道在线上跑着，不动 |
| `data/*.json` | 数据结构前端/后端依赖，不动 |
| `football_predictor/*.py` | 核心算法（验证过的），不动 |
| `vercel.json` | 部署配置，不动 |
| `requirements.txt` | 零依赖声明，不动 |
| 现有 pytest 文件 | 测试逻辑不动 |

---

## 8. Success Criteria

- [ ] 前端英文化（球队名括号带中文）
- [ ] 8 个 Tab 功能完整
- [ ] 参数面板实时生效
- [ ] 响应式布局（mobile/tablet/desktop）
- [ ] API 端点全部 200
- [ ] `python3 -m pytest tests -q` 全绿
- [ ] Vercel 可部署
