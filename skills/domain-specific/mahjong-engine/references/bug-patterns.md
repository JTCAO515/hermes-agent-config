# Bug Patterns — 国标麻将引擎

本文件记录该引擎在开发过程中发现的所有 bug 模式，作为未来调试的快速参考。

## 1. Composite Dragon Stub → 全局胡牌失效 🔥

**现象**：任何 14 张牌都被 `is_any_win()` 判定为可胡。

**根因**：`is_composite_dragon()` 在简化实现后，最后一行是 `return True`（注释"完善实现见 Phase 2"），被 `check_all_wins()` → `is_any_win()` 调用后，永远返回 True。

**修复**：改为严格的 6 种排列匹配检查，不匹配时 `return False`。

**教训**：任何 stub 函数，必须 `return False` 或 `raise NotImplementedError`。绝不能 return True。

**影响**：`enumerate_winning_tiles` 返回所有 34 张牌为可胡 → 听牌推荐引擎完全失效。

## 2. 听牌枚举重复（4 倍）

**现象**：每个听牌在结果中出现 4 次（同点数不同编码）。

**根因**：编码方案中每种点数有 4 个独立代码（风牌 3 个）。枚举所有 0-131 代码时，同一张 3 条的 4 个编码都通过了胡牌检测。

**修复**：`enumerate_winning_tiles` 用 `set()` 按 (suit, rank) 去重，每花色+点数只测一次。

## 3. FanContext.win_on_discard 未自动推导

**现象**：设置 `is_self_drawn=False` 后，`win_on_discard` 仍为 False → 门前清(4番) 不触发 → 平和+无字 组合只有 5番 < 8番 → 总番=0。

**根因**：`win_on_discard` 作为独立字段默认 False。`is_self_drawn=False` 时没有 `__post_init__` 自动设置。

**修复**：在 `FanContext` 上加 `__post_init__`：
```python
def __post_init__(self):
    if not self.is_self_drawn and not self.win_on_discard:
        self.win_on_discard = True
```

**影响**：平和+门前清的手牌（如 234万 456万 789万 33条 567条）点炮胡应为 9番，修复前显示 0番 → 被 listen_engine 过滤掉 → 两面听只列出一半听牌。

## 4. shanten 递归 compare 优先级错误

**现象**：4面子+0搭子+无将 优于 3面子+1搭子+有将 → 后者是合法的一上听，但被错误判断。

**根因**：`if cand > best:` 用元组比较，(4, 0, False) > (3, 1, True) 为 True。

**修复**：用 `_score_key = lambda v: (v[0], 1 if v[2] else 0, v[1])` 强制将牌(True)>搭子。

## 5. rank_arr 索引偏移 1

**现象**：向听数计算错误。

**根因**：`decode()` 返回 1-based rank，但 `rank_arr` 是 0-based。`rank_arr[rank] = cnt` 导致所有数据偏移一位。

**修复**：`rank_arr[rank - 1] = cnt`。

## 6. 风牌张数 3 而非 4

**现象**：牌池总数 516 而非 528（风牌每种 3 张）。

**根因**：国标规则风牌每样 3 张（东南西北各 3）。

**影响**：`remaining_pool`、`full_pool`、`TOTAL_TILES` 全部需要适配风牌 3 张逻辑。

## 7. JS-Python 牌编码不匹配 🔥

**现象**：
- JS 前端显示的牌与判断结果不一致（如点"1条"显示的是"8万"的逻辑）
- 所有非万花色（条/饼/风/箭）的编码都错
- 不同花色间编码重叠（万8 和 条1 都是 28）

**根因**：JS 前端用 `T(s,r) = s*28 + (r-1)*4`，Python 后端用 `encode(s,r) = offset[s] + (r-1)*per[s]`。

实际偏移量：
| 花色 | Python 偏移 | JS 旧公式 | 结果 |
|------|-------------|-----------|------|
| 万   | 0-35        | 0-35      | ✅ 碰巧对了 |
| 条   | **36**-71   | **28**-63 | ❌ 偏移8 |
| 饼   | **72**-107  | **56**-91 | ❌ 偏移16 |
| 风   | **108**-119 | **84**-99 | ❌ 偏移24 |
| 箭   | **120**-131 | 112-127   | ❌ 偏移8 |

