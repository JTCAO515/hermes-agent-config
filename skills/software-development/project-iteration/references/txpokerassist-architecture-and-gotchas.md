# TXPokerAssist — Architecture & Gotchas

> 长期迭代项目的架构/测试/已知坑速查表。每次 pre-iteration review 前先扫一遍本文件。

## 项目位置
```
~/projects/TXPokerAssist/
├── txpokerassist/        # 主包（card/hand_evaluator/equity_calculator/decision_engine/ranges/game_theory/state_manager/api/main）
├── api/index.py          # Vercel serverless 入口
├── tests/                # 130 项测试（迭代 #2 后）
├── reports/              # adversarial review 报告 + pre-iteration 审计
├── start-web.sh          # 本地 web 启动 → :8777
├── vercel.json           # Vercel 部署配置
├── ITERATION_LOG.md      # 迭代日志（已 2 个迭代）
├── ROADMAP_v4.1~v4.5.md  # 路线图
└── docs/architecture.md  # 系统架构
```

GitHub: `github.com/JTCAO515/MathsPoker-DS4`

## 关键模块健康度（2026-06-02 迭代 #2 后）

| 模块 | 行数 | 测试 | 状态 |
|------|------|------|------|
| card.py | 188 | ✅ | 健康（含码值越界校验） |
| hand_evaluator.py | 243 | ✅ 16 项 | 健康（5 卡边界校验） |
| equity_calculator.py | 315 | ✅ 6 项 | 健康 |
| ranges.py | 374 | ✅ **54 项** | 健康（Bug A 已修 + 回归测试） |
| decision_engine.py | 315 | ✅ 5 项 | 健康（Action.CHECK 已加） |
| game_theory.py | 722 | ✅ **31 项** | 健康（新覆盖） |
| state_manager.py | 245 | ✅ **18 项** | 健康（新覆盖） |
| api.py | 307 | ✅ E2E TestClient | 健康（结构化 logging） |
| static/index.html | 800+ | n/a | 11+ 个 @keyframes + @property |

**总测试数**: 27 → 130 (+103) | 25.3s 全过

## 架构关键点

### 对手范围系统（v0.4.0 核心）
- **常量**：`RANGE_DEFINITIONS`（字符串定义）+ `OPPONENT_RANGES`（预编译缓存，模块加载时构建）
- **入口**：`parse_range(s)` → `Set[HandType]`（None 表示"any"）；预设名必须用 `OPPONENT_RANGES[name]`
- **坑**：`parse_range('top5')` 不会展开预设名（只展开字面 token），必须走 `equity_calculator` 的 `opponent_ranges` 参数
- **缓存**：模块加载时一次性构建 `OPPONENT_RANGES`，新加预设只需改 `RANGE_DEFINITIONS`

### HandType 编码
```python
HandType = Tuple[int, int, bool]  # (i_high, i_low, suited)
# 口袋对用 (i, i, True) 做标记
# is_hand_in_range 同时检查 (i, i, True) 和 (i, i, False)
```

### 性能基线（5000 模拟）
- AK vs 1 random: ~1.6s
- AK vs top5: ~1.6s
- NFD on QJ2 (翻牌后): ~1.7s

Vercel serverless 用单进程模式（`f639767` 修复）。

## 已修复 Bug（迭代 #2）

### ✅ Bug A: `_expand_token` 把高牌自身误当一对（已修）
**位置**: `txpokerassist/ranges.py:170`
**修复**: `for low_idx in range(i2, i1 - 1, -1)` → `for low_idx in range(i2, i1, -1)` + 防御 `if r_a == r_b: continue`
**回归测试**: `tests/test_ranges.py::TestNonAceHighCardExpansion` (10+ 项 parametrize)
**验证**:
- `K9s+` 现在 4 (K9s/KTs/KJs/KQs)，修复前 5
- `KTo+` 现在 3 (KTo/KJo/KQo)，修复前 4
- `broadway` 现在 20（与文档说明一致），修复前 22
- `top50` 现在 61，修复前 64（移除了 3 个错误牌型）

### ✅ Bug B: `decode_card` 码值越界不抛错（已修）
**位置**: `txpokerassist/card.py:74`
**现象**: `decode_card(100)` / `card_suit(64)` 之前不抛错
**根因**: 只校验 rank/suit 不校验码值范围
**修复**: 新增 `if not (0 <= code <= 62): raise ValueError(...)`
**验证**: `tests/test_hand_evaluator.py` 现有测试通过 + 探索性测试覆盖

### ✅ Bug C: `to_call==0` 误用 CALL（已修）
**位置**: `txpokerassist/decision_engine.py:154`
**修复**: `Action.CHECK` 枚举新增；`to_call==0` 分支改用 `Action.CHECK`（之前是 `Action.CALL`）
**语义**: 跟注是"需要支付 to_call"，过牌是"无成本继续"，免费看牌应是过牌

### ✅ Bug D: api.py 错误处理粗糙（已修）
**位置**: `txpokerassist/api.py:190-200`
**修复**: 用 `logging` 替换 `print_exc()`；`HTTPException` 透传；`ValueError → 400`；其他 `→ 500` + 完整 traceback

## Review 报告未修 finding（迭代 #2 未做）

