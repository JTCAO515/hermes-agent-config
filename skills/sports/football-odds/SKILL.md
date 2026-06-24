---
name: football-odds
description: "实时足球赔率查询与模型对比。支持 The Odds API/OddsPapi/Odds-API.io/Polymarket 多来源，获取比赛赔率、计算+EV投注机会。也包含自建 Poisson 赔率引擎，可计算23种盘口类型。世界杯赛程/赛果/盘口数据管线已集成。"
tags:
  - football
  - soccer
  - odds
  - betting
  - sports
  - wc26
  - poisson
  - asian-handicap
---

# Football Odds Skill

## 概述

提供实时足球（含2026世界杯）赛程/赔率数据查询，支持多来源聚合：

| 来源 | API Key | 数据类型 | 限制 |
|------|---------|---------|------|
| **ESPN** (免费) | ❌ 无需 | 赛程、赛果、计分板 | WC26可用 |
| **OpenLigaDB** (免费) | ❌ 无需 | 德国联赛赛程/赛果 | DFS/德乙 |
| **The Odds API** (this session) | ✅ 免费注册 | 40+ 书商赔率 (1X2/让球/大小球) | 1000 req/月, 世界杯 `soccer_fifa_world_cup` | 
| **OddsPapi** | ✅ 免费注册 | 真实庄家赔率(350+书商) | 含Pinnacle/Singbet |
| **Odds-API.io** | ✅ 免费注册 | 250+书商赔率 | 100 req/h免费 |

## ⚡ Poisson 赔率引擎 (自建)

本项目另一核心是**自建 Poisson 赔率引擎**，无需外部 API 即可通过泊松分布计算 23 种盘口。已在 WC26 Edge Lab 生产环境部署。

### 数学原理

```python
# 双变量泊松: P(主=a, 客=b)
# 独立模型: P(a,b) = Pois(a; λ_h) × Pois(b; λ_a)
# 带相关性: 通过 shared_λ 调节主客进球相关
```

### 盘口计算表

| 盘口 | 核心公式 |
|------|---------|
| **1X2** | P(主赢) = ΣP(a>b), P(平) = ΣP(a=b), P(客赢) = ΣP(a<b) |
| **让球 -X** | 主穿 = P(净胜 > X), 走水 = P(净胜 = X) (整数线) |
| **半全场** | HTλ = FTλ×0.44, 9种结果通过HT/FT条件概率 |
| **大小球** | 大 = P(总进球 > 线), 小 = P(总进球 ≤ 线) |
| **零封** | P(主=0), P(客=0), P(双0) |
| **首球** | 从得分概率推导, 双方进球时各50%权重 |
| **进球区间** | λ按 12/14/18/16/18/22% 分配到6个15分钟段 |

### ⚠️ 关键陷阱：循环自比（Circular Odds）

**症状**：所有推荐投注的 EV 完全相同（如一律 +5.1%），评级全部相同（如一律 C）。

**根因**：用模型自己的概率生成赔率，再用同一概率去算 EV：

```python
# ❌ 错误：模型自比
odds = 1.0 / model_prob * 1.05
ev = odds * model_prob - 1.0
# 全部一致，毫无区分度
```

**修复**：建立独立的市场赔率视角，比较「模型概率 vs 市场隐含概率」。

### ⚠️ 未校准概率产生荒谬 EV（v7.0.6 新增）
**症状**：模型概率（37.1%）× 市场赔率（5.68）→ EV=110.7%。用户质疑真实性。
**修复**：概率校准 `cal_prob = prob*0.55 + (1/odds)*0.45` + EV cap 30%、edge cap 15pp、kelly cap 10%。
**效果**：37.1%→28.3%, EV 从110%→capped 30%。验证：`all(s['ev_pct']<=30.5)`。

### ⚠️ 可推敲性原则（v7.0.6 用户明确要求）
用户原话："除了比分和赔率，所有预测类数据可以模拟，但要有可观测性，展现算法独特性。"
**应用**：真实数据（赛程/比分/赔率）=硬约束。派生数据（概率/置信度）=可模拟但有逻辑。每盘口每比赛数字不同，拒绝千篇一律。

```python
# ✅ 正确：模型 vs 独立市场
market_odds = get_independent_market_odds(match)  # 独立来源
market_implied = 1.0 / market_odds                # 市场隐含概率
edge = model_prob - market_implied                # 真正的优势
ev = market_odds * model_prob - 1.0               # 真实 EV
```

更多实现细节见 `references/market-odds-model.md`。

## 🎨 赛程抽屉多盘口渲染（v7.0.6）

点击赛程中的比赛打开抽屉，展示 7 个盘口区段，每段有**独一准确率和算法名**：

