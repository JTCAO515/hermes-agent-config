---
name: project-iteration
description: 项目迭代管理框架 — 自动化迭代模式、进度统计、暂停汇报、遗留项追踪。适用于长期迭代开发项目（如 VisePanda）。触发词：自动化迭代 / 迭代 / iteration / 暂停 / 统计进度
---

# 项目迭代管理

## 概述

本技能定义用户猪猪微的项目迭代工作方式。适用于所有需要持续迭代的非一次性项目。

核心原则：
1. **自动化迭代** — 用户说"自动化迭代"后，不需要每次验证，持续推进
2. **精确统计** — 每次用户消息 = 1 条指令，每次部署/测试通过 = 1 次生效
3. **暂停汇报** — 用户说"暂停"时，汇总全部进度 + 跳过项
4. **跳过留痕** — 需要用户提供凭据/手动的步骤跳过但记录，暂停时汇总

## 进度统计规则

### 指令计数

| 事件 | 计数 | 说明 |
|------|:----:|------|
| 用户发一条消息 | **1 指令** | 每条用户消息独立计数，无论长短 |
| 自动 cron 触发 | **1 指令** | cron 的任务提示算一条用户指令 |
| Trae.ai 每条 prompt | **1 指令** | 迭代 prompt + 修正 prompt 都算 |

### 部署/生效计数

| 事件 | 计数 | 说明 |
|------|:----:|------|
| 代码注入 | **1 部署** | 每次 write_file / patch 写入生效 |
| 服务启动/重启 | **1 部署** | systemd restart / uvicorn start |
| git commit | **1 部署** | 代码变更落库 |
| Vercel 部署 | **1 部署** | deploy --prod |
| 数据库迁移 | **1 部署** | SQL 执行 / schema 变更 |
| 测试通过 | **1 部署** | 验证门禁通过 |
| 配置生效 | **1 部署** | config set / env var 设置 |

### 统计报告模板

```
| 日期 | 项目 | 指令 | 部署 |
|:----:|------|:----:|:----:|
| 5/17 | Italy Lux I1–I10 | 20 | 10 |
| 总计 | | 70 | 65 |
```

## PM 规划主导开发模式 (Plan-Led Development)

> **来源：** 用户 2026-06-16 明确要求「先写好产品的这个计划，每一步怎么做，需要调用什么工具，从资深的产品经理的角度去写清楚，然后再开始写」。随后指定「每一个步骤和我汇报一下，我确认了再开始写下一个步骤」。
> **适用场景：** 全新项目启动、Web→原生App迁移、大型架构改造。**不适用：** 已有自动化迭代协议的小步迭代项目。

### 触发

用户说以下任一即进入模式：
- "先写好规划再开始"
- "从资深的产品经理角度去写"
- "先写pm产品规划文档"
- 用户要求写 PM 文档之后再做

**注意：这个模式也适用于已有项目的小功能添加（如用户登录系统/管理后台），不只是全新项目。** 对于小功能，规划文档可以缩为单篇 `AUTH_PLAN.md` 或 `FEATURE_PLAN.md`，包含：Why / What / Architecture / Data Model / API / UI Flow / Iteration Plan。不必写完整三件套，但**不能跳过规划直接写代码**。

### 行为规则

| 阶段 | 动作 | 用户角色 |
|------|------|---------|
| ① **写 PM 文档** | 写完整产品规划（愿景·功能·技术选型·屏幕映射·API契约·工作量·风险） | 评审 |
| ② **确认规划** | 用户说「可以」「按照你的方式去写」后进入下一步 | **决策** |
| ③ **逐模块实施** | 按 Step 1→2→3 顺序执行，每个步骤完成时**汇报** | 里程碑确认 |
| ④ **等待门禁** | 每步完成后问「确认可以继续吗」，用户说「可以」/「继续」后再进入下一步 | **门禁** |

### 与自动化迭代模式的区别

| 维度 | PM 规划主导模式 | 自动化迭代模式 |
|------|----------------|--------------|
| 触发 | 全新项目 / 大迁移 | 已有项目的持续迭代 |
| 节奏 | Step-by-step，每步等确认 | 连续推进，不需确认 |
| 规划粒度 | 整份 PM 文档（12节） | 单轮 ITERATION_PLAN.md |
| 用户介入 | **每步汇报+确认**（门禁） | 仅暂停时介入 |
| 典型场景 | Web→原生App；第一次做某类型项目 | VisePanda/WC26 功能迭代 |

### 汇报模板（每步完成后）

```
## ✅ Step N 完成：[模块名]

### 交付清单
| 模块 | 状态 | 说明 |
|------|:----:|------|

### 关键文件
[列出新创建的文件]

### 下一步计划：Step N+1 — [模块名]
[一句话描述]

你确认可以继续吗？
```

用户回复「可以的」「继续」「按照你的方式」后进入下一步。

### PM 文档结构参考

完整的 VisePanda-Android PM 规划文档见 `android-native-development` skill 的 `references/pm-plan-led-workflow.md`。文档包含 11 个标准节：产品定位·功能全景·技术架构·ADR·屏幕映射·API契约·项目结构·关键实现策略·设计系统·开发计划·风险分析。

---

## 自动化迭代模式

### 触发

用户说以下任一即进入模式：
- "自动化迭代"
- "继续迭代不需要我验证"
- "不要停"
- 「继续」（在已有迭代上下文中）
- 「继续做完」/「全部做完」/「都做」 — **批量完成模式**（batch-completion）：一次性完成所有剩余工作，集中汇报一次。区别于「继续」（逐轮迭代），「继续做完」意味着评估所有剩余项→一口气做完所有能做的→commit+push→一次汇总报告。

### 触发对比

| 触发词 | 模式 | 节奏 | 汇报 |
|--------|------|------|------|
| 「自动化迭代」 | 连续单轮 | 一轮接一轮，每轮汇报 | 每轮一次小报告 |
| 「继续」 | 下一轮 | 执行下一轮 | 单轮报告 |
| 「继续做完」 | 批量完成 | 评估所有剩余→一口气干完 | 最终一次性汇总报告 |
| 「两个都做」/「都做」/「两个方向一起推」 | **平行执行** | 同时执行2个选项/方向，在同一轮内完成 | 一轮汇总报告 |
| 「全部都要」 | **多方向批量执行** | 对3-5个选项全部执行，分模块串行完成，统一commit+push | 一轮汇总报告多方向分节 |
| 「暂停」 | 停止 | 立即停止 | 暂停报告 |

#### 平行选项执行（两个都做）

当用户对选项做出「都做」回应时，进入平行执行模式。

...

#### 多方向批量执行（全部都要）

当用户对3-5个选项/方向做出「全部都要」回应时，进入多方向批量执行模式。区别于「两个都做」（只有2个方向），本模式用于用户选择**全面推进**时。

**执行规则：**
1. **分模块串行** — 按 CSS → JS → HTML → API 顺序依次完成，每个方向独立成块
2. **统一推送** — 全部方向完成后统一一次 git commit + push
3. **方向分组** — 3-5个方向按"先视觉→再功能→再后端"排序
4. **每方向验证** — 每完成一个方向做局部验证（CSS编译/JS lint/API测试），最后做全量验证
5. **汇报分节** — 每方向占一个小节

**典型模式：**
- 助手列出4个方向（A设计/B亮色/C响应式/D多轮对话）
- 用户回复「全部都要」→ 在同一迭代内全部完成
- 执行顺序：先CSS更新 → 再JS更新 → 再HTML更新 → 再API更新 → 最后全量测试

**Pitfall**：超过5个方向时建议让用户优选出前5个，其余排下一轮。每个方向至少需要独立的文件变更+验证，混搭太多会增大commit风险。

