# 纳米数据 tlive 实时文字直播实现参考

> 最后更新: 2026-06-15 | 项目: WC26Nami | 版本: v6.1.1

## 一、tlive 数据格式

纳米数据 `/football/match/live` 端点返回的每个比赛对象中包含 `tlive` 数组，是**已完成的中文文字解说**。

### 字段结构

```json
{
  "time": "5'",
  "type": 2,
  "data": "5分钟，图森女足获得本场第1个角球"
}
```

### 事件类型映射

| type | 图标 | 描述 | UI 样式类 |
|:----:|:----:|------|----------|
| 0 | 📋 | 赛前信息（天气、场地、欢迎语） | `live-tl-dot--info` |
| 1 | ⚽ | 进球 | `live-tl-dot--goal` |
| 2 | 🚩 | 角球 | `live-tl-dot--event` |
| 3 | 🟨 | 黄牌 | `live-tl-dot--card` |
| 4 | 🟥 | 红牌 | `live-tl-dot--card` |
| 8 | ⚪ | 点球 | `live-tl-dot--event` |
| 9 | 🔄 | 换人 | `live-tl-dot--event` |
| 10 | 🏁 | 开赛 | `live-tl-dot--info` |
| 11 | 🔚 | 半场/全场结束 | `live-tl-dot--info` |
| 12 | ⏸️ | 半场分界 | `live-tl-dot--info` |
| 15 | | 两黄变红 | `live-tl-dot--card` |
| 16 | | 罚丢点球 | `live-tl-dot--event` |
| 17 | | 乌龙球 | `live-tl-dot--goal` |

### 分类规则
- **赛前信息（preItems）**: type=0 或 type=10 — 渲染在时间线顶部，无时间标记
- **比赛事件（eventItems）**: type≥1 — 按时间顺序排列，有时间标记
- type=11/12 用特殊样式标记半场分界

## 二、后端端点: live-broadcast

**数据源**: 聚合两个 Nami API 端点
- `/football/match/live` → 实时比赛（含 tlive 解说）
- `/football/match/schedule/diary` → 已完赛比赛（补入列表）

**扫描范围**: 前2天 → 后2天（5天范围）

**输出结构 (v6.1.1)**:
```json
{
  "code": 0,
  "count": 10,
  "upcoming_count": 4,
  "matches": [
    {
      "id": 4553133,
      "home_team": "图森女足",
      "away_team": "...",
      "competition": "美女超",
      "home_score": 1,
      "away_score": 0,
      "status_id": 4,
      "minute": "68",
      "match_time": 1752345678,
      "timeline": [
        {"time": "5'", "type": 2, "text": "5分钟，图森女足获得本场第1个角球"},
        {"time": "12'", "type": 1, "text": "12分钟，...进球！"}
      ],
      "stats_summary": {},
      "lineup": {},
      "report_source": "native"
    }
  ],
  "upcoming": [
    {
      "id": 4480051,
      "home_team": "法国",
      "away_team": "德国",
      "competition": "世界杯",
      "home_score": 0,
      "away_score": 0,
      "status_id": 1,
      "minute": "",
      "match_time": 1752400000,
      "timeline": [],
      "report_source": "upcoming",
      "stats_summary": {},
      "lineup": {}
    }
  ]
}
```

**新增 `upcoming` 数组**: 从 `schedule/diary` 中提取未开赛（status_id≠4/8）的世界杯比赛（competition_id=1），按 match_time 排序。仅取今日或未来的比赛（>= now-2h）。

**排序**: matches 中 status_id=4 (进行中) 置顶 → status_id=8 (完赛) 置底

## 三、前端实现模式（v6.1.1 抽屉式UI）

### 文件变更清单

| 文件 | 改动 |
|------|------|
| `web/index.html` | Tab 按钮改名 `📋 赛事详情` + 新的 HTML 结构（live-section + live-card-list + live-detail-drawer） |
| `web/app.js` | 全部 Live 函数重写：renderLive / renderCard / toggleDrawer / findMatchById / renderDrawerContent / _startLiveRefresh |
| `web/app.css` | 新抽屉式样式：live-card / live-card-header / live-drawer / live-dr-stats / live-dr-entry 等 |
| `api/nami_proxy.py` | 新增 upcoming 数组提取逻辑 |