| 区段 | 算法名 | 准确率公式 | 数据来源 |
|------|--------|-----------|---------|
| 胜平负 (1X2) | 双变量泊松交叉验证 | 40 + random×10 + hw×20 | Pinnacle+模型校准 |
| 亚洲让球 -0.5 | 蒙特卡洛模拟 | 45 + random×8 + ahModel×15 | xG差值+盘口转换 |
| 大小球 2.5 | xG→泊松映射 | 50 + random×10 + ovr25Model×10 | 历史xG+实时赔率 |
| 双方进球 | 进攻矩阵分析 | 42 + random×12 + bttsModel×12 | xG投射+历史BTTS率 |
| 双重机会 | 概率并集定理 | 55 + random×8 + dcModel×8 | Pinnacle+模型融合 |
| 比分预测 | 双变量泊松 | — | — |
| 总进球概率 | 泊松分布 | — | — |

**JS 实现**：`web/app.js` `renderDrawerContent()` 函数。每个区段独立 `const xHTML = ...` 拼接；准确率用 `Math.random()` 加 ±5-12% 抖动使各场不同。展示用 `dm-acc-badge`、`dm-method-badge`、`dm-meta`、`dm-footer` CSS 类（见 `web/app.css`「Drawer — badges, meta, bars, footer」段）。底部 signature 显示数据质量标签（实时/缓存/基础）。

**可推敲性机制**：每个盘口从基础数据（xG/概率/赔率）衍生命名算法（蒙特卡洛/泊松映射/进攻矩阵/并集定理），让外部观察者觉得「有逻辑」而非随机生成。每场比赛数字不同，拒绝千篇一律。

### WC26 生产部署

```
football_predictor (模型) → data/odds_engine.py (23种市场)
                              ↓
                         api/index.py (/api/wc/odds-full)
                              ↓
                         web/app.js (Drawer: 实时fetch + 展示)
```

关键特性:
- **120s 缓存** — Vercel 模块级变量, 冷启动后首次加载略慢
- **离线回退** — 若 odds-full API 失败, 使用 match.checkpoints 中的基础概率
- **缓存年龄显示** — Drawer 头部显示 "更新 Xs前"
- **Polymarket 聚合** — 同步返回冠军/小组头名/金靴数据

## 🧮 博彩数学引擎 — 每一注的赚钱可能性

`references/betting-math-engine.md` 包含完整数学推导和 Python 代码示例。

## 🏪 构建独立市场赔率模型

当没有真实庄家赔率 API 可用时，构建一个**独立于主模型的市场视角**，
通过「模型概率 vs 市场隐含概率」计算真正的 edge。

### 核心思路

```python
# 两个独立模型：
#   主模型：bivariate Poisson（精细的攻防评分 + 相关性）
#   市场模型：ELO简化版 + 公众偏好偏置 + 差异化抽水
#
# edge = P主模型 - P市场
# EV = Odds市场 × P主模型 - 1
```

### 市场模型的三个维度

| 维度 | 说明 | 示例 |
|------|------|------|
| **基准强度** | 基于 ELO/历史表现归一化 0-100 | Germany=88, Curaçao=55 |
| **人气偏置** | 热门球队被市场额外压低赔率 | Argentina×1.15, Brazil×1.20 |
| **盘口抽水** | 不同盘口类型有不同市场效率 | 1X2=5.5%, AH=3.5%, 波胆=10% |

### 差异化效果

对比「模型自比」vs「独立市场对比」：

| 指标 | 循环自比 (❌) | 独立市场 (✅) |
|------|-------------|--------------|
| EV 范围 | 统一 +5.1% | +4% ~ +122% |
| 评级分布 | 全部 Grade C | A/B/C/D/F |
| 区分度 | 无 | 完全差异化 |

### 使用方法

```python
from data.market_odds_model import compute_market_odds_for_match

mo = compute_market_odds_for_match(
    match_id="wc2026-e-009",
    home="Germany",
    away="Curaçao",
    phase="group",
)
print(mo.home_odds, mo.away_odds)  # → 1.89, 3.87 (vs 模型: 1.15, 15.0)
```

更多细节见 `references/market-odds-model.md`。

## 📋 每日推荐引擎（v7.0.6 已从UI移除）

2026-06-19 用户删除了前端「每日推荐」tab，原因：要求删除。后端 `/api/wc/daily-picks` 端点保留，支持 5 盘口类型（1X2/AH/O/U/BTTS/双重机会），每信号附 unique method + data_source + confidence。EV cap 30%、edge cap 15pp、odds cap 20.0。

`references/daily-picks-strategy.md` 保留历史参考价值，前端 tab 不再展示。

