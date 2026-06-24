---
name: travel-planner
description: >
  交互式奢华自驾游行程规划器。生成可部署到 Vercel 的纯静态 HTML 页面，
  包含多路线、城市/景点/酒店/餐厅数据、高德地图、每日行程、实时预算。
  触发词：行程规划 / 旅游攻略 / 自驾游 / 旅行计划 / itinerary / travel planner。
version: 1.1.0
---

# 交互式行程规划器

生成任意地区的奢华自驾行程规划器（纯静态 HTML + 本地图片 + Vercel 部署）。

**参考案例：**
- `references/russia-session.md` — 俄罗斯双都+金环（26景点/14酒店/11餐厅/8套行程）
- `references/italy-50-iterations.md` — 意大利50轮迭代案例
- `references/region-planner-advanced-workflow.md` — 数据驱动+迭代追踪的高级工作流
- `references/region-planner-prompt.md` — 可复用的 AI Agent Prompt 模板
- `references/region-planner-design-spec.md` — 暗色奢华风设计规范

## 产物

1. `index.html` — 主页面（纯静态，无构建）
2. `assets/images/` — 所有图片本地化（WebP，200-500KB/张）
3. GitHub → Vercel 自动部署

## 数据模型

全部在 `index.html` 的 JS 常量区：

### 城市 (`const C`)
```js
const C = {
  rome: {
    name: "罗马", lat: 41.9028, lng: 12.4964,
    tag: "历史古都", timeline: "第1-2天",
    hotels: [{ name: "...", stars: 5, price: "¥3500", type: "宫殿酒店",
               desc: "...", url: "https://..." }],
  },
};
```

### 景点 (`const A`)
```js
const A = {
  rome_colosseum: {
    name: "罗马斗兽场", city: "rome", tag: "地标",
    desc: "...", img: "assets/images/poi_rome_colosseum.webp"
  },
  // ID 规则: <cityKey>_<poiKey>
};
```

### 餐厅 (`const R`)
```js
const R = {
  rome_lapergola: {
    name: "...", city: "rome", cuisine: "意式", price: "¥800",
    stars: "3星米其林", desc: "...",
    img: "assets/images/food_rome_lapergola.webp"
  },
};
```

### 自驾路段 (`const DRIVES`)
```js
const DRIVES = {
  "rome-florence": {
    fromCity: "rome", toCity: "florence",
    dist: "275km", time: "3h", road: "A1高速",
    toll: "€18", fuel: "€35"
  },
};
// 若非全程自驾，可使用 alt 字段标注替代交通：
// alt:"推荐高铁: 4小时, ¥450-800/人, 莫斯科→圣彼得堡萨普桑号"
```

### 路线 (`const ROUTES`)
```js
const ROUTES = {
  north: {
    name: "北意深度", color: "#...",
    cities: ["milan", "venice", ...],
    dailyByDays: {
      9: [{ day: 1, city: "milan", activities: [...] }, ...],
    }
  },
};
```

## 图片体系

| 类型 | 命名 | 格式 |
|------|------|------|
| 城市图 | `city_<cityKey>.jpg` | JPG |
| 景点图 | `poi_<attractionId>.webp` | WebP |
| 酒店图 | `hotel_<slug(name)>.webp` | WebP |
| 餐厅图 | `food_<slug(name)>.webp` | WebP |

`slug()` = 去符号、转小写、空格转 `-`、截断

## 工作流程

1. **确认路线** — 与用户对齐地区、城市、天数、是否自驾
2. **收集中文数据** — 城市/景点/酒店/餐厅/路段（写实描述，3-4句每项）
3. **生成 index.html** — 填入全部数据，地图高德优先
4. **JS 语法检查** — `node -e "new Function(html.match(/<script>([\s\S]*?)<\/script>/)[1])"`
5. **启动本地预览** — `python3 -m http.server 8888`（用 `terminal(background=true)`）
6. **迭代修正** — 切换路线/天数/偏好验证渲染正常
7. **生成图片** — 用 AI 图片生成每张图 → WebP 压缩
8. **部署** — 推 GitHub → Vercel 自动部署 → 绑定域名

## 多视角迭代框架

用户要求"50次迭代，从PM/顾客/商家/技术多个角度"时，按以下结构组织：

| 阶段 | 视角 | 典型轮数 | 关注点 |
|------|------|----------|--------|
| Phase 1 | 🔧 PM/产品基线 | 10 | Bug修复、MVP验证、数据骨架、核心功能 |
| Phase 2 | 🧑‍💼 CX/客户体验 | 15-20 | 内容丰富度、交互优化、信息密度、视觉打磨 |
| Phase 3 | 🏪 商家/商业 | 5-10 | 收益模型、增值服务、转化追踪、复购、合作伙伴 |
| Phase 4 | ⚙️ 技术/工程 | 10-15 | 性能、SEO、无障碍、安全、PWA、i18n、CI/CD、文档 |

