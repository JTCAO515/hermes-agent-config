# Supabase 通过代理访问（Management API）

当服务器在中国大陆无法直连 Supabase Postgres 时，通过 Xray 代理 + Supabase Management API 的 HTTP 查询端点实现数据库操作。

## 核心问题

Supabase Postgres 在 `ap-southeast-1` 区域，从中国大陆 VPS 无法直连。解决方案：不使用 Postgres 协议直连，改用 Supabase Management API 的 `/database/query` 端点。

## 配置

```python
import os
import httpx

SUPABASE_PAT = os.getenv("SUPABASE_PAT")  # Personal Access Token
SUPABASE_PROJECT_REF = "jdlinmdhmulozrjeseyc"
PROXY = "http://127.0.0.1:10809"  # Xray HTTP proxy

_HEADERS = {
    "Authorization": f"Bearer {SUPABASE_PAT}",
    "Content-Type": "application/json"
}
_QUERY_URL = f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_REF}/database/query"
_client = httpx.Client(proxy=PROXY, timeout=httpx.Timeout(20.0, connect=15.0))

def query(sql: str) -> list[dict]:
    r = _client.post(_QUERY_URL, headers=_HEADERS, json={"query": sql})
    if r.status_code >= 400:
        raise Exception(f"DB error: {r.text[:200]}")
    return r.json() if r.text.strip() else []
```

## 注意事项

1. **仅支持单条 SQL 语句** — 每次请求只发一条 SQL，不支持事务。多条语句分批调用。
2. **JSONB 默认值** — 建表时 `DEFAULT '{}'::jsonb` 需要在外部处理好引号，否则会被 shell/JSON 双重转义弄错。建议用 Python 的 `json.dumps()` 构建 payload 再通过 `@` 文件传入 curl。
3. **原始 SQL 语法** — 不支持 SQLAlchemy ORM 的参数化查询（如 `:email_1`）。所有的 filter 表达式必须编译为原始 SQL。
4. **不支持 `SELECT ... WHERE table.column = :param`** — 需要用 `literal_binds=True` 编译：
   ```python
   compiled = expr.compile(compile_kwargs={"literal_binds": True})
   ```
5. **PAT 权限** — Personal Access Token 需要 `pg_database_query` 权限。在 Supabase Dashboard → Settings → API → Personal Access Tokens 创建。
6. **httpx 版本注意** — httpx >= 0.28 用 `proxy=`（单数），< 0.28 用 `proxies=`（复数）。错误时返回 `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`。

## 适合的场景

| 场景 | 结论 |
|---|---|
| 开发/演示环境 | ✅ 可行，Management API 够用 |
| 生产高并发 | ❌ 性能差，建议原生 Postgres 直连 |
| 临时访问 | ✅ 适合需要临时查询/修改 |
| 批量导入 | ✅ 适合，但每条 SQL 单次请求 |