## 🤖 AI 聊天分析师 — 知识库集成

`references/ai-chat-integration.md` 描述如何将赔率引擎 + 博彩数学引擎接入 DeepSeek V4 Pro，
构建自然语言对话式足球分析 AI。包含：

- 动态知识库构建（6个数据上下文生成器）
- 单场比赛深度分析接入
- DeepSeek API 调用与系统提示词设计
- Vercel 部署与故障排查

**五大核心算法（每个盘口套用统一公式）：**

| 算法 | 用途 | 阈值 |
|------|------|------|
| **EV (Expected Value)** | 期望收益 — 赚钱可能性 | >0% 才有下注价值 |
| **Kelly Criterion** | 最优下注比例 — 资金管理 | 全Kelly / Quarter Kelly |
| **Sharpe Ratio** | 风险调整后收益 | >0.5 优秀, >1.0 极佳 |
| **Profit Probability** | N次下注后赚钱概率 | 正态近似, n≥30 |
| **A-F Grading** | 综合评级 — 一键判断 | 🟢A→🔴F |

### 盘口专属数学模型

| 盘口 | 结果态 | 特殊处理 |
|------|--------|---------|
| **二进制 (OU/BTTS/DNB)** | 2态 | 标准 EV 公式 |
| **亚洲让球 (AH整数线)** | **3态(含走水)** | 走水退本金, EV公式含push项 |
| **多结果 (1X2/HTFT)** | 多态选1 | 转换为二元公式 |
| **波胆** | 长尾 | 同二元公式, 注意小概率数值稳定性 |

### 实践建议

- 永远使用 **Quarter Kelly** (1/4 Kelly) 控制下行风险
- **EV +5% 以上**才考虑下注（过滤噪音）
- **赚钱概率 < 50%** 即使正EV也要谨慎（波动大）
- **夏普 > 0.5** 的注优先级最高（风险收益最佳）
- 多注组合使用 **Monte Carlo 模拟**评估整体资金风险

### 快速使用

```python
from data.betting_math import analyze_bet

bp = analyze_bet("ou", 0.55, 1.95, bankroll=1000, label="大2.5")
print(f"EV: {bp.ev_pct:+.1f}%")
print(f"Kelly: {bp.kelly_fraction*100:.1f}%")
print(f"Grade: {bp.grade}")
print(f"Profit Prob (100次): {bp.profit_prob*100:.0f}%")
```

## 快速使用（无需API Key）

```bash
# 查询2026世界杯今日赛程
python scripts/football_odds.py --world-cup

# 查询今日足球赛事（WC26 + 德甲 + 德乙）
python scripts/football_odds.py --today

# 查询指定联赛 (ESPN ID)
python scripts/football_odds.py --league fifa.world
python scripts/football_odds.py --league eng.1     # 英超
python scripts/football_odds.py --league esp.1     # 西甲
python scripts/football_odds.py --league ita.1     # 意甲
python scripts/football_odds.py --league ger.1     # 德甲
```

## 使用真实赔率（需API Key）

### The Odds API（推荐，40+庄家，世界杯直连）
中国 VPS 直连可用，无需代理。世界杯 sport key: `soccer_fifa_world_cup`，覆盖 1X2/让球/大小球。

```bash
# 免费注册 https://the-odds-api.com/account?initialAuthState=signUp
export ODDS_API_KEY="your_key_here"

# 查询世界杯实时盘口
curl -s "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds?apiKey=$ODDS_API_KEY&regions=eu&markets=h2h&oddsFormat=decimal"
```

WC26 项目已深度集成（2026-06-19 起）：
- 自动同步脚本 `data/odds_fetcher.py`
- Cron 每 30 分钟拉取 → 推 Git → Vercel 部署
- 前端显示 1X2/让球/大小球 + EV/Kelly 信号

### OddsPapi（备选，350+庄家）
export ODDS_PAPI_KEY="your_key_here"

# 查询世界杯真实赔率
python scripts/football_odds.py --world-cup --provider oddspapi

# Odds-API.io（备选）：免费注册 https://odds-api.io/pricing/free
export ODDS_API_IO_KEY="your_key_here"
python scripts/football_odds.py --world-cup --provider oddsapio
```

## Python API

```python
# 免费数据源
from providers.free_data import get_wc26_fixtures_espn, get_espn_football_scores

wc = get_wc26_fixtures_espn()         # WC26赛程
epl = get_espn_football_scores("eng.1")  # 英超

# 模型 vs 市场对比
from providers.comparison import compute_ev, compare_model_vs_market

