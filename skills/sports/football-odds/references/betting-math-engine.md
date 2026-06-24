# 博彩数学引擎 — Betting Math Engine

从"赚钱可能性"和"成功率"两个核心维度出发，计算每一注的价值。

## 核心算法体系

### 1. Expected Value (EV) — 期望收益

**二元盘口** (OU/BTTS/DNB/非整数AH):
```
EV = P(win) × (odds - 1) - P(loss) × 1
EV% = (odds × P(win) - 1) × 100
```

**亚洲让球含走水** (整数线AH):
```
EV = P(win) × (odds - 1) + P(push) × 0 - P(loss) × 1
```
走水时本金退回（净收益=0），三态模型。

**多结果盘口** (1X2/HTFT): 选一态，适用二元公式。

### 2. Kelly Criterion — 最优下注比例

**二元盘口:**
```
f* = (p × odds - 1) / (odds - 1)
```
- p = 你估计的真实概率
- odds = 市场小数赔率
- f* = 建议下注比例（银行资金的百分比）
- 负值 = 不该下注

**亚洲让球含走水 (三态):**
解析解近似：
```
f* = (p_win × net_odds - p_loss) / (net_odds × (p_win + p_loss))
```
上限 25% 防止过度下注。

**实践建议:** 使用 **Quarter Kelly**（1/4 Kelly）控制风险，即 `f = f* × 0.25`。

### 3. 夏普比率 — 风险调整后收益

```
Sharpe = EV / σ
σ = sqrt(P(win)×(odds-1-EV)² + P(loss)×(-1-EV)²)
```

| 夏普比率 | 含义 |
|---------|------|
| > 1.0 | 极佳 — 收益远高于风险 |
| > 0.5 | 优秀 — 值得重注 |
| > 0.2 | 可接受 — 有正期望 |
| < 0 | 风险过高 — 避开 |

### 4. 赚钱概率 — N次下注后盈利概率

使用正态近似（二项分布 → 正态）:
```
盈亏平衡所需胜场: break_even = n / odds
z = (break_even - n×p) / sqrt(n×p×(1-p))
P(盈利) = 1 - Φ(z)
```
Φ = 标准正态CDF

**解读**: 单注 EV +5%、胜率55%、赔率1.95 → 下100次中有77%概率赚钱。

### 5. Monte Carlo 模拟

模拟 N 次下注组合的最终资金分布：
1. 每次按 Quarter Kelly 比例下注
2. 随机决定输赢（按胜率）
3. 更新资金
4. 重复下一注

输出: 中位数终值、P10/P90、赚钱概率、破产概率、ROI

### 6. 综合评级体系 A-F

| 评级 | 条件 | 颜色 | 建议 |
|------|------|------|------|
| 🟢 A | EV≥8%, Edge≥5%, Sharpe≥0.5, 赚钱概率≥80% | 绿色 | 强烈推荐 |
| 🔵 B | EV≥5%, Edge≥3%, Sharpe≥0.3 | 蓝色 | 推荐 |
| 🟡 C | EV>0% | 黄色 | 可考虑 |
| 🟠 D | EV≈0 或 Sharpe<0 | 橙色 | 谨慎 |
| 🔴 F | EV<0 | 红色 | 不推荐 |

## 不同盘口类型的 EV 计算总结

| 盘口类型 | 结果数 | 特有参数 | EV 公式 |
|----------|--------|---------|---------|
| 1X2 | 3选1 | 无 | 二元公式 |
| 让球 -0.5 | 2 | 无 | 二元公式 |
| 让球 -1.0 | 3 | push_prob | 三态公式 |
| 大小球 | 2 | 无 | 二元公式 |
| BTTS | 2 | 无 | 二元公式 |
| 双倍机会 | 3选1 | 无 | 二元公式 |
| DNB | 2(去平) | 无 | 二元公式 |
| HT/FT | 9选1 | 无 | 二元公式 |
| 波胆 | 长尾 | 概率极低 | 二元公式 |
| 零封 | 2 | 无 | 二元公式 |
| 总进球 | 7选1 | 无 | 二元公式 |

## Python 实现核心函数

```python
from data.betting_math import (
    analyze_bet,           # 单笔下注全分析
    analyze_match_markets, # 一场比赛全部盘口
    monte_carlo_simulation,# N次下注模拟
    format_bet_analysis,   # 格式化输出
    format_match_analysis, # 格式化比赛报告
    BetProposal,           # 下注建议数据类
    BetResult,             # 比赛分析结果
)

# 单注分析
bp = analyze_bet(
    market_type="ou",
    model_prob=0.55,       # 你估计的真实概率
    decimal_odds=1.95,     # 市场赔率
    push_prob=0.0,         # AH走水概率
    bankroll=1000.0,       # 你的资金
    label="大2.5",
)
print(f"EV: {bp.ev_pct:+.1f}%")
print(f"Kelly: {bp.kelly_fraction*100:.1f}%")
print(f"Grade: {bp.grade}")
print(f"Profit Prob (100 bets): {bp.profit_prob*100:.0f}%")

# 全盘口分析
result = analyze_match_markets(markets_dict, bankroll=1000)
print(f"Best EV: {result.best_ev.selection_label} → {result.best_ev.ev_pct:+.1f}%")
```

## 数学推导参考

- **二元Kelly推导**: `f* = (p×b - q)/b` where b = odds-1, q = 1-p
- **三态Kelly(含走水)**: 最大化 E[log(1+f×R)]，R 为三态随机变量
- **正态近似误差**: n≥30 时误差可忽略；n<30 时建议用精确二项分布
- **夏普比率**: 默认假设无风险利率=0（赌注情境合理）
- **Monte Carlo**: 5000次模拟足够稳定P10/P90估值
