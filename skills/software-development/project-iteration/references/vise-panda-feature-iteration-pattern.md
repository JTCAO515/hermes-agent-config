# VisePanda 功能迭代标准模式

> 适用场景：在 VisePanda 单文件 FastAPI 应用上快速迭代新功能
> 已验证于 Iter 81-91 (2026-05-26, 10 rounds in one session) 和 Iter 92-101 (2026-05-26, coverage + bugfix)

## 五步流水线

```
数据层 → (验证层) → 路由层 → 页面层 → 导航层 → 知识层 → 部署层
```

### Step 1: 数据层 (data/knowledge/*.py)

创建或扩展结构化数据文件。VisePanda 知识库统一放在 `data/knowledge/`：

```python
# data/knowledge/mymodule.py
"""模块描述"""

SOME_DATA = { ... }

def format_for_prompt() -> str:
    """返回给 LLM system prompt 的精简文本"""
    return "..."

def get_item(key: str) -> dict | None:
    """提供给 API 路由的查询接口"""
    return SOME_DATA.get(key)
```

**每个数据文件的约定接口：**
- `format_for_prompt()` — 返回纯文本摘要，注入到 `prompt.py` 的 `SYSTEM_PROMPT`
- `get_*()` — 供 API 路由调用的查询函数
- 数据文件纯静态，不依赖任何外部模块（except stdlib）

### Step 1.5: 知识库一致性验证 (Knowledge Consistency Check)

**每次对 `data/knowledge/` 文件做批量增删改后，必须验证键名一致性。** 这是本 session (Iter 92-101) 发现的核心 bug 类型：food/hotel 文件中使用了 CITIES 数据库不存在的键名。

```bash
python3 -c "
from data.knowledge.cities import CITIES
from data.knowledge.food import FOOD
from data.knowledge.hotels import HOTELS

all_c = set(CITIES.keys())
food_k = set(FOOD.keys())
hotel_k = set(HOTELS.keys())
regions = {'yunnan','tibet','hainan','dali','macau','taipei'}  # 允许的 region/非城市名

for k in food_k:
    if k not in all_c and k not in regions:
        print(f'❌ FOOD 多余键: {k} (不在 CITIES 中)')
for k in hotel_k:
    if k not in all_c:
        print(f'❌ HOTEL 多余键: {k} (不在 CITIES 中)')

# Also check: 所有 CITIES 中的城市应该被 FOOD 和 HOTEL 覆盖
for k in all_c:
    if k not in regions and k not in food_k:
        print(f'⚠️   CITIES 有 {k} 但 FOOD 无')
    if k not in hotel_k:
        print(f'⚠️   CITIES 有 {k} 但 HOTEL 无')
print('✅ 一致性检查完成')
"
```

**已知键名陷阱：**
| 错误键名 | 正确键名 | 原因 |
|----------|----------|------|
| `kunming` | (属于 `yunnan` 区域) | 昆明是云南一部分，CITIES 中无独立 `kunming` 键 |
| `lhasa` | `lasa` | CITIES 数据库中拉萨拼音键为 `lasa` |
| `guizhou` | `guiyang` | 贵州是省份名，城市键是 `guiyang`（贵阳） |
| `macau` / `taipei` | — | 在 CITIES 中但通常不需要 food/hotel 数据 |

**扩展知识库时的核对步骤：**
1. `python3 -c "from data.knowledge.cities import CITIES; print(sorted(CITIES.keys()))"` → 列出所有有效键
2. 将新 food/hotel 数据使用**完全相同的键名**
3. 运行上述一致性验证脚本
4. 修复不匹配的键名

### Step 2: 路由层 (api/index.py)

新增 API endpoint 提供 JSON 数据：

```python
@app.get("/api/mymodule/{key}", response_class=JSONResponse)
def api_mymodule(key: str):
    try:
        from data.knowledge.mymodule import get_item
        data = get_item(key)
        if not data:
            raise HTTPException(404, f"'{key}' not found")
        return data
    except ImportError:
        return JSONResponse({"error": "Module not loaded"}, status_code=500)

@app.get("/api/mymodule", response_class=JSONResponse)
def api_mymodule_list():
    try:
        from data.knowledge.mymodule import get_list
        return {"items": get_list()}
    except ImportError:
        return JSONResponse({"error": "Module not loaded"}, status_code=500)
```

**重要：** 使用 `try/except ImportError` 包裹 import，这样即使 Vercel 冷启动时模块加载失败也会返回 500 而非崩溃。

### Step 3: 页面层 (api/index.py — page_* functions)