当用户对选项做出「都做」回应时，进入平行执行模式。区别于「继续做完」（评估所有剩余任务一口气干完），「都做」的典型场景是：助手给出了**多个选项/方向**（如「Option A: Prompt强化 / Option B: 前端美化」），用户选择同时推进。

**执行规则：**
1. 所有被选的选项在**同一轮迭代**内完成，不分先后Serial执行
2. 每个方向独立成块（如 Prompt 改完再写前端），但全部完成后统一 commit+push
3. 同一轮内可以包含跨模块变更（如后端 API + 前端 JS + CSS + HTML）
4. 汇报模板不变（一轮一次汇总报告），说明每个方向的完成内容

**典型模式：**
- 助手列出 Option A / Option B / Option C
- 用户回复「两个都做」→ 全部在同一轮内并行完成
- 用户回复「先做A」→ 单轮串行执行（等价于「继续」模式）
- 用户回复「都不做，先做X」→ 进入新的独立方向

**与「继续做完」的对比：**

| 维度 | 平行执行（两个都做） | 批量完成（继续做完） |
|------|---------------------|-------------------|
| 触发 | 用户对选项做出「都做」回应 | 用户对剩余任务说「继续做完」 |
| 范围 | 助手指定的选项 | 用户未完成的所有剩余任务 |
| 结构 | 多方向并行，每个方向独立成块 | 多任务串行，按任务列表逐个执行 |
| 常见场景 | A/B/C 方向选择 | 已规划的多轮迭代一次性交付 |

**⚠️ Pitfall**：平行执行模式下，不要试图用一轮并行混搭太多方向（>2-3个）。每个方向至少需要独立的文件变更和验证。如果超过3个方向，建议让用户优选出2-3个，其余排到下一轮。

### 每次迭代强制步骤

每次迭代完成后，**必须执行以下两步**，缺一不可：

**Step A — 部署到 GitHub：**
```bash
git add -A
git commit -m "Iter N: 改动简述"
git push origin main
```
- 每次迭代 = 至少 1 次 git commit + push
- push 后等待 Vercel 自动部署（sleep 15-20s）
- 用 curl 验证：`curl -sL -o /dev/null -w "%{http_code}" https://go2china.space/` 应为 200

**Step B — 迭代汇报（必走微信通知）：**  
每次 push 成功后，**必须立即通过微信（WeChat）DM 向用户发送本轮迭代汇报**，这是硬性要求。不准累积汇报、不准跳过、不准只写 changelog 不通知。格式如下：

```
## 📋 Iter N 完成汇报

### ✅ 本轮完成
[用简短列表描述本轮做了什么，包含文件变更、新增功能、修复内容]

### 📦 已部署上线
[描述部署结果，包含新路由/新功能的上线状态]

### 🔜 下一轮预期 (Iter N+1)
[描述下一轮迭代要做什么、预期达到的效果]
```

- **⚠️ 必须通过 `send_message` 显式指定微信 `target='weixin'` 投递，不能依赖当前会话渠道（否则可能串平台到元宝/CLI）**
- 汇报要**简洁具体**，让用户一眼知道本轮做了什么
- 下一轮预期要有明确目标，不是空话

### 行为规则（用户明确契约）

> 用户猪猪微的精确表述：**"所有流程不需要我确认，如果有需要我人工介入的环节就先跳过，但是记录好，在我暂停任务后你同意发给我"**

1. **零确认推进** — 除非功能必须用户决策才能继续，否则不停顿、不请示、不询问"这样可以吗"或"下一步做什么"
2. **跳过人工步骤留痕** — 需要用户提供凭据/手动在浏览器操作的步骤直接跳过，在暂停报告中以 `⏸️ 跳过项` 表格记录：跳过的内容 + 跳过原因 + 用户需要做什么
3. **持续记录累积变化** — 每个子步骤完成后记录做了什么：文件变更摘要 + 关键决策理由 + 统计（指令数/部署数）
4. **模块化迭代** — 一次迭代聚焦一个模块（如知识库、UI、地图），不交叉
5. **先写规划文件再执行** — 每个迭代批次开始时，写 `docs/ITERATION_PLAN.md` 定义本次 In Scope / Out of Scope，然后按计划推进

**关键约束：**

- **不能写/改的文件**：`.env`、`~/.hermes/.env`、任何含 API Key 或 Secrets 的配置文件
- **不能动的系统服务**：Xray、cron、systemd 服务
- **部署方式**：git push → 自动 Vercel 部署。不手动执行 `vercel deploy`
- **每次迭代必须 git push**：没有 git push 就不算一次完成的迭代。用户明确要求「每次迭代完后必须同步推送至 GitHub」
- **每次 push 后必须微信汇报**：每次部署后必须通过微信DM向用户发送本轮小结 + 下一轮预期。不准漏、不准攒。

### 所有项目必须有 ITERATION_LOG.md（除非另有明确约定）

用户在 2026-05-30 明确要求：**「以后所有项目都需要有一个迭代进度说明，迭代都需要延续之前的编号，并且将每个迭代版本的内容都记录」**

具体要求：
1. 每个项目的根目录下（或 `docs/` 目录下）必须有 `ITERATION_LOG.md`
2. 每次迭代完成后立即更新，记录：日期、改动内容、验证结果
3. 迭代编号从 git log 的最新编号延续，不从 1 重新开始
4. 内容要详实——每个改动的具体说明、改了什么文件、达到什么效果

**例外规则：** 对于 **WC26 Edge Lab** (`26-WorldCup-Edge`)，用户已明确批准 `PLAN.md` 替代 `ITERATION_LOG.md`（见下方 WC26 专用迭代模式）。当某个项目有显式的用户授权文档替代方案时，以该授权为准。判断标准：项目根目录下有 `PLAN.md` 且 WC26 模式在该项目上被用户明确启用过 → 用 PLAN.md 替代 ITERATION_LOG.md。

### ⚡ Pre-Deployment Verification（必做）

每次 git push 前（尤其是多轮迭代后），必须执行以下验证：

**Step 1 — 编译检查：**
```bash
# 验证 Python 语法 + 导入正确
python -c "
import sys; sys.path.insert(0,'api')
from index import app
print('✅ App imports OK')
"
```

**Step 2 — 数据文件语法检查：**
```bash
# 验证所有 Python 数据文件无语法错误
python -m py_compile data/knowledge/cities.py
python -m py_compile data/knowledge/*.py  # 如多个文件
```

**Step 3 — 关键路由快速验证：**
```bash
# 启动本地测试（如果项目支持）
python -c "
from index import app
from fastapi.testclient import TestClient
client = TestClient(app)
r = client.get('/')
assert r.status_code in (200, 307), f'Landing failed: {r.status_code}'
print('✅ Landing OK')
"
```

