# Vercel Python 模块级缓存模式

> Vercel Serverless 环境下，同一 Lambda 实例的模块级变量在**热调用间持久存在**。
> 利用此特性可实现内存缓存，避免每次请求都重复计算。

## 适用场景

- 计算结果重、调用频率高（预测/赔率/模拟结果）
- 数据更新频度低（一天几次而非每秒）
- 对缓存过期容忍度高（数秒到数分钟延迟可接受）
- 不适用的场景：用户个性化数据、实时行情、支付状态

## 核心模式

```python
# ── 模块级缓存（跨热调用持久） ──
_CACHE: dict | None = None
_CACHE_TS: float = 0.0
_CACHE_TTL: float = 120.0  # 2 分钟过期


def _warm_cache(fn, *args, **kwargs):
    """从已有数据预填充缓存（在 predict 等主端点内调用）。"""
    import time
    global _CACHE, _CACHE_TS
    result = fn(*args, **kwargs)
    _CACHE = result
    _CACHE_TS = time.time()


# 在 handler 内部：
if path == "/api/wc/markets" and method == "GET":
    try:
        import time
        global _CACHE, _CACHE_TS
        now = time.time()
        if _CACHE is not None and (now - _CACHE_TS) < _CACHE_TTL:
            return _json(start_response, _CACHE)

        # ... 计算逻辑 ...
        _CACHE = {"count": len(market_data), "matches": market_data}
        _CACHE_TS = time.time()
        return _json(start_response, _CACHE)
    except Exception as ex:
        return _json_error(start_response, str(ex))
```

## 缓存预热（Cache Warming）

在用户访问主页面时预热缓存，确保用户切换到二级页面时零等待：

```python
# 在 predict/首页等高频端点的 handler 内：
core_report = get_predictions(...)
report = translate_report(core_report)

# 预热 markets 缓存（用户下一步可能切到 market 标签）
try:
    _warm_markets_cache(report)
except Exception:
    pass  # 预热失败不影响主页面响应

return _json(start_response, {"report": report})
```

## 关键约束

| 约束 | 说明 |
|------|------|
| **仅热调用生效** | 冷启动时缓存为空，需重新计算 |
| **不跨实例共享** | Vercel 可能启动多个并发实例，每个实例各自维护缓存 |
| **Vercel 回收不确定** | 空闲实例可能在 5-60 分钟后被回收 |
| **global 声明必须** | 函数内修改模块级变量需 `global _CACHE, _CACHE_TS` |
| **TTL 不宜过大** | 建议 60-300s，过长会导致用户看到过时数据 |

## 实例：WC26 Edge Lab

- **端点**: `/api/wc/markets`（104 场 × 13 市场类型的完整赔率）
- **计算耗时**: ~4.7 秒（含 get_predictions + 市场展开）
- **缓存命中**: ~0.001 秒
- **预热触发点**: `/api/wc/predict` 每次调用后
- **TTL**: 120 秒

--- 

*2026-06-14 由 WC26 Edge Lab API 500 调试引入*
