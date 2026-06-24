# Vercel Python 文件备份预计算缓存模式 (File-Backed Precompute Cache)

> 当 module-level 内存缓存（warm invocations）不够用时 —— **冷启动**仍是瓶颈。
> 解决：把预计算结果写入 JSON 文件，API 端点从文件读而非重新计算。

## 问题背景

WC26 Edge Lab 的 quant 端点 (`/api/wc/quant/portfolio`, `/api/wc/quant/arbitrage`, `/api/wc/quant/backtest`) 每次请求都调用 `get_predictions()` 运行 Poisson 模型：

```
cold start: get_predictions() (~5s) → _build_enriched() (~3s) → _build_candidates() (~1s) → quant (~0.1s)
                                                                                          总耗时 ~8-10s
```

Vercel Serverless 的 **10 秒超时限制**（免费套餐 10s Pro 60s）+ 实例回收（空闲 5-60min 后回收）导致：
- 每次用户切到量化 Tab 都有 50%+ 概率冷启动 → 请求超时 → 前端收不到数据 → 显示空内容

## 解决方案：预计算 + JSON 文件读取

### 核心思路

1. **预计算管线**（在本地或 Cron 中运行）将预测结果存储到 JSON 文件
2. **API 端点**从 JSON 文件读取缓存结果，而非重新运行模型
3. **文件读取 ≈ 0.001s**，纯 I/O 无计算，Vercel 上稳如磐石

### 代码模式

```python
def _build_candidates_from_cache() -> list:
    """Fast path: read predictions from cached JSON instead of running Poisson model."""
    from data.market_odds_model import compute_market_odds_for_match
    from data.betting_math import calc_ev_binary, calc_kelly_binary, calc_sharpe_ratio
    from data.quant_engine import BetAllocation

    data_file = ROOT / "data" / "wc2026_matches.json"
    try:
        raw = json.loads(data_file.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # 文件不存在时返回空，不崩溃

    candidates = []
    for match in raw.get("matches", []):
        # 从 JSON 中读取预计算概率
        preds = match.get("predictions", {})
        probs = preds.get("probs", {})
        if not probs:
            continue
        # ... 构建候选投注 ...
        candidates.append(BetAllocation(...))

    return candidates
```

相应地在 API 端点中替换：

```python
# ❌ 慢路径（Vercel 超时）
core = get_predictions()
enriched = _build_enriched(core)
candidates = _build_candidates(enriched)

# ✅ 快路径（~0.2s）
candidates = _build_candidates_from_cache()
```

### 效果数据

| 指标 | 旧路径（重跑模型） | 新路径（文件缓存） |
|------|------------------|-------------------|
| Portfolio API | ~8s | ~0.06s |
| Arbitrage API | ~10s | ~0.11s |
| Backtest API | ~5s | ~0.01s |
| 并行总耗时 | ~10s（串行） | ~0.18s（Promise.all） |
| 冷启动 | 100% 超时 | ✅ 正常 |

## 关键设计决策

### 1. 什么时候需要文件缓存 vs 内存缓存

| 场景 | 用内存缓存 | 用文件缓存 |
|------|-----------|-----------|
| 数据实时变化（秒级） | ✅ | ❌ |
| 冷启动能容忍 5s 延迟 | ✅ | ❌ |
| 免费套餐 Vercel（10s 超时） | ❌（冷启动超时） | ✅ |
| 数据预计算一次、多次读取 | ✅ 也可 | ✅ **更优** |
| 多个并发实例需要一致数据 | ❌ 各实例独立 | ✅ 都读同一文件 |

### 2. 数据结构设计

JSON 文件结构需同时支持 **预计算读取** 和 **原始模型输出** 两个消费方：

```python
# 一个 match 记录中的 predictions 字段：
{
    "predictions": {
        "probs": {
            "team_a_win": 0.55,
            "draw": 0.21,
            "team_b_win": 0.24,
            "over_2_5": 0.41,
            "under_2_5": 0.59
        },
        "expected_goals": {
            "home": 1.24,
            "away": 1.09
        },
        "scoreline_probabilities": {  # 可选
            "over_2_5": 0.41,
            "under_2_5": 0.59
        }
    }
}
```

### 3. 字段名兼容性陷阱 ⚠️

**Poisson 模型输出**的字段名和 **回测/量化引擎读取**的字段名可能不一致：

```python
# Poisson 引擎输出
probs = {
    "team_a_win": 0.55,   # <-- team_a_win
    "draw": 0.21,
    "team_b_win": 0.24,   # <-- team_b_win
}

# 回测引擎期望
model_hw = probs.get("home_win", 0)    # = 0 ❌（应为 0.55）
model_aw = probs.get("away_win", 0)    # = 0 ❌（应为 0.24）
```

**修复模式**：用 `or` 链式回退兼容双命名：

```python
model_hw = probs.get("home_win") or probs.get("team_a_win", 0)
model_aw = probs.get("away_win") or probs.get("team_b_win", 0)
model_dr = probs.get("draw", 0)        # draw 名称一致
```

### 4. 回测引擎市场赔率计算

另一个常见陷阱：用 `pred.get("h2h", {})` 读市场赔率，但 JSON 中不存在此字段：

```python
# ❌ 错误：h2h 字段不存在
market_odds = 1.0 / (1.0 / pred.get("h2h", {}).get("home_win", 0.33))

# ✅ 正确：用独立的 market_odds_model
mkt = compute_market_odds_for_match(mid, home, away, phase)
market_odds = mkt.home_odds
```

## 何时更新缓存文件

文件缓存需要数据更新时重新生成。常见策略：

1. **Cron 定期更新**：每天凌晨运行预计算管线 → 写 JSON → 部署
2. **手动触发**：在 API 中添加 `/api/refresh-cache` 端点（需认证）
3. **GitHub Actions**：数据源变化时自动运行 → push 更新后的 JSON
4. **Cache warming**：主端点调用后异步预热文件缓存（memory→file write）

## 与其他缓存模式的关系

```
数据获取层级（从快到慢）：
1. 模块级内存缓存 (_CACHE 全局变量) — ~0.001s, 仅热调用
2. 文件备份预计算缓存 (JSON read) — ~0.01s, 冷启动也有
3. 实时计算 (Poisson model) — ~5-10s, 仅当需要更新时
```

**推荐组合**：文件缓存做保底 + 内存缓存做加速。冷启动走文件缓存，热调用走内存缓存。

---

*2026-06-14 由 WC26 v5.2.0 Quant Tab 内容空白问题引入*
