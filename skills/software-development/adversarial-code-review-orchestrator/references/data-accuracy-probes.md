# Data Accuracy Probe Patterns

> 用于对抗式审查中验证数学/数据模块正确性的探针模板。
> 无需运行完整测试套件，通过 10-20 行探针即可暴露多数边界 bug。

## 核心原则

探针比审查报告更可靠 — TXPokerAssist 的 8 份双模型 adversarial review 漏掉了 `Kx+/Qx+/Jx+/Tx+` 范围扩展误把高牌自身当一对的 critical bug，但一个 5 行的探针立刻就发现了。

**策略**：针对每个核心模块的**边界条件**写一个探针，而非审阅生产代码。

---

## 0. 循环自比检测（circular self-reference）

这是审查预测/推荐系统时的**首要探针**。检查系统的"对比基准"是否来自自身。

### 探针：市场赔率 vs 模型概率的独立性

```python
# 如果一个系统的 market_odds 和 model_probs 都来自同一引擎，
# 所有推荐的 EV 将惊人地一致（因为循环自比）
from data.odds_engine import cache_all_matches, get_cached_matches, is_cache_fresh
from data.market_odds_model import compute_market_odds_for_match

# 获取 5 场不同比赛的盘口数据
if not is_cache_fresh():
    from football_predictor.wc_api import get_predictions
    core = get_predictions()
    cache_all_matches(core.get("matches", []))

enriched = get_cached_matches()[:5]
ev_values = []
for em in enriched:
    home = em.get("home") or em.get("team_a", "?")
    away = em.get("away") or em.get("team_b", "?")
    match_id = em.get("id", "")
    phase = em.get("phase", "group")
    mk = em.get("markets", {})
    home_prob = mk.get("home_win", 0)
    
    market = compute_market_odds_for_match(match_id, home, away, phase)
    market_prob = market.home_win_market
    
    # 如果模型概率 ≈ 市场概率，所有 bet 的 EV ≈ 抽水率
    ev = (home_prob / market_prob) - 1.0
    ev_values.append(ev * 100)

unique_ev = len(set(round(v, 2) for v in ev_values))
if unique_ev <= 2:
    print("⚠️ 疑似循环自比 — 各比赛 EV 几乎一致")
    print(f"   EV 值: {[f'{v:.2f}%' for v in ev_values]}")
    print("   检测建议: 检查 market_odds 和 model_probs 是否来自独立引擎")
else:
    print(f"✅ 市场赔率独立 — {unique_ev} 个不同 EV 值")
```

### 判断标准

| 条件 | 判定 |
|------|------|
| 所有比赛 EV 在 ±0.5% 内一致 | ❌ 循环自比 |
| EV 介于 4-6% 且 uniformly distributed | ⚠️ 可疑（存在统一抽水强制拉平）|
| EV 横跨 -20% ~ +80% (正负皆有) | ✅ 市场独立 |

### 深层原因

循环自比的典型成因链：
1. `data/wc2026_matches.json` 包含 model predictions（home_win/draw/away_win）
2. 这些 predictions 由 bivariate Poisson 引擎生成
3. `market_odds_model.py` 也用 bivariate Poisson 生成"市场赔率"
4. 两者共享同一底座模型，差异化仅来自抽水率
5. `betting_math.py` 比较两者 → EV 永远等于 vig

**修复**：独立市场赔率模型要用不同参数体系（ELO 排名 + 公众偏好偏置 + 差异化抽水），让 market_odds 和 model_probs 来自两套不共享参数的引擎。

---

## 1. 赔率/数学模块探针

### 概率和验证
```python
# 验证所有概率和 = 1.0（含舍入误差）
from data.market_odds_model import compute_market_odds_for_match

mo = compute_market_odds_for_match('test', 'Germany', 'Curaçao', 'group')
total = mo.home_win_market + mo.draw_market + mo.away_win_market
assert abs(total - 1.0) < 0.01, f"Probs sum to {total}"
```

### EV 边界验证
```python
from data.betting_math import calc_ev_binary, calc_kelly_binary

# 5% prob @ 20.0 odds → EV = 0 (fair odds)
ev, pct = calc_ev_binary(0.05, 20.0)
assert abs(ev) < 0.001, f"Fair odds should be 0 EV: {ev}"

# 95% prob @ 1.05 → EV negative (vig eats in)
ev2, pct2 = calc_ev_binary(0.95, 1.05)
assert ev2 < 0, f"High prob low odds should be negative EV"

# 30% @ 2.0 → EV = -40%
ev3, pct3 = calc_ev_binary(0.30, 2.0)
assert abs(pct3 - (-40.0)) < 0.1, f"EV should be -40%: {pct3}"

# Kelly should be 0 for non-positive EV
kelly = calc_kelly_binary(0.30, 2.0)
assert kelly <= 0, f"Negative EV should have Kelly <= 0: {kelly}"
```