添加 HTML 页面函数 + 路由。每个页面的函数体是一整个大的 return 字符串。

```python
def page_mymodule() -> str:
    """页面描述"""
    return """<!doctype html>..."""
```

**页面路由：**

```python
@app.get("/mymodule", response_class=HTMLResponse)
def mymodule_page():
    return page_mymodule()
```

### Step 3.5: 导航栏集成 (Nav Bar Integration)

**所有新建的独立页面（非 chat/trip 核心 UI）必须在 HTML 开头插入统一导航栏。** 使用全局 `_nav("/page-path")` 函数。

**模式 A — 函数式页面 (推荐)：**
```python
def page_mymodule() -> str:
    return _nav("/mymodule") + """<!doctype html>..."""
```

**模式 B — 内联路由页面 (适用于小页面)：**
```python
@app.get("/mymodule", response_class=HTMLResponse)
def mymodule_page():
    return _nav("/mymodule") + """<!doctype html>..."""
```

**⚠️ 为什么用 `nav + """..."""` 而不是 f-string？**
Python f-string 中的 `{` 和 `}` 需转义为 `{{` `}}`。如果 nav 通过 f-string 嵌入，所有现有 CSS 花括号需再翻倍成四花括号。**规则：** 字符串拼接，绝不将 nav 嵌入 f-string。

**注册新页面到导航栏：** `NAV_ITEMS` 常量位于 `api/index.py` 全局区（404 处理器之后）。追加新条目：
```python
NAV_ITEMS = [
    ("/phrases", chr(127481)+chr(127472)+" Phrases"),
    ("/fx", "💰 FX"),
    ("/packing", "🎒 Pack"),
    ("/hotels", "🏨 Hotels"),
    ("/export", "📄 Export"),
    ("/journal", "📖 Journal"),
    # ← 在此追加
]
```
_nav() 会自动为当前页面添加 `.act` 高亮类。

**CSS 风格指南（VisePanda 暗色主题）：**
- 背景: `#0d1117`
- 卡片: `#161b22`
- 边框: `#30363d`
- 强调色: `#f0883e` (标题渐变), `#bc3a2c` (按钮)
- 文字: `#e6edf3` (主要), `#8b949e` (次要), `#c9d1d9` (正文)
- 字体: `'Inter', sans-serif`
- header 渐变: `linear-gradient(135deg,#1a1f2e 0%,#0d1117 100%)`
- 标题渐变: `linear-gradient(135deg,#f0883e,#e05a2a)` → `-webkit-background-clip:text`

**页面结构模板：**
```html
<div class=header>
<h1>...</h1>
<p>...</p>
</div>
<div class=container>...</div>
<div class=footer><a href=/>← Back to VisePanda</a></div>
```

### Step 4: 知识层 (api/prompt.py)

将新知识注入 LLM system prompt，让 AI 在对话中知道并使用新功能：

```python
# 1. 文件顶部导入
from data.knowledge.mymodule import format_for_prompt as mymodule_prompt

# 2. SYSTEM_PROMPT 中添加
**模块名（中文描述）：**
{mymodule_prompt()}
```

**同时更新 prompt.py 的 behavior section，让 LLM 知道如何推荐这个新工具：**
```python
### 5. XX功能
当用户需要XX时，你可以...并推荐用户访问 /XX 页面
```

### Step 5: 部署层

```bash
# 编译检查
python -c "import sys; sys.path.insert(0,'api'); from index import app; print('✅ App OK')"

# 数据文件检查
python -m py_compile data/knowledge/*.py

# 知识库一致性检查（如新增 food/hotel/transport）
python3 -c "
from data.knowledge.cities import CITIES
from data.knowledge.food import FOOD
from data.knowledge.hotels import HOTELS
# ... 运行完整的键名一致性验证
"

# 提示词文件检查
python -m py_compile api/prompt.py

# git push
git add -A && git commit -m "Iter N: 改动简述" && git push origin main

# 等待部署 + 验证
sleep 20
curl -sL -o /dev/null -w "%{http_code}" https://go2china.space/mymodule
# 如果第一次非 200，再等 10s 重试（Vercel 传播延迟）
```

## 批处理模式

当一次性添加大量同类数据（如补全 14 城美食 + 16 城酒店），遵循以下规则：
1. **数据源** — 使用真实城市的美食/酒店知识，不编造
2. **数据结构一致** — 每个条目字段相同（name_zh, name_en, type, price_range, description, must_try）
3. **最少 5 条/城** — 每个城市至少 5 项，包含 must_try=True 的经典 + must_try=False 的特色
4. **每轮 commit 只做一件事** — 数据添加单独 commit，页面单独 commit

