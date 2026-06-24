---
name: mahjong-engine
description: 国标麻将决策引擎构建 — 编码、胡牌检测、向听数、番数算分、听牌推荐、Web API。参考 TXPokerAssist 的 TDD+数学引擎先行的模式。
trigger: 麻将/国标/General Mahjong Assist/胡牌/向听数/番数算分/番种/listen/听牌/API
---

# Mahjong Decision Engine

## 架构

```
core/ → decision/ → api/+web/
```

**core** 层先做（高复杂度高风险），decision 层第二，UI 最后。

## 牌编码（0–132，单字节）

| 花色 | 代码范围 | 张数/种 | 点数 |
|------|----------|----------|------|
| 万   | 0–35     | 4        | 1–9  |
| 条   | 36–71    | 4        | 1–9  |
| 饼   | 72–107   | 4        | 1–9  |
| 风   | 108–119  | **3**    | 1–4  |
| 箭   | 120–131  | 4        | 1–3  |

**关键坑**：风牌每种 3 张而非 4 张。`encode()` 必须按花色区分 `base_per_tile`。

```python
base_per_tile = {WAN: 4, TIAO: 4, BING: 4, FENG: 3, JIAN: 4}[suit]
offset + (rank - 1) * base_per_tile
```

**命名规则**：风/箭牌不附加花色后缀（"东"非"东风"）。

### ⚠️ 硬性要求：JS-Python 编码双向验证

每次修改前端 `T(s,r)` 函数或后端 `encode()` 时，**必须**执行交叉验证。这是本引擎最高频的 bug 来源。

```bash
# 对每个花色取首/中/尾三点，确认 JS 公式精确匹配 Python encode()
python3 -c "
from core.tile import encode
# 必须与 JS T(s,r) 中的 base 和 per 完全一致
base = [0, 36, 72, 108, 120]
per  = [4, 4, 4, 3, 4]
for s, name in enumerate(['万','条','饼','风','箭']):
    for r in [1, 5, 9] if s < 3 else [1, 2, 4]:
        py = encode(s, r)
        js = base[s] + (r-1) * per[s]
        assert py == js, f'{name}{r}: py={py} js={js}'
print('JS-Python 编码验证通过')
"
```

**历史教训**：旧 JS 公式 `s*28+(r-1)*4` 导致条/饼/风/箭全部编码错误且跨花色重叠（万8=28=条1）。详见 `references/bug-patterns.md` 第7条。

## 手牌结构

```python
class Hand:
    tiles: List[int]       # 原始牌列表
    counts: Dict[int, int] # {编码: 张数}
    suit_counts: Dict[int, Dict[int, int]] # {花色: {点数: 张数}}
    melds: List[List[int]] # 副露
```

## 胡牌检测

### 标准胡牌（4 面子 + 1 将）

**算法**：贪心法 — 从低点到高点扫描，刻子优先，顺子填充。

```python
def _remove_melds_from_array(arr):
    result = 0
    for i in range(7):
        while arr[i] > 0:
            if arr[i] >= 3:     # 刻子优先
                arr[i] -= 3; result += 1
            elif arr[i+1] > 0 and arr[i+2] > 0:  # 顺子
                arr[i] -= 1; arr[i+1] -= 1; arr[i+2] -= 1; result += 1
            else:
                break
    return result
```

**缺陷**：贪心法对部分缠连边张手牌会误判（如 22233344466789 → 贪心取 222/333/444 后从 66789 取 789 剩 6 单张）。后续需改用递归/DP 回溯。详见 `references/bug-patterns.md` #11。

### 七对

- 14 张，每种牌最多 4 张（物理约束）
- 所有牌张数为偶数 → 可分解为 7 对
- 不能有副露

```python
def is_seven_pairs(tiles):
    if len(tiles) != 14 or any(c > 4 for c in counts.values()):
        return False
    return all(c % 2 == 0 for c in counts.values())
```

### 十三幺

- 预计算 13 种幺九牌集合
- 14 张 = 13 种各 1 张 + 其中 1 种重复（将）
- 不能有非幺九牌

### ⚠️ 组合龙检测禁区

组合龙检测 **永远不能无条件返回 True**。这是该 session 发现的关键 bug：

```python
# ❌ 严重错误 — 任何 14 张牌都会被认为是胡牌
def is_composite_dragon(tiles):
    if len(tiles) != 14: return False
    # ... 某种宽松的检查
    return True  # ← 这个 return True 导致全局胡牌检测器永远为真！

# ✅ 正确做法：不满足条件时返回 False
def is_composite_dragon(tiles):
    if len(tiles) != 14: return False
    # 严格检查三个花色是否匹配 147/258/369 的标准组合龙排列
    suit_ranks = {s: set() for s in [WAN, TIAO, BING]}
    for code, cnt in Counter(tiles).items():
        s, r = decode(code)
        if s in (WAN, TIAO, BING):
            suit_ranks[s].add(r)
    if sum(len(s) for s in suit_ranks.values()) < 9:
        return False
    patterns = [
        ({1,4,7}, {2,5,8}, {3,6,9}),
        ({1,4,7}, {3,6,9}, {2,5,8}),
        ({2,5,8}, {1,4,7}, {3,6,9}),
        ({2,5,8}, {3,6,9}, {1,4,7}),
        ({3,6,9}, {1,4,7}, {2,5,8}),
        ({3,6,9}, {2,5,8}, {1,4,7}),
    ]
    for p0, p1, p2 in patterns:
        if (suit_ranks[WAN] >= p0 and suit_ranks[TIAO] >= p1 and suit_ranks[BING] >= p2):
            return True
    return False  # ← 必须返回 False！
```