### 亚洲盘口 push 概率
```python
# AH 整数盘口应有 push 概率 > 0
ah_odds = mk.get('asian_handicap', {})
for h_line in ah_odds.get('home', []):
    if h_line['line'] == -1.0:
        assert h_line.get('push_prob', 0) > 0, \
            f"AH -1.0 should have non-zero push probability"
        break
```

---

## 2. 推荐引擎探针

### 三策略差异化验证
```python
from data.daily_picks import compute_daily_picks

r_aggro = compute_daily_picks(bankroll=1000, strategy='aggressive')
r_growth = compute_daily_picks(bankroll=1000, strategy='growth')
r_stable = compute_daily_picks(bankroll=1000, strategy='stable')

assert r_aggro.total_bets > r_growth.total_bets or r_aggro.avg_odds > r_growth.avg_odds, \
    "Aggressive should differ from Growth"
assert r_stable.total_bets <= r_growth.total_bets or abs(r_stable.avg_odds - r_growth.avg_odds) > 0.1, \
    "Stable should differ from Growth"

# All EVs must be positive (never recommend -EV)
for name, r in [('aggro', r_aggro), ('growth', r_growth), ('stable', r_stable)]:
    all_pos = all(b.ev_pct > 0 for b in r.bets)
    assert all_pos, f"{name}: found negative EV bet"
    
    all_stake_pos = all(b.recommended_stake > 0 for b in r.bets)
    assert all_stake_pos, f"{name}: found 0 or negative stake"
```

### 资金管理边界
```python
# 小资金不产生 sub-$1 的投注
r_small = compute_daily_picks(bankroll=50)
for b in r_small.bets:
    assert b.recommended_stake >= 0.5, \
        f"Sub-$0.50 stake: {b.selection} ${b.recommended_stake}"

# 大资金不应爆仓（总曝险不超过上限）
r_big = compute_daily_picks(bankroll=100000, strategy='growth')
assert r_big.total_stake < 60000, \
    f"Growth 50% exposure exceeded: ${r_big.total_stake}"

# 0 笔数限制正确处理
r_zero = compute_daily_picks(max_bets_per_match=0)
assert r_zero.total_bets >= 0, "Zero max_bets should not throw"

# 有效性过滤：不推荐 EV <= 0 的投注
r_neg = compute_daily_picks(bankroll=1000)
assert all(b.ev_pct > 0 for b in r_neg.bets), "Negative EV leaked"
```

---

## 3. API 数据完整性探针

```python
import json
from pathlib import Path

# 所有 JSON 文件有效
for f in Path('data').glob('*.json'):
    try:
        json.loads(f.read_bytes())
    except json.JSONDecodeError as e:
        assert False, f"Invalid JSON: {f.name}: {e}"

# API 端点 200 + 预期字段
def verify_endpoint(app, path, query='', checks=[]):
    sr = MockStartResponse()
    body = app({'PATH_INFO': path, 'REQUEST_METHOD': 'GET', 'QUERY_STRING': query}, sr)
    assert '200' in sr.status, f"{path} returned {sr.status}"
    text = body[0].decode('utf-8')
    for c in checks:
        assert c in text, f"{path}: missing field '{c}'"
```

---

## 4. Python 编译检查（所有模块）

```bash
# 验证全部 .py 文件无语法错误
find . -name '*.py' -not -path './.*' | while read f; do
    python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>&1 || echo "FAIL: $f"
done
```

---

## 探针编写原则

| 场景 | 探针策略 |
|------|---------|
| 数学公式 | 用已知边界值验证：0%、50%、100% 概率对应的正确输出 |
| 条件分支 | 每个 if/else 分支至少一组输入覆盖 |
| 数据文件 | 全部加载 + 校验结构 |
| API 端点 | 所有端点返回 200 + 预期响应结构 |
| ETL 管道 | 输入边缘值（空/极值/重复）验证输出 |
| 推荐算法 | 不同策略/参数必须产生不同结果 |