### IIFE onclick 陷阱

JS 在 IIFE 闭包内，直接 `function fn()` 不可被 onclick 访问。**必须**: `window.toggleDrawer = function(uid){...}`

### 抽屉式 UI 渲染流程

```
renderLive()
  ├─ 从 /api/nami/live-broadcast 获取数据
  ├─ window._liveData = data  ← 全局存储，供 drawer 查找
  ├─ upcoming 数组 → 渲染 📅 今日赛程 区域
  │   └─ 每个比赛调用 renderCard(m, 'upcoming')
  │       └─ 显示 等待开赛 badge + 两队名 + 开赛时间
  └─ matches 数组（仅世界杯比赛） → 渲染 🏆 世界杯战况 区域
      └─ 排序：正在进行的置顶 → 已完赛按时间倒序
          └─ renderCard(m, 'result')
              └─ 显示 badge（🔴 进行中 / ✅ 完赛）+ 两队名 + 比分

点击卡片 → toggleDrawer('mc_' + matchId)
  ├─ 如果有已打开的抽屉 → 关闭它（clear innerHTML）
  ├─ 查找匹配数据: findMatchById(parseInt(matchId))
  │   └─ 从 window._liveData 的 matches[] 或 upcoming[] 中查找
  ├─ 如果 report_source === 'upcoming':
  │   └─ 显示 ⏳ 比赛尚未开始 + 比赛时间
  └─ 否则 → renderDrawerContent(drawer, match)
      ├─ 标题区: 队伍名 + 比分 + 状态badge + 赛事名
      ├─ 赛事实录（timeline）
      │   └─ 分隔 preItems (type=0/10) 和 eventItems (type≥1)
      │       └─ 每事件: 圆点 + 时间 + 文本（进球绿色/黄牌橙色/半场蓝色）
      ├─ 数据面板（stats_summary）
      │   └─ 解析"控球率:62% 射门:14 射正:5"格式
      │       └─ parseStats(str) → split(/\s+/) → split(':') → dict
      │       └─ 渲染 grid: 主队数据 | 标签 | 客队数据
      └─ 阵容（lineup）
          └─ 阵型 + 主客两队首发 xi 列表

_startLiveRefresh() → 30s interval（仅当无打开的抽屉时刷新）
```

### 关键 JS 模式

```javascript
// 1. 全局数据存储
window._liveData = data;  // 在 renderLive() 中设置

// 2. Drawer toggle（一次只开一个）
let openDrawerId = null;
window.toggleDrawer = function(uid) {
  // Close previous
  if (openDrawerId && openDrawerId !== uid) {
    const oldDrawer = $('#drawer_' + openDrawerId);
    if (oldDrawer) {
      oldDrawer.classList.remove('live-drawer--open');
      oldDrawer.innerHTML = '';
    }
    $('#arrow_' + openDrawerId)?.classList.remove('live-card-arrow--open');
  }
  // Toggle current
  const drawer = $('#drawer_' + uid);
  const arrow = $('#arrow_' + uid);
  if (openDrawerId === uid) {
    drawer.classList.remove('live-drawer--open');
    drawer.innerHTML = '';
    arrow.classList.remove('live-card-arrow--open');
    openDrawerId = null;
    return;
  }
  openDrawerId = uid;
  arrow.classList.add('live-card-arrow--open');
  // 渲染内容...
  drawer.classList.add('live-drawer--open');
};

// 3. 查找比赛（需要 window._liveData）
function findMatchById(id) {
  const data = window._liveData;
  if (!data) return null;
  for (const m of (data.matches || [])) { if (m.id === id) return m; }
  for (const m of (data.upcoming || [])) { if (m.id === id) return m; }
  return null;
}

// 4. Stats 解析（从 "控球率:62% 射门:14 ..." 格式）
function parseStats(str) {
  const obj = {};
  const parts = str.split(/\s+/);
  for (const p of parts) {
    const kv = p.split(':');
    if (kv.length === 2) obj[kv[0]] = kv[1];
  }
  return obj;
}
```

### CSS 抽屉模式

```css
.live-drawer {
  border-top: 1px solid var(--border);
  padding: 0 12px;
  max-height: 0; overflow: hidden;
  transition: max-height 0.25s ease, padding 0.25s ease;
}
.live-drawer--open { max-height: 600px; padding: 12px; overflow-y: auto; }
```

