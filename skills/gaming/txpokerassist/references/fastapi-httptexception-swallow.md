# FastAPI HTTPException 吞噬 Bug 模式

## 问题

FastAPI 中 `HTTPException` 继承自 `Exception`。当 endpoint 用 `try/except Exception` 做兜底错误处理时，业务逻辑中主动抛出的 `HTTPException(400)` 也会被捕获，然后被重新包装成 `HTTPException(500)` 返回。

## 症状

- 服务器日志出现 `HTTPException: 400: xxx` 的 traceback
- 客户端实际收到 `500 Internal Server Error`
- 所有通过 `raise HTTPException(status_code=400, ...)` 做的输入校验全部失效

## 根因

```python
# FastAPI 的 HTTPException 继承链
HTTPException → Exception  # 是 Exception 的子类！

# 所以 except Exception 会捕获它
try:
    raise HTTPException(status_code=400, detail="bad")
except Exception:  # ← 这里也捕获了 HTTPException
    raise HTTPException(status_code=500, detail="Internal server error")  # 覆盖为 500
```

## 修复模板

```python
from fastapi import HTTPException

@app.post("/api/endpoint")
async def endpoint(req: Request):
    try:
        # 业务逻辑 + 主动校验
        if invalid_input:
            raise HTTPException(status_code=400, detail="Invalid input")
        ...
    except HTTPException:
        raise  # ← 关键：让 FastAPI 正确处理 HTTPException
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
```

## TXPokerAssist 中的实例（2026-06-02 修复）

### Bug 列表

| 输入 | 预期 | 实际 | 根因 |
|------|------|------|------|
| 1张公共牌 | 400 "无效的公共牌数量" | 500 | HTTPException(400) 被 except Exception 吞掉 |
| 重复手牌 Ah Ah | 400 "Duplicate card" | 500 | 同上 |
| ranges 长度不匹配 | 400 "ranges 长度不匹配" | 500 | 同上 |

### 涉及文件

- `txpokerassist/api.py` — 两个端点 `/api/calculate` 和 `/api/analyze` 均受影响
- 修复：在 `except ValueError` 前加 `except HTTPException: raise`

## 相关前端 Bug（同一 session 修复）

| Bug | 修复 |
|-----|------|
| `board.split(' ')` 空串产生 `['']` | `.filter(c => c.trim())` |
| action-banner CSS 类用英文 `===` 匹配中文值 | 改用 `includes('加注')` 等 |
| 快捷选牌全进 hero 数组 | 智能：hero≤2 → hero，其余 → board |
| SPR=0 显示为 0（应为 ∞） | 后端返回 -1.0 表示 ∞，前端判断 `spr<0?'∞'` |
| stack=0 时建议加注 | decision_engine 增加 stack=0 检查 |

## 通用教训

**在 FastAPI 中，`except Exception` 永远要在 `except HTTPException: raise` 之后。** 这是框架特有的陷阱，因为 HTTPException 既是"业务异常"（400 级校验失败）又是 Python Exception。
