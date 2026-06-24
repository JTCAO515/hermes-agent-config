# 独立市场赔率模型 — Market Odds Model

## 为什么需要独立市场赔率

### 问题：循环自比（Circular Odds）

当赔率来自模型自己的概率时，EV 计算变成恒等式：

```python
# ❌ 模型自比（永远得到相同结果）
odds = 1.0 / model_prob * 1.05          # 赔率来自同一模型
market_implied = 1.0 / odds              # ≈ model_prob / 1.05
edge = model_prob - market_implied       # ≈ model_prob * 0.05/1.05 = 常数
ev = odds * model_prob - 1.0             # ≈ 5% 常数
```

结果：**所有盘口 EV 相同**（如 +5.1%），**所有评级相同**（如 Grade C），毫无区分度。

### 解决方案：独立市场视角

```python
# ✅ 模型 vs 独立市场
market_odds = get_independent_market_odds(match)  # 独立来源
market_implied = 1.0 / market_odds                # 市场隐含概率
edge = model_prob - market_implied                # 真正的优势
ev = market_odds * model_prob - 1.0               # 真实 EV（差异化！）
```

## 市场模型架构

### 三个维度

| 维度 | 说明 | 示例 |
|------|------|------|
| **基准强度** | 48 队 ELO 归一化评分 0-100 | Germany=88, Curaçao=55 |
| **人气偏置** | 热门球队被公众追捧 → 市场压低赔率 | Argentina×1.15, Brazil×1.20 |
| **盘口抽水** | 不同类型市场效率不同 | 1X2=5.5%, AH=3.5%, 波胆=10% |

### 与主模型的差异

| 方面 | 主模型 (bivariate Poisson) | 市场模型 (ELO-based) |
|------|--------------------------|---------------------|
| 预期进球 λ | 精细攻防评分推导 | 强度比率 × 总进球基准 |
| 相关性 | shared_λ 调节主客相关 | 独立泊松 (shared=0.05) |
| 概率校准 | 纯统计 | + 人气偏置修正 |
| 目标 | 精确概率估计 | 反映市场共识定价 |

### 效率标签

根据比赛特征动态调整市场效率：

| 场景 | 标签 | 基准抽水 | 逻辑 |
|------|------|---------|------|
| 淘汰赛 | tight | 4.5% | 大市场、高流动性 |
| 强弱差距大 | normal | 5.5% | 常规市场效率 |
| 实力接近/冷门 | wide | 6.5% | 小市场、低流动性 |

## 关键代码

### 市场赔率生成

```python
from data.market_odds_model import compute_market_odds_for_match

mo = compute_market_odds_for_match(
    match_id="wc2026-e-009",
    home="Germany",
    away="Curaçao",
    phase="group",
)
print(f"市场赔率: {mo.home_odds} / {mo.draw_odds} / {mo.away_odds}")
# → 1.89 / 3.73 / 3.87  (vs 模型: 1.15 / 8.50 / 15.0)
print(f"市场效率: {mo.market_efficiency}, 抽水: {mo.h2h_vig:.1%}")
```

### 亚洲让球盘

```python
ah = mo.ah_market["-1.5"]  # 主让1.5球
print(f"主穿: {ah['home_prob']:.1%} @ {ah['home_odds']:.2f}")
print(f"客穿: {ah['away_prob']:.1%} @ {ah['away_odds']:.2f}")
print(f"走水: {ah['push_prob']:.1%}")
```

### 大小球盘

```python
ou = mo.ou_market["2.5"]
print(f"大2.5: {ou['over_prob']:.1%} @ {ou['over_odds']:.2f}")
print(f"小2.5: {ou['under_prob']:.1%} @ {ou['under_odds']:.2f}")
```

## 效果验证

以 2026-06-14 的五场比赛为例：

| 比赛 | 模型概率(主) | 市场赔率(主) | 市场概率(主) | Edge |
|------|------------|-------------|-------------|------|
| Germany vs Curaçao | 86% | 1.89 | 50% | **+36%** |
| Netherlands vs Japan | 65% | 2.38 | 40% | **+25%** |
| Haiti vs Scotland | 49% | 2.92 | 32% | **+17%** |
| Australia vs Türkiye | 42% | 2.68 | 35% | **+7%** |

每个比赛有不同的 edge → 不同的 EV → 不同的推荐排序。
