---
name: poker-equity
description: 德州扑克权益计算与博弈分析。构建蒙特卡洛决策工具，含手牌评估、对手范围、多玩家行为预测引擎。适用于牌桌实时决策辅助系统。
---

# 德州扑克权益计算与博弈分析

## 概述

构建扑克数学决策工具的完整流水线：从卡牌编码 → 手牌评估 → 蒙特卡洛模拟 → 决策引擎 → 博弈预测分析。

典型架构：

```
card.py → hand_evaluator.py → equity_calculator.py → decision_engine.py → api.py
                                                                          └─ game_theory.py
ranges.py ────────────────────┘
```

## 核心模块

### 1. 卡牌编码 (`card.py`)

**6-bit 编码方案：** `(suit << 4) | rank`
- `rank`: 2-14 (2=2, ..., 10=10, J=11, Q=12, K=13, A=14)
- `suit`: 0-3 (c=0, d=1, h=2, s=3)

```python
def encode_card(rank, suit): return (suit << 4) | rank
def card_rank(card):         return card & 0x0F
def card_suit(card):         return (card >> 4) & 0x3
```

**关键约束：** 用 `if not: raise ValueError` 替代 `assert`。`assert` 在 `python -O` 下被禁用。

### 2. 手牌评估 (`hand_evaluator.py`)

**10 种牌型枚举** (HandRank): HIGH_CARD=0 → ROYAL_FLUSH=9

**evaluate_5**: 从 5 张牌中找出最佳组合（枚举所有 C(5,5)=1 组合）
**evaluate_7**: 从 7 张牌中枚举 C(7,5)=21 种 5 张组合，取最高分

**`compare_hands` 踢脚比较：** 必须用 `max(len(k1), len(k2))` 逐位对比，不能用 `zip()` 截断。

```python
for i in range(max(len(k1), len(k2))):
    v1 = k1[i] if i < len(k1) else 0
    v2 = k2[i] if i < len(k2) else 0
```

### 3. 蒙特卡洛模拟 (`equity_calculator.py`)

**💣 CRITICAL: EV 公式**
```
正确:  Win$ = pot         # 跟注额不算利润
错误:  Win$ = pot + call  # 翻倍EV，导致 -EV 被误判为 +EV
EV = win% * Win$ - lose% * Lost$
```

**💣 CRITICAL: 多路底池统计**
```
错误（逐对手累加）: win_rate = total_wins / (sims * num_opponents)
                    → 3 对手时 hero 赢 2 输 1 = 66%，正确值约 33%
正确（whole-pot）:  _simulate_one 返回 (1,0) 全部赢 / (0,1) 平局 / (0,0) 输
                    win_rate = total_wins / num_simulations
```

**并行化：**
```python
def monte_carlo_equity(..., num_workers=None):
```

⚠️ **Vercel Serverless 约束：** `ProcessPoolExecutor` 在 Vercel/AWS Lambda 上禁止 fork，**100% 崩溃**。
- 代码中 `n_workers = num_workers or 1`（默认单进程），`os.cpu_count()` 不可用
- 仅在本地显式传入 `num_workers > 1` 且 `sims >= 2000` 时走多进程
- 单进程 10000 sims 在 Vercel 上约 20-30s（慢但稳定）

| 环境 | 默认行为 | 备注 |
|------|---------|------|
| 本地开发 | 单进程 (1 worker) | 可显式启用多进程 |
| Vercel 生产 | 强制单进程 | fork 被禁，多进程崩溃 |
| CLI 使用 | 单进程 | 自动选择最优模式 |

### 4. 对手范围 (`ranges.py`)

**预设范围：** any / top5 / top10 / top15 / top20 / top35 / top50 / pair+ / broadway / suited-connector

**自定义范围：**
```python
"AA, KK, AKs, AKo"       # 指定手牌
"TT+, AJs+, KQo"         # 扩展 (+)
```

