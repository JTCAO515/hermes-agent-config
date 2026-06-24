# Poisson Odds Computation — Math Reference

## 核心公式

### 泊松分布 PMF
```
P(X = k) = (λ^k × e^(-λ)) / k!
```

### 双变量泊松（带相关性）
```python
# 独立模型
P(home=a, away=b) = Pois(a; λ_h) × Pois(b; λ_a)

# 带 shared_lambda 相关性
# corr = shared_λ / (1 + shared_λ)
# P_joint = P_h × P_a × (1 + corr × (a - λ_h) × (b - λ_a) / (λ_h × λ_a))
```

## 盘口计算实现参考

### Asian Handicap (让球盘)

通用规则：**主队穿盘当且仅当 `home_goals - away_goals > -line`**

| 盘口 | 穿盘条件 | 走水条件 |
|------|---------|---------|
| -0.5 | 主净胜 > 0.5 (即a≥b+1) | 无（半盘） |
| -1.0 | 主净胜 > 1.0 (即a≥b+2) | a-b = 1 |
| -1.5 | 主净胜 > 1.5 (即a≥b+2) | 无（半盘） |
| +0.5 | 主净胜 > -0.5 (即a≥b) | 无（半盘） |
| +1.0 | 主净胜 > -1.0 (即a≥b) | a-b = -1 |
| +1.5 | 主净胜 > -1.5 (即a≥b-1) | 无（半盘） |

关键：**半盘无走水**，整盘有走水。

### Half Time / Full Time (半全场)

**HT目标率估算**: λ_ht = λ_ft × 0.44

**条件概率矩阵**（从Poisson相关性推导）:
```
        FT=H   FT=D   FT=A
HT=H    0.75   0.20   0.05
HT=D    0.15   0.70   0.15
HT=A    0.05   0.20   0.75
```
P(HT=R, FT=S) = P(HT=R) × P(FT=S | HT=R)

### 首球（First Team to Score）

```python
# 简化逼近：
h_first = P(主>0) - P(双>0) × 0.5
a_first = P(客>0) - P(双>0) × 0.5

# 归一化（剔除无进球概率）
total = 1.0 - P(0-0)
h_first /= total
a_first /= total
```

### 进球区间

15分钟段权重分布（基于真实比赛数据经验）：
```
0-15:  12%   16-30: 14%   31-45: 18%
46-60: 16%   61-75: 18%   76-90: 22%
```
各区段 λ = (λ_h + λ_a) × 权重 / 总权重
区段至少1球概率 = 1 - e^(-区段λ)

## 缓存策略

```
Vercel冷启动: 模块级变量 _cache, _timestamp
TTL: 120s
刷新触发: /api/wc/odds-full 请求时检查 stale
回退: 若 odds_engine 计算结果为空或异常，返回 stale 缓存
```

## 验证检查

- AH -0.5 概率应精确等于主胜概率
- AH +0.5 概率应等于(主胜+平局)概率
- 各盘口总和应为1.0（归一化）
- 半全场9种概率之和应为1.0
- 总进球分布之和应为1.0