**⚠️ 常见部署失败模式：**
| 模式 | 原因 | 预防 |
|------|------|------|
| `NameError: name 'Column' is not defined` | 单文件 app 新增模型时忘了 import | Step 1 可捕获 |
| `SyntaxError: invalid syntax` + `Perhaps you forgot a comma?` | 大型 dict/JSON 数据文件新增条目后少逗号 | Step 2 可捕获 |
| `ModuleNotFoundError` / `ImportError` | 新增文件的 import 链断裂 | Step 1 可捕获 |
| `FROM module import X` 本地正常，Vercel 返回 500 | **Vercel Serverless 模块导入路径 bug** — 同目录模块 (`from fx import convert`) 在 Vercel 上解析失败，本地正常。**修复：将依赖逻辑内联到路由函数内**，不要单独建文件再 import。或者从 `index.py` 所在目录使用绝对路径导入 | 新建功能模块时优先**内联到现有路由函数**，而非创建新 .py 文件。必须创建新文件时，将逻辑复制到路由函数体内作为 fallback |
| `FUNCTION_INVOCATION_FAILED` (Vercel 500) | 未在 Vercel 设置环境变量 | 暂停报告时列出所有缺失的 env var |
| **Vercel cold start timeout — all endpoints share `get_predictions()`** | All API endpoints (`/wc/predict`, `/wc/odds-full`, `/wc/odds-math`, `/wc/daily-picks`) call `get_predictions()` which runs the ~5s Poisson model. On Vercel cold start, every endpoint independently reruns this → 5-8s each, easily exceeds 10s limit. **Fix:** Create `_from_cache()` variants that read pre-computed JSON. Each endpoint tries cache first, falls back to live model only if cache is empty. See `references/wc26-data-persistence-api-extension-pattern.md` section "Vercel Cold Start Caching Pattern" | Before deploying new predictive features, run `grep -n "get_predictions" api/index.py` to find ALL endpoints that call it. Every one needs a cache variant. |
| **Vercel `DEPLOYMENT_NOT_FOUND` — 域名项目被删除** | curl 返回 `"The deployment could not be found on Vercel"` — 域名绑定的 Vercel 项目已被卸载/删除，不是冷启动或构建延迟。**特征：** 根路径 `/` 和 API 端点都返回相同 `DEPLOYMENT_NOT_FOUND`，而不是 307→404→200 的构建传播链。**修复：** 需要用户重新在 Vercel Dashboard import GitHub 仓库关联域名，或提供 `VERCEL_TOKEN` 后用 CLI 重新 `vercel deploy --prod`。不要继续 git push + curl 等待——项目不存在时 Vercel 不会自动触发构建。迭代汇报中注明「❌ Vercel 项目已删除，需要你重新关联」。 | 任何 Vercel 项目；git push 后 curl 返回 `DEPLOYMENT_NOT_FOUND` 先怀疑项目被删，而非构建延迟 |
| **JS 0 || "?" falsy bug 导致比分显示异常** | 使用 `m.result.team_b_goals || "?"` 时，`0` 是 falsy → 合法比分 0 显示为 `?`。**修复：** 用显式 `!= null` 检查替换 `||` 默认值。详细见 coding-workflow skill「JavaScript 0 || 默认值陷阱」 | render 函数中所有数字字段（比分/xG/概率）用 `_val(v) { return v != null ? v : "?" }` 包裹 |
| FastAPI `request.json()` 报错 | 同步路由函数中调用了 `await request.json()`（async 方法）。**修复：** 路由函数必须是 `async def` 才能 `await request.json()`；同步路由用 Pydantic 请求体模型 | Step 3 可捕获 |
| **在错误项目中修改代码（VP-Hermes-Web vs VP-Hermes-APK）** | 两个独立仓库都部署到同一个域名 `hermesapp.go2china.space`，代码库完全不同。`VP-Hermes-Web` = 旅行聊天 SPA（单页 travel chat），`VP-Hermes-APK` = 管理后台 React SPA（后端/admin 面板）。修改 APK 的 `admin/` 目录不会影响 Web 的前端页面。**预防：** 每次修改前先 `pwd` + `git remote -v` 确认当前仓库。用户说「VP-Hermes 页面」时追问是聊天页还是管理后台。修改后 push 到对应仓库的对应 git remote。 | 听到「vp-hermes」「visepanda」时先确认子项目 |
| **登录按钮默认隐藏，JS 初始化未调用 UI 更新函数** | HTML 中登录按钮写死了 `style="display:none"`，JS 的 `_updateAuthUI()` 只在 `if (_authToken)` 分支内部调用（token 存在时才调）。**没有 token 时 `else` 分支不存在** → `_updateAuthUI()` 从不执行 → 按钮保持 `display:none` 永不可见。**修复：** 在 `if/else` 双分支出口都调用 `_updateAuthUI()`，或无条件在 `init()` 末尾调一次。**预防：** 所有登录按钮的初始可见性应由 JS 驱动，而非 HTML 硬编码隐藏。`_updateAuthUI()` 必须在 auth 模块的每个出口（有 token / 无 token / 获取失败）都被调用。 | 任何有登录按钮的前端项目；测试方法：清除 localStorage 后刷新页面，看按钮是否可见 |
| **前端版本号从 API 动态拉取代 HTML 值，API 版本号不同步** | 前端 JS 在 `init()` 中 `fetch('/api/health').then(d => { ver = d.version })` 覆盖 HTML 中的 `version-badge`。如果后端 API 返回的 `version` 字段与 HTML 硬编码值不同（如 API 返回 `"0.1.0"` 而 HTML 写 `"v4.0.5"`），用户看到的永远是 API 的旧版本。**根本原因：** 后端 API 的 version 字段来自不同项目/部署（如 VP-Hermes-APK 的 admin 后端覆盖了 VP-Hermes-Web 的 API 端点）。**修复：** 确保 `/api/health` 的 version 与 HTML 同步更新（改 HTML 号的时候一起改 API）。或者让 JS 只 fallback 到 API（HTML 值 = 最终显示值），API 仅用于强校验。**预防：** `grep -rn 'version' web/index.html web/app.js api/index.py` 确认三处一致。特别注意 Vercel 路由重写时 `/api/*` 可能被代理到不同后端。 | 版本号页面显示异常时排查顺序：① curl /api/health 看返回 ② 确认请求的正是本项目的 API 而非代理到其他后端 ③ grep 三处版本号 |
| **Duplicate function definition after patch** | 在大型单文件 app 中 `patch` 同一函数两次以上，会产生重复的函数定义（`@app.get(...)` + `def fn():` 出现两次）。Python 中第二个定义会覆盖第一个，编译时可能报 `IndentationError`，运行时导致 route 注册混乱。**修复：** patch 前先 `read_file` 确认函数边界；patch 后立即 `python -c "from index import app"` 编译验证 | 避免连续 patch 同一大文件的重叠区域；每次 patch 后独立验证 |
| `SyntaxError: f-string: invalid syntax` | 在 f-string 中嵌入 CSS 时 keyframe 百分号冲突。**修复：** 双重大括号 `{{0%{{...}}}}` | `python3 -c "import ast; ast.parse(...)"` 语法检查 |
| **Skeleton CSS 类名不同步** | chat.js 用 `skel-block/skel-line/skel-w-*` 但 CSS 用 `skel-text/skel-card` 等→骨架不可见。**修复：** 确保 JS 引用的所有 class 在 CSS 中都有定义 | 修改动效时，列出 JS `msg()` 函数全部 CSS 类名，与 CSS 逐一核对 |
| **i18n 中文自动检测覆盖 English 设置** | `navigator.language.startsWith('zh')` 自动切中文。**修复：** English-native 站点须注释/移除自动检测逻辑 | 英文化后连带移除 i18n.js 自动检测 |
| **SSE stream 缺少 error 处理** | 后端的 `/api/chat` 流式端点可能返回 `{"error":"..."}` 但前端 SSE 解析循环只处理 `j.token` 和 `j.trip_update`，忽略 `j.error` → 骨架 loading 一直显示，用户看不到错误。**修复：** chat.js 的 stream parser 中增加 `if (j.error) { show error + restore send button }` | 所有流式 API 响应必须在前端处理 error 字段 |
| **Vercel 冷启动返回空 body** | API 端点首次请求（冷启动）可能返回空 body 而非预期的 JSON，导致 curl 脚本解析错误。不是代码问题，是 Serverless 冷启动 + CDN 缓存共同作用。**修复：** 验证 API 端点时，对第一个非 JSON 响应等待 5-10s 重试一次 | 验证脚本中增加重试逻辑；非 200/非 JSON 不立即判定失败 |
| **New route returns 307→404→200** | Vercel 部署传播有延迟。push 后第一次 curl 可能返回 307 (redirect)，第二次 404 (旧 build)，第三次才 200。**规则：** push 后先 sleep 15s，curl 看状态码；若非 200 再 sleep 10s 重试一次；不要因一次 404 就判定部署失败 | sleep 15-20s 后再首次 curl；若非 200 重试一次；最终检查页面内容 header 确认是新代码 |
| 上线后立即 curl 验证所有路由（含新增的） |
| **Vercel 部署拒绝 — commit author email 无效** | Vercel 要求 commit author email 必须与 GitHub 账号绑定的邮箱一致。如果 `git config user.email` 填了非 GitHub 注册邮箱，Vercel 拒绝部署并提示 `not a valid email address`。**修复：** `git config user.email "实际GitHub邮箱"` → `git commit --amend --author="用户名 <邮箱>" --no-edit` → `git push origin master --force` (注意: force push 会覆盖远端历史, 单人项目可接受) | 首次为项目 commit 前先确认 git config user.email 正确。**坑：** 不能从 GitHub 公开资料查到邮箱（可能设为 null），必须问用户。新项目的首次 commit 就应确保 email 正确，避免后续反复 amend |