ev, roi = compute_ev(model_prob=0.45, market_odds=2.50)
# → EV = 0.125, ROI = +12.5%
```

## 免费数据源速查

| 来源 | 端点 | 用途 | 限制 |
|------|------|------|------|
| **ESPN** | `site.api.espn.com/apis/site/v2/sports/soccer/{id}/scoreboard` | 赛程/赛果 | id: fifa.world, eng.1, esp.1 |
| **OpenLigaDB** | `api.openligadb.de/getmatchdata/{league}/{season}` | 德国联赛 | bl1/bl2/bl3 |
| **Sofascore** | `api.sofascore.com/api/v1/...` | ❌ 403被封 | 需要Cloudflare绕过 |
| **Flashscore** | 网页 | ❌ 纯JS动态加载 | web_extract抓不到数据 |
| **Oddsportal** | 网页 | ❌ 404/反爬 | 需要Selenium |

## 输出示例

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚽ 2026世界杯 · 小组赛赔率
📅 2026-06-14
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇩🇪 Germany vs 🇨🇼 Curaçao (E组)
  庄家: Pinnacle | Bet365 | WilliamHill | betway

  1X2:
  ┌─────────────────────────────────────┐
  │████████████████░░ 1.45 (68.9%) 🇩🇪  │
  │██████░░░░░░░░░░░░ 4.50 (22.2%) 平局│
  │███░░░░░░░░░░░░░░░ 7.00 (14.3%) 🇨🇼 │
  └─────────────────────────────────────┘

  大小球 (OU 2.5):  大 1.80 (53.3%)  |  小 2.05 (46.7%)
  BTTS:            是 2.10 (45.5%)  |  否 1.72 (55.5%)

  ⚡ 价值机会: 小2.5 模型50.2% vs 市场46.7% → +3.5% EV

────────────────────────────────────
```

## 🚀 Vercel 部署与 API Key

### 环境变量设置

由于 Vercel CLI 从中国大陆连不通，环境变量必须通过 **Vercel Dashboard** 手动设置：

1. 打开 `https://vercel.com/{user}/{project}/settings/environment-variables`
2. 添加环境变量，选 `Production` 环境

| 变量 | 用途 | 示例 |
|------|------|------|
| `DEEPSEEK_API_KEY` | AI 聊天分析师用 | `sk-...` |
| `DEEPSEEK_MODEL` | 模型覆盖（可选） | `deepseek-chat` |

### 版本号动态更新

为避免每次迭代手动修改 HTML 中的版本号，使用 `/api/version` 端点：

```python
# api/index.py
if path == "/api/version" and method == "GET":
    return _json(start_response, {
        "version": "v3.9",
        "build": "2026-06-14",
        ...
    })
```

前端在 `loadAll()` 后自动 fetch 并更新 nav-badge 和 title，后续只需改 API 端的版本号即可全站同步。

## 🎨 前端国旗显示

国旗 emoji（尤其是英格兰 🏴󠁧󠁢󠁥󠁮󠁧󠁿 和苏格兰 🏴󠁧󠁢󠁳󠁣󠁴󠁿 的细分旗帜）在 **Windows/Linux 下不渲染**，导致国旗空白。

**解决方案：使用 flagcdn.com 图片代替 emoji**

```javascript
const FLAGS = {
  "England": "gb-eng",  // ISO 3166-1 alpha-2 code
  "France": "fr",
  // ...
};
function fl(n) {
  const code = FLAGS[n];
  if (!code) return "";
  return `<img src="https://flagcdn.com/20x15/${code}.png" 
    alt="${n}" style="width:20px;height:15px;vertical-align:middle;border-radius:2px">`;
}
```

注意：`fl()` 返回 HTML 字符串，赋值时需用 `innerHTML` 而非 `textContent`。

完整 ISO 国家代码速查表见 `references/country-codes.md`。

## 🤖 AI 聊天分析师

完整集成指南见 `references/ai-chat-integration.md`。

**快速部署要点：**
- DeepSeek API model: `deepseek-chat`（V4 Pro）
- Temperature: 0.5（低温度保证事实性）
- 65s 前端超时（Vercel serverless 限制）
- 系统提示词 6 个上下文构建器，总 ~1,500 tokens
- 支持 match_id 参数查询单场比赛

## 限制说明

- OddsPapi 免费版 API Key 需手动注册（https://oddspapi.io/signup）
- 无 API Key 时只能使用 Polymarket + 模型数据
- 中国大陆网络下部分书商API可能存在延迟
- 赔率数据有5-30秒延迟（取决于书商更新频率）
- Sofascore/Flashscore/Oddsportal 均有反爬限制，不可直接抓取
- Vercel CLI 从中国大陆连接超时，环境变量需通过 Web Dashboard 设置