**💣 CRITICAL: 预筛策略**
- 使用 `build_range_pool()` 预先计算所有有效组合（O(n²) 只做一次）
- **不要用拒绝采样**（4% 命中率下 100 次尝试会频繁失败）
- 预筛完成后 O(1) 随机选取

### 5. 博弈预测引擎 (`game_theory.py`)

结构化分析框架，适用于所有多玩家决策场景：

```
输入: hero_cards + community + pot/call/stack + players/position + actions_history
  ↓
阶段1: 意图逆向工程
  - 从对手操作反推范围方向
  - 基于下注尺度 (pot%) / 反应时间 / 位置 / 画像
  ↓
阶段2: 局势评估
  - SPR (stack-to-pot ratio) 计算
  - 位置优势评分
  - 底池赔率 vs 胜率
  ↓
阶段3: 决策树生成
  - Fold (EV=0)
  - Call (EV = win%*pot - lose%*call)
  - Raise 2x (EV = FE*pot + (1-FE)*[win%*(pot+raise) - lose%*(raise+call)])
  - All-in (SPR<=4 时)
  ↓
阶段4: 最优解锁定
  - 按 EV 排序
  - 最优 + 备选
  ↓
输出: 局势洞察 → 最优解/推演/风险 → 备选 → 决策树
```

**意图标签表：**
| 标签 | 含义 | 识别特征 |
|------|------|---------|
| value | 价值下注 | pot 40-75%, 短思考 |
| bluff | 诈唬 | pot > 80%, 长思考或不自然 |
| semi_bluff | 半诈唬 | 听牌 + 激进 |
| probe | 探注 | pot < 40%, 小注试探 |
| trap | 埋伏 | 慢打强牌, 秒跟 |
| steal | 偷池 | BTN/CO 位置, 翻前加注 |
| defense | 防守 | BB 位抵抗 |

### 6. Vercel 部署

```json
// vercel.json
{
  "builds": [{"src": "api/index.py", "use": "@vercel/python", "config": {"maxLambdaSize": "15mb"}}],
  "routes": [{"src": "/(.*)", "dest": "api/index.py"}]
}
```

```python
# api/index.py — 入口
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from txpokerassist.api import app
```

⚠️ Vercel Serverless 有 **10s 超时**。推荐默认 `sims=5000` 以规避超时。

## 结构化输出模式

博弈分析使用**六模块结构化输出**，可复用至其他决策分析场景：

```
📊 局势洞察     — 1-2 句总结 + 关键指标
🔍 对手意图     — 逐人分析（操作 + 推断范围）
🌳 决策树       — EV 排序的分支列表（最优标★）
🎯 推荐动作     — 最优解 + 置信度 + 策略推演
⚠️ 风险提示     — 操作弱点 + 场景限制
🔄 备选方案     — Plan B + 推演
📈 关键指标     — Equity / Win-Tie-Lose / SPR / Pot
```

## 常见陷阱

| # | 陷阱 | 表现 | 修复 |
|---|------|------|------|
| 1 | EV 公式包含跟注额 | EV 翻倍，-EV 误判为 +EV | Win$ = pot |
| 2 | 多路底池逐对手累加 | 3 路底池胜率偏大 2x | whole-pot 统计 |
| 3 | 范围拒绝采样失败 | 紧范围 + 牌池小 → 频繁 ValueError | 预筛 O(n²) 一次 |
| 4 | `assert` 被 `-O` 吞掉 | 传入非法 rank 静默产生乱码 | `if not: raise ValueError` |
| 5 | `compare_hands` zip 截断 | kicker 不等长被判平局 | `max(len)` 逐位 |
| 6 | f-string + CSS 冲突 | `patch` 工具在 f-string 内嵌 CSS 时产生语法错误 | 用 `python3 << 'PYEOF'` heredoc 完整重写 |
| 7 | 用户/协作者邮箱不匹配 Vercel | Vercel 阻止部署 | `git config user.email` 设 Vercel 注册邮箱 |
