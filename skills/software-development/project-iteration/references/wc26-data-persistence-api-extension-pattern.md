# WC26 数据持久化 + API + 前端扩展模式

> 适用于 `26-WorldCup-Edge` 项目，总结 v5.0.2 → v5.1.0 迭代中踩过的坑和已验证的模式。

---

## 1. 数据持久化 — 预测数据写回 JSON

### 核心约束

`data/wc2026_matches.json` 中每个 match 的 `checkpoints` 字段是 **list**，不是 dict：

```json
{
  "checkpoints": [
    {"name": "T-48h", "time": "2026-06-09T12:00:00+00:00"},
    {"name": "T-6h",  "time": "2026-06-11T11:00:00+00:00"},
    {"name": "T-60m", "time": "2026-06-11T16:00:00+00:00"}
  ]
}
```

⚠️ **绝对不能**将 `checkpoints` 替换为 dict 类型。`football_predictor/backtest.py` 依赖 list 结构的 `checkpoint["name"]` 做迭代。

### 正确做法

1. 调用 `get_predictions()` 获取实时计算数据
2. 从返回的 `checkpoints` dict 中提取最新 checkpoint 的概率
3. 新增 `predictions` 字段（不修改 `checkpoints`）

```python
from football_predictor.wc_api import get_predictions
from pathlib import Path
import json, time

report = get_predictions()
data = json.loads(Path("data/wc2026_matches.json").read_text())

for match in data["matches"]:
    mid = match["id"]
    pred = {m["id"]: m for m in report["matches"]}.get(mid, {})
    ck = pred.get("checkpoints", {})
    ck_names = sorted(ck.keys()) if ck else []
    if not ck_names:
        continue
    latest = ck[ck_names[-1]]
    match["predictions"] = {
        "probs": latest.get("probabilities", {}),
        "expected_goals": latest.get("expected_goals", {}),
        "market_probs": latest.get("market_probs", {}),
        "recommendation": latest.get("recommendation", {}),
        "computed_at": time.time(),
    }

data["predictions_timestamp"] = time.time()
Path("data/wc2026_matches.json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False)
)
```

### 验证

保存后运行 `run_backtest()` 确认兼容：

```python
from football_predictor.backtest import run_backtest
bt = run_backtest(Path("data/wc2026_matches.json"), Path("configs/default.json"), mode="preview")
assert len(bt["matches"]) == 104  # 原流程不受影响
```

---

## 2. WSGI API 扩展模式

项目使用纯 Python stdlib WSGI 框架，路由通过 if-elif 链匹配。新增端点时：

### 模式

在 `api/index.py` 的 `app()` 函数中，在 `# POST /api/wc/update` 之前插入新端点：

```python
# GET /api/wc/quant/portfolio — Portfolio optimization
if path == "/api/wc/quant/portfolio" and method == "GET":
    try:
        from urllib.parse import parse_qs
        qs = parse_qs(environ.get("QUERY_STRING", ""))
        bankroll = float(qs.get("bankroll", ["1000"])[0])
        
        core = get_predictions()
        enriched = _build_enriched(core)
        candidates = _build_candidates(enriched)
        
        from data.quant_engine import optimize_portfolio, compute_signals
        portfolio = optimize_portfolio(candidates, bankroll=bankroll)
        signals = compute_signals(portfolio.allocations)
        
        return _json(start_response, {
            "portfolio": {
                "total_bets": portfolio.total_bets,
                # ...
            },
            "signals": [...],
        })
    except Exception as ex:
        return _json_error(start_response, str(ex))
```

### 辅助函数模式

在 `app()` 前定义新的辅助函数，用**局部 import** 避免 Vercel 的循环依赖：

```python
def _build_enriched(core: dict) -> list:
    """Build enriched match list with markets data for quant engine."""
    from data.odds_engine import cache_all_matches, get_cached_matches
    enriched = cache_all_matches(core.get("matches", []))
    if not enriched:
        enriched = get_cached_matches()
    return enriched
```

### 关键规则

| 规则 | 原因 |
|------|------|
| 每个端点用 `try/except Exception` 包裹 | WSGI 无框架级错误处理 |
| 局部 import（函数内 import） | 避免 Vercel 冷启动时模块解析失败 |
| `_json()` + `_json_error()` 统一 | 保持响应格式一致 |
| 所有数据类对象手动序列化为 dict | JSON 不序列化 Python dataclass |
| 新端点之间路径名用 `quant/` 前缀分组 | 路由可读性 + 前端匹配清晰 |

---

## 3. 前端 Tab 扩展模式（3 层同步）

为 SPA 添加新 Tab 必须同步修改**3 个文件**：

### HTML — 添加 Tab 按钮 + 内容块