| **Service Worker cache-first 导致静态文件更新不被浏览器感知** | JS/CSS/HTML 更新部署后，浏览器仍使用 SW 缓存的旧版本 → 页面卡在 loading spinner。**原因：** SW 使用 cache-first 策略（`caches.match(e.request).then(hit => hit || fetch(e.request))`），浏览器从缓存读取。**修复：** 在 `sw.js` 中变更缓存名称（如 `wc26-v1` → `wc26-v2`），这会触发 SW 重新安装 → 重新缓存所有静态资源。仅修改 sw.js 内容不够（必须让浏览器检测到 SW 字节变化）。**验证：** `browser_console` 运行 `caches.keys()` 查看活跃缓存，`navigator.serviceWorker.getRegistrations()` 检查 SW 状态。清除所有缓存 + 注销 SW 后再 reload 确认。**详见** `references/wc26-sw-cache-bust-pattern.md` | 所有使用 Service Worker 的 Vercel 前端项目；部署 JS 修复后若页面仍不工作，先查 SW 缓存 |

### 迭代完成强制流程

**⚠️ 重要前提 — 上下文衰减防护：**

自动化迭代跑多轮后，系统提示和早期指令会被挤出上下文窗口，导致模型忘记通知步骤。这是"前面几轮会汇报，后面就没声了"的根本原因。

**解决方案 — 每轮迭代开始前必须重置上下文提醒：**

在开始每轮迭代的代码工作前，必须向自己重申一次：
> "本轮迭代完成后，必须使用 `send_message(target='weixin')` 通过微信向用户发送迭代汇报。不通知 = 本轮未完成。"

也可以在执行第 3 步之前对自己发一条内部提醒（通过 todo 工具或终端 echo 打印）。

**四步走 + 最终检查清单**：

每次迭代完成后，按以下顺序执行，**缺一不可**。最后必须通过最终检查清单才算完成。

| 步骤 | 动作 | 跳过后果 |
|:----:|------|---------|
| ① | 代码修改 + 版本号更新 + Pre-Deployment 验证 | 代码不可上线 |
| ② | git push 到 GitHub | 代码不同步 |
| ③ | curl 验证部署 | 可能上线即挂 |
| **④** | **send_message 微信通知** | **用户不知道你做完** |

**最终检查清单（每轮迭代完成后，逐项确认，全部 ✅ 才算完成）：**

```
□ ① my code changes are done and verified
□ ② git push succeeded (or I checked there's nothing to push)
□ ③ curl verification returned 200
□ ✅ I called send_message(target='weixin') — NOT just text output, NOT sent to wrong platform
```

如果清单不完整（尤其第④项缺失），则本轮迭代视为「未完成」。

---

### 第0步：确认项目仓库（防止修改错误项目）

> **风险来源：** 用户有多个独立项目 (VP-Hermes-Web / VP-Hermes-APK / WC26-Main / WC26-Nami)，都在本地 `~/projects/` 下。domain `www.go2china.space` = VP-Hermes-Web (Vercel vise-panda-2)；`hermesapp.go2china.space` = VP-Hermes-APK Admin (另一个 Vercel 项目)。搞混会导致修改了错误项目、推送到了错误的 repo。

**每次开始新一轮迭代前，必须执行：**

```bash
# 检查当前目录
pwd
git remote -v
git log --oneline -1
```

**对照目标项目确认：**
- 用户说「VP-Hermes 页面」= VP-Hermes-Web（旅行聊天 SPA），不是 APK 管理后台
- 用户说「登录/Admin 面板」= VP-Hermes-APK（React Admin SPA）
- 听到「vp-hermes」「visepanda」时先确认子项目再动手
- 修改后推送到**正确的 git remote** — 不同项目有各自的 GitHub 仓库和 Vercel 自动部署

**已知项目映射：**
| 项目 | 本地路径 | GitHub | Vercel | 域名 |
|------|---------|--------|--------|------|
| VP-Hermes-Web | `~/projects/VP-Hermes-Web/` | JTCAO515/VP-Hermes-Web | vise-panda-2 | www.go2china.space |
| VP-Hermes-APK Admin | `~/projects/VP-Hermes-APK/admin/` | JTCAO515/vp-hermes-APK | (独立项目) | hermesapp.go2china.space |

### 第1步：检查最新迭代编号
查看 git log 确定最新的实际迭代编号，避免跳号或重复：
```bash
git log --oneline --grep="Iter" | head -3
```
**下一迭代编号** = 最新 commit 中的 Iter 号 + 1。不要依赖 ITERATION_LOG.md 中的编号（可能不完整）。

### 第1.5步：版本号更新（强制 — 每次 push 前必做）

> **来源：** 用户 2026-06-19 明确纠正「每次迭代后都需要在github上面部署，每次都需要更新版本号，现在版本v4.0.1」

**每次 git push 前，必须先更新版本号。没有版本号更新的提交 = 未完成的迭代。**

```bash
# 1. 找到所有版本号出现的位置
# 每个项目可能在不同文件中，必须主动搜索
grep -rn "v[0-9]\+\.[0-9]\+\.[0-9]\+" web/index.html web/app.js web/app.css README.md CONTEXT.md api/ 2>/dev/null
# 也可能是 vX.Y 格式（两段式）
grep -rn "v[0-9]\+\.[0-9]\+" web/index.html web/app.js 2>/dev/null | grep -v "//\|/\*\|\.css"

# 2. 用 sed 统一替换为新版本号
sed -i 's/旧版本号/新版本号/g' web/index.html web/app.js web/app.css README.md CONTEXT.md api/prompt.py

# 3. grep 验证全部更新，不应有旧版本号残留
grep -n "旧版本号" web/index.html web/app.js web/app.css README.md 2>/dev/null
# 应返回空
```

**常见陷阱：**
- 版本号可能在 5+ 个文件中出现（index.html 的 title/nav-badge/footer + app.js 头部注释 + README.md 标题/版本表 + CONTEXT.md + API 文档）
- 需要全部同步更新，任何一个残留都会导致版本号不一致
- 使用 `sed` 批量替换后必须 grep 验证，防止遗漏

---

### 第2步：Pre-Deployment 验证
执行上节 `Pre-Deployment Verification` 中的所有检查（编译检查 / 数据文件语法检查 / 关键路由验证）。

如果验证失败：先修复，再继续。绝不跳过。

### 第2b步：git push 到 GitHub
```bash
cd /home/ubuntu/projects/vise-panda-2
git status  # 确认变更内容
git add -A
git commit -m "Iter N: 改动简述"
git push origin main
```

### 第3步：验证部署
```bash
sleep 20  # 等待 Vercel 构建
curl -sL -o /dev/null -w "%{http_code}" https://go2china.space/
# 如果返回值不是 200，检查 Vercel Dashboard 日志
# ⚠️ Vercel 冷启动：首次 curl 可能返回 000 或空 body
# 对 API 端点：第一次非 JSON 响应不代表失败，等 5-10s 重试一次
```

