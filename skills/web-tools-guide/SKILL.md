---
name: web-tools-guide
description: "MANDATORY before calling web_search, web_fetch, browser, or opencli. Contains required error-handling procedures (web_search failure → must guide user to configure API), fallback chain (opencli CLI covers 70+ sites as structured fallback before browser), and site-specific login URLs. Without reading this skill, you WILL handle failures incorrectly and miss available tools. Trigger on: 搜索/上网/查资料/打开网站/抓取网页/新闻/热点/web search/fetch/browser/opencli."
---

<!-- baseDir = /root/.openclaw/workspace/skills/web-tools-guide -->

# Web 工具策略

遵循 ReAct 范式。**四个工具不是层级关系，是分支决策**：

```
┌─ 没有 URL，需要搜索 ──────→ web_search   （关键词搜索）
│
├─ 已知 URL，静态内容 ──────→ web_fetch    （直取页面）
│
├─ 以上失败 / 不适用 ──────→ opencli      （CLI 结构化访问，70+ 站点）
│
└─ 全都不行 ───────────────→ browser      （浏览器自动化，兜底）
```

先按场景选 web_search 或 web_fetch；失败时先试 opencli，最后才上 browser。
每次切换工具告知用户原因，不要静默降级。

---

## 决策流程

```
有明确 URL？
├─ YES → 静态内容（文章/文档/API/RSS）？
│        ├─ YES → web_fetch
│        │        失败（空白/403/CAPTCHA）？→ opencli → browser
│        └─ NO（需要 JS/登录/交互/截图）→ opencli → browser
└─ NO  → web_search
         ├─ 成功 → 对结果 URL 按上述逻辑选 fetch/opencli/browser
         ├─ 失败（API 错误）→ 引导配置（见"web_search 失败处理"）
         └─ 无结果/不适用 → opencli → browser
```

---

## web_search

**何时用**：没有明确 URL，需要搜索信息（新闻、热点、查资料、比较信息）。

**怎么用**：直接调用 `web_search`，传入搜索关键词。

**结果处理**：返回的 URL 按决策流程选 `web_fetch`、`opencli` 或 `browser` 深入获取。

**失败时**：见下方"web_search 失败处理"。

---

## web_fetch

**何时用**：已知 URL，页面为静态内容——新闻文章、博客、技术文档、API 端点、RSS 源。

**怎么用**：直接调用 `web_fetch`，传入 URL。

**失败信号**：返回空白页、403、CAPTCHA、骨架 HTML → 尝试 `opencli`，仍不行再升级到 `browser`。

---

## opencli（Fallback，优先于 browser）

**何时用**：web_search / web_fetch 失败或不适用时，先试 opencli 再考虑 browser。覆盖 70+ 主流网站，秒级返回结构化数据。

**首次使用前**：如果执行 `opencli` 提示 command not found，需要先运行安装脚本（幂等，可重复运行）：
```bash
bash {baseDir}/scripts/setup-opencli.sh
```
该脚本会自动完成：安装 opencli CLI → 编译 Browser Bridge 插件 → 重启浏览器加载插件。

**渐进式发现（不需要记命令）**：
```bash
opencli --help                    # 有没有这个站？
opencli <site> --help             # 这个站能做什么？
opencli <site> <command> --help   # 这个命令怎么用？
```

**详细用法**：`read {baseDir}/references/opencli-guide.md`

**失败时**：告知用户 opencli 失败原因，降级到 browser。

---

### Browser console as raw-data fallback

When terminal tools (`curl`, `web_fetch`) fail due to network timeouts or return
cached/rendered content instead of raw data, the browser console can fetch and
extract structured data directly:

```text
# Navigate to any URL that returns JSON (or renders a page with structured data)
browser_navigate(url='https://example.com/api/data.json')

# Use browser_console to fetch + extract in one call
browser_console(expression="
  fetch('https://example.com/api/data.json')
    .then(r => r.json())
    .then(d => {
      // Extract just the fields you need
      let out = [];
      d.items.forEach(i => {
        out.push(i.rank + '|' + i.name + '|' + i.author);
      });
      return out.join('\\n');
    })
")
```

**To pipe data into a local file (JSON/text):**
1. Inject the raw response into a DOM element
2. Read it back via `browser_console`
3. Write to disk with `write_file`

```text
browser_console(expression="
  fetch('https://example.com/api/data.json')
    .then(r => r.text())
    .then(t => {
      let p = document.createElement('pre');
      p.id = 'temp_data';
      p.textContent = t;
      document.body.appendChild(p);
    })
")
# Then read back:
browser_console(expression="document.getElementById('temp_data').textContent")
# Then write_file:
write_file(path='/tmp/data.json', content='<paste output here>')
```

**When to use this instead of `curl`:**
- `curl` exits with code 28 (timeout) or 124 (soft timeout)
- `web_fetch` returns cached/stale markdown rather than live JSON
- You need raw structured data (JSON, CSV) that `web_extract` would summarize
- The target host is slow but the browser can eventually connect

