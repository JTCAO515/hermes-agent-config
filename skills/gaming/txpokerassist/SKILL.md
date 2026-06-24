---
name: txpokerassist
description: "TXPokerAssist - 德州扑克纯数学决策辅助CLI+Web。位运算牌力评估 + 蒙特卡洛模拟 + EV期望值模型 + 博弈预测引擎。项目路径: ~/projects/TXPokerAssist。当前版本 v4.4，27/27 测试通过。"
category: gaming
---

# TXPokerAssist

> 项目路径: `~/projects/TXPokerAssist`
> GitHub: `github.com/JTCAO515/MathsPoker-DS4`\n> Vercel: 自动部署（已关联 GitHub）\n> 当前版本: **v5.0**（多对手独立范围 + 完整测试覆盖 + v4.4 动画 2026-06-02）\n> Git tag: `v4.0`（20+ CRITICAL/HIGH 修复）→ `v4.1`（26 项 MEDIUM/LOW 修复）→ `hotfix`（pot=0 ZeroDivisionError）→ `v4.2`（卡牌交互重做 + 视觉优化）→ `v4.3`（视觉精修 roadmap）→ `v4.4`（CSS-only 交互动画）

德州扑克纯数学决策辅助工具。支持 **CLI 命令行模式**、**Web 手机端模式**、**博弈预测引擎**。

## 快速启动

```bash
cd ~/projects/TXPokerAssist

# CLI 交互式
python -m txpokerassist.main

# CLI 命令行（AA翻前决策）
python -m txpokerassist.main --hand Ah Ad --pot 60 --call 10 --stack 200 --players 2 --sims 10000

# CLI 带对手范围
python -m txpokerassist.main --hand Ah Ad --pot 60 --call 10 --stack 200 --players 3 --sims 10000 --ranges top10 tight20

# Web 模式（手机端GUI）
bash start-web.sh
# 访问 http://localhost:8777

# 运行测试
python -m pytest tests/ -v
```

## CLI 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--hand` | 手牌 | `Ah Ks` |
| `--board` | 公共牌 | `Qd Jh 2c` |
| `--pot` | 底池 | `100` |
| `--call` | 跟注 | `30` |
| `--stack` | 筹码 | `400` |
| `--players` | 人数 | `2` |
| `--sims` | 模拟次数 | `10000` |
| `--ranges` | 对手范围 | `top10 any tight20` |
| `--stage` | 阶段 | `preflop/flop/turn/river` |
| `--benchmark` | 性能测试 | 开关 |

## 项目结构

```
TXPokerAssist/
├── txpokerassist/
│   ├── card.py               # 6-bit 卡牌编码与解析（52张→2-62编码）
│   ├── state_manager.py      # 牌局状态管理 + 交互式输入
│   ├── hand_evaluator.py     # 位运算牌力评估引擎（evaluate_5 + evaluate_7 + compare_hands）
│   ├── equity_calculator.py  # 蒙特卡洛模拟（单进程/多进程并行，whole-pot统计）
│   ├── ranges.py             # 对手范围系统（预设+自定义，build_range_pool + is_hand_in_range）
│   ├── decision_engine.py    # EV 决策模型（calculate_ev + make_decision）
│   ├── game_theory.py        # 博弈预测引擎（意图逆向 + 决策树 + 最优解 + 听牌检测）
│   ├── api.py                # FastAPI Web 后端（/api/calculate + /api/analyze）
│   ├── static/
│   │   └── index.html        # 手机端前端（双模式：决策 + 博弈分析）
│   └── main.py               # CLI 入口
├── scripts/
│   └── adversarial_review.py # 对抗式双模型代码审查脚本（GLM 5.1 + DeepSeek V4 Flash）
├── tests/                    # 27 项测试（卡牌/牌力/MC/决策）
├── reports/                  # 审查结果缓存（.gitignore排除）
├── start-web.sh              # Web 一键启动脚本
├── ROADMAP_v4.1.md           # 下一版迭代计划
├── vercel.json               # Vercel Serverless 配置
└── README.md
```

## 模块详解

### card.py — 卡牌编码
- 6-bit 编码方案（4-bit rank + 2-bit suit）
- 编码范围 2-62（非连续，gap codes 存在）
- `encode_card` / `decode_card` / `parse_card` / `cards_str` / `validate_no_duplicates`
- ⚠️ `decode_card` 此前缺输入验证（gap codes 静默产垃圾），v4.0 中 `card_str` 已加防御