**增强验证（前端改动后必做）**：curl 返回 200 后，用 `browser_navigate` 打开部署 URL 导航至各关键 Tab，确认新功能/修复在线上生效：
1. `browser_navigate(url)` — 检查页面加载、summary bar、nav
2. 依次 `browser_click` 各 Tab 按钮 → `browser_snapshot` 确认内容渲染
3. 如果是静态文件/图标改变（manifest.json/sw.js/icon.svg），用 `browser_snapshot` 或直接 curl 确认 200
4. 确认新增 UI 元素可见（如 CSV 导出按钮、淘汰赛进度条、推荐Badge）
5. 如果页面需要从 API 加载数据，等待 3-5s 后检查 snapshot 是否包含渲染后的内容

### 第4步：向用户汇报（强制微信投递）

**⚠️ 重要：必须使用 `send_message` 工具显式指定微信 `target='weixin'` 进行投递，禁止依赖"当前聊天渠道"。** 因为自动化迭代可能在元宝/CLI 等非微信上下文中执行，依赖当前渠道会导致汇报串平台。

```python
# 正确做法 — 通过 send_message 显式指定微信
from hermes_tools import send_message
send_message(target='weixin', message=report_text)

# 不要这样做 — 依赖当前渠道会串平台
# 直接输出文本 → 依赖"当前聊天渠道"
```

按以下模板发送汇报：

```
## 📋 Iter N 完成汇报

### ✅ 本轮完成
[简短列表：新增了什么、改了哪些文件、修复了什么]

### 📦 已部署上线
[描述部署结果、新功能的上线状态、路由是否可用]

### 🔜 下一轮预期 (Iter N+1)
[下一轮要做什么、预期效果]
```

汇报要点：
- 简明扼要，用户扫一眼就懂
- 涉及外部动作（新 API 端点 / 新 UI）要说明在哪里能看到
- 下一轮预期要有明确目标，不是套话

#### ⚠️ send_message 超时失败处理

`send_message(target='weixin')` 有时会返回 `"Weixin send failed: Timeout context manager should be used inside a task"`。这是 Hermes 运行时的异步上下文错误，不一定是网络问题。

**处理方式：**
1. 第一次失败后，**重试一次**（用更短的文案，减少内容长度可能缓解问题）
2. 如果再次失败，**不要卡住迭代流程** — 本轮报告内容仍然输出到对话中（用户可见），继续下一轮迭代
3. 记录到迭代日志中：`⚠️ 微信通知投递超时（内容已输出到对话）`
4. 不因此重试第三次 — 连续超时意味着系统层问题，重试无意义

> 此错误不影响推送本身（消息可能实际已送达）。关键是确保用户能看到报告内容，渠道可以是对话输出。不要因通知失败而重做或中断迭代。

### 批量完成汇报（多轮迭代一次性交付）
当用户要求"X轮迭代"且一次性完成所有轮次（中间无暂停）时，在全部完成后发送**批量完成汇报**，包含：

```
## ✅ X轮迭代完成报告 (Iter A → B)

### 本次新增页面
| 页面 | 功能 | 状态 |
|------|------|------|

### 知识库扩充
[总结新增的数据文件/知识注入]

### git 记录
[列出每轮的 commit message]

### 总体统计
| 指标 | 数值 |
|------|------|
| 总迭代数 | |
| 新增文件 | |
| 新增页面 | |
| 部署验证 | |
```

批量汇报模板见 `references/10-iteration-batch-report-template.md`。

### 5. 更新迭代文档
每次迭代完成后（或每批迭代完成后），更新项目内的迭代跟踪文档：
- `docs/ITERATIONS.md` — 追加本轮记录（功能描述、文件变更、关键决策）
- `docs/VISION_N_ITERATIONS.md` — 如果存在路线图文档，将已完成的迭代标记为 ✅

### 6. 版本追踪（用户查询用）
用户可能随时问"迭代到哪个版本了"。因此每次迭代的 git commit message 必须包含 `Iter N:` 前缀，以便通过 `git log --oneline --grep="Iter"` 快速查询。

在迭代汇报的最后，附带当前版本号：`当前版本: Iter N`。

### 7. 继续下一轮
- 如果用户说"继续"或处于自动化迭代模式 → 进入下一轮
- 如果用户说"暂停" → 执行暂停汇报流程

### 暂停与汇报

用户说"暂停"、"汇报"、"先到这"、"打一份报告"时：

1. 以 `project-iteration` skill 的暂停报告模板格式汇总：
   - 已完成的功能模块（含状态和说明）
   - 跳过的步骤及原因
   - 下一轮迭代建议
2. 更新 `docs/ITERATIONS.md` 追加本轮记录
3. 报告发送给用户

#### 特殊模式：定格冻结（Freeze & Ship）

当用户明确说「定格在这一刻」/「定格」/「冻结」/「冻结在现在」时，进入特殊的**定格冻结模式**，与普通暂停不同：

| 维度 | 普通暂停 | 定格冻结 |
|------|---------|---------|
| 触发 | 「暂停」「先到这」 | 「定格」「冻结」「定格在现在」 |
| 剩余工作 | 列出到待办清单 | **直接丢弃剩余工作**，不写入待办 |
| 代码状态 | 可能未完成 | 清理未完成文件（如损坏的占位文件），只提交已完成的 |
| 提交范围 | 所有变更 | 只提交**已完成的功能**，不包含半成品代码 |
| 文档 | 暂停报告 | 写 HANDOFF.md（完整快照），标注未完成项为「尚未开始」而非「进行中」 |

**规则：**
- **不追完成度** — 不试图补完剩余工作再提交。当前完成了什么就提交什么
- **清理损坏状态** — 删除因失败尝试留下的空/损坏文件（如 city-macau.jpg 29B），避免污染代码库
- **HANDOFF.md 必须写** — 定格冻结后必须产出完整的 HANDOFF.md，作为项目快照
- **记忆必须更新** — 将项目记忆标记为 ⏸️ 已暂停，清理旧的项目详情记忆条目
- **git push 必须做** — HANDOFF.md 写完后必须 commit + push 到远程仓库（`git add HANDOFF.md && git commit -m "vX.Y: Handoff document" && git push`），确保其他设备可恢复

#### 项目切换（Handoff → Clone → Continue）

当用户说「切到XX项目」时，按以下顺序操作：

**Step 1 — 当前项目 HANDOFF**
- 写 `HANDOFF.md`（完整12节模板见 handoff skill）
- `git add -A && git commit -m "vX.Y: Handoff — project paused" && git push`
- 更新 memory：将当前项目标记为 ⏸️ 已暂停

**Step 2 — 准备新项目**
- 如果新项目是 fork：`git clone <source> ~/projects/NEW_NAME && cd ~/projects/NEW_NAME`
- 如果是现有项目恢复：`cd ~/projects/<EXISTING> && git status` 验证状态

**Step 3 — 验证新项目状态**
- `git log --oneline -3` — 确认代码基线
- `git status` — 确认工作树干净
- 关键文件存在性检查（如 `data/*.json`, `web/index.html`）

**Step 4 — 读取 HANDOFF.md（如果存在）**
- 按 handoff skill 的恢复流程执行
- 先读文档，再验证，再提方向

### 用户说"暂停"、"汇报"、"先到这"、"打一份报告"时：

1. 以 `project-iteration` skill 的暂停报告模板格式汇总：
   - 已完成的功能模块（含状态和说明）
   - 跳过的步骤及原因
   - 下一轮迭代建议
2. 更新 `docs/ITERATIONS.md` 追加本轮记录
3. 报告发送给用户