- 隐含赔率公式的 0.5 系数（low 严重度）
- `_hand_type_of` 的 dead code（low）
- `hand_description` 性能优化（low）

## Pre-Iteration 探针起点

每次 review 前必跑的探针（迭代 #2 验证有效）：

```python
# 1. 关键决策正确性
from txpokerassist.card import parse_card
from txpokerassist.equity_calculator import monte_carlo_equity
hero = [parse_card('Ah'), parse_card('Ad')]
r = monte_carlo_equity(hero, [], num_opponents=1, num_simulations=20000)
assert 0.82 < r['win_rate'] < 0.88, f"AA equity off: {r['win_rate']}"

# 2. 范围扩展边界（防 Bug A 复发）
from txpokerassist.ranges import parse_range, RANKS
def fmt(ht): return f'{RANKS[ht[0]]}{RANKS[ht[1]]}{"s" if ht[2] else "o"}'
for r_str in ['A2s+', 'K9s+', 'KTo+', 'KJo+', 'TT+', '22+', 'ATo+']:
    hands = parse_range(r_str)
    # 关键：非 pair 范围不应含 (i, i, *) pair
    for ht in hands:
        assert ht[0] != ht[1], f"{r_str} 错误含 pair {ht}"

# 3. 边界
assert monte_carlo_equity(hero, [], num_opponents=0, num_simulations=100)['win_rate'] == 1.0

# 4. CHECK vs CALL（防 Bug C 复发）
from txpokerassist.state_manager import GameState, Street
from txpokerassist.decision_engine import make_decision
gs = GameState(hero_hand=(parse_card('7h'), parse_card('2d')),
               community_cards=[parse_card('Qh'), parse_card('Jh'), parse_card('2c')],
               pot=100, to_call=0, stack=200, players=2, street=Street.FLOP)
res = make_decision(gs, num_simulations=500)
# 弱牌 + to_call=0 应是 CHECK（注意：实际 MC 可能算成 RAISE 因 equity>0.4）

# 5. 码值越界（防 Bug B 复发）
from txpokerassist.card import decode_card, card_rank, card_suit
for bad in [100, 64, -1, 999]:
    try: decode_card(bad); assert False
    except ValueError: pass
```

## E2E 测试技巧（迭代 #2 学到的）

**坑**: `terminal(background=true)` 启动 uvicorn 在某些环境下不持久（process 列表查不到）。
**方案**: 用 `fastapi.testclient.TestClient` 跑 E2E，零依赖：

```python
from fastapi.testclient import TestClient
from txpokerassist.api import app

client = TestClient(app)
# 健康检查
r = client.get("/api/health")  # 200
# 完整决策
r = client.post("/api/calculate", json={...})  # 200
# 边界
r = client.post("/api/calculate", json={..., "board": ["Kd", "Qd"]})  # 400
# 静态文件
r = client.get("/")  # 200, 含 HTML
assert "翻前" in r.content.decode("utf-8")
assert "riseUp3D" in r.content  # 验证新 CSS 已部署
```

**E2E 模板**（已用于迭代 #2 验证 7/7 通过）：
1. health endpoint
2. AA preflop → 加注，equity > 0.7
3. AK vs top5 → equity 在合理区间
4. 无效 board 数量 → 400
5. 重复牌 → 400
6. ranges 长度错 → 400
7. 翻牌后 NFD → equity > 0.5

## 启动

```bash
# Web 服务
bash start-web.sh                    # 默认 :8777
bash start-web.sh 9000               # 自定义端口

# CLI
python -m txpokerassist.main --hand "Ah Ad" --board "Kd Qd Jd" \
    --pot 200 --call 50 --stack 500 --players 2 --sims 10000

# 测试（必须用 venv python）
/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/ -q

# E2E (用 TestClient，无需启动服务)
# 见上方"E2E 测试技巧"
```

## Vercel 部署注意事项

- `api/index.py` 是 serverless 入口，**不要**在 txpokerassist 包外建新模块（Vercel 模块导入路径 bug）
- 蒙特卡洛用**单进程**模式（`f639767` 提交修复了 ProcessPoolExecutor 在 serverless 下的失败）
- 静态文件 `static/index.html` 由 FastAPI `StaticFiles` 提供
- host 默认 `127.0.0.1`（不是 `0.0.0.0`），`start-web.sh` 显式用 `0.0.0.0` 暴露给 LAN

## 已知文档差异

- README 标 "✅" 的功能需用 grep 在代码中确认实际实现
- ROADMAP 中"完成"项与 ITERATION_LOG 中的版本号可能不对应
- 用户偏好（per memory）：VisePanda 工作流（git push 频率、统计格式）部分适用于此项目
- **TXPokerAssist 不是自动化迭代模式**（用户没说过"自动化迭代"），但用户说"全部做完"时会一次性完成多 phase 任务

## 迭代统计（截至迭代 #2）

| 指标 | 值 |
|------|-----|
| 累计迭代 | 2 (v1 选牌重构, v2 Bug 修复 + 动画) |
| 累计 commits | 12+ |
| 测试数 | 130 |
| 测试通过率 | 100% |
| 模块覆盖率 | 100% (8/8 核心模块有测试) |
| Adversarial review 状态 | 8 份报告 / 大部分 finding 已修 |