## 已用此模式实现的迭代

| Iter | 数据层 | 路由/页面 | 知识层 | 类型 |
|:----:|--------|-----------|--------|------|
| 82 | `data/knowledge/phrases.py` | `/phrases` + `/api/phrases/{cat}` | 注入 SYSPROMPT | 🆕 新页面 |
| 83 | (内联 random) | `/fx` + `/api/fx/rates` | 无(纯 UI) | 🆕 新页面 |
| 84 | `data/knowledge/packing.py` | 无 | 注入 SYSPROMPT | 🧠 知识扩增 |
| 85 | `data/knowledge/hotels.py` + food.py 扩增 | 无 | 注入 SYSPROMPT | 🧠 知识扩增 |
| 86 | 无 | `/export` | 无 | 🆕 新页面 |
| 88 | `data/knowledge/emergency.py` | 无 | 注入 SYSPROMPT | 🧠 知识扩增 |
| 89 | 无 | `/journal` | 无 | 🆕 新页面 |
| 90 | 无 | `/links` + `/sitemap.xml` | 无 | 🆕 新页面 |
| 91 | 无 | 无 | 更新 Behavior 引导 | 🧠 知识扩增 |
| 92-93 | 14+ 城 food + 17+ 城 hotel 扩增 | 无 | 注入 SYSPROMPT | 🧠 知识扩增 |
| 94-95 | 无 | 404/500 error pages + nav bar | 无 | ⚙️ 系统 |
| 96-101 | 数据一致性修复 | 无 | 无 | 🐛 Bugfix |

## 多小迭代合并提交策略

### 什么时候合并
当多个小迭代的改动互补、互不冲突时（例如：数据文件 + 页面的 API 调用），可以合并为一个 commit。

### 什么时候分开
当一个迭代的改动有风险或需要独立验证时（例如：修改核心路由逻辑、数据库 schema 变更），必须单独 commit。

### 合并时的 commit message 格式
```
Iter N-M: 总描述（子描述A + 子描述B + 子描述C）
```
示例：`Iter 86-88: Trip PDF export page, Emergency assistance data (9 embassies, 4 scenarios, emergency numbers), hotel+food knowledge expansion`

### 实践案例
Iter 81-91 (当前批次) 分为 7 个 commit（含 3 次合并）：
| Commit | Iter | 类型 | 原因 |
|--------|:----:|------|------|
| 1 | 82 | 独立 | 语言急救卡需要独立验证 API + 页面 |
| 2 | 83 | 独立 | 新页面 + Canvas 图表，需独立验证 |
| 3 | 84 | 独立 | 仅知识注入，简单独立 |
| 4 | 85 | 独立 | 酒店+美食数据全为扩增，独立验证 |
| 5 | 86-88 | **合并** | 3 个小迭代（页面+数据+知识），互不冲突 |
| 6 | 89-90 | **合并** | 2 个页面 + 1 个 XML 文件 |
| 7 | 91 | 独立 | 仅 1 行 prompt 修改 |

## 已知问题

1. **新建路由第一次 curl 可能 404** — Vercel 需要约 20-30s 完成构建 + 全球 CDN 传播。push 后等 20s 再验证
2. **patch 可能导致函数重复定义** — 在单文件 app 中连续 patch 同一区域，旧定义不会被覆盖而是重复出现。每次 patch 后必须编译验证
3. **页面数量膨胀** — 所有 HTML 页面都内联在 index.py 中，大文件（2000+ 行）的 patch/search 越来越慢。可考虑将纯文本页面移到 `data/pages/` 目录按需加载，但需要在 Vercel 上验证 import 路径
4. **API 端点冷启动返回空响应而非 JSON 错误** — Vercel Serverless 冷启动时，如果模块 import 失败，第一个请求可能返回空 body（非 JSON），导致前端解析崩溃。**修复：** 所有 API 端点用 try/except ImportError 包裹 import 逻辑，并返回 JSON error 而非崩溃
5. **Vercel 冷启动首次 curl 返回 `000` 或空 body** — 非代码问题，但会干扰部署验证脚本。**规则：** 验证 API 端点时，对第一个非 200/非 JSON 响应不要立即判定失败；等待 5-10s 重试一次
6. **知识库键名一致性** — food/hotel/transport 等数据文件的键必须与 CITIES 数据库完全一致。不一致会导致 LLM 知识引入失效。**修复：** 每次扩展后运行 Step 1.5 的一致性检查
7. **导航栏漏加** — 新建独立页面后容易忘记加 `_nav()`。**规则：** 在写页面 return 语句时就带上，不要后续补