This is **not** the first choice — try `curl` / `web_fetch` first. Reserve this
for when those tools demonstrably fail.

## browser（最后手段）

这是最重量级的工具，也是当前问题最多的场景。以下是详细操作指引。

### 何时用

- **JS 渲染页面**：SPA、动态加载内容（微博 feed、知乎回答、小红书瀑布流）
- **需要登录态**：登录后才可见的内容、管理后台
- **页面交互**：点击按钮、填写表单、翻页、滚动加载更多
- **截图需求**：需要页面视觉信息
- **其他工具全部失败的兜底**

### 操作流程

**信息获取（只读）：**
1. 导航到目标 URL
2. 等待关键元素出现（不要用固定时间等待）
3. 提取所需内容（文本、链接、图片等）
4. 返回结果给用户

**登录操作：**
1. 查找登录页 URL → `read {baseDir}/references/well-known-sites.json`
2. **告知用户即将执行登录操作，获取确认**
3. 导航到登录页
4. 填写凭证（用户提供）或提示用户扫码
5. 等待登录成功，确认后继续后续操作

**页面交互：**
1. 导航到目标页面
2. 使用 CSS 选择器定位元素（辅以文本内容匹配）
3. 执行交互：点击、输入、选择、滚动
4. 等待响应/页面变化
5. 提取结果或截图

### 关键注意事项

- **登录操作必须获得用户授权** — 任何涉及账号登录的操作前，先告知用户并等待确认
- **敏感操作必须二次确认** — 发帖、删除、支付等不可逆操作
- **优先 CSS 选择器** — 比 XPath 更稳定，辅以文本匹配
- **智能等待** — 等待目标元素出现，而非 `sleep(3)` 式固定等待
- **CAPTCHA/验证码** — 无法自动处理时告知用户需手动介入
- **页面加载超时** — 设置合理超时，失败时告知用户并建议重试
- **多步操作保持状态** — 登录后的后续操作复用同一浏览器上下文，不要重新打开

---

## web_search 失败处理

**当 `web_search` 返回错误时，不要静默降级，必须引导配置：**

1. **`read {baseDir}/references/web-search-config.md`**
2. 按文件中 Step 1 **原样输出**配置引导给用户（不要改写表格或省略内容）
3. 等待用户回复：
   - 用户提供 API Key → 再次 `read {baseDir}/references/web-search-config.md`，按 Step 2-5 执行
   - 用户说"暂不配置" → 进入降级方案
   - 其他回复 → 正常响应
4. **降级方案**（仅在用户明确拒绝配置后）：
   - `read {baseDir}/references/well-known-sites.json` 获取常用网站 URL
   - 用 `web_fetch` 直接获取目标网站内容
   - 仍不行 → 升级到 `browser`

---

## 常用网站

需要常用网站 URL 时（登录页、搜索引擎、热搜榜等）：

```
read {baseDir}/references/well-known-sites.json
```

通过 key 查找（如 `social.weibo.login`、`search.baidu`）。带 `{query}` 的 URL 替换为实际搜索词。

---

## Multi-Engine Search Reference

> Absorbed from `multi-search-engine` (archived). Use when web_search's primary backend is unavailable or you need a Chinese-domestic search engine.

### Available Search Engines

**Domestic (7):** Baidu, Bing CN, Bing INT, 360, Sogou, WeChat, Shenma
**International (9):** Google, Google HK, DuckDuckGo, Yahoo, Startpage, Brave, Ecosia, Qwant, WolframAlpha

### Language Selection
- Chinese query → Domestic engines first
- Non-Chinese query → International engines

### Advanced Operators
| Operator | Example | Description |
|----------|---------|-------------|
| `site:` | `site:github.com python` | Search within site |
| `filetype:` | `filetype:pdf report` | Specific file type |
| `""` | `"machine learning"` | Exact match |
| `-` | `python -snake` | Exclude term |
| `OR` | `cat OR dog` | Either term |

### Time Filters
`tbs=qdr:h` (hour) / `:d` (day) / `:w` (week) / `:m` (month) / `:y` (year)

### Chinese Search Engine Blocking
- Baidu → CAPTCHA for all curl requests
- Bing CN/Bing INT → JS-rendered, curl gets boilerplate only
- 360/Sogou/WeChat → same JS-rendering issue

### Working Chinese News Fallbacks
```bash
# Sina Finance API (lid=2509=finance, 2515=tech)
curl "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1"

# Toutiao Hot Board
curl "https://www.toutiao.com/hot-event/host-board/?origin=toutiao_pc"

# ThePaper.cn headlines
python3 -c "import re; t=__import__('urllib.request').request.urlopen('https://www.thepaper.cn').read().decode(); print('\\n'.join(re.findall(r'<h[23][^>]*>(.*?)</h[23]>', t)))"
```

### Cookie Management
- Cookies stored in-memory only during the search session
- Acquired on-demand when search requests get 403/429
- Cleared after session completes
- No cookies read from or written to config files

### Full details → `references/multi-search-engine-guide.md`
