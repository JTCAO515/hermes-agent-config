# Deployment Verification Checklist

> 适用场景：多轮自动化迭代后，git push 前执行。防止服务器返回 500。

## Step 1: Python 编译检查

```bash
cd /path/to/project
python -c "
import sys
sys.path.insert(0, 'api')
try:
    from index import app
    print('✅ App imports OK')
except Exception as e:
    print(f'❌ {e}')
    sys.exit(1)
"
```

**检查项：**
- [ ] 所有 import 链完整
- [ ] 无 `NameError`（如 `Column` 未导入）
- [ ] 无 `ModuleNotFoundError`

## Step 2: 数据文件语法验证

```bash
# 逐文件检查
python -m py_compile data/knowledge/cities.py
python -m py_compile data/knowledge/hotels.py
python -m py_compile data/knowledge/restaurants.py
# ... 其他 data 文件

# 或批处理
for f in data/knowledge/*.py; do
  python -m py_compile "$f" || echo "❌ $f"
done
```

**常见错误：**
| 症状 | 原因 | 修复 |
|------|------|------|
| `SyntaxError: invalid syntax` | dict 条目间缺逗号 | 在上一行末尾加 `,` |
| `SyntaxError: unexpected character after line continuation character` | 字符串中有反斜杠未转义 | 用 raw string 或转义 |

## Step 3: 关键路由验证

```bash
python -c "
import sys; sys.path.insert(0, 'api')
from index import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 测试首页
r = client.get('/')
assert r.status_code in (200, 307), f'Landing: {r.status_code}'
print('✅ Landing OK')

# 测试 API 路由
r = client.post('/api/chat', json={'message': 'hello'})
assert r.status_code == 200, f'Chat API: {r.status_code}'
print('✅ Chat API OK')

# 测试收藏 API
r = client.get('/api/favorites')
assert r.status_code in (200, 401), f'Favorites: {r.status_code}'
print('✅ Favorites API OK')
"
```

## Step 4: Vercel 环境变量核对

git push 后如果返回 500，检查 Vercel Dashboard 是否缺少以下变量：

```bash
# 本地 .env
cat .env | grep -E "export.*=" | sed 's/export //' | cut -d= -f1
```

**与 Vercel Dashboard 逐行对比：**
- [ ] SUPABASE_URL
- [ ] SUPABASE_ANON_KEY
- [ ] LLM_API_KEY
- [ ] LLM_BASE_URL
- [ ] LLM_MODEL
- [ ] LLM_ENABLED
- [ ] AUTH_TEST_BYPASS
- [ ] SUPABASE_PAT（如果用了数据库操作）
- [ ] SMS_PROVIDER（如果用了短信）

## Step 5: 部署后验证

```bash
# push 后等 ~10 秒
sleep 15
curl -sL -o /dev/null -w "%{http_code}" https://your-domain.com/
# 期望输出: 200
```

### ⚠️ curl 测试陷阱：http_proxy 环境变量

许多服务器（尤其是 Vultr/阿里云）设置了全局代理环境变量：

```bash
$ echo $http_proxy
http://127.0.0.1:10809
```

当你 `curl http://64.176.82.81:8080/health` 时，curl 会走代理而非直达目标。如果代理服务挂了或端口不对，会返回 `Connection refused` 或超时。

**修复：** 每次 curl 外部服务时加 `--noproxy '*'`：
```bash
# ❌ 错误 — 走代理
curl http://64.176.82.81:8080/health

# ✅ 正确 — 直连
curl --noproxy '*' http://64.176.82.81:8080/health
```

**更深层陷阱：** Python 的 `urllib.request.urlopen()` 也受 `http_proxy`/`HTTPS_PROXY` 环境变量影响。如果代码在代理环境中跑，请求外部 API 可能走代理。使用 `urllib.request.build_opener(urllib.request.ProxyHandler({}))` 构建无代理的 opener。

### 诊断 Vercel 出站 IP

当 API 需要 IP 白名单时，通过项目的 `/api/nami/myip` 端点（或类似自定义端点）查询 Vercel 当前出站 IP：

```bash
curl -s https://wc26nami.jtcao.space/api/nami/myip
# → {"ip":"44.220.193.15","note":"Vercel当前出站IP, 用于API白名单配置"}
```

如果项目尚未部署该端点，可在代码中临时添加（纯 stdlib，无外部依赖）：
```python
import urllib.request, json

def myip_endpoint(environ):
    """返回当前Vercel出站IP（通过ipify.org查询）"""
    try:
        resp = urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5)
        ip = json.loads(resp.read())["ip"]
    except Exception:
        ip = "unknown"
    payload = json.dumps({"ip": ip, "note": "Vercel当前出站IP, 用于API白名单配置"}, ensure_ascii=False)
    return [payload.encode()], [("Content-Type", "application/json; charset=utf-8")]
```

如果仍返回 500：
1. 检查 Vercel 日志（Dashboard → Deployments → Latest → Function Logs）
2. 或本地复现：见 Step 1-3
3. 如果无法访问 Vercel 日志，优先本地复现

## 典型案例

### 案例 A: Column 未导入
```
症状: Vercel 返回 500，本地 `from index import app` 报 `NameError: name 'Column' is not defined`
原因: 单文件 app 新增 UserPreference/Favorite 模型，用了 `Column()` 但 import 只有 `from sqlalchemy import ...`
修复: 加 `Column` 到 import: `from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text`
验证: python -c "from index import app" → OK
```

### 案例 B: 数据文件少逗号
```
症状: Vercel 500，`python -m py_compile cities.py` 报 `SyntaxError: invalid syntax. Perhaps you forgot a comma?`
原因: 50 城扩展时，新增条目的 `}` 后忘了加逗号
修复: 在对应的 `}` 后加 `,`
验证: python -m py_compile cities.py → OK
```