## 四、后端数据提取逻辑

### 从 schedule/diary 提取 upcoming 比赛

```python
# 在 live-broadcast handler 中，处理完 matches 后：
upcoming = []
now_ts = int(datetime.now().timestamp())
for m in all_sched_matches:
    mid = m["id"]
    sid = m.get("status_id", 0)
    cid = m.get("competition_id")
    is_wc = cid == 1 or str(cid) == "1"
    if not is_wc or mid in seen_ids:
        continue
    if sid == 4 or sid == 8:
        continue  # 已在 matches 中
    mt = m.get("match_time", 0)
    if mt > 10000000000:
        mt = int(mt / 1000)
    if mt < now_ts - 7200:
        continue  # 不算两小时前的比赛
    upcoming.append({
        "id": mid,
        "home_team": all_teams.get(hid, str(hid)),
        "away_team": all_teams.get(aid, str(aid)),
        ...
        "report_source": "upcoming",
    })
upcoming.sort(key=lambda m: m["match_time"])
```

### Stats Summary 格式

`team_stats/detail` 端点的数据被格式化为球队名字典：

```python
stats_summary = {}
if "home" in ts_data:
    stats_summary[ts_data["home"]["team_name"]] = "控球率:{}% 射门:{} 射正:{} 角球:{} 犯规:{} 黄牌:{} 红牌:{}".format(...)
if "away" in ts_data:
    stats_summary[ts_data["away"]["team_name"]] = "..."
```

前端解析时用 `parseStats()` 按空格分割，冒号分隔 key/value。

## 五、部署验证

```bash
# 后端
curl -s --max-time 20 "https://wc26nami.jtcao.space/api/nami/live-broadcast"
# → {"code": 0, "count": N, "upcoming_count": M, "matches": [...], "upcoming": [...]}

# 前端语法
node --check web/app.js

# 浏览器验证
browser_navigate → 检查页面加载、JS 错误
browser_snapshot → 确认 Tab 按钮为 📋 赛事详情
```

## 六、中继代理（Relay）架构

**问题：** Vercel Serverless 无固定 IP，被 Nami API IP 白名单拒绝
**方案：** 在 Hermes agent 服务器 (64.176.82.81, Vultr 新加坡，已加纳米白名单) 运行中继代理

### 中继文件

`~/projects/WC26Nami/nami_relay.py` — 约80行，Python stdlib http.server

### 端点映射

| 请求路径 | Nami 目标 |
|----------|-----------|
| `/api/v5/xxx?params` | `open.sportnanoapi.com/api/v5/xxx?params+auth` |

### Vercel 接入

在 Vercel 项目设置环境变量：`NAMI_RELAY=http://64.176.82.81:8080`

nami_proxy.py 的 live-broadcast handler 检测到该变量后：
```python
relay = os.environ.get("NAMI_RELAY", "")
if relay:
    base_raw = relay.rstrip("/")  # → http://64.176.82.81:8080
    auth_str = ""                 # 中继自带认证，Vercel 不含 Key
```

### systemd 自启

```bash
sudo systemctl enable nami-relay   # 开机启动
sudo systemctl status nami-relay   # 检查状态
```

监听 `0.0.0.0:8080`，CORS 全开，30s 内存缓存。

### ⚠️ Vultr 云防火墙端口拦截

中继服务器是 **Vultr 新加坡** (64.176.82.81, The Constant Company / AS20473)。Vultr 的云防火墙**只开放了 SSH (22) + 少数 Docker 暴露端口 (8000/5055/8502)**，8080 端口对外被拦截。

**解决（三选一）：**