### hand_evaluator.py — 牌力评估
- `evaluate_5` — 5 张牌牌型判断（HIGH_CARD → ROYAL_FLUSH）
- `evaluate_7` — 7 选 5 最佳组合（C(7,5)=21 种）
- `compare_hands` — 相同牌型比较 kickers
- 性能：单次 evaluate_7 < 2μs
- v4.0 新增输入校验 + sorted kickers + kicker 长度断言

### equity_calculator.py — 蒙特卡洛
- 支持单进程/多进程（ProcessPoolExecutor）
- whole-pot 统计（win/tie/lose 互斥）
- 对手范围约束（build_range_pool 预筛）
- 10,000 次模拟 ~1.1s（多进程）
- ⚠️ v4.0 修复：Tie 逻辑（输给一人+平局他人→算输而非平局）、多对手牌碰撞

### ranges.py — 对手范围
- 预设范围：any / top5 / top10 / top15 / top20 / top35 / top50 / pair+ / broadway / suited-connector
- 自定义范围：标准扑克记法（如 "TT+, AJs+, KQo"）
- `build_range_pool` / `is_hand_in_range` / `random_hand_in_range`
- ⚠️ v4.0 修复：口袋对在 `is_hand_in_range` 中同时检查 suited/offsuit

### game_theory.py — 博弈预测
- `PlayerAction` / `PlayerProfile` / `DecisionBranch` / `GameTheoryResult` 数据结构
- 意图逆向：`_infer_opponent_range` + `_infer_intent`
- 决策树：Fold / Check / Call / Raise(2x) / All-in
- 数学工具：`_required_fold_equity` / `_ev_raise` / `calculate_ev`
- 听牌检测：`_detect_draws`（同花/两头顺/卡顺，含 Ace=1 wheel）
- ⚠️ v4.0 修复：EV 公式双倍计数 → 改为 `equity*(pot+raise-to_call) - (1-equity)*raise`，fold_equity 误用（break-even FE → 33% 估算），听牌标签错乱（卡顺/两头顺/已成花），IndexError（wheel + Ace 边界）

## 对抗式审查管道

```bash
cd ~/projects/TXPokerAssist

# 全量审查（4 批次）
python scripts/adversarial_review.py

# 只看 P0/P1
python scripts/adversarial_review.py --p0-only

# 只看汇总（从已有结果读取）
python scripts/adversarial_review.py --summary-only

# 指定批次
python scripts/adversarial_review.py --rounds 1,3
```

| 维度 | 说明 |
|------|------|
| 模型 | GLM 5.1（全面）+ DeepSeek V4 Flash（快速） |
| 批次数 | 4（每批 2-3 文件） |
| 结果格式 | JSON（`reports/review_*.json`） |
| 汇总 | 含分级统计 + 双模型交叉对比 |
| 结果 | v4.0 审查：GLM 33 findings + DeepSeek 19 findings = 52 |

## v4.0 修复清单

**CRITICAL（5）：**
- Tie 逻辑：输给一人+平局他人 → 算输而非平局
- 多对手范围牌碰撞 → 动态过滤已发牌
- 已成花/听花标签 → 已修正
- 卡顺/两头顺标签 → 已修正
- EV 公式双倍计数 → 已修正
- fold_equity 误用（break-even FE → 33% 估算）

**HIGH（8）：**
- 口袋对范围 → 同时检查 suited/offsuit
- wheel (A-2-3-4-5) 顺子检测
- API board 非法大小校验
- /api/analyze 重牌校验
- ranges 长度匹配
- CLI --ranges 参数
- board 大小校验（cli + api）
- fold_equity 硬编码改为保守估算

## v4.1 修复清单

**HIGH（10项）：**
- `_infer_opponent_range` 改用相对尺度（pot×0.4 + BB 基准）
- 弃牌率硬编码 → 基于对手画像动态估算（`bluff_freq` / `fold_to_cbet_pct`）
- 多对手联合弃牌率（`1-(1-fe)^n`）
- `calculate_ev` stack 参数真正用于 cap to_call（all-in 场景）
- `ev_check = equity * pot` 加注释说明为近似值
- `ranges.py`: A2s+ 展开修复（移除 break at '2'）
- `ranges.py`: 非 Ax 连张滑动修复（固定高牌，迭代低牌）
- `decision_engine.py`: `to_call > stack` 时 cap 为 all-in
- `decision_engine.py`: implied odds 乘数模型 → 加法模型（剩余筹码×因子×0.5）
- 风险提示加上 all-in 场景

