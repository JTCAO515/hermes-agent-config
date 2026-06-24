# 中文汉化模式记录 (2026-06-02)

## 汉化范围

| 内容 | 文件 | 说明 |
|------|------|------|
| 前端界面 | `static/index.html` | 按钮、标签、占位符、结果说明 |
| 快速决策文案 | `decision_engine.py` | Action/Confidence枚举值、explanation/risk_note/raise_suggestion |
| 博弈分析文案 | `game_theory.py` | INTENT_TAGS、位置名、置信度标签、决策树推理、格式化输出 |
| 牌局阶段 | `state_manager.py` | Street.__str__ 返回值 |
| 错误信息 | `api.py`、`equity_calculator.py` | HTTPException detail、ValueError 消息 |

## 翻译对照

### 游戏术语
| 英文 | 中文 |
|------|------|
| Pre-Flop / Flop / Turn / River | 翻前 / 翻牌 / 转牌 / 河牌 |
| Fold / Call / Raise / Check | 弃牌 / 跟注 / 加注 / 过牌 |
| All-in | 全下 |
| BTN / SB / BB / UTG | 庄位 / 小盲 / 大盲 / 枪口 |
| MP | 中位 |
| Any / Top5/10/20/35/50 | 任意 / 顶5%/10%/20%/35%/50% |

### 结果文案
| 英文 | 中文 |
|------|------|
| Strong / Moderate / Marginal / Speculative | 强烈 / 中等 / 边缘 / 投机 |
| Equity | 胜率 |
| Pot Odds | 底池赔率 |
| EV | 期望值(EV) |
| Win / Tie / Lose | 胜 / 平 / 负 |
| Pot / To Call / Stack / Players | 底池 / 跟注 / 筹码 / 玩家 |
| SPR | SPR |
| Need FE | 需弃牌率 |

### 对手意图标签
| 英文 | 中文 |
|------|------|
| value — has a made hand, wants a call | 价值下注 — 有成牌，希望被跟 |
| bluff — wants you to fold | 诈唬 — 希望你弃牌 |
| semi_bluff — drawing but aggressive | 半诈唬 — 听牌但激进 |
| probe — testing your strength | 探注 — 试探牌力 |
| defense — protecting hand/pot | 防守 — 保护手牌/底池 |
| trap — slow-playing a monster | 埋伏 — 慢打强牌 |
| steal — using fold equity | 偷池 — 利用弃牌率 |
| information — small bet for info | 信息下注 — 小额获取信息 |
| isolation — heads-up play | 隔离 — 制造单挑 |

## 安全做法

1. **不要用脚本批量替换** — 容易把占位符或不全匹配的字符串写坏
2. **用 `skill_manage(action='patch')` 逐块修改** — 每次只改一个逻辑段
3. **每次改完检查语法** — `python3 -c "import ast; ast.parse(open('file.py').read())"`
4. **跑测试** — `python -m pytest tests/ -v`
5. **本地模拟 API 请求验证** — 确保前端能正确显示中文