**暂停报告模板：**
```markdown
## ✅ 本轮完成

| 迭代 | 模块 | 状态 | 说明 |
|:----:|------|:----:|------|

## ⏸️ 跳过项（需你提供）

| # | 项目 | 原因 | 需你配合 |
|---|------|------|---------|

## 📈 统计

| 项目 | 值 |
|------|-----|

## 建议下一步
- ...
```

**如需用户手动操作的详细文档（如暂停后用户问"需要我做什么"）：**
使用 **优先级分组 + 详细教程** 格式，而非简单列表：

```markdown
## 🔴 第一优先：[类别名]
### N️⃣ [任务名]
**步骤：**
1. 打开 X 网站
2. 点击 Y
3. 复制 Z
**要点：** [关键注意事项]

## 🟡 第二优先：[类别名]
...
```

分组原则：
- 🔴 第一优先 = 阻断性（服务不可用/功能不跑）
- 🟡 第二优先 = 功能性（功能可用但受限）
- 🔵 第三优先 = 增强性（锦上添花）
- ⚪ 第四优先 = 未来方向（不着急）

每组任务按实施难度/依赖顺序排列，每个任务附可执行的步骤教程。

> 参考案例见 `references/vise-panda-manual-steps-example.md`（VisePanda 80轮迭代暂停后的手动操作文档）

### 统计报告规则

- 每次迭代结束时累计统计：用户消息数（指令）、代码注入次数（部署）、commit 数、文件变更数
- 在暂停报告中包含统计表格

## WC26 专用迭代模式（强制 Changelog + Next Plan + GitHub Push + 汇报）

当迭代项目为 **2026 世界杯预测平台** (`26-WorldCup-Edge`) 时，应用以下增强规则。这个模式由用户在 2026-06-14 明确指定，优先级高于通用迭代规则。

### 每次迭代的三项强制产出

每次迭代完成后，**必须同时产出以下三项，缺一不可**：

**① Changelog（git commit message）**
- 必须包含清晰的变更摘要，格式：
  ```
  feat/fix/docs: 一句话概括本轮核心改动
  
  - 子项1
  - 子项2
  - ...
  ```
- commit message 末尾附 API 验证结果（如果改动涉及 API）

**② Next Iteration Plan（PLAN.md 更新）**
- 更新项目根目录的 `PLAN.md`，追加：
  - 本轮完成内容（markdown 表格：模块 | 状态 | 说明）
  - 数据亮点（如有预测结果变化，写出关键数字）
  - 下一轮计划（表格：模块 | 说明 | 优先级）
- `PLAN.md` 即为迭代路线图，不再需要单独的 `ITERATION_LOG.md`

**③ 微信汇报（必须用 `send_message` 显式指定微信投递）**
  ```
  ## ⚡ [项目名] — Iter N 汇报
  
  ### ✅ 本轮完成
  [简短列表]
  
  ### 📊 核心数据
  [关键指标/数字]
  
  ### 🔜 下一轮预期
  [明确的下轮目标]
  ```

### 流程约束

| 约束 | 规则 |
|------|------|
| Push 频率 | 每次迭代至少 1 次 git push，禁止攒多个迭代一起推 |
| 跳过确认 | 不需要用户确认「这样可以吗」，直接推进 |
| 用户主动叫停 | 用户说「停」时出暂停报告，否则不停 |
| 格式提醒 | 前端必须为 HTML（Vercel 静态文件），不要输出纯文本 UI。**用户已纠正过：「别忘了我是要部署到vercel上面的，格式要HTML」** |
| Vercel 部署凭证 | 若 `vercel whoami` 提示 `Error: No existing credentials found`，则无法自动部署。需要用户手动 `vercel login` 或设置 `VERCEL_TOKEN` 环境变量，或用户自行 `vercel --prod` 部署。此时应在迭代汇报中注明「❌ Vercel 未部署 — 需要你的 Token/手动登录」并给出操作说明 |
| 迭代编号 | 从 git log 最新 Iter 号延续，不重启编号 |
| 启动检查 | 每次恢复 WC26 项目时，先 `git status` 检查是否有未提交的改动。历史已出现多次「代码写了但没推」的情况。有未提交代码时：先 `git diff --stat` 了解变更内容，再决定是直接 commit+push 还是先补齐再推 |
| 版本发布重命名 | 每一个大版本迭代（vX.0）必须执行版本重命名流程，详见 `references/wc26-version-release-checklist.md` |

### 数据持久化 + API + 前端扩展模式

当为 WC26 添加新的算法模块（如量化引擎、新盘口类型、新的预测管线）时：
1. 不要修改 `data/wc2026_matches.json` 的 `checkpoints` 字段结构（它是 **list**，不是 dict）
2. 新增 `predictions` 字段存储计算数据，不破坏原 schema
3. 前端加新 Tab 必须同步 HTML/CSS/JS 三层
4. WSGI 路由用 try/except + 局部 import 模式

- `references/wc26-data-persistence-api-extension-pattern.md`
- `references/backtest-statistical-patterns.md` — Bootstrap 回测置信区间 + 置换检验 p-value + Sortino/Calmar + 资金曲线最大回撤。纯 stdlib，适用于所有带回测的项目

### 版本发布重命名流程

每个 WC26 大版本迭代（vX.0）必须执行版本重命名。这包括更新网站名称、文档、导航栏和 PWA 配置。

**标网站命名格式**：`26年世界杯预测vX.Y - JTCao出品`

具体步骤和检查清单见 `references/wc26-version-release-checklist.md`。

### 与通用迭代规则的关系

| 维度 | 通用规则（VisePanda） | WC26 增强规则 |
|------|---------------------|--------------|
| 触发 | 用户说「自动化迭代」 | 用户说「写完迅速迭代，要一直迭代到我说停」 |
| 记录 | ITERATION_LOG.md | PLAN.md 追加式更新 |
| 汇报 | 可选 | **必做**（每一次迭代完成后都必须汇报） |
| 计划 | 先写规划文件再执行 | 每次迭代在 PLAN.md 追加「下一轮预期」 |
| GitHub | 每次迭代必须 git push | 同上，强调 changelog 质量 |

## OpenSpec 集成

对于长期迭代项目，建议在实施重要功能前先走 OpenSpec SDD 流程：

1. **提案** — `openspec new change "<feature-name>"` → 创建 proposal.md + design.md + specs/ + tasks.md
2. **验证** — `openspec validate <change-name>` → 确保规格通过
3. **实施** — 按 tasks.md 逐步实现（自动化迭代模式）
4. **归档** — `openspec archive <change-name>` → 归档到 openspec/changes/archive/

**并发规则：** 自动化迭代遇到 OpenSpec 提案时，先提交提案让用户确认，确认后按 implement-apply 循环执行。

### Pre-Iteration Review（项目健康审计）

用户说 "先 review 项目" / "先 audit 一下" / "看下项目状态" 时，在决定下一迭代方向**之前**先做一次健康审计。区别于"Review-Driven Fix Iteration"（已审查、要修），本阶段是**先审查再决策**。

#### 何时使用
- 长时间没碰的项目（>1 周）恢复工作时
- 接到新项目不知道从哪开始时
- 准备做大改/重构前的基线评估
- 任何"先看再说"型请求

#### 标准流程

**Step 1 — 项目元数据收集（3-5 条命令）**
```bash
# 仓库状态
cd ~/projects/<project> && git status && git log --oneline -10

# 代码规模
wc -l <module_dir>/*.py <module_dir>/static/*.html

# 测试基线
/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 -m pytest tests/ -q 2>&1 | tail -5

# 未解决问题清单
ls reports/ 2>/dev/null  # adversarial review reports
ls ROADMAP_*.md ITERATION_LOG.md 2>/dev/null
```