**MEDIUM（8项）+ LOW（8项）：**
- decode_card gap codes 校验 / card_rank/suit 校验
- parse_card docstring 0-51 → 2-62
- build_range_pool O(n²) → itertools.combinations
- docstring 16-bit → 6-bit
- compare_hands zip + 长度断言（替代补0 fallback）
- API 500 隐藏内部细节
- /api/analyze board 大小校验 + 重牌校验
- opponent_ranges 长度校验
- dead code / import 清理
- semi-bluff 阈值 15% → 25%

## Hotfix（post-v4.1）

**Bug:** `_raise_reasoning` 中 `raise_amt/pot` → `pot=0` → `ZeroDivisionError` → 博弈分析页面 Internal Server Error

**连带修复：** SPR=inf 导致 JSON 序列化失败

**Root cause pattern:** 格式化输出字符串时未考虑分母为零场景。博弈分析中 `raise_amt/pot` 概率论计算、SPR 计算均有此风险。

v4.2 新增：
- **智能文本输入** — 输入 "Ah Ks / Qd Jh 2c" 自动解析并展示已选卡牌
- **紧凑快捷选牌** — 13 rank × 4 suit 按钮（17 按钮替代 52 网格），折叠面板
- **卡牌即时渲染** — 选中以微卡片展示，点击可删除
- **视觉重设计** — 深色质感主题、毛玻璃顶栏、卡片式参数输入、金色点缀

## v4.5 Bugfix + 选牌交互重构 ✅ 已完成（2026-06-02）

**后端 Bug 修复（6项）：**
1. ❗ **HTTPException 被 except Exception 吞掉变 500** — 根因修复：在 except Exception 前加 `except HTTPException: raise`
2. API: 无效 board 数量(1/2张) → 现正确返回 400 而非 500
3. API: 重复牌 → 现正确返回 400 而非 500
4. API: ranges 长度不匹配 → 现正确返回 400 而非 500
5. decision_engine: stack=0 时不再建议加注
6. SPR: pot=0 时返回 -1.0（前端显示 ∞）

**前端 Bug 修复（5项）：**
1. board 空字符串过滤：`board.split(' ')` → `.filter(c=>c.trim())`
2. 快捷选牌智能分配：hero 先填2张 → 剩余进 board → 满7张提示
3. action-banner CSS 类：中文关键词匹配（`includes('加注')` 等）
4. GT tab board 空字符串过滤
5. 阶段选择器与 board 张数不一致时显示警告

**选牌交互重构（已完成）：**
- v4.2 的 rank→suit 两步选牌 → v4.5 的 13×4 牌面网格（点1次出1张）
- 4行（♠♥♦♣）× 13列（A→2），已选牌灰掉
- 起手牌快速预设：AA/KK/QQ/JJ/AKs/AKo/AQs/TT
- 竞品调研来源：Equilab/Flopzilla/PokerCruncher/Fast Poker Odds/Odds Calculator for Poker/SnapShove/Enterra/OpenPokerTools（9款）
- 详见 `references/poker-card-ui-research.md` + `references/card-input-pattern.md`

## Web 模式

```bash
bash start-web.sh
# 或
/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 -m uvicorn txpokerassist.api:app --host 127.0.0.1 --port 8777
```

- **快速决策模式** — 手牌 → 公共牌 → EV/胜率 → 行动建议
- **博弈分析模式** — 意图逆向 + 对手范围 + 决策树 + 最优解
- 52 张 CSS 扑克牌，触屏优化
- 后端 API: `/api/calculate`（决策）+ `/api/analyze`（博弈）+ `/api/health`

## 迭代模式

```bash
# 部署
git add -A
git commit -m "vX.Y: 改动摘要"
git push origin main

# 下一版计划写在 ROADMAP_vX.Y.md
```

参考 `ROADMAP_v4.1.md` 为下一版迭代计划。

## 已知坑点

### ❗ FastAPI: HTTPException 被 except Exception 吞掉变 500
**这是最常见的 FastAPI bug 模式之一。** 当 endpoint 用 `try/except Exception` 做兜底时，`HTTPException(status_code=400)` 也会被捕获，然后被重新包装成 500 返回。