**教训**：任何 stubbed-out 特殊胡牌型检测，必须 `return False` 或 `raise NotImplementedError`，**绝不能默认返回 True**。否则 `is_any_win` 全局胡牌检测器会返回 True 给任何 14 张牌。

## 向听数计算（`shanten.py`）

### 4 类取最小

```python
shanten = min(standard, seven_pairs, thirteen_orphans, composite_dragon)
```

返回格式：`{"min": N, "standard": N, "seven_pairs": N, "thirteen_orphans": N, "composite_dragon": N}`

⚠️ **注意**：返回值没有 "type" 键。如果需要知道哪种类型的向听数最小，需遍历 type_names 字典匹配。

### 标准面子手向听数

**公式**：`shanten = 8 - 2*melds - min(partials, 4-melds) - pair`

**算法**：递归回溯枚举所有面子/搭子/对子/单张组合。

```python
@lru_cache(maxsize=100000)
def _calc_meld_partial_recursive(arr, has_pair):
    # 找到第一个非 0 位置
    # 尝试分支（按优先级）：
    #   1. 刻子 → meld+1
    #   2. 顺子 → meld+1
    #   3. 对子 → pair=True（仅当 has_pair=False）
    #   4. 两面搭(rank, rank+1) → partial+1
    #   5. 边张搭(rank, rank+2) → partial+1
    #   6. 单张 → 废弃（无贡献）
```

### ⚠️ 关键坑：排序优先级

**`score_key` 必须将将牌优先级高于搭子数量！**

```python
# ❌ Python 原生元组比较会选 (4, 1, False) 优于 (4, 0, True) — 因为 1 > 0
if cand > (best_melds, best_partials, best_pair):  # WRONG

# ✅ 必须用自定义评分键
def _score_key(value):
    m, p, hp = value
    return (m, 1 if hp else 0, p)  # pair(True=1) 优先于 partials 数量
```

**原因**：`(melds=4, partials=1, hp=False)` 在贪心路径中会吃掉将牌的配对牌当搭子，导致 `has_pair=False`。虽然 partials=1 看起来更好，但 shanten 公式中 pair 的权重更高。

### ⚠️ 关键坑：数组索引偏移

`decode()` 返回的点数是 1-based（1-9），但 `rank_arr` 是 0-based。必须做 -1 转换：

```python
# ❌ rank_arr[rank] = cnt   # rank 从 1 开始 → 数据全偏移了
# ✅ rank_arr[rank - 1] = cnt  # 正确
```

### 花色的独立处理

手牌按花色分组后独立计算，再累加 melds/partials/pair：

```python
for suit in [WAN, TIAO, BING]:
    rank_arr = [0] * 11
    for code, cnt in counts.items():
        s, r = decode(code)
        if s == suit and 1 <= r <= 9:
            rank_arr[r - 1] = cnt  # ← -1 偏移
    m, p, hp = calculate_melds_partials(rank_arr)
    total_melds += m; total_partials += p
    if hp: has_pair = True  # 仅首个 pair 生效
```

字牌（风/箭）独立处理：只能做刻子（cnt≥3 → meld+1）或对子（cnt≥2 → pair），单张字牌不计入 partials。

### 边界条件

| 场景 | 13 张 → shanten | 说明 |
|------|-----------------|------|
| 4 面子 + 1 将 | -1 | 已胡牌 |
| 4 面子 + 1 单 | 0 | 单骑听 |
| 3 面子 + 1 将 + 1 搭 | 0 | 两面听/边张听 |
| 3 面子 + 1 将 + 1 单 | 1 | 一上听 |
| 2 面子 + 1 将 + 2 搭 | 1 | 一上听 |

### 七对向听数

```
shanten = 6 - pairs    # pairs = sum(cnt // 2 for cnt in counts.values())
```

4 张相同的牌算 2 个对子。

### 十三幺向听数

```
shanten = 13 - unique_orphans - (1 if any cnt >= 2 else 0)
```

非幺九牌不计数。

### 进张数计算

```python
def calculate_acceptance(tiles, melds=None, remaining=None):
    current = calculate_shanten(tiles)["min"]
    acceptance = 0
    for each possible tile_code:
        new_shanten = calculate_shanten(tiles, melds, draw_tile=code)["min"]
        if new_shanten < current: acceptance += available
    return acceptance
```

**关键**：用 `draw_tile=code` 参数而非 `tiles + [code]`。因为 `tiles` 是 13 张（不包含刚摸的牌），用参数添加第 14 张牌，避免手牌长度突变。

### 候选出牌评估

```python
def discard_analysis(tiles, melds=None, remaining=None):
    result = []
    for discard in unique_tiles:
        new_tiles = tiles.copy(); new_tiles.remove(discard)
        post = calculate_shanten(new_tiles)["min"]
        acc = calculate_acceptance(new_tiles)
        result.append({"discard": code, "name": ..., "post_shanten": post, "acceptance": acc})
    return sorted(result, key=lambda r: (r["post_shanten"], -r["acceptance"]))
```

