# Daily Picks v3 — 三策略引擎：成功率 × 潜在收益

## 概述

v3 将前两代（真实市场对比 → 交互参数）升级为**三策略选择器**，
在「成功率」和「潜在收益率」两个维度上让用户自主选择风险偏好。

### 迭代历史

| 版本 | 核心能力 | 文件 |
|------|---------|------|
| v1 (基础) | 模型自比 → 统一 5.1% EV | `daily_picks.py` |
| v2 (真实) | 独立市场对比 → 差异化 EV (4~122%) | + `market_odds_model.py` |
| v3 (策略) | 激进/增长/平稳 → 三套完整逻辑 | 重构 `daily_picks.py` + 前端选择器 |

## 三策略核心矩阵

```
                   激进型 (Aggressive)    增长型 (Growth)     平稳型 (Stable)
   ────────────────────────────────────────────────────────────────────
   优先级           潜在收益 >> 胜率        收益 ≈ 胜率        胜率 >> 收益
   目标赔率范围      ≥ 2.5 (不限高)         1.3 ~ 5.0          ≤ 2.0
   模型概率门槛      ≥ 0%                   任意              ≥ 55%
   最低 EV 门槛     ≥ 5%                    ≥ 3%              ≥ 1% (低门槛但其他条件严)
   最低 Edge       ≥ 0% (只看EV)             ≥ 2%              ≥ 1%
   排序依据         EV × 赔率               EV 降序            概率 × EV
```

### 仓位控制差异

| 参数 | 激进型 | 增长型 | 平稳型 |
|------|--------|--------|--------|
| Kelly 乘数 | 0.20× (最保守) | 0.25× (标准) | 0.50× (最自信) |
| 单注上限 | 5% 资金 | 10% 资金 | 20% 资金 |
| 单场上限 | 20% 资金 | 30% 资金 | 40% 资金 |
| 总曝险上限 | 40% 资金 | 50% 资金 | 65% 资金 |
| 注数倾向 | 分散多注 | 适度集中 | 极少注数 |

## 策略逻辑详解

### 🔥 激进型 (aggressive)

**哲学**：只要 1-2 笔高赔率命中就能覆盖其他所有失败。

```python
cfg = StrategyConfig(
    label="激进型",
    min_ev_pct=5.0,           # 高 EV 门槛
    min_odds=2.5,             # 不碰低赔率
    max_odds=999.0,           # 越高越好
    min_model_prob=0.0,       # 不看概率高低
    max_model_prob=1.0,
    kelly_multiplier=0.20,    # 更小 Kelly（保本金）
    max_single_pct=0.05,
    max_match_pct=0.20,
    max_total_pct=0.40,
    rank_by="ev_x_odds",      # EV × 赔率排序 → 重视潜在收益
    min_edge=0.0,             # 不看 edge，只看 EV
)
```

**典型输出特征**：
- 平均赔率 **6.0+**，平均概率 **~25%**
- 22 注 / 5 场比赛
- ROI +59%（期望回报 $220 / $371）
- 大量亚洲让球远线、大小球极端线

### 📈 增长型 (growth)

**哲学**：平衡胜率和收益，追求稳定增值。

```python
cfg = StrategyConfig(
    label="增长型",
    min_ev_pct=3.0,
    min_odds=1.3,
    max_odds=5.0,
    min_model_prob=0.0,
    max_model_prob=1.0,
    kelly_multiplier=0.25,
    max_single_pct=0.10,
    max_match_pct=0.30,
    max_total_pct=0.50,
    rank_by="ev",
    min_edge=0.02,
)
```

**典型输出特征**：
- 平均赔率 **~2.5**，平均概率 **~56%**
- 11 注 / 3 场比赛
- ROI +22%（$109 / $500）
- 1X2 为主 + 近线亚洲盘口

### 🛡️ 平稳型 (stable)

**哲学**：只投高概率低赔率，追求确定性。

```python
cfg = StrategyConfig(
    label="平稳型",
    min_ev_pct=1.0,           # 低 EV 门槛（因其他条件严格）
    min_odds=1.05,
    max_odds=2.0,             # 绝不投高赔率
    min_model_prob=0.55,      # 模型至少 55% 置信度
    max_model_prob=1.0,
    kelly_multiplier=0.50,    # 更大 Kelly（高置信度）
    max_single_pct=0.20,
    max_match_pct=0.40,
    max_total_pct=0.65,
    rank_by="prob_x_ev",      # 概率优先 × EV
    min_edge=0.01,
)
```

**典型输出特征**：
- 平均赔率 **~1.4**，平均概率 **~82%**
- 4 注 / 2 场比赛
- ROI +15%（$100 / $650）
- 几乎全是 AH 近线、低赔率 1X2

## 前端选择器

三个按钮并排，点击切换即重新计算：

```html
<div class="picks-strategy">
  <button class="picks-strategy-btn" data-strategy="aggressive">🔥 激进型</button>
  <button class="picks-strategy-btn picks-strategy-btn--active" data-strategy="growth">📈 增长型</button>
  <button class="picks-strategy-btn" data-strategy="stable">🛡️ 平稳型</button>
</div>
```

- 点击后：更新 `currentStrategy` → 调用 `renderDailyPicks()` → fetch 带 `strategy` 参数
- 每个策略按钮有独立颜色：激进=红色，增长=蓝色，平稳=绿色
- 下方显示「策略签名栏」：平均赔率 / 平均概率 / 期望 ROI

## API

```http
GET /api/wc/daily-picks?bankroll=1000&max_bets=5&include_wdl=1&strategy=growth
```

新增响应字段：

| 字段 | 类型 | 示例 | 说明 |
|------|------|------|------|
| `strategy` | str | "growth" | 当前策略 |
| `avg_odds` | float | 2.47 | 策略平均赔率（签名指标） |
| `avg_prob` | float | 0.56 | 策略平均模型概率（签名指标） |

## 生产示例对比

```python
from data.daily_picks import compute_daily_picks

# 三个策略
for s in ["aggressive", "growth", "stable"]:
    r = compute_daily_picks(bankroll=1000, max_bets_per_match=5, strategy=s)
    print(f"{s:12s}  {r.total_bets:2d}注  ${r.total_stake:3.0f}  "
          f"Odds={r.avg_odds:.2f}  Prob={r.avg_prob:.0%}  ROI={r.expected_roi:+.1%}")
# 输出:
# aggressive   22注  $371  Odds=6.34  Prob=25%  ROI=+59.1%
# growth       11注  $500  Odds=2.47  Prob=56%  ROI=+21.9%
# stable        4注  $650  Odds=1.42  Prob=82%  ROI=+15.4%
```

## 工程实现

### 文件结构

```
data/
  daily_picks.py         # v3: StrategyConfig, compute_daily_picks, 3种rank逻辑
  market_odds_model.py   # 独立市场赔率（不受策略影响）
  betting_math.py        # 每盘口 EV/Kelly/评级（不受策略影响）
api/
  index.py               # GET /api/wc/daily-picks?strategy=...
web/
  index.html             # 策略选择器 + 控制面板
  app.css                # .picks-strategy / .picks-signature
  app.js                 # renderDailyPicks(currentStrategy)
```

### 关键设计决策

1. **策略只影响选盘 + 仓位，不影响赔率计算**：`betting_math.py` 和 `market_odds_model.py` 保持策略无关
2. **同一组候选人 + 策略过滤**：先生成所有盘口的 `DailyBet`，再按策略配置过滤/排序/分配仓位
3. **策略签名在下发前计算**：后端在 `compute_daily_picks` 中直接计算 avg_odds/avg_prob 作为策略特征指标