每轮迭代在 `CHANGELOG.md` 记录：迭代编号 + 方向 + 具体成果 + 版本号。完成后另生成独立的 `迭代汇报材料_vX.X.md`（含四视角分析矩阵、版本演进图、交付清单）。

### 批量 HTML 代码注入（Python）

当需要一次性注入大量迭代变更到 HTML 时，使用 `execute_code` + Python string manipulation：

```python
with open("index.html", "r") as f:
    html = f.read()

# 精确字符串替换注入
html = html.replace("OLD_STRING", "OLD_STRING + NEW_CODE")

with open("index.html", "w") as f:
    f.write(html)
```

关键原则：
- 每次替换后立即验证目标字符串存在（`print(f"✓" if "new_marker" in html else "✗")`）
- 替换目标必须是唯一字符串（避免误匹配）
- 修改后用 `terminal` 运行 Node.js 语法检查 + 数据完整性检查
- 括号/大括号/方括号计数验证平衡性

### 产物交付清单

每次大版本迭代完成后交付：
1. `index.html` — 主程序（单文件）
2. `CHANGELOG.md` — 全部迭代详细日志（每轮含方向+成果+版本）
3. `迭代汇报材料_vX.X.md` — 正式汇报文档（概述+历程+四视角矩阵+决策+清单）
4. 配套文件按需：`manifest.json` / `sw.js` / `build.sh` / `.github/workflows/deploy.yml`

## Advanced Mode: Data-Driven JSON Architecture

For production-grade, multi-region planners with structured iteration tracking, use the **data-driven workflow** described in `references/region-planner-advanced-workflow.md`.

Key differences from the inline approach:
- **Data files** (data/*.json) loaded on demand — not embedded in index.html
- **Scripted iteration** via `iter.js` (start → modify → validate → images → test → deploy → done)
- **Structural validation** via `validate-data.js`
- **Commercial skeleton** — buildOtaLink, localStorage analytics, partner tab
- **Design consistency** — pre-defined dark luxury theme spec

When to use which:
| Scenario | Approach |
|----------|----------|
| Quick one-off itinerary | Inline (this skill's default) |
| Multi-region / production / reusable | Data-driven (see reference) |

## AMap (高德地图) JS API 集成

详见 `references/amap-js-api-integration.md`。

完整集成模式（VisePanda 项目已验证）：
- **Dual-engine**: AMap when API key configured, Leaflet fallback otherwise
- **Security code**: AMap JS API v2.x requires `_AMapSecurityConfig.securityJsCode` BEFORE loading script
- **Environment config**: `/api/config` endpoint exposes key/security code/version
- **Coordinate endpoint**: `/api/map` serves all city coordinates
- **Dark style**: AMap `mapStyle: 'amap://styles/darkblue'` for dark theme

This pattern is reusable for any web app needing accurate China map data — not just travel planners.

## 常见陷阱

### JS 语法错误（内联 HTML 生成时）
当通过字符串拼接生成大量 HTML 内嵌代码时，容易出现残留语法碎片（如 `h.innerHTML+=;`）。
**必须在步骤 4 用 node 做语法检查**，纯 curl 200 不代表 JS 可运行。

### `loading="lazy"` 注入 JS 数据字符串导致语法错误
当用全局字符串替换给图片 URL 添加 `loading="lazy"` 时，如果图片 URL 存储在 JavaScript 对象字面量中（如 `img:"https://...?w=800"`），替换后会变成 `img:"https://...?w=800" loading="lazy"`——`loading="lazy"` 在字符串外被当作 JS 赋值语句，导致 `Unexpected identifier` 语法错误。
**修复**：仅在 HTML `<img>` 标签上添加 `loading="lazy"`，JS 数据中的 URL 字符串只改 URL 参数（如 `&auto=format&q=80`），不改属性。

### hermes_tools read_file 去重陷阱
同一文件在同一会话中第二次调用 `read_file()` 时，返回 `{"content_returned": false, "dedup": true}`，不返回内容。
**绕过**：用 Python `open().read()` 或 `terminal("cat file")` 读取文件。

### Python 环境
本项目用 Hermes Agent venv（uv-managed CPython 3.11）。安装 HTTP server 等直接用系统 `python3` 即可，
但安装 pip 包需用 `/home/ubuntu/.hermes/hermes-agent/venv/bin/pip3 install <pkg>`。

### 地图高德优先
Leaflet 加载使用 CDN 多源回退（unpkg → cdnjs），高德瓦片作为默认底图以适配国内网络。

## 质量检查

参考 `references/CHECKLIST.md`
- 页面无 JS 报错
- 地图可加载/缩放
- 每个景点/酒店/餐厅有不同本地图片
- 懒加载正常、首屏快
- `DRIVES` 覆盖相邻路段，无「暂无数据」
- 切换路线/天数后详情页渲染正常