输出格式：`[{discard, name, post_shanten, acceptance}]`，按向听数↑ 进张数↓ 排序。

详细算法说明见 `references/shanten.md`。

## 番数算分（`fan_calculator.py`）

### 注册系统

使用装饰器模式注册每个番种判定函数：

```python
@register_fan(6, "碰碰和")
def _check_all_triplets(ctx: FanContext) -> int:
    ...
```

### FanContext

```python
@dataclass
class FanContext:
    hand: Hand                  # 手牌
    win_tile: int               # 胡牌编码
    is_self_drawn: bool         # 自摸（默认 True）
    win_on_discard: bool        # 点炮胡（由 __post_init__ 自动推导）
```

**关键**：`win_on_discard` 必须从 `is_self_drawn` 自动推导：

```python
def __post_init__(self):
    """自动推断派生字段"""
    if not self.is_self_drawn and not self.win_on_discard:
        self.win_on_discard = True
```

如果不加这个，使用 `FanContext(hand=hand, is_self_drawn=False, ...)` 创建时 `win_on_discard` 仍为 False，导致 门前清(4番) 不会触发，平和(4)+无字(1)=5番 < 8番 → 总番=0。对于 平和+门前清 的手牌，点炮胡应该是 9番。

### 规则约束

- **起胡门槛**：8 番 — `result.total < 8 → clear → 0`
- **封顶**：88 番 — 达到后停止检测
- 非胡牌 → 总番 = 0

### 关键坑

1. **碰碰和检测**：不要用"连续顺子"来排除——连续三组刻子（如 111 222 333）也会触发顺子检查导致错误排除。正确的做法：每张牌逐 3 减，最多 1 种剩 2（将牌）。
2. **花龙/青龙误报**：`tiles_to_rank_array` 不区分顺子和刻子，只要一个花色有 123/456/789 的覆盖位就可能误报。后续需传入实际面子分解。
3. **一色三同顺误报**：`rank_arr[i] >= 3` 会在三个连续刻子时触发（如 111 222 333 444 → 检测出 111 222 333 三组相同的"顺子"序列）。这是贪心法的缺陷。
4. **箭刻/双箭刻**：箭牌只有 3 种（中发白），计数时用 `sum(cnt for code where decode(code)[0]==JIAN and decode(code)[1]==rank)`。
5. **小于 8 番测试难构造**：多数手牌自带至少 4-6 番（碰碰和 6 + 无字 1 + 自摸 1 = 8）。构造 < 8 番的手牌需要混合刻子和顺子，避免触发青龙/花龙等高番条件。

| 已实现番种（76/81 注册，标准对齐度提升，最新 2026-06-03）

注：Iter 006 番值修正 — 大四喜 64→**88**, 喜相逢 4→**2**, 连六 1→**2**
缺 5 个番种：4暗杠(88), 连七对(48), 全双刻(24), 推不倒(8), 无番和(8)

## 番种缺口攻坚方向

| 番种 | 番值 | 难度 | 实现方案 |
|---|---|---|---|
| 4暗杠 | 88 | ⭐⭐⭐ | 检测 4 组暗杠（手牌必须全暗） |
| 连七对 | 48 | ⭐⭐⭐ | 同花色 7 对连续点数 |
| 全双刻 | 24 | ⭐⭐ | 全部刻子为 2/4/6/8 点数 |
| 推不倒 | 8 | ⭐⭐ | 所有牌左右对称判断 |
| 无番和 | 8 | ⭐⭐⭐ | 排除法：胡牌但不触发任何番种 |

详见 `PLAN.md` §6 或项目根目录的迭代计划。