**方案 A（推荐）**：在 Vultr 控制台 [my.vultr.com](https://my.vultr.com) → Firewall → 添加规则：
- 协议: TCP
- 端口: 8080
- 来源: 0.0.0.0/0

**方案 B**：用 bore 隧道 `bore local 8080 --to bore.pub`（无需注册，但必须服务器可出站访问 bore.pub）。注意 curl 走本地代理时需 `--noproxy '*'` 绕过。

**方案 C**：查 Vercel 出站 IP → 直接加纳米白名单（动态 IP，可能换）

### 🔌 连通性探测与快速回退（v6.1.3+）

nami_proxy.py 的 `live-broadcast` handler 中，使用 relay 前先做 socket 级别探测：

```python
# 仅当 relay 可达时才使用中继地址
import socket
_parsed = urllib.parse.urlparse(relay_url)
_host = _parsed.hostname or "localhost"
_port = _parsed.port or 80
_relay_ok = False
try:
    _s = socket.create_connection((_host, _port), timeout=2)
    _s.close()
    _relay_ok = True
except Exception:
    _relay_ok = False
if _relay_ok:
    base_raw = relay_url.rstrip("/") + "/api/v5"
    auth_str = ""
else:
    # 直接返回空数据（避免回退到纳米直连也超时）
    return {"code": 0, "matches": [], "upcoming": [], ...}
```

**核心原理：** TCP 层的端口丢弃（SYN 无响应）和 HTTP 错误响应（401/403）有本质区别。前者要等 TCP 重试超时（10-30s），后者瞬间返回。不能用 HTTP timeout 解决网络层阻断——必须在 HTTP 请求之前用 socket 探测。

**为什么不回退到纳米直连？** Vercel 的 IP 段未被纳米数据白名单，从 Vercel 直接请求纳米 API 也会在网络层被丢弃，导致同样的 TCP 超时问题。回退直连只会把 12s 的失败变成 8s 的失败，不值得。

### 🔍 Vercel 出站 IP 查询

创建了 `/api/nami/myip` 端点，从 Vercel 内部调用 ipify.org 返回其出站 IP：

```python
_resp = urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5)
_ip = json.loads(_resp.read()).get("ip", "unknown")
# 备用: https://httpbin.org/ip
```

**使用方法：** `curl https://wc26nami.jtcao.space/api/nami/myip`

**当前值（2026-06-15）：** `44.220.193.15`（AWS us-east-1，Vercel 函数出站节点）

### 🧪 诊断步骤

```bash
# 1. 从服务器本地测试 relay 进程存活
curl http://127.0.0.1:8080/health          # → 应在 1ms 内返回

# 2. 从外网测试 relay（注意 ⚠️ 绕过本地代理）
curl --noproxy '*' http://64.176.82.81:8080/health --connect-timeout 5

# 3. 从 Vercel 测试端点耗时
#   - 12s+  = relay 阻断（socket 探测定时 2s + 冗余超时）
#   - 5-7s  = Vercel 冷启动 + fallback timeout
#   - <3s   = relay 正常工作

# 4. 看响应体判断 relay 状态
curl -s https://wc26nami.jtcao.space/api/nami/live-broadcast | jq .relay_status
#   - "unreachable" → 端口未开放
#   - "ok" → 中继正常工作
#   - null → 中继未配置（NAMI_RELAY 未设）

# 5. 查 Vercel 当前出站 IP
curl -s https://wc26nami.jtcao.space/api/nami/myip | jq .
```

### ⚠️ 重要陷阱：`http_proxy` 环境变量干扰连通性测试

这台服务器设置了 `http_proxy=http://127.0.0.1:10809`（Xray 代理），**curl 默认走代理**。外网端口测试（如 `curl http://64.176.82.81:8000/`）会经过本地代理，代理返回 503，**误判为端口正常**。

**必须使用 `--noproxy '*'` 跳过代理做端口测试。**

```bash
# ❌ 错误：走代理，端口阻断被误判为 503
curl http://64.176.82.81:8080/health

# ✅ 正确：直连测试
curl --noproxy '*' http://64.176.82.81:8080/health
```

## 七、v6.1.0 已上线：文字战报引擎（Match Report Synthesis）

### 问题

已完赛比赛（status_id=8）从 `schedule/diary` 捞取时，**没有 tlive 字段**，且 `score` 字段为 null。只有 `live` 端点返回的近期完赛比赛才有 tlive。

### 方案：get_match_report()

在 `data/nami_client.py` 中新增 `NamiClient.get_match_report(match_id)` 方法，合并三个 Nami 接口合成结构化战报。

### 实现代码

```python
def get_match_report(self, match_id):
    # 1. trend/detail → 事件时间线
    trend = self._request("football/match/trend/detail", params={"id": mid})
    incidents = trend.get("results", {}).get("incidents", [])
    
    timeline = []
    for e in incidents:
        typ, minute, pos = e.get("type"), e.get("time"), e.get("position")
        timeline.append({"time": str(minute), "type": typ, "text": label, "position": pos})
    
    # 2. team_stats → 数据面板
    stats = self._request("football/match/team_stats/detail", params={"id": mid})
    
    # 3. lineup → 球员名单+阵型
    lineup = self._request("football/match/lineup/detail", params={"id": mid})
    # lineup 的 "home"/"away" 含 players[{id, team_id, first, name: "中文名", ...}]
    
    return {"code": 0, "timeline": timeline, "stats": ..., "lineup": ...}
```

### 数据源

| 端点 | 数据内容 | API 限速 |
|------|----------|----------| 
| `/football/match/trend/detail?id=X` | 事件时间线：进球(type=1), 角球(2), 黄牌(3), 红牌(4), 换人(9) | 120次/min |
| `/football/match/analysis?id=X` | 比赛分析：历史交锋、近期战绩、goal_distribution | 60次/min |
| `/football/match/team_stats/detail?id=X` | 球队统计：控球率、射门、角球、黄牌数等 45+ 字段 | 120次/min |
| `/football/match/lineup/detail?id=X` | 阵容：阵型(home_formation, away_formation) + 球员名单(name/中国名) | 120次/min |
| `/football/match/player_stats/detail?id=X` | 球员统计：52个球员每人40+字段（但不含姓名） | 120次/min |

### 事件类型映射（trend/detail incidents）

| type | 图标 | 含义 |
|:----:|:----:|------|
| 1 | ⚽ | 进球 |
| 2 | 🚩 | 角球/定位球 |
| 3 | 🟨 | 黄牌 |
| 4 | 🔴 | 红牌 |
| 5 | 🔄 | 换人 |
| 9 | 💥 | 危险进攻 |
| position=1 | | 主队事件 |
| position=2 | | 客队事件 |

### 比分推导

`schedule/diary` 的 `score` 字段为 null，从 `trend/detail` 的 type=1 事件中推导：

```python
home_goals = sum(1 for t in timeline if t.get("type") == 1 and t.get("position") == 1)
away_goals = sum(1 for t in timeline if t.get("type") == 1 and t.get("position") == 2)
```

### 输出格式示例（本地测试已通过）

```
瑞典 vs 突尼斯
  M7   ⚽ 进球 (主队)
  M30  ⚽ 进球 (主队)
  M33  🚩 角球/定位球 (主队)
  M54  🟨 黄牌 (客队)
  M60  ⚽ 进球 (主队)
  📊 控球49% · 13射7正 · 4角球 · 10犯规 · 0黄0红
  📊 控球51% · 6射2正 · 2角球 · 8犯规 · 1黄0红
  阵型: 3-4-1-2 vs 4-2-3-1
  首发: '克里斯托弗·努德费尔特', '古斯塔夫·拉格比耶尔克', ...
```

### 限制

- trend/detail 和 team_stats 只返回前30天的数据
- 事件数据不含球员姓名（type=1只有时间和位置，无球员ID或名称）
- 如需从 lineup 交叉匹配球员名，需要额外解析事件数据格式（纳米未提供）
- 合成战报的 `data`/`text` 字段为空（需从 type+position 推断中文描述）

## 八、v6.1.1：赛事详情 Tab 重构 — 抽屉式 UI

### 变更摘要

| 维度 | v6.0.3/v6.1.0 | v6.1.1 |
|------|---------------|--------|
| Tab 名称 | 🔴 直播 | 📋 赛事详情 |
| 布局 | 两页切换（列表→时间线详情） | 单页抽屉式（卡片+展开） |
| 未开赛比赛 | 不显示 | 📅 今日赛程 区域（抽屉→"比赛尚未开始"） |
| 已开赛比赛 | 主客居中+比分大号 | 紧凑卡片+抽屉展开解说 |
| 详情展示 | 全屏时间线页面+返回按钮 | 卡片内嵌抽屉+数据面板+阵容 |
| 数据访问 | 每次渲染调用 API | window._liveData 全局缓存 |
| 自动刷新 | 列表页刷新（无详情页刷新） | 无抽屉打开时刷新 |
| 同时打开详情 | 只能看一个（页面切换） | 一次只开一个抽屉（点其他自动关） |