**Step 2 — 文档阅读（15s 内定位关键文件）**
- `README.md` — 宣称的能力与状态
- `ITERATION_LOG.md` — 历史迭代
- `ROADMAP_vX.Y.md` — 当前路线图
- 最近 5 个 git commit — 近期改动方向

**Step 3 — 交叉对照，发现宣称与现实的偏差**
- README 说"✅ X"但代码里搜不到实现
- ROADMAP 标"[ ]"但实际已完成
- 迭代日志说"修 bug X"但测试套件里没有回归测试

**Step 4 — Probe 驱动探针（关键差异点）**
如果项目有数学/算法模块，**写一个 Python 探针**跑边界 case。这一步在 adversarial review 之前就能发现 review 报告**没**标出的 bug。模板：
```python
# 对可疑模块的核心函数跑探针
from txpokerassist.ranges import parse_range, _expand_token
for r_str in ['A2s+', 'K9s+', 'KTo+', 'KJo+', 'TT+', '22+']:
    print(f'{r_str}:', sorted(parse_range(r_str)))
```

**为何重要**: 8 份 adversarial review 报告（DeepSeek + GLM 双模型）漏掉了 `Kx+/Qx+/Jx+/Tx+` 范围扩展误把高牌自身当一对的 critical bug，但一个 5 行的探针立刻就发现了。

**Step 5 — 写 review 报告 + 给用户选项**
保存到 `reports/review_vX.Y_pre_iteration.md`，结构：
1. 项目状态总览（一行表）
2. 模块健康度
3. **探针发现的 bug**（独立小节，与 review 报告 finding 区分）
4. 测试覆盖盲点
5. Adversarial review 状态（哪些修了/未修）
6. Roadmap 完成度
7. 3 个推荐下一迭代方向（按优先级 + 推荐组合）

#### 输出给用户
不要直接进入下一迭代，先呈现 3 个选项 + 推荐组合，让用户决策。

#### Pitfalls
- ❌ **只跑 pytest 不过探针** — 测试通过 ≠ 没有 bug。已知脆弱模块（边界条件、数学公式、范围解析）必须有针对性探针
- ❌ **跳过 git log 直接看 ITERATION_LOG.md** — 后者可能遗漏历史迭代。前者才是真实记录
- ❌ **把 review 报告 finding 当作"已修"** — review 报告里的 finding 必须用探针/测试**重新验证**，不能信任"上次迭代修了"
- ❌ **直接进迭代不做审计** — 用户说"先 review"的明确意图是**先看再说**，不是"review + 立即开干"

#### 复用支持文件
- `references/txpokerassist-architecture-and-gotchas.md` — TXPokerAssist 项目的架构、已知坑、探针起点

### Review-Driven Fix Iteration

当项目经历**对抗式审查**后进入修复阶段时，使用以下模式（区别于 VisePanda 式的功能迭代）：

### 区别

| 维度 | 功能迭代（VisePanda） | 审查修复迭代（TXPokerAssist） | 前端重设计迭代（TXPokerAssist） |
|------|----------------------|------------------------------|-------------------------------|
| 驱动 | 用户需求 + 脑暴 | 审查结果 + 模型发现 | 用户审美 + 可用性反馈 |
| 节奏 | 自动化不停 | 先修 Critical → High → Medium → Low | 先交互 → 再视觉 |
| 验证 | 每轮 push + curl | 先测试通过 → 再审查汇总验证 | 测试 + 手动验收 |
| 产出 | 新功能上线 | 修复确认 + ROADMAP 遗留项 | 新 UI 上线 |
| 版本 | Iter N | vX.Y | vX.Y+1 |

### 标准流程

1. **优先级排序** — 按 CRITICAL → HIGH → MEDIUM → LOW 逐级修复
2. **聚焦式修复** — 每个修复专注一个文件的一个 bug（避免大改）
3. **测试验证** — 每次修复后运行完整测试套件
4. **审查回读** — 修复完所有 CRITICAL+HIGH 后，再跑 `--summary-only` 确认发现数下降
5. **部署** — 统一 git commit + push（tag 版本号如 v4.0）
6. **遗留规划** — 写入 `ROADMAP_vX.Y.md` 作为下一迭代计划

### 修复批注规则

- 每个修复在代码中添加 `⚠️ vX.Y 修复：` 注释（便于审查确认修复）
- 修复描述用 `git commit -m "vX.Y: 20+ fixes from adversarial review"` 汇总而非逐个 commit
- 测试必须**全部通过**才能 git push

### 页面版本号同步（硬性要求 — 每次修改必做）

> **来源：** 用户 2026-06-15 明确要求「每一次修改必须要将页面上面的版本号更新为正确的迭代版本。每一个版本我都会做页面记录，所以必须要在页面上面显示正确的迭代版本」

**核心规则：** 每次代码修改并部署时，必须同时将页面显示的版本号更新为当前迭代的实际版本号，版本号与 git commit message 保持一致。

**需要同步的位置（WC26/WC26Nami 项目）：**

```python
# web/index.html 中共4处
<title>26年世界杯预测vX.Y - JTCao出品</title>
<span class="nav-title">26年世界杯预测vX.Y</span>
<span class="nav-badge" style="color:var(--accent)">vX.Y</span>
<p class="loading-text">26年世界杯预测vX.Y · JTCao出品</p>

# api/index.py — /api/version 端点
"version": "vX.Y"
```

**验证方法：** `grep "v6\."` (或对应版本模式) 检查所有出现位置。应该只有 5 处（4个HTML + 1个API），且全部一致。

**Pitfall：** 使用 `patch` 工具时注意转义问题。HTML 中直接使用 `vX.Y` 字符串匹配即可。patch 后立即 grep 验证。

### 版本号规则（高优先级 — 硬性要求）

> **来源：** 用户 2026-06-01 明确要求「每一个迭代都需要有版本序号，迭代说明，push github。硬性要求」

**核心规则：**
1. **每一个迭代必须有版本标识** — 不得有「无版本号的改动」。每次 git push 必须附有版本号（Iter N 或 vX.Y）
2. **版本序号 + 迭代说明 + git push 三者缺一不可** — 仅本地修改不推送到 GitHub 不算完成一次迭代
3. **版本说明必须反映改动实质** — ITERATION_LOG.md 中的改动明细、git commit message 中的简概、版本说明三者一致
4. **迭代定义**：一次 git push = 一次迭代。多个小改动可以在同一个 push 中（一次迭代），但绝不能把一个大改差分拆成 N 次无命名的 push

| 必需元素 | 说明 | 示例 |
|---------|------|------|
| 版本序号 | Iter N 或 vX.Y | Iter 107 / v4.3 |
| 迭代说明 | 1-2 行描述本轮核心改动 | 前端视觉精修：动画、微交互、质感 |
| git push | 推送到 GitHub main | git push origin main |
| 验证 | 测试通过 + 部署确认 | 27/27 passed |

**Pitfall —「小改动不配版本号」的陷阱：**
错误做法：改了 3 行 CSS 觉得不值得单独迭代，攒着跟下个大 feature 一起推
正确做法：每次 git push 都必须有版本号。3 行 CSS = v4.4.1 或 Iter 108。不攒活
- 版本号在 `SKILL.md` 头部、`ROADMAP_vX.Y.md` 文件命名、`git commit message` 中保持一致

### 触发条件

用户明确要求制定长期计划。典型表达：
- "做一个50个迭代的计划书"
- "做一个长期路线图"
- "规划未来N个迭代"
- "给我一个大的规划"

### 标准流程

1. **评估当前状态** — 核查已完成迭代列表，了解项目当前在哪个阶段
2. **确定维度** — 从用户表述中提取迭代方向（如视觉/UI/知识库/Prompt/地图/社交等）
3. **分阶段编排** — 按4个自然阶段组织：
   - Phase 1 基础：确保项目可运行、核心功能闭环
   - Phase 2 体验：视觉打磨、交互优化、易用性
   - Phase 3 智能：LLM 深度集成、知识扩展、个性化
   - Phase 4 生态：社交、商业化、多平台