| 番值 | 番种 |
|------|------|
| 88 | 天胡/地胡/人胡/四杠子/九莲宝灯/绿一色/**大四喜** |
| 64 | 小四喜/小三元/四暗刻 |
| 48 | 大三元/一色四同顺/一色四节高 |
| 32 | 混幺九/七星不靠 |
| 24 | 七对/清一色/一色三同顺/一色三节高/全大/全中/全小 |
| 16 | 青龙/三色同刻(三同刻) |
| 12 | 大于五/小于五/全不靠/三风刻 |
| 8 | 花龙/三色三同顺/杠上开花/抢杠和/海底捞月(妙手回春)/杠上炮 |
| 6 | 碰碰和/混一色/五门齐/双箭刻/全求人/三色三步高/双暗杠 |
| 4 | 全带幺/不求人/双明杠/和绝张/箭刻 |
| 2 | 断幺九/双暗刻/一般高/幺九刻/双同刻/圈风刻/门风刻/单钓将/喜相逢/连六 |

合计 **75/81 种注册**（Iter 003-004 新增 20 种：四暗刻/一色四同顺/一色四节高/杠上炮/双暗杠/双明杠/圈风刻/门风刻/边张/坎张/十三幺/一色双龙会/连七对/清幺九/一色四步高/三杠/组合龙/推不倒/和绝张/单钓将(2番)）。
完整番表见 `references/fan_table.md`（已标注每种状态）。

## 听牌推荐（`decision/listen_engine.py`）

### 枚举可胡牌

对 0 向听的手牌，枚举所有可能的胡牌：

```python
def enumerate_winning_tiles(tiles, melds=None, remaining=None):
    winners = []
    seen = set()  # 按 (suit, rank) 去重
    for code in range(TOTAL_TILES):
        s, r = decode(code)
        if (s, r) in seen: continue  # 同一花色的同一点数只测一次
        seen.add((s, r))
        if remaining and not remaining.get(code, 0): continue
        if is_any_win(tiles + [code], melds):
            winners.append(code)
    return winners
```

**关键**：必须按 (花色, 点数) 去重！编码里每种点数有 4 个独立代码（3 个风牌），不去的重的话同一张听牌会重复出现 4 次。

### 评分系统

```python
def score_listen_tile(tile_code, hand_tiles, melds, remaining, ...):
    # 1. 计算番数（统一用 discard-win，不含自摸）
    ctx = FanContext(hand=Hand(test_hand), win_tile=tile_code,
                     is_self_drawn=False)  # ← 固定点炮胡，自摸额外算
    fan = calculate_fan(ctx)
    if fan.total < 8: return None  # 不起胡的牌不算有效听牌
    
    # 2. 计算剩余张数
    # 3. 综合评分 = 番数 × 剩余张数
    score = fan.total * remaining
```

评分用 `is_self_drawn=False` 确保门前清（4番）计入，避免平和+无字+自摸=6番<8番被过滤。

### 单面听 vs 两面听

```
单面听: 123万 456万 789万 55条 12条 → 3条 ×4 → 33番 (青龙+花龙+平和+门前清+无字)
两面听: 234万 456万 789万 33条 67条 → 5条/8条 ×4 → 9番 (平和+门前清+无字)
```

## 全面牌局分析引擎（`decision/game_engine.py`）

Session-005 新增。在基础分析之上扩展为**完整牌局决策**。

### GameState 模型

```python
@dataclass
class GameState:
    hand: List[int]                      # 我的手牌
    melds: List[List[int]]              # 我的副露
    discards: Dict[int, List[int]]      # 各家舍牌 {座位: [编码]}  1=下家 2=对家 3=上家
    opponent_melds: Dict[int, List[List[int]]]  # 他家副露
    seat_wind: int = 0
    round_wind: int = 0
    is_self_drawn: bool = True
    last_discard: Optional[int] = None  # 他家刚打出的牌（用于吃碰杠判断）
```

### 核心分析管道

```python
def full_analysis(state: GameState) -> GameAnalysis:
    # 1. 根据可见牌（手牌+副露+舍牌）计算剩余牌池
    remaining = build_remaining(...)
    
    # 2. 向听数 + 进张
    shanten_val = calculate_shanten(hand)["min"]
    acceptance = calculate_acceptance(hand, melds, remaining)
    
    # 3. 出牌建议（含防守评分）
    discard_options = rank_discard_options(hand, melds, remaining, discards)
    # 排序: 向听数↑ → 危险等级低↑ → 进张数↓
    
    # 4. 吃碰杠评估
    action_options = evaluate_actions(hand, melds, last_discard, remaining, ...)
    
    # 5. 听牌分析
    listen_analysis = analyze_listen(hand, melds, remaining, ...)
    
    # 6. 防守信息
    defense = analyze_defense(state.discards, state.opponent_melds, remaining)
```

出牌建议的 danger_level 字段值由旧版 "低/中/高" 改为了 6 级制：极危/高危/中危/警惕/安全/绝对安全。详见 [防守分析（安全度矩阵）](#防守分析安全度矩阵)。

### 出牌推荐（含防守评分）

```python
def rank_discard_options(tiles, melds, remaining, discards,
                         opponent_melds=None) -> List[DiscardOption]:
    raw = core_discard_analysis(tiles, melds, remaining)
    for each option:
        tile_type = classify_tile_type(tile_code)  # "字牌"/"幺九"/"中张"
        base = _safety_score(tile_type, global_count)
        # 如果有对手副露信息，做精细调整
        danger_level_num = base
        if opponent_melds:
            for seat in (1,2,3):
                adj = _per_opponent_adjust(base, code, seat, discards, opponent_melds)
                if adj < danger_level_num: danger_level_num = adj
        danger_level = _safety_level(danger_level_num)  # 6级制
    # 排序: post_shanten ↑ → danger_level(极危0→绝对安全5) ↑ → acceptance ↓
```

### 吃碰杠评估

```python
def evaluate_actions(hand, melds, last_discard, remaining, ...):
    # 碰：hand 中有 2+ 张 last_discard
    # 杠：hand 中有 3+ 张 last_discard（明杠）
    # 加杠：已有碰出的副露 + hand 中有第4张
    # 吃：枚举3种顺子组合（discard在左/中/右），每个点位检查hand_ranks
    # 胡（tsumo）：hand + last_discard 可胡，返回番数+番种
    # 排序: post_shanten ↑ → acceptance ↓
```

### 防守分析（安全度矩阵）

**迭代007升级（2026-06-03）**：从"全局舍牌统计"升级为**每对手独立评分**的安全度矩阵。

### 核心函数

```python
def analyze_defense(discards: Dict[int, List[int]],
                    opponent_melds: Dict[int, List[List[int]]],
                    remaining: Dict[int, int]) -> DefenseInfo:
    """
    计算每张牌 × 3 家对手的安全度矩阵。

    返回:
      DefenseInfo.safety_matrix: Dict[int, TileSafety] — {编码: TileSafety}
      DefenseInfo.top_danger: List[TileSafety] — 最危险的10张牌
      DefenseInfo.top_safe: List[TileSafety] — 最安全的10张牌
      DefenseInfo.summary: str — "⚡ 5条·6条·8万  |  ✅ 东·南·白"
    """
```

### 安全度评分模型

```python
# 基线（基于牌类型 + 这家对手出过几张）
def _safety_score(tile_type: str, opp_discard_count: int) -> int:
    字牌+0=40  字牌+1=70  字牌+2+=95
    幺九+0=15  幺九+1=50  幺九+2+=80
    中张+0=5   中张+1=35  中张+2+=75

# 调整（基于对手副露/舍牌模式）
def _per_opponent_adjust(base, tile_code, opponent_seat, ...) -> int:
    跟打(对手刚出过同牌且只出过1张)  +20
    对手有同花色刻子/杠              -20
    对手有2+字牌副露(字牌场景)       -30
    对手出3+张同花色中张             -10

# 等级映射
def _safety_level(score: int) -> str:
    >=96: 绝对安全  81-95: 安全  61-80: 警惕
    41-60: 中危     21-40: 高危   0-20: 极危
```

**整体安全度** = min(3 家对手的安全度) — 最危险的那家决定全局。

### API 响应新增字段

```python
class DefenseResp(BaseModel):
    dangerous_tiles: List[dict]       # 旧格式（向后兼容）
    safe_tiles: List[dict]            # 旧格式
    summary: str
    safety_matrix: Optional[dict]     # 新增：{编码: {name, tile_type, overall_safety, per_opponent: [...]}}
    top_danger: Optional[List[dict]]  # 新增：最危险的10张
    top_safe: Optional[List[dict]]    # 新增：最安全的10张
```

### 旧测试适配

`analyze_defense` 签名从 `(discards, remaining)` 变为 `(discards, opponent_melds, remaining)`。旧测试调用需要补 `{}` 作为 opponent_melds。出牌建议的 danger_level 从 "低/中/高" 变为 6 级制。详见 `tests/test_defense.py`（24项）。

### ⚠️ 关键坑

1. **仅对手出过1张且为最后出牌时才加跟打分**。出过2+张说明肯定不胡这张，不加跟打。
2. **整体安全度=min(3家)**。即使对手1绝对安全，只要对手2极危，整体就是极危。这是保守策略。
3. **剩余0张的牌不进入 safety_matrix**。
4. **字牌未出≠安全**。字牌基线40(中危级)，但如果有对手有多个字牌副露，降至10(极危级)。

### ⚠️ 关键坑：`is_any_win_fast` 漏检特殊胡牌型

`calculate_fan` 入口函数使用 `is_any_win_fast` 判断是否胡牌。**该函数必须检查所有胡牌型**，否则特殊胡牌（全不靠/七星不靠/一色双龙会/连七对）会被过滤掉，导致番数计算返回 0。

```python
# ❌ 错误 — 只检查标准/七对/十三幺
def is_any_win_fast(tiles, melds=None):
    from core.win_checker import is_standard_win, is_seven_pairs, is_thirteen_orphans
    return (is_standard_win(tiles, melds) or
            is_seven_pairs(tiles, melds) or
            is_thirteen_orphans(tiles, melds))

# ✅ 正确 — 检查全部 7 种胡牌型
def is_any_win_fast(tiles, melds=None):
    from core.win_checker import (
        is_standard_win, is_seven_pairs, is_thirteen_orphans,
        is_composite_dragon, is_all_sequences_no_pairs,
        is_seven_stars, is_double_dragon_one_suit,
        is_consecutive_seven_pairs,
    )
    return (is_standard_win(tiles, melds) or
            is_seven_pairs(tiles, melds) or
            is_thirteen_orphans(tiles, melds) or
            is_composite_dragon(tiles, melds) or
            is_all_sequences_no_pairs(tiles, melds) or
            is_seven_stars(tiles, melds) or
            is_double_dragon_one_suit(tiles, melds) or
            is_consecutive_seven_pairs(tiles, melds))
```

### ⚠️ 关键坑：14 张手牌的进张计算

`calculate_acceptance()` 内部调用 `calculate_shanten(tiles, melds, draw_tile=code)` — 如果传入 14 张手牌 + draw_tile，会构建一个 15 张的 `Hand` 对象 → Hand 构造函数拒绝(上限 14)。

**修复**：在 `full_analysis` 中，手牌 > 13 张时不计算进张牌列表：
```python
hand_for_acceptance = state.hand[:13] if len(state.hand) > 13 else state.hand
acceptance = calculate_acceptance(hand_for_acceptance, ...)
# 进张牌: if len(hand) > 13: break  # 14张需先出牌
```

## 性能优化：LRU 缓存

热路径函数使用 `functools.lru_cache` 消除重复计算。

### `is_any_win` 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=4096)
def _cached_win_check(tiles_tuple, melds_tuple):
    """缓存胡牌检测结果。tiles_tuple 是 sorted(tiles) 的元组版本。"""
    ...
```

**关键**：缓存 key 用 `tuple(sorted(tiles))` 而非 `frozenset(tiles)` — 牌池有重复牌，set 会去重导致错误命中（如 111 → 1，丢失刻子信息）。

### `calculate_shanten` 缓存

```python
@lru_cache(maxsize=4096)
def _cached_shanten(tiles_tuple, melds_tuple, remaining_tuple):
    ...
```

### 缓存验证

```python
def test_win_cache_hits():
    tiles = [0,1,2, 36,37,38, 72,73,74, 108,109,110, 4,4]
    result1 = is_any_win(tiles)
    result2 = is_any_win(list(tiles))  # 不同 List 对象，但 sorted(tiles) 相同
    assert result1 == result2
    info = is_any_win.cache_info()
    assert info.hits > 0  # 第二次命中缓存
```

### 蒙特卡洛模拟决策引擎（`decision/monte_carlo.py`）

Iter 004 新增。对每张可能打出的牌，模拟 N 局摸牌走向，统计每张出牌的 EV。用于辅助判断「该打哪张」，绕过纯规则分析无法评估的远期牌效差异。

完整说明见 `references/monte_carlo.md`。

### 接口

```python
def evaluate_all_discards(hand, melds=None, remaining=None,
                          simulations=500, max_draws=8,
                          workers: int = 0) -> List[dict]:
    """
    对每张手牌（按花色+点数去重），模拟 simulations 局：
      - 移除该牌 → 13 张
      - 从牌池中随机摸牌模拟进张
      - 直到摸到第 max_draws 张或可胡牌
      - 统计胜率、平均番数 → EV = 胜率 × 平均番数
    workers: 并行进程数（0=自动=CPU核数）
    返回按 EV 降序的：{tile, tile_name, simulations, wins, win_rate, avg_fan, ev}
    """
```

#### ⚠️ 关键坑：按编码去重 vs 按牌型去重

`evaluate_all_discards` 必须按 `(suit, rank)` 去重，而不是 `set(tiles)`。因为每种点数有 4 个编码（风牌 3 个），`set(tiles)` 会让同一张牌被模拟多次。

```python
# ❌ 错误 — 手牌 [0,1,2,3, ...] → set = {0,1,2,3,...} → 1万模拟 4 次
unique_tiles = set(hand)

# ✅ 正确 — 按 (suit, rank) 分组，只保留一个编码
unique_by_type: Dict[Tuple[int, int], int] = {}
for tile in hand:
    suit, rank = decode(tile)
    key = (suit, rank)
    if key not in unique_by_type:
        unique_by_type[key] = tile
```

#### 并行加速（Iter 006）

使用 `ProcessPoolExecutor` 并行模拟不同出牌：

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

with ProcessPoolExecutor(max_workers=workers) as executor:
    future_map = {
        executor.submit(simulate_discard, hand, tile, melds, pool,
                        simulations, max_draws): tile
        for tile in tiles_to_eval
    }
    for future in as_completed(future_map):
        results.append(future.result())
```

- 每张出牌独立模拟，并行到全部 CPU 核
- 错误隔离：单张模拟失败只返回零结果，不阻塞其他牌
- `workers=0` → `min(os.cpu_count(), 出牌数)`

#### MC → 出牌建议融合（Iter 006）

当 `use_monte_carlo=True` 时，EV 结果被融合到 `DiscardOption` 排序中：

```python
# 1. 建立 (suit, rank) → EV 查找表
mc_by_type: Dict[Tuple[int, int], dict] = {}
for r in mc_results:
    s, rk = decode(r["tile"])
    mc_by_type[(s, rk)] = r

# 2. 更新每个 DiscardOption
for opt in discard_options:
    s, rk = decode(opt.tile)
    key = (s, rk)
    if key in mc_by_type:
        opt.mc_ev = mc_r["ev"]
        opt.reason += f" | MC: 胜率{wr_pct:.1f}% EV={ev:.2f}"

# 3. 按 EV 降序重排序（启用 MC 时替代原有向听数+安全等级排序）
discard_options.sort(key=lambda o: (-o.mc_ev, o.post_shanten, ...))
```

**排序规则变更**：启用 MC 时，主排序键从 `(post_shanten, danger_level, -acceptance)` 变为 `(-mc_ev)`。EV 最高的牌排第一位，不受传统规则约束局限。

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `num_games` | 500 | 每张出牌的模拟局数。500 局约 1-2 秒。 |
| `max_depth` | 8 | 每局最大摸牌深度。模拟「未来 8 步内能否胡牌」。 |

### 内置保护

```python
def simulate_one_game(tiles, melds, remaining):
    """单局模拟：从剩余牌池随机摸牌，直到胡牌或深度耗尽或牌池不足。"""
    hand = list(tiles)
    pool = list(remaining.elements())
    random.shuffle(pool)
    for i in range(max_depth):
        if not pool:
            return 0  # 牌池耗尽立判失败
        draw = pool.pop()
        hand.append(draw)
        if len(hand) > 14:  # 手牌超过 14 张保护
            break
        if is_any_win(hand, melds):
            # 查番数
            ctx = FanContext(hand=Hand(hand), win_tile=draw, is_self_drawn=True)
            fan = calculate_fan(ctx)
            return fan.total if fan else 0
    return 0
```

### 集成到 GameEngine

```python
@dataclass
class GameAnalysis:
    ...
    monte_carlo: Optional[List[Dict]] = None  # [{discard, name, ev, win_rate, avg_fan}]

def full_analysis(state: GameState, use_monte_carlo=False) -> GameAnalysis:
    ...
    if use_monte_carlo:
        from decision.monte_carlo import evaluate_all_discards
        analysis.monte_carlo = evaluate_all_discards(
            state.hand, state.melds, remaining, num_games=500, max_depth=8)
```

**默认关闭**（`use_monte_carlo=False`）— 500 次模拟耗时 1-2 秒，影响 API 响应时间。

### 关键限制

1. **随机性**：模拟结果有随机方差。增加 `num_games` 可降低方差但线性增加耗时。
2. **番数估算**：只计算胡牌时的番数，不模拟「听牌但不胡」的局 — 这是一阶近似。
3. **对手行为**：不模拟对手出牌/吃碰杠 — 仅考虑自摸晋升。

详见 `references/monte_carlo.md`。

## Web API（`api/main.py`）

### 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/analyze` | POST | 基础手牌分析 |
| `/api/game-analyze` | POST | **全面牌局分析（含吃碰杠+防守）** |
| `/api/tiles` | GET | 所有牌面信息 |
| `/api/health` | GET | 健康检查 |
| `/` | GET | 静态前端（index.html） |

### 全面分析请求（`/api/game-analyze`）

```python
{
    "hand": [int],                # 13-14 张手牌编码
    "melds": [[int], ...],        # 可选，自家副露
    "discards": {"1": [int], ...}, # 各家舍牌 1=下家 2=对家 3=上家
    "opponent_melds": {"1": [[int], ...]},  # 他家副露
    "seat_wind": int,             # 座风
    "round_wind": int,            # 圈风
    "is_self_drawn": bool,        # 自摸还是吃牌
    "last_discard": int | None    # 对方刚打出的牌（吃碰杠判断）
    "use_monte_carlo": bool       # 是否启用蒙特卡洛模拟（默认 false，500 局/出牌，多核并行）
}
```

### 全面分析响应

```python
{
    "shanten": int,
    "shanten_types": {"standard": int, ...},
    "acceptance": int,
    "acceptance_tiles": [TileInfo],
    "discard_options": [{"tile": TileInfo, "post_shanten": int, "acceptance": int, "danger_level": str, "reason": str, "mc_ev": float}],
    "action_options": [{"action": str, "tiles": [TileInfo], "post_shanten": int, "acceptance": int, "fan": int}],
    "listen_analysis": {"is_tenpai": bool, "options": [...]},
    "defense": {"dangerous_tiles": [...], "safe_tiles": [...], "summary": str},
    "hand_display": str,
    "monte_carlo": [{"tile": int, "tile_name": str, "simulations": int, "wins": int,
                     "win_rate": float, "avg_fan": float, "ev": float}]
}
```

### 分析请求

```python
{
  "hand": [int],          # 13-14 个牌编码
  "melds": [[int]],       # 可选，副露
  "remaining": {int:int}, # 可选，剩余牌池
  "seat_wind": int,       # 座位风 (default=1)
  "round_wind": int,      # 圈风 (default=1)
  "is_self_drawn": bool   # 是否自摸 (default=True)
}
```

### 分析响应

```python
{
  "is_tenpai": bool,
  "shanten": {"min": int, "face_str": str, "acceptance_count": int, "acceptance": [TileInfo]},
  "listen": [{"tile": TileInfo, "remaining": int, "fan": int, "fan_items": [...], "score": float}],
  "discard_advice": [{"discard": int, "name": str, "shanten_after": int, "acceptance_count": int}],
  "raw_hand": str
}
```

### 启动

```bash
cd ~/projects/general-mahjong-assist
python3 -m api.main   # borg: :8778
```

或 `bash start-web.sh`。

### 前端（当前版：单页合并式）

手机端暗绿桌布风格，HTML+CSS+JS 单页（零外部依赖），所有操作在同一页面完成。

**布局从上到下**：
1. **手牌预览条** — 实时显示已选牌，合并相同牌（"1万×3"），点 ✕ 移除一张
2. **牌选择网格** — 5 花色分组，9列网格，短按+1张，长按清空
3. **设置行** — 座风/圈风/摸牌模式切换
4. **三家舍牌**（默认展开）— 玩家 pill 切换，相同 ADD+长按清空 模式
5. **他家副露**（默认折叠）— 文字编码输入
6. **对方打牌**（默认折叠）— 小网格选择，用于吃碰杠判断
7. **分析按钮** — ≥13 张时亮金色提示
8. **结果区** — 操作英雄卡（最大的建议在最上方，可点击自动执行）

**交互模式**：

| 元素 | 短按 | 长按 |
|------|------|------|
| 手牌按钮 | +1 张 | 清空该牌 |
| 舍牌按钮 | +1 张（上限4） | 清空该牌 |
| 手牌条 ✕ | -1 张 | — |
| 结果"打 X"卡 | 从手牌移除该张 | — |

**花色配色**：万=金色、条=绿色、饼=蓝色、风=橙色、箭=红色

**显示函数关键规则**：
- `ts(c)` 短名：`t.rank + ['万','条','饼'][t.suit]` → "1万" "5条"、"东" "中"（字牌通过字符索引）
- `tn(c)` 全名：`n[r-1]+'万'` → "一万" "五条"
- ⚠️ 索引偏移坑：`['万','条','饼']` 而非 `['','万','条','饼']`

详见 `references/web-ui-impl.md`、`PLAN.md`（产品规划）、`PRODUCT_SPEC.md`（产品说明书）、`REPORT.md`（汇报文档）。

### Vercel 部署（Session-005）

国标麻将引擎可部署到 Vercel Serverless Functions。

**必需文件**:
| 文件 | 作用 |
|------|------|
| `api/index.py` | Vercel 入口，re-export `api.main.app` |
| `requirements.txt` | Python 依赖（fastapi, uvicorn, pydantic） |
| `vercel.json` | 路由 + build 配置 + Python 3.11 |
| `runtime.txt` | `python-3.11`（Vercel 备选版本声明） |

**api/index.py 示例**:
```python
"""
Vercel Serverless Function 入口。FastAPI app 在 api/main.py 中，此处直接 re-export。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from api.main import app
```

**vercel.json**:
```json
{
  "builds": [{
    "src": "api/index.py",
    "use": "@vercel/python",
    "config": { "maxLambdaSize": "15mb", "runtime": "python3.11" }
  }],
  "routes": [{
    "src": "/(.*)",
    "dest": "api/index.py"
  }]
}
```

**依赖**: fastapi, uvicorn[standard], pydantic — 通常 < 30MB，远低于 50MB Lambda 限制。

**常见失败原因**:
1. 缺少 `api/index.py` — Vercel 找不到 Serverless 入口
2. 缺少 `requirements.txt` — 依赖无法安装
3. `vercel.json` 路由未配置 — 所有请求 404
4. `sys.path.insert` 路径不对 — 内部模块 import 失败
5. Python 版本不匹配 — 默认 3.9，需声明 3.11

## 通用陷阱（Anti-Patterns）

1. **任何检测器 stubbed 为 True** → 会导致全局胡牌检测永远为真。必须返回 False 或 raise NotImplementedError。
   **真实案例**：`is_composite_dragon()` 在简化实现后 `return True` → `is_any_win()` 对任何 14 张牌都返回 True → 听牌推荐引擎完全失效，返回 34 张"可胡牌"。
2. **未去重的听牌枚举** → 编码里每点数有 3-4 个独立代码，遍历所有代码会返回重复听牌。必须按 (suit, rank) 去重，每花色+点数只测一次。
3. **FanContext.win_on_discard 不自动推导** → 直接设 `is_self_drawn=False` 时 `win_on_discard` 还是 False → 门前清检测失败 → 平和+无字 组合只有 5番 < 8番 → 被起胡门槛过滤 → 两面听的一半听牌显示不出。必须在 FanContext 加 `__post_init__` 自动推导。
4. **向听数返回值无 "type" 键** → API 需要自己遍历 type_names 匹配最小值。
5. **discard_analysis 返回键名** → 是 `post_shanten` 和 `acceptance`，不是 `shanten_after` 和 `acceptance_count`（API 层需做映射）。
9. **全求人测试的手牌结构** → 全求人时手牌包含 2 张相同的牌（单钓牌+胡牌），不能是 1 张。`len(tiles) == 2 and tiles[0] == tiles[1]` 才是正确的单钓检测。
10. **九莲宝灯检测「< vs >」反转** → 原实现用 `rank_arr[i] > target[i]: return 0` 禁止任何点数多出1张，导致14张胡牌永远判否；后面的 `total_extra = sum(... if rank_arr[i] > target[i])` 因前句已 return 而永不执行。**修复**：改为 `rank_arr[i] < target[i]: return 0`（基础不足），14张时允许恰好1个点数多1张。

## 测试统计

| 版本 | 测试数 | 模块 |
|------|--------|------|
| Phase 0 | 98 | tile(24) + hand_parser(27) + win_checker(27) + fan_calculator(20) |
| Phase 1 | 117 | + shanten(19) |
| Phase 2+API | 128 | + listen_engine(11) |
| Phase 2 番种补完 | 143 | + test_new_fans(15) — 番种 33→44 |
| Phase 3 Game Engine | 153 | + test_game_engine(10) — 番种 56/81 |
| Iter 004 深度推进 | 183 | + test_new_depth(18) + test_depth_b(12) — 番种 76/81 + MC |
| Iter 006 番种校准+九莲 | **197** | + test_nine_gates(14) — 大四喜88, 喜相逢2, 连六2 |
| **当前基线 (2026-06-03)** | **221** | 番种76/81, 防守安全度矩阵(迭代007—每对手独立评分), Phase 2 计划已完成。项目文档: `PLAN.md`(产品规划) · `PRODUCT_SPEC.md`(产品说明书) · `REPORT.md`(汇报文稿) · `docs/ITERATION_PLAN.md`(迭代计划) |
