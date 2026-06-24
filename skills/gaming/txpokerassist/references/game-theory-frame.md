# 博弈预测引擎参考 — 会话 2026-06-01

## 用户需求原文

> 你是一个专业的「多玩家博弈与行为预测分析引擎」。你的核心能力是能够根据用户设定的动态玩家数量、实时同步的玩家操作反馈，结合当前的游戏/交互环境状态，进行深度逻辑推演，从而精准预测"我"（当前用户）在下一回合的最优或最可能的操作步骤。

## 输入结构

```python
@dataclass
class PlayerAction:
    player_id: int          # 0=hero, 1+=opponents
    action: str             # fold/check/call/raise/all_in
    amount: int
    street: str             # preflop/flop/turn/river
    position: int           # 0=BTN, 1=SB, 2=BB, ...
    timing_s: float         # reaction time in seconds
    emotional_tag: str      # aggressive/hesitant/confident

# Full input:
# - hero_cards: 2 cards
# - community_cards: 0-5 cards
# - pot, call, stack: ints
# - hero_position: 0-9
# - num_players: 2-10
# - actions_history: List[PlayerAction]
# - opponent_ranges: Optional[List[str]]
```

## 输出模板

```
📊 局势洞察
  1-2 句话总结

🔍 对手意图
  P1: intention — evidence
    推断范围: range_name

🌳 决策树
  ★ all_in (200)              EV= +63.52  🟢 Strong
    raise_2x (to 100)         EV= +44.24  🟢 Strong
    call                      EV= +22.58  🟢 Strong
    fold                      EV=  +0.00  🔴 Low

🎯 推荐操作
  动作: all_in (200)
  置信度: 🟢 Strong
  策略推演: 推演依据文本
  ⚠️ 风险: 风险提示

🔄 备选方案 (Plan B)
  动作: raise_2x (to 100)
  推演: 推演依据

📈 关键指标
  Equity: 60.8% | Win: 60.1% | Tie: 1.5% | Lose: 38.4%
  SPR: 4.0 | Pot: $50 | To Call: $20 | Players: 2
```

## 策略推演自动化

推演文本由 `_optimal_reasoning()` 函数动态生成，基于：
- 当前动作（fold/call/raise/all_in）
- 手牌描述 + 胜率
- 底池赔率 vs 胜率关系
- SPR 判断深/浅筹码
- 对手意图摘要

## 用户偏好

- 纯策略输出，不加情绪安抚（"不用管心态"）
- 每个动作必须附风险提示和备选方案
- 决策树必须按 EV 降序排列，最优解标 ★
- 置信度标签: 🟢 Strong / 🟡 Moderate / 🟠 Marginal / 🔴 Speculative