```html
<!-- 1. Tab 按钮（在 tabs section 末尾） -->
<button class="tab" data-tab="quant">📊 量化</button>

<!-- 2. Tab 内容块（在对应位置，一般在上一个 tab-content 之后） -->
<section id="tab-quant" class="tab-content">
  <div class="quant-container">
    <!-- KPI 卡片 -->
    <div class="quant-kpis" id="quant-kpis">
      <div class="quant-kpi-card">...</div>
    </div>
    <!-- 表格/列表/网格 -->
    <div class="quant-section">...</div>
  </div>
</section>
```

### CSS — 添加样式

所有新样式写在 `app.css` 末尾（保持线性增长），响应式断点也写在末尾：

```css
/* ═══ Quant Engine Tab ═══ */
.quant-container { max-width: 960px; margin: 0 auto; ... }
.quant-kpis { display: grid; grid-template-columns: repeat(6,1fr); ... }

@media (max-width: 640px) {
  .quant-kpis { grid-template-columns: repeat(2,1fr); }
}
```

### JS — 添加 switchTab 路由 + render 函数

```javascript
// Step 1: switchTab 中加入路由
function switchTab(tab) {
    // ... 原有代码
    else if (tab === "quant") renderQuant();
}

// Step 2: render 函数（async，缓存在首次加载之后）
async function renderQuant() {
    if ($('#quant-signals-body').children.length > 1 && $('#qk-bets').textContent !== '—') return;
    
    try {
        // 并行加载多个 API
        const portRes = await fetch('/api/wc/quant/portfolio?bankroll=1000&max_exposure=0.5');
        const portData = await portRes.json();
        const pf = portData.portfolio;
        
        // 填充 KPI
        $('#qk-bets').textContent = pf.total_bets;
        $('#qk-roi').textContent = (pf.expected_roi * 100).toFixed(1) + '%';
        
        // 渲染表格
        const tbody = $('#quant-signals-body');
        tbody.innerHTML = portData.signals.map(s => `<tr>...</tr>`).join('');
        
        // 加载其他数据...
    } catch (err) {
        console.error('Quant render error:', err);
    }
}
```

### 缓存策略

- `renderQuant()` 首次调用的结果通过 cache-before-return 条件缓存（检查 `children.length` 和 `textContent`）
- 用户切走再切回时不重新加载（除非硬刷新页面）

---

## 4. 量化引擎模块结构模式

`data/quant_engine.py` 采用**按功能分区**的单文件结构，适合 stdlib-only 项目：

```
Module 1: Arbitrage Scanner   (套利检测)
  └─ scan_arbitrage(matches, enriched) → ArbitrageResult
      ├─ Surebet detection (1X2, AH)
      ├─ Cross-market pricing diff (1X2 vs AH)
      └─ Time-value (odds movement)

Module 2: Portfolio Optimizer  (组合优化)
  ├─ optimize_portfolio(candidates) → PortfolioResult
  ├─ _build_correlation_matrix()  内部
  └─ _compute_strategy_comparison() 内部

Module 3: Signal Fusion        (多因子信号)
  └─ compute_signals(candidates) → list[QuantSignal]
      ├─ Value factor (35%)
      ├─ Risk factor (25%)
      ├─ Confidence factor (20%)
      ├─ Momentum factor (10%)
      └─ Diversity factor (10%)

Module 4: Backtest             (策略回测)
  └─ run_backtest(predictions, matches) → BacktestResult
```

### 模式优势

- 每个模块使用 `@dataclass` 结果类型，避免深嵌套 dict
- 每个模块独立可测试
- 模块间通过 dataclass 类型传递，IDE 友好
- 全部 stdlib-only，零外部依赖

---

## 5. 常见 Pitfalls

### Pitfall 1 — checkpoints 结构混淆
**症状**：`run_backtest()` 抛出 `TypeError: string indices must be integers`
**原因**：误将 `checkpoints` 从 list 改为 dict
**修复**：`git checkout -- data/wc2026_matches.json` 恢复，重新用正确的 `predictions` 字段写入

### Pitfall 2 — enriched cache key 命名
**症状**：脚本报 `KeyError: 'home'`
**原因**：`cache_all_matches()` 返回的数据用 `team_a`/`team_b` 而非 `home`/`away`
**修复**：始终用 `em.get("team_a", "")` 或兼容写法 `em.get("home") or em.get("team_a", "")`

### Pitfall 3 — dataclass 字段未对齐
**症状**：`TypeError: __init__() got an unexpected keyword argument 'kelly_pct'`
**原因**：前端传给 `BetAllocation()` 的字段名与 dataclass 定义不一致
**修复**：向 dataclass 添加缺失字段（`kelly_pct: float = 0.0`）或移除调用中的多余参数