```python
# ❌ 错误 — HTTPException(400) 被 except Exception 吞掉，变成 500
@app.post("/api/calculate")
async def calculate(req):
    try:
        ...
        if invalid:
            raise HTTPException(status_code=400, detail="bad request")  # 会被下面吞掉！
        ...
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # ← HTTPException 继承 Exception，也被这里捕获！
        raise HTTPException(status_code=500, detail="Internal server error")

# ✅ 正确 — 在 except Exception 前加 except HTTPException: raise
    except HTTPException:
        raise  # 让 FastAPI 正确处理 HTTPException
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

**识别信号：** 服务器日志中看到 `HTTPException: 400: xxx` traceback，但客户端收到 500。

### ❗ 前端空字符串 split 陷阱
JS 中 `''.split(' ')` 返回 `['']` 而非 `[]`。发送到后端时 `board: ['']` 可能导致 parse_card("") 报错。

```javascript
// ❌ 错误
const board = boardStr.split(' ');  // [''] when empty

// ✅ 正确
const board = boardStr ? boardStr.split(' ').filter(c => c.trim()) : [];
```

### ❗ 中英文 action 值匹配
后端 decision_engine 返回中文 action（"加注"/"跟注"/"弃牌"），前端 CSS 类判断需用 `includes` 而非 `===`：

```javascript
// ❌ 错误 — 只匹配英文
banner.className = d.action.toLowerCase() === 'raise' ? 'raise' : 'fold';

// ✅ 正确 — 兼容中英文
const act = d.action.toLowerCase();
banner.className = act.includes('加注') || act === 'raise' ? 'raise' : 'fold';
```

### ❗ 安全批量修改：永远不要用占位符做替换
当对项目做批量字符串替换（如汉化）时，**不要用脚本一次性改所有字段**——容易遗漏或误替换：
- ❌ 用 `'...'` 做占位符 → 会把实际字符串替换成 `...`，造成语法错误
- ✅ 用 `skill_manage(action='patch')` 逐块修改，每次确认语法无误
- ✅ 改完后 `python -m pytest tests/ -v` 确保所有测试通过
- ✅ 本地启动 API 模拟一次请求验证

### ❗ Vercel Serverless：ProcessPoolExecutor 不可用
Vercel Python Serverless（AWS Lambda）**不支持 `multiprocessing` / `os.fork()`**。
`equity_calculator.monte_carlo_equity` 在 Vercel 上**必须走单进程**。

修复方式（已完成）：
```python
# ❌ 旧代码（Vercel 崩）
n_workers = os.cpu_count() or 1

# ✅ 新代码（Vercel 稳）
n_workers = num_workers or 1  # 默认单进程
```
- 仅在显式传入 `num_workers > 1` 时才启用 `ProcessPoolExecutor`
- 单进程 10000 sims 在 Vercel 上约 20-30s，慢但不会崩
- `concurrent.futures` import 保留但仅本地使用

### ❗ 500 Internal Server Error 排查链路
当 Vercel 返回 500 时：
1. 先确认本地 `python -m pytest tests/ -v` 是否通过
2. 如果本地过但 Vercel 崩 → 99% 是 serverless 环境限制（如 ProcessPoolExecutor）
3. 刷新 Vercel 部署缓存：`git commit --allow-empty -m "force redeploy" && git push`

## 运行测试

```bash
cd ~/projects/TXPokerAssist
python -m pytest tests/ -v
# 27 passed
```

## Absorbed Sub-Skills

This umbrella skill absorbed two standalone sibling skills. Their full detail is preserved as reference files.

### Poker Equity (`references/poker-equity-detail.md`)
Deep equity computation detail: Monte Carlo formulas (EV calculation, multi-way pot stats), range pre-filtering, card encoding, hand evaluation, and Vercel serverless constraints. Use when debugging equity calculations or adding new simulation modes.

### Poker Game Theory (`references/poker-game-theory-detail.md`)
Game theory engine detail: four-stage pipeline (intent reverse engineering → situation assessment → decision tree → optimal move), intention signal taxonomy, draw detection, range definitions, and API endpoint contracts. Use when extending the GT analysis or adding new opponent profiles.

## 参考文件

- `references/hotfix-pot-zero.md` — pot=0 ZeroDivisionError 根因分析、修复模式和扫描清单
- `references/css-only-animation-pattern.md` — 纯 CSS 动画方案（v4.4）：card flip / shimmer / pulse / number rollup / spring easing
- `references/card-input-pattern.md` — 选牌交互演进：v4.2 rank→suit 两步 → v4.5 13×4 网格点选 + 坑点记录
- `references/poker-card-ui-research.md` — 市面竞品选牌交互调研（Equilab/Flopzilla/PokerCruncher 等 9 款产品对比 + 最佳实践）
- `references/fastapi-httptexception-swallow.md` — FastAPI HTTPException 被 except Exception 吞噬变 500 的 bug 模式、修复模板和实例
