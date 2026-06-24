# FIFA API v3 自动同步指南

> 基于 2026-06-16 实操记录。取代旧的 web_extract FIFA.com 方法。

## 数据源总览

| 数据源 | 类型 | 可用性 | 用途 |
|--------|------|--------|------|
| FIFA API v3 | REST API | ✅ 从 Vultr SG 直连（需headers） | 赛果（主数据源） |
| worldcup26.ir | REST API | ✅ 无认证 | 球队名/国旗/代码 |
| Nami v5 | REST API | ⏳ 到 2026-06-22 | 赔率/阵容/统计（仅补充） |

## FIFA API v3 集成

### 端点

```
GET https://api.fifa.com/api/v3/calendar/matches?idSeason=285023&count=104&language=en
```

**Season ID:** `285023`（FIFA World Cup 2026™）

### 认证方式

无需 API Key。**但必须设置以下 HTTP headers**（缺 `Origin` + `Referer` 会 SSL 握手超时）：

```python
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.fifa.com",
    "Referer": "https://www.fifa.com/",
}
```

### 数据解析

```python
def extract_name(obj):
    """从 {ShortClubName:[{Description:...}]} 提取队名"""
    if isinstance(obj, dict):
        lst = obj.get("ShortClubName", [])
        if lst and isinstance(lst, list) and isinstance(lst[0], dict):
            return lst[0].get("Description", "?")
    return "?"

def parse_completed(data):
    results = data.get("Results", [])
    for m in results:
        if m.get("MatchStatus") != 0:
            continue  # 只处理已赛 (status=0)
        yield {
            "home_team": extract_name(m.get("Home", {})),
            "away_team": extract_name(m.get("Away", {})),
            "home_score": m.get("HomeTeamScore", 0),
            "away_score": m.get("AwayTeamScore", 0),
            "group": m.get("GroupName", [{}])[0].get("Description", "") if m.get("GroupName") else "",
            "stage": m.get("StageName", [{}])[0].get("Description", "") if m.get("StageName") else "",
            "matchday": m.get("MatchDay", 1),
            "date": m.get("Date", ""),
        }
```

### 配对匹配

使用**无序集合匹配**避免 home/away 方向歧义：

```python
for m in local_matches:
    ta, tb = m["team_a"], m["team_b"]
    for fc in fifa_completed:
        if {ta, tb} == {fc["home_team"], fc["away_team"]}:
            # 确定分数方向
            if ta == fc["home_team"]:
                new_r = {"team_a_goals": fc["home_score"], "team_b_goals": fc["away_score"]}
            else:
                new_r = {"team_a_goals": fc["away_score"], "team_b_goals": fc["home_score"]}
            m["result"] = new_r
            m["result_source"] = "fifa_official"
```

### 自动同步框架

**脚本链：**

```
fifa_sync.py  →  fifa_sync_wrapper.sh  →  cron (每2h)
     ↓                  ↓
  FIFA API          git commit + push
  拉取+解析              ↓
     ↓             Vercel auto-deploy
  更新 JSON
```

- `data/fifa_sync.py` — Python 同步引擎
- `data/fifa_sync_wrapper.sh` — Bash 包装器（检测变化→commit→push）
- Cron: `0 */2 * * *`

### 已知坑点

1. **headers 必须有** — 缺 `Origin`/`Referer` 导致 SSL 握手超时（CDN 限制）
2. **`ShortClubName` 是列表** — `m["Home"]["ShortClubName"][0]["Description"]`，字段名随语言变化
3. **配对用无序集合** — `{ta, tb}` 不用 `(ta, tb)`，避免 home/away 方向问题
4. **`MatchStatus=0` 标识已赛** — 别把 `None`/`null` 当 0 处理
5. **同一个赛场次可能出现在多个 GroupName** — 淘汰赛没有 group，`GroupName` 为空列表

### 间歇性故障排查流程

**现象：** `SSLEOFError: [SSL: UNEXPECTED_EOF_WHILE_READING]` 但 `curl -sI https://api.fifa.com/api/v3/` 返回 200 OK。

按以下顺序排查：

1. **Proxy 环境变量干扰（最常见）** — 腾讯云服务器默认设 `http_proxy=http://127.0.0.1:10809`。
   - 诊断：`echo "http_proxy=$http_proxy https_proxy=$https_proxy"`
   - 修复：运行前 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY`
   - 验证：`python3 -c "import urllib.request; print(urllib.request.urlopen(urllib.request.Request('https://api.fifa.com/api/v3/calendar/matches?idSeason=285023&count=104', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Origin': 'https://www.fifa.com', 'Referer': 'https://www.fifa.com/'}), timeout=15).status)"`
   - 当前状态：`fifa_sync_wrapper.sh` 尚未添加 unset，`fifa_sync.py` 也未处理。

2. **CDN 间歇性断连（第二个最常见）** — FIFA API CDN 的 SSL 保活策略偶发断开。
   - 诊断：unset proxy 后仍然失败 → CDN 问题
   - 修复：**重试即可**（通常 1 次重试就成功，本 session 首次失败、第二次成功）
   - 建议：wrapper 脚本中捕获非零退出码后 `sleep 5 && retry`
   - `ssl._create_unverified_context()` 不解决问题且不安全，不要用

3. **Headers 缺失（修复 proxy 后仍出现）** — 确认已设 `Origin` + `Referer`。

## worldcup26.ir 免费数据源

### 端点

```
GET https://worldcup26.ir/get/teams    → 48支球队（含国旗URL）
GET https://worldcup26.ir/get/groups    → 12组积分榜（⚠️ 数据为模拟，非真实）
GET https://worldcup26.ir/get/games     → 所有比赛赛程（⚠️ 模拟数据，非真实）
GET https://worldcup26.ir/get/game/{id} → 单场比赛详情
```

### 返回字段（重要差异）

worldcup26.ir 的字段名与常见命名不同：

| 含义 | 字段名 |
|------|--------|
| 英文队名 | `name_en`（⚠️ 不是 `name`） |
| 波斯语队名 | `name_fa` |
| FIFA 3字母代码 | `fifa_code`（⚠️ 不是 `code`） |
| 国旗URL | `flag`（flagcdn.com） |
| ISO国家代码 | `iso2` |
| 所属小组 | `groups`（⚠️ 字符串，如 `"A"`） |
| 数字ID | `id`（字符串） |

### 使用场景

- **球队名/国旗/代码：** ✅ 完美可用，48队全量
- **实时赛果：** ❌ 不可用（数据为赛前模拟）
- **积分榜：** ❌ 不可用（全部为0）

## 三层数据源架构

```
┌─────────────────────────────────────────┐
│              🥇 FIFA API v3              │ ← 权威赛果来源
│     api.fifa.com/api/v3/calendar/...     │
└──────────────────┬──────────────────────┘
                   │ fallback
┌──────────────────▼──────────────────────┐
│              🥈 worldcup26.ir            │ ← 球队/国旗/代码
│          worldcup26.ir/get/teams         │
└──────────────────┬──────────────────────┘
                   │ fallback
┌──────────────────▼──────────────────────┐
│         🥉 Nami API (到期6/22)            │ ← 赔率/阵容/统计
│    open.sportnanoapi.com/api/v5/...      │
└─────────────────────────────────────────┘
```