编码重叠：万8(code=28) 和 条1(code=28) 在 JS 中相同 → `ALL.find` 返回万8条目 → 显示"8万"。

**修复**：
```javascript
function T(s, r) {
  const base = [0, 36, 72, 108, 120];
  const per = [4, 4, 4, 3, 4];
  return base[s] + (r - 1) * per[s];
}
```

**教训**：前端与后端之间的编码方案必须在首次实现时通过单元测试双向验证。

**验证方法**：
```bash
python3 -c "
from core.tile import encode
base = [0, 36, 72, 108, 120]; per = [4, 4, 4, 3, 4]
for s, name in [(0,'万'),(1,'条'),(2,'饼')]:
    for r in [1,5,9]:
        py = encode(s, r)
        js = base[s] + (r-1)*per[s]
        assert py == js, f'{name}{r}: py={py} js={js}'
print('All OK')
"
```

## 8. `is_any_win_fast` 漏检特殊胡牌型 🔥

**现象**：全不靠（12番）、七星不靠（32番）、一色双龙会（88番）、连七对（88番）等特殊胡牌型在 `calculate_fan` 中返回总番 0。

**根因**：`is_any_win_fast`（`fan_calculator.py` 底部）只检查 `is_standard_win` / `is_seven_pairs` / `is_thirteen_orphans`，不检查特殊胡牌型。`calculate_fan` 用此函数判断"是否胡牌"，不通过就返回空结果。

**修复**：将所有胡牌型检测加入：
```python
return (is_standard_win(tiles, melds) or
        is_seven_pairs(tiles, melds) or
        is_thirteen_orphans(tiles, melds) or
        is_composite_dragon(tiles, melds) or
        is_all_sequences_no_pairs(tiles, melds) or
        is_seven_stars(tiles, melds) or
        is_double_dragon_one_suit(tiles, melds) or
        is_consecutive_seven_pairs(tiles, melds))
```

**教训**：`is_any_win_fast` 必须与 `check_all_wins`（`win_checker.py`）保持同步。新增特殊胡牌型时两个地方都要更新。

## 9. 风刻检测 0/1 基索引不兼容

**现象**：GameState 用 seat_wind=0（0=东）传给 FanContext 后，圈风刻/门风刻检查器调用 `encode(FENG, 0)` 抛出 ValueError。

**根因**：GameState 默认 0 基，但 `encode(FENG, rank)` 要求 rank ∈ [1,4]。

**修复**：在检查器内做归一化：
```python
rw = ctx.round_wind if ctx.round_wind >= 1 else ctx.round_wind + 1
if rw < 1 or rw > 4: return 0
wind_code = encode(FENG, rw)
```

**教训**：GameState 与 FanContext 的 wind 字段语义不一致（0基 vs 1基）。新增需使用 wind 的检查器时必须兼容两种格式。

## 10. `count_available` API 误用

**现象**：和绝张检查器调用 `count_available(pool, ctx.hand.tiles, ctx.hand.melds)` 抛出 TypeError。

**根因**：`count_available(tile_code, remaining)` 只接受 `(单个编码, 剩余池dict)` — 传入池、手牌、副露是错误用法。

**修复**：改为基于手牌和副露中同牌数量的统计。

**教训**：使用不熟悉的工具函数前先确认签名。`full_pool()` 返回 `List[int]`，`count_available` 接受 `(code, Dict)` 返回 `int`。

## 11. 贪心消除算法对缠连边张误判

**现象**：标准胡牌检测的贪心算法在特定手牌布局下失败。典型场景：将牌（对子）可同时作为顺子的组成部分。

**示例**：饼 22233344466789 — 贪心算法优先取刻子（222, 333, 444），然后从 6,6,7,8,9 中取 789 顺子，剩下 6 单张。正确分解应为（222, 333, 444, 789, 66将）。

**根因**：`_remove_melds_from_array` 用严格从左到右的贪心策略（刻子优先→顺子），不回溯。

**影响**：某些合法胡牌被判定为非胡牌。不影响已测试通过的牌型，但长期应改用递归/DP回溯。

**当前处理**：已有测试用例避免触发此边界条件。如需严谨支持，需重写为递归回溯+剪枝。
