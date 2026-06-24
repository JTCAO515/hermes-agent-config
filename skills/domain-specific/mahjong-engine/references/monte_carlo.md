# 蒙特卡洛模拟决策引擎 — 参考说明

## 原理

对每张可能打出的牌（手牌去重后），模拟 N 局后续摸牌走向：

1. **出牌**：从手牌中移除该牌（剩 13 张）
2. **摸牌晋升**：从剩余牌池中随机摸牌，尝试接近胡牌
3. **终止条件**：摸到第 max_depth 张 或 手牌可胡
4. **统计**：记录每局的胜败 → 胜率；胡牌局记录番数 → 平均番数
5. **EV 计算**：`EV = win_rate × avg_fan`（胜率×平均番数，类似德州扑克的 EV）

## 历史背景

Iter 004 引入。之前的决策引擎是纯规则式的：
- 向听数分析 → 进张数排序 → 防守评分
- 局限性：无法评估「长远来看哪张牌更有潜力」

蒙特卡洛模拟弥补了这个缺口。虽然比纯规则慢（500 局/出牌 × 13 张 ≈ 6 秒），但能发现规则无法捕捉的细节差异。

## 典型结果解释

```
打 9万 → EV=3.97  胜率 7%  平均番 55.3
打 1饼 → EV=0.55  胜率 1%  平均番 44.3
打 1万 → EV=0.00  胜率 0%  平均番 0.0
```

- **9万 EV 最高**：虽然是边张，但打掉后手牌结构优，远期牌效好
- **1饼 EV 中等**：保留后手牌结构稍差
- **1万 EV 为 0**：打掉 1 万导致手牌永远无法胡牌（非听牌状态）

## `evaluate_all_discards` 函数签名

```python
def evaluate_all_discards(
    tiles: List[int],
    melds: Optional[List[List[int]]] = None,
    remaining: Optional[Counter] = None,
    num_games: int = 500,
    max_depth: int = 8,
) -> List[Dict]:
```

**返回**：按 EV 降序排列的字典列表：
```python
[
    {"discard": code, "name": "9万", "ev": 3.97,
     "win_rate": 0.07, "avg_fan": 55.3},
    {"discard": code, "name": "1饼", "ev": 0.55,
     "win_rate": 0.01, "avg_fan": 44.3},
    ...
]
```

## `simulate_one_game` 单局模拟函数

```python
def simulate_one_game(tiles, melds, remaining) -> int:
    """
    单局模拟流程：
    1. 创建 13 张手牌的副本
    2. 从剩余牌池中随机取一个摸牌序列（shuffle）
    3. 逐张摸牌，摸一张看一次是否胡牌
    4. 胡了 → 计算番数并返回
    5. 摸完 max_depth 张还没胡 → 返回 0
    6. 牌池耗尽 → 返回 0
    """
```

**返回**：胡牌番数（int），不胡为 0。

## 实现细节

```python
def evaluate_all_discards(tiles, melds=None, remaining=None,
                          num_games=NUM_GAMES, max_depth=MAX_DEPTH):
    if remaining is None:
        from core.tile import full_pool
        pool_counter = Counter(full_pool())
        for code in tiles:
            pool_counter[code] -= 1
        remaining = pool_counter
    if melds:
        for m in melds:
            for code in m:
                remaining[code] -= 1

    unique_by_type: Dict[Tuple[int, int], int] = {}
    for tile in tiles:
        suit, rank = decode(tile)
        key = (suit, rank)
        if key not in unique_by_type:
            unique_by_type[key] = tile

    results = []
    for discard in unique_by_type.values():
        remaining_hand = [t for t in tiles if t != discard]
        # 因去重，如果手牌中有 3 张相同的，只模拟 1 张
        # 但 remaining_hand 少了 (count - 1) 张
        delta = tiles.count(discard) - 1
        if delta > 0:
            # 补回被多减的去重牌张
            # 逻辑：实际打掉 1 张后还有 (count-1) 张
            pass  # 见实际代码

        total_fan = 0
        wins = 0
        for _ in range(num_games):
            fan = simulate_one_game(remaining_hand, melds, remaining)
            if fan > 0:
                wins += 1
                total_fan += fan
        win_rate = wins / num_games
        avg_fan = total_fan / wins if wins > 0 else 0
        ev = win_rate * avg_fan
        name = tile_name(discard)
        results.append({"discard": discard, "name": name,
                        "ev": round(ev, 2),
                        "win_rate": round(win_rate, 4),
                        "avg_fan": round(avg_fan, 1)})

    return sorted(results, key=lambda r: -r["ev"])
```

## 性能数据

| 手牌复杂度 | num_games | 耗时 | 说明 |
|-----------|-----------|------|------|
| 13 张，无副露 | 500 | ~1.5 秒 | 典型场景 |
| 13 张，有副露 | 500 | ~2.0 秒 | 牌池更小 |
| 标准 13 张 | 2000 | ~6.5 秒 | 高精度场景 |
| 混牌型 | 500 | ~2.5 秒 | 多个出牌选项需要更多模拟 |

**经验法则**：每张出牌 500 局 × 13 张 = 6500 局可接受。超 2000 局/出牌开始延迟明显。

## 与本引擎其他模块的集成

```
monte_carlo.py ──calls──▶ simulate_one_game()
    │                        │
    │                        ├── is_any_win()  [core/win_checker.py]
    │                        ├── FanContext    [core/fan_calculator.py]
    │                        ├── calculate_fan [core/fan_calculator.py]
    │                        └── Hand()        [core/hand.py]
    │
    └── called_by ◀── game_engine.full_analysis(use_monte_carlo=True)
```

## 已知限制

1. **不模拟对手行为**：摸牌晋升仅考虑自摸，不含荣和（点炮）。因此 EV 偏向自摸型牌型。
2. **单一深度**：max_depth=8 对所有选手统一。对近听牌（0-1 向听）深度足够，对远听牌（3+ 向听）可能不够。
3. **重计算**：每次模拟都重新随机 shuffle 牌池。可改用固定种子做对比实验，但当前未实现。
4. **方差控制**：500 局/出牌的误差约 ±3%。增加局数到 2000 可降到 ±1.5%。