4. **标注已完成的迭代** — 让用户一目了然当前进度
5. **标注人工介入项** — 需要用户提供凭据/密钥的环节单独列出

### 输出格式

保存为 `docs/VISION_<N>_ITERATIONS.md`，包含：

```
# [项目名] N 次迭代路线图

> 6 大方向: X · Y · Z
> 4 个阶段: 基础 → 体验 → 智能 → 生态

## 📈 迭代阶段总览
[ASCII 路线图]

## Phase 1：基础搭建 (Iter 1-N) ✅ 已完成
[表格：迭代号 | 名称 | 状态 | 说明]

## Phase 2：体验打磨 (Iter N-M)
[表格，按子方向分组（视觉美观 / UI排版 / 地图设计）]

## Phase 3：智能升级 (Iter M-K)
[表格，按子方向分组（LLM Prompt / 知识库 / 主动提问）]

## Phase 4：生态构建 (Iter K-N)
[表格，按子方向分组（社交/运营 / 商业化）]

## ⏸️ 等待人工介入项
[表格：项 | 关联迭代 | 原因]

## 📊 统计
[总计 / 已完成 / 待完成 / 需人工]
```

### 迭代编号规则（高优先级）

> **来源：** 用户 2026-05-30 对 VisePanda 迭代规划的纠正——「迭代的排名要延续之前迭代的序号，不是从新开始一套新排名」

**核心规则：**

1. **序号连续性** — 新计划的迭代必须从现有序列的下一个数字开始，不得重新开始编号（如「Iter 1、Iter 2」或自创新序列）
2. **编号依据 — 先查 git log，再查 ITERATION_LOG.md** — 以 `git log --oneline --grep="Iter"` 的**最新一条 commit 中的 Iter 号**为准。ITERATION_LOG.md 可能不完整（历史迭代被遗漏/未记录），而 git commit message 强制要求包含 `Iter N:` 前缀，是更可靠的数据源。`ITERATION_LOG.md` 仅作为补充参考，不替代 git log
3. **VISION doc 编号 ≠ 实际编号** — `docs/VISION_N_ITERATIONS.md` 中的迭代号是规划编号，不是执行编号。实际执行中迭代号从 git log 的最新编号继续，与 VISION doc 中的规划号无关。不要在 git log 显示 Iter 106 时跳到 VISION doc 的 Iter 15
4. **已有规划不冲突** — 如果存在 `docs/ITERATION_PLAN.md` 或 `docs/VISION_N_ITERATIONS.md` 中的后续规划，新迭代的编号从这些规划之后继续
5. **不得替换编号** — 不得将新迭代插入已有的编号区间。已预留的迭代号（如 VISION doc 中的 Phase 2 Iter 15-22）仍在原位置，新迭代从所有已规划迭代之后开始

**⚠️ Pitfall — VISION doc 编号陷阱：**
| 错误做法 | 正确做法 |
|---------|---------|
| 打开 VISION_80_ITERATIONS.md 看到 Phase 2 从 Iter 15 开始就以为下一步是 Iter 15 | 先 `git log --oneline --grep="Iter" \| head -3` 看实际最新迭代号，再从该号+1继续 |
| Iteration_Log.md 只记录到 Iter 13 就觉得只做到了 Iter 13 | git log 可能显示 Iter 106，说明 Iter 14-105 的记录被遗漏了。ITERATION_LOG.md 不是完整记录 |

创建 VISION 文档后，继续执行 Automation Loop：
- 从当前下一个未完成的迭代号开始执行
- 每完成一次迭代，回到 VISION.md 更新状态
- 用户说"继续"时查阅 VISION.md 确定下一迭代

### 迭代计划排序规则（高优先级）

> **来源：** 用户 2026-05-30 对 VisePanda 美观+速度迭代计划的排序方式确认

当制定多轮迭代计划时，使用以下排序标准排列优先级：

1. **价值/复杂度比** — 高影响、低复杂度排前面
2. **依赖顺序** — 基础设施改动（框架/速度）先于表面改动（视觉/排版）
3. **用户感知** — 用户能立刻感知的变化优先于后台优化

**计划呈现格式：**
```
| Iter | 模块 | 内容 | 复杂度 |
|:----:|------|------|:------:|
| N | 🚀 改动名 | 一句话描述 | ⭐/⭐⭐/⭐⭐⭐ |
```

复杂度定义：
- ⭐ — 单文件CSS/JS修改，无风险
- ⭐⭐ — 多文件/涉及逻辑，需要验证
- ⭐⭐⭐ — 架构变动/新组件，需谨慎测试

### 迭代规划

### 路线图分层

| 层级 | 说明 |
|------|------|
| Phase 1 — 基础补全 | 让项目能跑，数据不丢，注册/登录可用 |
| Phase 2 — 核心功能 | MVP 闭环功能 |
| Phase 3 — 增强 | 锦上添花 |

### 迭代节奏

- 每次迭代聚焦一个模块（不混搭）
- 先修复阻断性问题（数据库、配置、部署）
- 再开发新功能
- 最后做体验优化

## 文件记录

每次迭代涉及的文件变更记录在项目内：
```
docs/ITERATIONS.md    ← 技术迭代日志（修改了什么、为什么）
docs/ROADMAP.md       ← 路线图
docs/ITERATION_LOG.md ← 日期/状态/改动明细/测试结果
```

## 参考文件

- `references/vise-panda-iteration-example.md` — VisePanda 项目迭代实操记录
- `references/showcase-display-multiplier-pattern.md` — 展示金额放大模式：API响应层×N倍放大bankroll/stake/profit，不改数学逻辑。适用于WC26(×10)/WC26Nami(×170)等演示展示需求
- `references/vise-panda-v3-iteration-example.md` — VisePanda v3.0 多方向并行迭代实操案例（知识库/Prompt/UI/地图）
- `references/80-iteration-vision-example.md` — VisePanda 80轮迭代VISION规划实操案例（含12个脑暴方向+签证）
- `references/deployment-verification-checklist.md` — Push 前部署验证清单 + 典型案例（Column导入故障/数据文件语法错误）
- `references/10-iteration-batch-template.md` — 自动化迭代N轮时的规划和执行模板（含计划、执行、暂停三阶段完整流程）
- `references/vise-panda-feature-iteration-pattern.md` — VisePanda 单文件 FastAPI 功能迭代七步流水线（数据→验证→路由→页面→导航→知识→部署），含 CSS 风格指南、API 设计模式、**知识库一致性验证步骤**、导航栏集成规则、已示例迭代统计
- `references/brainstorming-to-iteration-pipeline.md` — 脑暴规划→PLAN.md+ADR→分批实现流水线（三视角发散→grill压力测试→正式规划→分批落地）
- `scripts/verify-knowledge-consistency.py` — 知识库一致性验证脚本（检查 food/hotel/tips 的键名是否与 CITIES 数据库匹配）
- `references/txpokerassist-architecture-and-gotchas.md` — TXPokerAssist 项目的架构、已知坑、探针起点、E2E TestClient 模板（迭代 #2 验证 7/7 通过）
- `references/nuwa-image-generation.md` — NUWA API 图片生成（gpt-image-2 + Gemini 模型）
- `references/feature-add-remove-pattern.md` — 功能添加/移除的4层同步模式（HTML/JS/CSS/API），适用于 Tab 式单页应用
- `references/self-contained-markdown-renderer.md` — 自建轻量Markdown渲染器（零依赖），用于LLM Chat输出的bold/list/code格式化，含SSE流式增量渲染模式
- `references/llm-content-persistence-pattern.md` — LLM生成内容持久化模式：自动检测→保存→视图→加载→分享，纯前端localStorage方案
