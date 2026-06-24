# 回测统计工具模式 — Bootstrap + 置换检验

> 纯 stdlib Python 实现，零外部依赖。适用于所有带回测功能的项目（体育预测/量化交易/选股策略）。

---

## Bootstrap 重采样（ROI 置信区间）

### 用途

从 N 条回测记录中**有放回采样** N 次，重复 1000 次，形成 ROI 的抽样分布 → 计算 95% 置信区间。

### 实现

```python
import random

def bootstrap_backtest(bets_log, initial_bankroll, n_iterations=1000):
    """Bootstrap 重采样回测，计算 ROI 置信区间."""
    if not bets_log:
        return (0.0, 0.0, 0.0)
    n = len(bets_log)
    rois = []
    for _ in range(n_iterations):
        sample = [random.choice(bets_log) for _ in range(n)]
        bankroll = initial_bankroll
        for b in sample:
            bankroll += b["profit"]
        if initial_bankroll > 0:
            rois.append((bankroll - initial_bankroll) / initial_bankroll * 100)
    rois.sort()
    return (
        round(rois[int(n_iterations * 0.025)], 2),   # 2.5% 分位
        round(rois[int(n_iterations * 0.975)], 2),    # 97.5% 分位
        round(sum(rois) / n_iterations, 2),            # 均值
    )
```

### 解读

| ROI CI | 含义 |
|--------|------|
| (-2%, +15%) | 策略可能亏损，也可能大赚 — 不确定性高 |
| (+3%, +8%) | 窄区间且全部 >0 — 策略稳健 |
| (-5%, -1%) | 区间全部 <0 — 统计上可以确认是亏钱策略 |

### Pitfall — 小样本偏差

- **N < 10 条回测记录时**，Bootstrap 的 CI 极度不稳定（同一数据跑两次可能 CI 差 10%+）
- **修复**：N < 10 时在返回值中标注 `confidence: "LOW"`，N ≥ 30 时可认为 CI 稳定
- **硬下限**：N < 5 时 Bootstrap 基本无意义，直接返回空 CI

---

## 置换检验（统计显著性 p-value）

### 用途

检验策略的累计收益是否显著高于「随机下注」。通过打乱收益符号（50% 概率正/负）构造零假设分布，看原收益落在分布的多极端位置。

### 实现

```python
def permutation_test(bets_log, n_permutations=500):
    """置换检验: 打乱收益符号, 看原策略的累计收益是否显著高于随机."""
    if not bets_log:
        return 1.0
    actual_total = sum(b["profit"] for b in bets_log)
    profits = [b["profit"] for b in bets_log]
    count_extreme = 0
    for _ in range(n_permutations):
        shuffled = [p * (1 if random.random() > 0.5 else -1) for p in profits]
        perm_total = sum(shuffled)
        if perm_total >= actual_total:
            count_extreme += 1
    return count_extreme / n_permutations
```

### 解读

| p-value | 含义 | 行动 |
|---------|------|------|
| < 0.01 | 高度显著 — 收益几乎不可能是随机产物 | ✅ 继续优化策略 |
| 0.01–0.05 | 显著 — 策略有真实 edges | ✅ 可信任 |
| 0.05–0.10 | 边缘显著 | ⚠️ 需要更多数据 |
| > 0.10 | 不显著 — 当前收益可被随机解释 | ❌ 策略可能无效 |

### Pitfall — 置换次数不足

- 500 次 permutation 的 p-value 精度约 ±0.02
- 如果想检测 p < 0.01 的显著性，至少需要 2000 次
- **性能**：2000 次 permutation × 50 条记录 ≈ 10ms（Python stdlib）

---

## 最大回撤修复算法

### 问题

简单求 `min(profit)` 不准确 — 回撤是按**资金曲线**追踪的，不是按单笔。

### 正确实现

```python
def compute_max_drawdown(bets_log, initial_bankroll):
    """按资金曲线追踪最大回撤（%）。"""
    running = initial_bankroll
    peak = initial_bankroll
    max_dd = 0.0
    for b in bets_log:
        running += b["profit"]
        if running > peak:
            peak = running
        dd = (peak - running) / peak * 100  # 当前回撤%
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)
```

---

## Sortino 比率

### 公式

```
Sortino = (avg_return - 0) / σ_downside
```

其中 `σ_downside = sqrt( sum(r² for r in returns if r < 0) / n_negative )`

### 与 Sharpe 对比

| 指标 | 考虑 | 忽略 |
|------|------|------|
| Sharpe | 全部波动 | 方向 |
| Sortino | **只惩罚亏损** | 盈利波动 |

- Sharpe > 1 = 好，Sortino > 2 = 非常好
- 高 Sortino + 低 Sharpe = 盈利波动大但亏损很少（例如：高赔率低频策略）

---

## Calmar 比率

### 公式

```
Calmar = compound_return / max_drawdown
```

### 与 Sharpe 对比

| 指标 | 关注 | 适用 |
|------|------|------|
| Sharpe | 单期风险调整收益 | 通用 |
| Calmar | 历史最大亏损 vs 总收益 | 资金管理敏感型策略 |

- Calmar > 1 = 收益超过最大回撤
- Calmar > 3 = 极优
- **注意**：回测窗口短时（< 20 bet），Calmar 可能不显著

---

## 完整回测报告模板

```python
return {
    "total_bets": n_bets,
    "winning_bets": winning,
    "win_rate": winning / n_bets,
    "total_stake": total_stake,
    "net_profit": net_profit,
    "roi_pct": net_profit / total_stake * 100,
    "sharpe_ratio": sharpe,
    "sortino_ratio": sortino,
    "calmar_ratio": calmar,
    "max_drawdown": compute_max_drawdown(bets_log, initial_bankroll),
    "profit_factor": gross_win / gross_loss,
    "p_value": permutation_test(bets_log),
    "permutation_significant": p_val < 0.05,
    "boot_roi_ci": bootstrap_backtest(bets_log, initial_bankroll),
}
```
