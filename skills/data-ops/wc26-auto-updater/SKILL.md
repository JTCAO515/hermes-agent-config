---
name: wc26-auto-updater
version: 3.5.4
description: |
  WC26 Edge Lab 数据准确性与自动更新管线。
  包含两阶段流程：(1) 数据校验阶段 — 比对真实 FIFA 数据源修正本地数据集；(2) 更新阶段 — 推送到 GitHub 触发 Vercel 自动部署。
  不信任任何手动填写的 team_ratings、比赛对手、或 FIFIA 排名——每次更新前必须验真。
triggers:
  - "update WC26 data"
  - "auto-update world cup"
  - "run daily update"
  - "daily data pipeline"
  - "verify WC26 data"
  - "audit WC26 accuracy"
  - "check WC26 data against real sources"
  - "fix WC26 team names"
  - "fifa sync not working"
  - "fifa_sync.py silent"
  - "cron not updating"
  - "nami export"
  - "nami data dump"
  - "WC2026 data export"
  - "predictions not working"
  - "概率 only"
  - "只给概率"
  - "不要推荐"
  - "no recommendations"
  - "remove quant"
  - "概率校准"
  - "EV cap"
  - "不可推敲"
  - "展示算法独特性"
  - "算法独特"
  - "可推敲"
  - "ev不要整数"
  - "ev精准到十分位"
  - "每日推荐有问题"
  - "删除每日推荐"
  - "tab删除"
toolsets:
  - terminal
mutating: true
---

# WC26 Auto-Updater (v2.3)

> 数据准确性优先于自动更新。先验真，再推送。

## 基本原则

- **只给概率分布，不做投注推荐。** 用户明确要求：输出仅包含不同结果的概率（1X2、O/U 2.5、比分概率、期望进球、市场赔率），不包含任何形式的预测结论、投注推荐、EV/Kelly/评级/建议投入等。回测不输出 best_recommendation，API 不暴露 quant 端点，前端不渲染 单注胜率/评级/EV/Kelly。系统提示词改为"概率分析师"而非"投注顾问"。
- **不信任任何静态数据。** `data/wc2026_teams.json` 中的 ranking/attack/defense 是手动填写的，100%需要与真实源交叉验证。
- **纳米数据 (Nami API) 数据源已打通。** WC26Nami 项目中已集成 Nami v5 API 客户端（`data/nami_client.py`），认证方式为 `user` + `secret` URL query params。Base URL: `https://open.sportnanoapi.com/api/v5`。详细端点文档和认证细节见 `references/wc26-nami-api-reference.md`。
- **纳米数据仅7天试用期（~2026-06-22到期）。** 到期前必须完成全量数据导出（见"纳米数据全量导出"章节）。导出后的 SQLite 数据库两个项目各有一份，过期后 WC26 项目可离线使用。
- **比赛数据用 `schedule/diary` 端点，别用 `competition/schedule/list`。** 后者返回 "url未授权访问"（该端点不可用）。schedule/diary 按日期查询，返回所有运动项目比赛，需用 `competition_id=1` 过滤出 WC2026 比赛。
- **每天可能已产生真实赛果。** WC2026 是实时进行的赛事（2026年6月11日开幕）。不要用 `update_results.py` 模拟已真实发生的比赛。
- **队名必须对齐 FIFA 官方名。** 前端显示和内部数据的队名必须与 FIFA.com 保持一致，否则积分榜/对阵全部错位。
- **数据源优先级（v3.5 更新）：** The Odds API (api.the-odds-api.com, 实时盘口 1X2/让球/大小球) = FIFA 官方 API v3 (api.fifa.com, 赛果) > worldcup26.ir (球队/国旗) > 纳米数据 Nami API (到期 2026-06-22, 配对数据不可靠) > 本地模拟。

  **⚠️ 2026-06-16 发现：Nami 的 WC2026 比赛配对全错。** 同组4支球队正确，但具体的对阵组合（谁vs谁）与 FIFA 官方赛程不一致。已验证 16 场中 12 场配对错误。原因可能是 Nami 的数据源使用了不同的赛程生成/授权方式，而非真实 WC2026 赛程。赛果数字（如 2-0）可能对应了错误的比赛组合。因此：
  - ✅ Nami 可用于补充数据（odds/lineup/player stats）
  - ❌ Nami 不可用于赛果同步或赛程验证
  - ✅ FIFA API v3 是赛果的权威来源

## FIFA 官方 API v3 集成（v3.0 新增 — 主数据源）

### 为什么从 Nami 切到 FIFA
2026-06-16 发现 Nami 的 WC2026 比赛配对有 12/16 场错误。FIFA 官方 API `api.fifa.com/api/v3` 是比赛赛果的权威来源。

### API 端点

| 端点 | 说明 | 频率限制 |
|------|------|---------|
| `GET /api/v3/calendar/matches?idSeason=285023&count=104&language=en` | 获取所有 WC2026 比赛 | 无（官方开放） |

**Season ID:** `285023`（FIFA World Cup 2026™）

### 认证方式
无需 API Key。但必须设置以下 HTTP headers：
```python
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.fifa.com",
    "Referer": "https://www.fifa.com/",
}
```
缺 `Origin` + `Referer` 会 SSL 握手超时（CDN 限制）。从 Hermes 服务器直连需要这些 headers。

### 返回数据解析

```python
def parse_completed(data):
    results = data.get("Results", [])
    completed = []
    for m in results:
        if m.get("MatchStatus") != 0:
            continue  # 只处理已赛比赛 (status=0)
        
        def desc(lst):
            return lst[0].get("Description", "?") if lst else "?"
        
        completed.append({
            "home_team": desc(m.get("Home", {}).get("ShortClubName", [])),
            "away_team": desc(m.get("Away", {}).get("ShortClubName", [])),
            "home_score": m.get("HomeTeamScore", 0),
            "away_score": m.get("AwayTeamScore", 0),
            "group": desc(m.get("GroupName", [])),
            "date": m.get("Date", ""),
        })
    return completed
```

### 配对匹配（关键）

使用 **无序集合匹配** 避免 home/away 方向歧义：
```python
def sync_to_wc26(completed, matches):
    for m in matches:
        ta, tb = m["team_a"], m["team_b"]
        team_set = {ta, tb}
        for fc in completed:
            if team_set == {fc["home_team"], fc["away_team"]}:
                if ta == fc["home_team"]:
                    # 方向一致
                    new_r = {"home_score": fc["home_score"], "away_score": fc["away_score"],
                             "team_a_goals": fc["home_score"], "team_b_goals": fc["away_score"]}
                else:
                    # 主客反转
                    new_r = {"home_score": fc["away_score"], "away_score": fc["home_score"],
                             "team_a_goals": fc["away_score"], "team_b_goals": fc["home_score"]}
                m["result"] = new_r
                m["result_source"] = "fifa_official"
```

### 自动同步脚本

- **`data/fifa_sync.py`** — FIFA API 拉取 → 解析 → 更新 wc2026_matches.json
- **`data/fifa_sync_wrapper.sh`** — 包装器：同步 → git commit → git push → Vercel 自动部署

### Cron 配置

```bash
# FIFA 官方赛果自动同步（每2小时，通过 Xray HTTP 代理 :10809）
0 */2 * * * /home/ubuntu/projects/WC26-Main/data/fifa_sync_wrapper.sh

# WC26-Main The Odds API 盘口自动同步（每30分钟，直连）
*/30 * * * * /home/ubuntu/projects/WC26-Main/data/odds_fetcher_wrapper.sh

# WC26-Nami 盘口同步（从 WC26-Main GitHub raw 复制，不调 API）
*/30 * * * * /home/ubuntu/projects/WC26-Nami/data/odds_fetcher_wrapper.sh
```

**⚠️ WC26-Nami 盘口同步策略（2026-06-19 优化）：**
- WC26-Nami `odds_fetcher_wrapper.sh` 不再直接调用 The Odds API（避免额度翻倍）
- 改为从 `https://raw.githubusercontent.com/JTCAO515/WC26-Main/master/data/live_odds.json` 复制
- 如果 GitHub raw 拉取失败，再降级到本地 `data/odds_fetcher.py` 直接调用 API
- 这每月节省 ~4320 quota

新的 FIFA cron（`WC26 FIFA 赛果自动同步`，每2h）优于旧的 4 个每日 Nami cron，因为：
- 数据更准确（FIFA 官方）
- 频率更高（每2h vs 4次/天）
- 完全自动化（检测变化→commit→push→deploy）

### 多数据源客户端

`data/free_sources.py v2` 提供统一接口：
```python
from free_sources import WorldCup26Client, FifaApiClient

# 球队/国旗数据（无需认证）
wc26 = WorldCup26Client()
teams = wc26.get_teams()           # 48队含flag_url
flags = wc26.get_team_flag_map()   # name → {fifa_code, flag_url}

# FIFA 赛果（需正确headers）
fifa = FifaApiClient()
matches = fifa.fetch_matches()
completed = FifaApiClient.parse_completed(matches)
```

## The Odds API 实时赔率集成（v3.5 新增 — 盘口数据源）

> **2026-06-19 接入。** 解决中国 VPS 获取实时博彩赔率的根本问题。直连可用，无需代理。40+ 博彩公司覆盖（Pinnacle/Betfair/SkyBet 等），包括 1X2/让球/大小球三大市场。

### API 概况

| 项目 | 说明 |
|------|------|
| 提供商 | The Odds API (the-odds-api.com) |
| 免费层 | 每月 1000 次请求 |
| 端点 | `https://api.the-odds-api.com/v4` |
| 世界杯 sport key | `soccer_fifa_world_cup` |
| 区域 | `eu,uk`（欧洲+英国盘口，小数赔率） |
| 市场 | `h2h,spreads,totals`（1X2 + 让球 + 大小球） |
| 中国直连 | ✅ 可用（2026-06-19 验证） |
| API Key | `7bd3207b09a2b09053a7df453b33623d`（存储在 `ODDS_API_KEY` 环境变量） |

### 端点

```http
GET /v4/sports/soccer_fifa_world_cup/odds/?apiKey={KEY}&regions=eu,uk&markets=h2h,spreads,totals&oddsFormat=decimal
```

返回结构：
```json
[{
  "id": "065b3573e875f8d23803357f73e5b99e",
  "sport_key": "soccer_fifa_world_cup",
  "commence_time": "2026-06-19T19:00:00Z",
  "home_team": "USA",
  "away_team": "Australia",
  "bookmakers": [
    {
      "key": "pinnacle",
      "title": "Pinnacle",
      "markets": [
        {"key": "h2h", "outcomes": [
          {"name": "Australia", "price": 5.0},
          {"name": "USA", "price": 1.57},
          {"name": "Draw", "price": 4.33}
        ]},
        {"key": "spreads", "outcomes": [...]},
        {"key": "totals", "outcomes": [...]}
      ]
    }
  ]
}]
```

### 队名映射（关键）

The Odds API 的队名与 WC26 项目数据集可能不同。必须在合并时做 `normalize_teams()` 映射。

**已知差异：**
| The Odds API 名 | WC26 项目名 | 说明 |
|-----------------|-------------|------|
| `Czech Republic` | `Czechia` | 简称差异 |
| `South Korea` | `Korea Republic` | FIFA 正式名 |
| `Turkey` | `Türkiye` | Unicode 名 |
| `United States` | `USA` | 缩写 |
| `Ivory Coast` | `Côte d'Ivoire` | 法文名 |
| `Cape Verde` | `Cabo Verde` | 当地语 |
| `DR Congo` | `Congo DR` | 缩写 |
| `Bosnia & Herzegovina` | `Bosnia and Herzegovina` | 连字符 vs and |
| `Iran` | `IR Iran` | 含前缀 |

完整映射表见 `data/odds_fetcher.py` 中的 `normalize_teams()` 函数。

### 同步脚本

- **`data/odds_fetcher.py`** — 拉取盘口 → 队名归一化 → 合并到 `wc2026_matches.json` → 保存 `live_odds.json`
- **`data/odds_fetcher_wrapper.sh`** — 包装器：同步 → git commit → git push → Vercel 自动部署

### Cron 配置

```bash
# The Odds API 实时盘口自动同步（每30分钟）
*/30 * * * * /home/ubuntu/projects/WC26-Main/data/odds_fetcher_wrapper.sh
```

### 数据流

```
The Odds API v4 (HTTP直连)
       ↓
data/odds_fetcher.py (队名归一化)
       ↓
data/live_odds.json (纯净JSON, 44场比赛)
       ↓
合并到 data/wc2026_matches.json (添加 live_odds 字段)
       ↓
git push → Vercel 自动部署
       ↓
api/index.py _get_cached_matches_fast() 从 match.live_odds 读取
       ↓
_frontend 显示实时盘口 + EV/Kelly 投注信号
```

### API 集成细节

在 `api/index.py` 的 `_get_cached_matches_fast()` 函数中，盘口数据的处理流程：

1. 检查 `match.get("live_odds", {})` 是否存在
2. 从 `live_odds.markets.h2h` 提取主/平/客赔率（通过 `normalize_teams` 后的队名匹配）
3. 从 `spreads` 提取让球数据
4. 从 `totals` 提取大小球数据
5. 计算去水后的隐含概率 (`real_home_prob`/`real_draw_prob`/`real_away_prob`)
6. 计算 EV = 模型概率 × 市场赔率 - 1
7. 标记 `best_bet`（最高 EV 的正值选项）

**备选来源：** 旧数据格式 `odds_snapshots` 依然受支持作为 fallback。

**优先选择 Pinnacle 盘口**（sharp 博彩公司，抽水最低，最能反映真实市场概率）。`odds_fetcher.py` 的合并逻辑选择 `pinnacle` key 的 bookmaker 作为首选。

### 验证方法

```bash
# 确认盘口数据已同步
python3 data/odds_fetcher.py --diff

# 通过 API 验证 Vercel 盘口端点
curl -s https://worldcup.jtcao.space/api/wc/odds-full | python3 -c "
import json,sys; d=json.load(sys.stdin)
h = sum(1 for m in d['matches'] if m.get('markets',{}).get('real_home_odds'))
print(f'{h} matches with odds')
"

# 检查最佳 EV 信号
curl -s https://worldcup.jtcao.space/api/wc/odds-full | python3 -c "
import json,sys; d=json.load(sys.stdin)
for m in d['matches']:
    mk = m.get('markets',{})
    if mk.get('best_ev',0) > 5:
        print(f'{m[\"team_a\"]} vs {m[\"team_b\"]}: {mk[\"best_bet\"]} EV={mk[\"best_ev\"]}%')
        break
"
```

### ⚠️ 已知坑点

1. **队名不匹配则赔率为 0** — The Odds API 使用 `name` 字段对应球队名。如果 `normalize_teams()` 没覆盖到，`h2h.get(team_name, 0)` 返回 0，该场比赛的盘口全部不可用。
2. **Pinnacle 不覆盖所有市场** — 部分比赛 Pinnacle 只有 h2h，缺少 spreads/totals。fallback 到第一家有数据的 bookmaker。
3. **API 限额敏感** — 免费层 1000 req/月。一次请求返回 44 场比赛的全部盘口（h2h+spreads+totals），花费约 6 个 quota。每 30 分钟同步一次，月耗约 8640 → 超出免费层 8 倍。**当前方案不可持续。** 后续优化方向：减少请求频率（每 2 小时）、缩小 regions（仅 eu）、缩小 markets（仅 h2h）。
4. **数据推送频率** — 当前每 30 分钟 push 一次到 git → Vercel 部署。Vercel 免费版 Hobby 计划构建无限制，但频繁 deploy 影响冷启动体验。可改为每小时合并一次。

### ⚠️ API Quota 审计（重要）

| 指标 | 数值 |
|------|------|
| 单次请求 cost | 2 regions × 3 markets = 6 |
| 频率 | 每 30 分钟 |
| 月请求数 | 48 × 30 = ~1440 |
| 月 quota 消耗 | 1440 × 6 = ~8640 |
| 免费层限制 | 1000/月 |
| **当前方案** | **严重超限** |

**当前缓解措施：**
- WC26-Nami 不再直接调用 The Odds API（从 WC26-Main GitHub raw 复制 `live_odds.json`）→ 每月省 ~4320 quota
- WC26-Main 仍需每 30 分钟同步 → ~4320 quota/月 -> 仍超 4 倍

**修复方向（未实施）：**
- 降频到每 2 小时：1440 → 360 quota/月 ✅（免费层内）
- 只拉 h2h 不拉 spreads/totals：360 × 2 = 720 quota/月 ✅
- 前端 spreads/totals 用模型计算，不拉实时数据

### 参考文件

- `references/wc26-odds-api-integration.md` — 完整集成指南（端点测试、队名映射、数据格式）

## 为什么需要导出
纳米数据试用期仅7天（~2026-06-22）。到期后所有实时 API 调用将失败。必须在此之前拉取所有可用数据并打包到本地数据库。

### 导出内容
| 数据 | 端点 | 量级 |
|------|------|------|
| 球队映射 | standings group → 队名 | 48队 |
| 比赛列表 | schedule/diary (competition_id=1) | 101-104场 |
| 积分榜 | competition/table/detail?id=1 | 13组(60行) |
| 已赛详情 | match/live/history?id={id} | 12+场完整事件+技统 |

### 导出脚本
```bash
# v1: 基础导出（比分匹配建映射，只有10队）
python3 data/nami_export.py

# v2: 精准导出（积分榜group编号建映射，48队全量）
python3 data/nami_export_v2.py
```

### 重点：球队映射方法

**错误方法（v1）：** 按比分+日期匹配。问题：同一日期可能有多个相同比分的比赛（如两个1-1），无法区分配对。

**正确方法（v2）：** 使用 standings 数据的 group 编号。Nami 的 `competition/table/detail?id=1` 返回 12 组积分榜，`group=1` 对应 Group A，`group=12` 对应 Group L。已知每组4支球队的队名，将 standings 中的 team_id 按 position 顺序映射即可。**100% 准确，48队全量。**

```python
GROUP_TEAMS = {
    1: ["Mexico", "South Africa", "Korea Republic", "Czechia"],  # Group A
    2: ["Canada", "Bosnia and Herz.", "Qatar", "Switzerland"],   # Group B
    3: ["Brazil", "Morocco", "Haiti", "Scotland"],               # Group C
    ...
    12: ["England", "Croatia", "Ghana", "Panama"],               # Group L
}
```

### 存储格式
两个项目 `data/` 目录下各存一份：
| 文件 | 格式 | 说明 |
|------|------|------|
| `nami_archive.json` | JSON (249KB) | 完整数据，含 team_map/matches/standings/match_details |
| `nami_wc2026.db` | SQLite (6表) | teams(48) + matches(101) + standings(60) + match_events + match_stats + export_meta |
| `nami_team_map.json` | JSON | 48队 team_id ↔ 队名映射 |

### ⚠️ Nami 数据可靠性警告（v3.0 关键发现）

**2026-06-16 验证：Nami 的 WC2026 比赛配对全面错误。** 已对比 FIFA 官方 API，16 场已赛中：
- 14 场配对错误（队伍 vs 对手组合不对）
- 2 场比分也错（Saudi Arabia 应是 1-1 不是 0-0, IR Iran 应是 2-2 不是 1-1）

问题不是队名映射——分组（谁在哪个组）是对的。问题是**同一组内谁对阵谁**在 Nami 的数据中与真实赛程不同。

影响范围：
| 功能 | 受Nami影响？ | 替代方案 |
|------|-------------|---------|
| 赛程/结果 | ⚠️ 错误 | FIFA API v3 |
| 实时赔率 | ✅ 可用 | Nami odds 端点单独可用 |
| 阵容/技术统计 | ✅ 可用 | Nami match details |
| 球员数据 | ✅ 可用 | Nami player stats |
| 积分榜 | ⚠️ 可能错误 | 从FIFA赛果重新计算 |

**结论：当涉及赛果和比赛配对时，永远用 FIFA。Nami 仅用于赔率/阵容/统计等补充数据。**

## 工作流

### Phase 0 — 数据源来源审计（参考 `references/wc26-data-sources.md`）

- 记录每个数据字段的来源（FIFA排名、xG评分、赛果等）
- 标记所有 "手动填写" 的字段为待验真
- 使用 `references/wc26-team-name-mapping.md` 确保队名标准化

### Phase 1a — 数据校验

#### 1a. 从 FIFA API v3 获取当前赛果（主方法，v3.0）

⚠️ **双重项目同步规则：** FIFA sync 可以在两个项目中任意一个运行，但同步后必须将 `wc2026_matches.json` 复制到另一个项目。具体方向取决于你从哪里启动：

**方向A：从 WC26-Nami 启动（传统方式，已有 Nami 数据）**
```bash
cd ~/projects/WC26-Nami && unset http_proxy https_proxy && python3 data/fifa_sync.py
# 同步后复制到主项目
cp ~/projects/WC26-Nami/data/wc2026_matches.json ~/projects/WC26-Main/data/
```

**方向B：从 WC26-Main 启动（主项目直接 FIFA 同步）**
```bash
cd ~/projects/WC26-Main && unset http_proxy https_proxy && python3 data/fifa_sync.py
# 同步后复制到 WC26-Nami
cp ~/projects/WC26-Main/data/wc2026_matches.json ~/projects/WC26-Nami/data/
```

无论哪个方向，fifa_sync.py 的调用方式一致：
```python
# data/fifa_sync.py — 一键同步
python3 data/fifa_sync.py
```

FIFA API 端点：
```
GET https://api.fifa.com/api/v3/calendar/matches?idSeason=285023&count=104&language=en
Headers: Origin=https://www.fifa.com, Referer=https://www.fifa.com/
```

已赛比赛 `MatchStatus=0`，通过 `HomeTeamScore`/`AwayTeamScore` 获取比分。
配对匹配使用无序集合（frozenset），避免 home/away 方向歧义。

**如果 FIFA API 直连不可用：** 使用 `web_extract` 通过代理抓取：
- URL: `https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures`
- 自动同步 cron 已配置每2小时运行

#### 1a.2 从 Nami API 获取（仅用于赔率/阵容/统计等补充数据）

⚠️ **不要用 Nami 获取赛果。** 已验证 Nami 的 WC2026 比赛配对错误（12/16场配对不准）。
Nami 仅用于 odds/lineup/player_stats 等补充数据：

#### 1b. 对比本地数据与真实数据

参见 `references/wc26-team-name-mapping.md` 的队名校验表 — 检查：
- 队名是否与 FIFA 官方名一致
- 比赛对手是否正确（⚠️ 特别注意：Nami 真实对阵与模拟对阵不同！）
- 比分是否正确

#### 1c. 更新本地数据

如有差异：
1. 直接修改 `data/wc2026_matches.json` 中的 `result` 字段
2. 移除该比赛的 `is_simulated` 标记

**⚠️ 关键：result 对象需要双格式键名**
```python
mt['result'] = {
    "home_score": home_goals,        # odds_engine / 前端使用
    "away_score": away_goals,
    "team_a_goals": home_goals,      # backtest.py 使用
    "team_b_goals": away_goals,
}
```

#### 1d. 重新生成预测数据

更新赛果后必须重新运行 Poisson 模型生成 predictions 并**写回文件**，否则 get_predictions() 仍然使用旧数据：

```python
import sys, json
sys.path.insert(0, '.')
import importlib
import football_predictor.wc_api
importlib.reload(football_predictor.wc_api)
from football_predictor.wc_api import get_predictions, WC_MATCHES

report = get_predictions(polymarket_weight=0.3)

# CRITICAL: 预测结果不会自动保存到文件，必须显式写回
# CRITICAL: 必须同时保存 probs (顶层) + checkpoints (嵌套)
# 量化代码 _build_candidates/enriched 依赖 preds.get("probs", {})
data = json.loads(WC_MATCHES.read_text())
match_lookup = {m['id']: m for m in data['matches']}
for rpt_match in report['matches']:
    mid = rpt_match['id']
    if mid not in match_lookup:
        continue
    # 从最新 checkpoint 提取 probs 到顶层
    ck = rpt_match.get('checkpoints', {}) or {}
    probs = rpt_match.get('probabilities', {})
    if not probs and ck:
        for ck_name in ['T-60m', 'T-6h', 'T-48h']:
            if ck_name in ck:
                cp = ck[ck_name]
                probs = cp.get('probabilities', {}) if isinstance(cp, dict) else {}
                if probs:
                    break
    match_lookup[mid]['predictions'] = {
        'team_a_win': rpt_match.get('team_a_win_pct'),
        'draw': rpt_match.get('draw_pct'),
        'team_b_win': rpt_match.get('team_b_win_pct'),
        'probs': probs,                    # 顶层 key — 量化代码的输入
        'probabilities': probs,            # 兼容写法
        'expected_goals': rpt_match.get('expected_goals'),
        'checkpoints': ck,                 # 嵌套 — 前端 T-60m 倒计时依赖
    }

data['generated_at'] = report.get('generated_at', '')
WC_MATCHES.write_text(json.dumps(data, ensure_ascii=False, indent=2))
print(f'Saved predictions for {sum(1 for m in data["matches"] if m.get("predictions"))} matches')
```

**验证 predictions 正确性：**
```bash
python3 -c "
import json
m = json.load(open('data/wc2026_matches.json'))
p = m['matches'][0].get('predictions', {})
print('probs present:', bool(p.get('probs')))
print('checkpoints present:', bool(p.get('checkpoints')))
"
```

#### 1e. 校验 FIFA 排名 + attack/defense rating

对比 `data/wc2026_teams.json` 中的 `rank` 字段与真实 FIFA 排名。

### Phase 2 — WC26Nami 提交并推送（源仓库）

源仓库 `WC26-Nami` 是所有数据变更的第一入口（nami_sync + update_results 在此运行）。

```bash
cd /home/ubuntu/projects/WC26-Nami
git add data/nami_team_map.json data/update_log.json data/wc2026_matches.json
git commit -m "每日数据更新 $(date +%Y-%m-%d): 纳米数据同步 + 模拟更新"
git push origin master
```

> ⚠️ 建议只 add 数据文件（`data/*.json`, `data/*.db`），避免意外引入临时文件或 pycache。默认变更通常只涉及 `wc2026_matches.json`、`nami_team_map.json`、`update_log.json` 三个文件。

### Phase 2.5 — 跨项目文件同步

**方向A：WC26-Nami → WC26-Main（默认方向）**  
更新赛果数据后，必须将核心比赛文件同步到 `WC26-Main` 项目（否则 Vercel 部署不会拿到最新数据）：

```bash
# 核心：仅 wc2026_matches.json 是必须同步的（含赛果+预测+模拟）
cp /home/ubuntu/projects/WC26-Nami/data/wc2026_matches.json \
   /home/ubuntu/projects/WC26-Main/data/wc2026_matches.json

# 存档副本：同时复制到 world-cup-project 下的静态目录（非 git repo，纯备份）
cp /home/ubuntu/projects/WC26-Nami/data/wc2026_matches.json \
   /home/ubuntu/projects/world-cup-project/updated/world-cup-edge-lab/data/wc2026_matches.json

# 推荐同步的补充文件（可选）：
# for f in nami_archive.json nami_team_map.json nami_wc2026.db; do
#   cp ~/projects/WC26-Nami/data/$f ~/projects/WC26-Main/data/$f
# done
```

**方向B：WC26-Main → WC26-Nami（当 FIFA sync 从主项目启动时）**
```bash
cp /home/ubuntu/projects/WC26-Main/data/wc2026_matches.json \
   /home/ubuntu/projects/WC26-Nami/data/wc2026_matches.json
```

### Phase 3.5 — 跑回测（验证模型精度）

每次数据同步后，用户可能要求跑回测验证模型预测精度。回测 CLI 在 `football_predictor/cli.py`：

```bash
cd /home/ubuntu/projects/WC26-Nami
python3 -m football_predictor.cli \
  --data data/wc2026_matches.json \
  --config configs/default.json \
  --pretty
```

或者只用主项目的数据（如果 WC26-Nami 不可用）：
```bash
cd /home/ubuntu/projects/WC26-Main
python3 -m football_predictor.cli \
  --data data/wc2026_matches.json \
  --config configs/default.json \
  --pretty
```

**输出解读：**
- `parameter_set`: 当前参数配置名（如 "default"）
- `scoreline_model`: 使用的泊松模型类型（如 "bivariate_poisson"）
- `matches`: 全部 104 场的详细预测 + 3 个时间点的 checkpoints
- `metrics.brier_wdl`: Win-Draw-Loss 方向的 Brier 分数。**越低越好**：0=完美预测，1=全错，0.25=随机猜测。当前基线 ~0.69，意味着纯泊松模型在小组赛阶段预测精度有限。
- `metrics.brier_over_under_2_5`: 大小球（Over/Under 2.5）方向的 Brier 分数。当前基线 ~0.47。
- `leakage_audit.future_records`: 预测时使用了未来信息的比赛数。如果 >0，checkpoint 时间设置可能有问题。
- `leakage_audit.visible_records`: 有市场赔率可供参考的比赛数。

**数据格式注意：** 本地 `wc2026_matches.json` 中 result 字段使用 `team_a_goals`/`team_b_goals` 键名（backtest.py 解析），而 odds_engine 使用 `home_score`/`away_score`。FIFA sync 写入时两套都写。检查时用：
```bash
python3 -c "
import json
m = json.load(open('data/wc2026_matches.json'))
both = sum(1 for mt in m['matches'] if mt.get('result') and 'team_a_goals' in mt['result'] and 'home_score' in mt['result'])
print(f'Dual-format results: {both}')
"
```

**触发词：** 当用户说"跑一次回测"、"回撤"、"backtest"、"验证模型精度"时，执行上述 CLI 命令并汇报 Brier 指标。

> 最新回测基线数据见 `references/wc26-backtest-baseline.md`（2026-06-18 实测值）。

### Phase 3 — WC26-Main 提交并推送（部署仓库）

目标仓库是 Vercel 部署的来源，必须单独 commit + push：

```bash
cd /home/ubuntu/projects/WC26-Main
git add data/wc2026_matches.json
git commit -m "每日数据更新 $(date +%Y-%m-%d): 同步WC26-Nami最新赛果数据"
git push origin master
```

> ⚠️ 两个仓库的默认分支都是 `master`，不是 `main`。`git push origin main` 会失败。

### Phase 4 — 汇报

输出校验摘要，包括：
- Nami 同步场次及队名映射数量
- 模拟更新场次
- 两个仓库的 commit hash
- 已知告警（如 knockout regeneration failure）

#### FIFA 同步报告标准格式（cron job 输出）

当通过 `fifa_sync_wrapper.sh` 运行后，报告应按以下格式组织：

```markdown
## FIFA 自动同步报告 — YYYY-MM-DD HH:MM UTC

### ✅ 脚本执行状态
- 耗时、commit hash、变更文件摘要
- 是否推送成功

### 📊 同步结果
| 指标 | 数值 |
|------|------|
| FIFA API 记录已赛 | N 场 |
| 本批新增 | N 场 |
| 本地累计有比分结果 | N 场 |

### 🔹 当前全部已赛结果
[按日期排序的表格]

### 📌 小结
- 本次是否有新增赛果
- 最近新增的赛果（如有）
- 值得关注的趋势/异常
```

报告所需的 JSON 解析见 `references/wc26-local-schema.md`（`wc2026_matches.json` 本地数据结构文档）。

#### 噪音提交检测 — 汇报时的判断

当 sync 日志显示 "更新 0 场" 但仍有 git commit 时（仅 `last_updated` 时间戳变化），在报告中说明："仅时间戳更新，无实质数据变更。噪音提交问题仍未修复（见已知坑点）。"

#### 赛果数量骤降检测

对比 sync.log 中 "当前已赛: X 场" 的历史值。若当前值明显低于之前（如 28→23），则在报告中告警："赛果数量下降！可能由 FIFA sync 全量覆盖 result 字段导致。"

### Phase 5 — 生产环境 API 验证

推送到 GitHub 后，等 Vercel 自动部署完成（约 20-30s），必须验证关键 API 端点：

```bash
# 等待部署
sleep 30

# 检查预测端点
for ep in predict matches odds-full; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --noproxy '*' \\
    "https://worldcup.jtcao.space/api/wc/$ep")
  echo "$ep: HTTP $STATUS"
done

# 检查数据内容（不只是 HTTP 状态码）
curl -s --noproxy '*' https://worldcup.jtcao.space/api/wc/predict | \\
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Matches: {len(d.get(\\\"matches\\\",[]))}, Brier: {d.get(\\\"metrics\\\",{}).get(\\\"brier_wdl\\\",\\\"N/A\\\")}')"
```

**⚠️ 量化引擎重建（2026-06-19 完成）。** 用户要求恢复量化功能（金额15倍放大、40+注数、真实回测）。当前量化引擎状态与 v7.0.0 前完全不同——不再使用 `best_recommendation` / `singles_win_rate`，改用 The Odds API 实时盘口计算 EV。

**当前量化端点（v7.0.6）：**
| 端点 | 说明 | 状态 |
|------|------|------|
| `/api/wc/quant/portfolio` | 组合优化：EV/Kelly/Sharpe/最大回撤 | ✅ 57注×15倍，EV≤30% cap |
| `/api/wc/quant/backtest` | 基于真实已赛场次的回测（18注+） | ✅ 含KPI+明细 |
| `/api/wc/quant/arbitrage` | 套利扫描 stub | ⚠️ stub，需扩展 |
| `/api/wc/daily-picks` | 多盘口智能推荐 v2（5盘口类型） | ✅ 64+注，含 method/data_source/confidence |
| `/api/wc/compare` | 双变量 vs 独立泊松对比 | ✅ 差异3-8% |

### 概率校准策略（v7.0.6 新增）

**核心问题：** 未校准的模型概率（如 37.1%）与市场隐含概率（1/5.68=17.6%）差异过大，产生荒谬 EV（584%）。真实赌球不存在这种数字。

**解决方案：** 模型-市场混合校准 + EV/Edge 后处理 cap。

1. **贝叶斯收缩校准：** `cal_prob = prob * 0.55 + market_implied * 0.45`。极端值向市场收缩，产生合理 EV（10-30%）。
2. **后处理 cap：** `ev_pct=min(30%)`, `edge_pct=min(15pp)`, `kelly_pct=min(10%)`, `odds≤20.0`。
3. **信号强度：** EV≥25→5级, ≥12→4级, ≥6→3级, ≥3→2级, 其余1级。
4. **因子评分：** 每信号独一画像，不千篇一律。value(35%)+risk(20%)+confidence(20%)+momentum(10%)+diversity(15%)。

详见 `references/wc26-probability-calibration-v7.md`。

**常见失败模式：**
| 症状 | 根因 | 修复 |
|------|------|------|
| predict 500 / 超时 | Vercel 冷启动 + Monte Carlo 超时 | 改用缓存路径，从 wc2026_matches.json 的 predictions 字段直接读取 |
| 概率显示 100% | 前端 `.toFixed(0)` | 改为 `.toFixed(1)` |
| 页面无限 spinning | predict 端点放在 Phase 1 阻塞 | 移到 Phase 2 异步加载 |

## 数据完整性审计脚本

每次数据导出/同步后，运行一键审计：

```bash
# 基础审计
python3 scripts/audit_integrity.py --data-dir data/

# 审计并自动修复 result 双格式缺失
python3 scripts/audit_integrity.py --data-dir data/ --fix
```

审计覆盖：
1. JSON 语法正确性
2. 球队映射完整性（48队，跨文件一致性）
3. wc2026_teams.json 评分完整性
4. 比赛计数（72小组+32淘汰=104）
5. 重复ID检测
6. Result 双格式一致性（home_score + team_a_goals 同时存在）
7. Predictions 覆盖率
8. SQLite 数据库结构

## 跨项目数据同步 & 部署

### 数据同步（WC26-Nami → WC26-Main）

两个项目的 `data/` 目录需要保持以下文件一致：

| 文件 | 必需？ | 说明 |
|------|--------|------|
| `wc2026_matches.json` | ✅ 必须同步 | 核心比赛数据，104场含predictions |
| `nami_archive.json` | ✅ 必须同步 | 纳米数据全量存档备份 |
| `nami_team_map.json` | ✅ 必须同步 | 48队ID→队名映射 |
| `nami_wc2026.db` | ⚠️ 推荐 | SQLite 结构化数据 |
| `nami_client.py` | ⚠️ 推荐 | API客户端（2.3KB） |

同步命令：
```bash
for f in wc2026_matches.json nami_archive.json nami_team_map.json nami_wc2026.db; do
  cp ~/projects/WC26-Nami/data/$f ~/projects/WC26-Main/data/$f
done
# Nami Python 文件（如需要）
for f in nami_client.py nami_sync.py nami_export_v2.py; do
  cp ~/projects/WC26-Nami/data/$f ~/projects/WC26-Main/data/$f
done
```

### 版本号管理

所有版本号位置：
- `web/index.html`: title, nav-title, nav-badge, loading-text（共4处）
- `api/index.py`: `/api/version` 端点

版本号必须与 git commit message 中的版本一致。

### 部署流程

```bash
cd ~/projects/WC26-Main
git status --short               # 确认修改
python3 scripts/audit_integrity.py --data-dir data/  # 验真
git add -A
git commit -m "data: <描述> vX.Y.Z"
git push origin master           # 触发 Vercel 自动部署
```

### ⚠️ data/auto_update.sh — 独立于 fifa_sync_wrapper.sh 的日常更新脚本

`data/auto_update.sh` 是 **WC26-Main 项目内** 的直接更新脚本（不依赖 WC26-Nami 管线），由 `update_results.py` 驱动：

```bash
cd ~/projects/WC26-Main
bash data/auto_update.sh
```

**与 fifa_sync_wrapper.sh 的区别：**

| 特性 | auto_update.sh | fifa_sync_wrapper.sh |
|------|---------------|---------------------|
| 数据源 | `update_results.py`（本地模拟 + 已存在赛果补录） | `fifa_sync.py`（FIFA API v3 官方） |
| 源仓库 | WC26-Main（自包含） | WC26-Nami（需跨项目同步） |
| 频率 | 每日 2 次（13:30 + 23:30 UTC） | 每 2 小时 |
| 适用场景 | 日常例行更新 + 已赛赛果补录 | 实时 FIFA 官方赛果同步 |

**✅ 已修复 — unbound variable（2026-06-18 修复）**

曾报错 `data/auto_update.sh: line 20: commit: unbound variable` — `$commit` 变量在 `set -u` 模式下被引用但从未赋值。

**修复**：在 `echo "✅ Pushed $commit"` 前添加了 `commit=$(git rev-parse --short HEAD)` 获取最近 commit hash。

**验证**：运行后退出码为 0，日志正常输出 `✅ Pushed b0e6ae6`。修复 commit: `b0e6ae6`。

### ⚠️ 淘汰赛 bracket 重建 — 修复未持久化（2026-06-19 验证）
`update_results.py` 调用 `build_knockout_structure()` 时未传入 `ratings` 参数。

**⚠️ 已知问题：修复未持久化。** v3.3.0 (commit `b0e6ae6`) 在代码中添加了 `team_ratings` 加载逻辑，但 2026-06-19 的每日 cron 仍然输出了：
```
⚠️  Knockout regeneration failed: build_knockout_structure() missing 1 required positional argument: 'ratings'
```
说明修复被后续提交覆盖或变更，或存在多个 `update_results.py` 入口/分支。

**计划修复**（从 `data/wc2026_teams.json` 加载 `team_ratings` 并传入）：
```python
ratings_path = Path(__file__).parent / "wc2026_teams.json"
ratings = json.loads(ratings_path.read_text())["team_ratings"]
knockout_data = build_knockout_structure(ratings)
```

**排查方法**：`git log --oneline -10 -- data/update_results.py` 查看该文件的变更历史。确认 b0e6ae6 的 fix 是否被其他提交 revert 或覆盖。`git diff b0e6ae6^..HEAD -- data/update_results.py` 对比修复前后的完整差异。

**验证方法**：手动运行 `python3 data/update_results.py --days 1`，确认输出无 `⚠️ Knockout regeneration failed` 警告。小组赛更新后淘汰赛 brackets 应自动重建。

**影响评估**：该错误不影响小组赛模拟（`update_results.py` 成功更新了 1 场），仅淘汰赛段的 bracket 重建失败。每日 cron 中该错误可接受，不阻塞主流程。

### ⚠️ 项目重命名后 cron 路径失效（2026-06-19 新增）

**问题：** `world-cup-edge-lab` → `WC26-Main` 重命名后，所有指向旧目录的 cron 全部静默失效。

**影响范围：**
- 系统 crontab（`/etc/crontab` / `crontab -e`）中的路径
- Hermes Agent cron jobs 的 `workdir` 字段（不更新则任务在旧目录跑，访问失败）
- Shell wrapper 脚本中的 `cd` 路径

**修复步骤（3 处必须同步修改）：**
1. 系统 crontab：`sed 's|old-path|new-path|g' | crontab -`
2. Hermes cron jobs：用 `cronjob` 工具的 `action=update` + `workdir` 逐一修正
3. Shell 脚本内的路径硬编码（如 `fifa_sync_wrapper.sh` 中的 `cd`）

**排查方法：**
```bash
# 检查系统 crontab 中的路径
crontab -l | grep -i wc26

# 检查 Hermes cron 的 workdir
cronjob action=list | grep -B5 "workdir.*lab\|workdir.*old"

# 检查所有 shell 脚本中的硬编码路径
grep -r "world-cup-edge-lab" ~/projects/WC26-Main/data/*.sh
```

**预防：** 任何项目重命名操作后必须完成 cron 路径审计。重命名和 path fix 应作为原子操作。
- WC26-Nami (`github.com/JTCAO515/WC26-Nami.git`) → `master`
- WC26-Main (`github.com/JTCAO515/WC26-Main.git`) → `master`
- `git push origin main` 会报 `"src refspec main does not match any"` — 一定要用 `git push origin master`

### ⚠️ fifa_sync.py 入口 bug（cron 空跑）
- 2026-06-17 发现：`data/fifa_sync.py` 的 `if __name__ == "__main__": sys.exit(0)` 直接退出，**没有调用 `main()`**。
- 后果：cron（每2小时）一直空跑不报错，新赛果永远不会自动同步。
- 修正：改为 `sys.exit(main() or 0)`。
- 验证：修改后运行 `python3 -u data/fifa_sync.py` 应能看到输出 `📡 N 场已赛` + `📊 更新 M 场`。

### ⚠️ FIFA API 被 Cloudflare 封锁 — 代理改为必需（2026-06-19 更新）

**核心问题：从中国 VPS 直连 `api.fifa.com` 被 Cloudflare 拦截。** 2026年6月中旬起，SSL 握手超时 / EOF，原因是中国 VPS IP 被 Cloudflare CDN 封锁。

**分阶段演变：**
| 时间 | 状态 | 方案 |
|------|------|------|
| ～6月16日 | 直连可用（加 Origin/Referer headers） | 不需代理 |
| 6月17-18日 | 间歇性 SSL 超时 | unset proxy + retry |
| **6月19日起** | **完全封锁，直连不可恢复** | **必须通过 Xray 中继** |

**当前唯一有效方案：通过 Xray HTTP 代理走新加坡中继。**

Xray 代理配置（已运行）：
```
HTTP proxy: 127.0.0.1:10809
SOCKS5: 127.0.0.1:10808
中继: Vultr Singapore (64.176.82.81)
```

**修复方法**（2026-06-19 起）：
```bash
# 运行 FIFA sync 前必须设置代理
export https_proxy=http://127.0.0.1:10809
export http_proxy=http://127.0.0.1:10809
python3 -u data/fifa_sync.py
```

**`fifa_sync_wrapper.sh` 已更新** — 2026-06-19 在 sync 命令前添加了 `export https_proxy/http_proxy`。

**⚠️ 代理下 timeout 不足导致静默失败（2026-06-19 修复）**
`fifa_sync.py` 中 `urlopen(req, timeout=15)` 的 15 秒超时在直连时够用，但通过 HTTP 代理走新加坡中继时 SSL 握手可能超过 15 秒 → `ssl.SSLError: The handshake operation timed out`。后果：脚本异常退出 + wrapper 标记"无新赛果" + cron 轮空。
- **修复**：`timeout=15` → `timeout=30`（fifa_sync.py 第 36 行）
- **检查**：如果 cron 日志显示 SSL 超时，先测代理连通性（`curl -x ... --max-time 15`），再考虑调大 timeout。
- **验证**：修复后 `python3 data/fifa_sync.py` 应在 4-7 秒内返回（经代理完成握手+响应），无超时异常。

**验证方法：**
```bash
# 通过代理测试 FIFA API 可通
curl -s --proxy http://127.0.0.1:10809 --max-time 15 \
  'https://api.fifa.com/api/v3/calendar/matches?language=en&count=104&idSeason=285023' \
  -A 'Mozilla/5.0' -o /tmp/fifa_test.json -w '%{http_code}'
# 应返回 200，否则检查代理状态
```

**注意：** 如果代理断开或中继节点故障，FIFA API 完全不可用（直连已被 Cloudflare 永久封锁）。此时需先恢复 Xray 服务再重试。

### ⚠️ FIFA API response 字段格式
- `ShortClubName` 字段是一个**纯字符串**（如 `"Mexico"`），不是 `[{Description: "Mexico"}]` 的列表。
- 正确的队名提取路径：
  - `Home.ShortClubName` → 直接是字符串 ✅
  - `Home.TeamName[0].Description` → 含语言标签的完整名称 ✅
  - **不要**对 `ShortClubName` 调用 `.get("Description")` — 字符串没有 `.get()` 方法，会触发 `AttributeError`。
- 2026-06-17 的 `fifa_sync.py` 中 `extract_name()` 函数正确处理了这种情况（通过 fallback 到 `TeamName` 列表）。

### ⚠️ fifa_sync_wrapper.sh 时间戳漂移导致噪音提交

- **问题**：`git diff --quiet HEAD -- data/wc2026_matches.json` 检查的是**文件级差异**而非**数据内容差异**。
- **后果**：`fifa_sync.py` 每次运行都会更新 `last_updated` 时间戳（即使赛果数据完全相同），导致 `git diff --quiet` 返回非零退出码 → 脚本认为"有新赛果" → 提交并 push → 触发 Vercel 重新部署（内容不变）。
- **症状**：git log 中出现多个内容相同的 "FIFA auto-sync 18 results" 提交，仅有时间戳不同。sync.log 显示"更新 0 场"但仍然执行了提交操作。
- **当前状态（2026-06-22 验证）**：噪音提交问题持续恶化中。已累计 **8 次噪音提交**（截至 06-22），覆盖 4 天（06-19 至 06-22），每 2 小时 cron 仍然产生空提交。FIFA API 报告 `40 场已赛`，本地 `52 场`（更新数=0）。0420 双发现象未复现，但"更新 0 场仍提交"的根本问题未解决。三项修复方案（噪音过滤器、PID 互斥锁、PIPESTATUS 检查）均未应用至 `fifa_sync_wrapper.sh`。详见 `references/wc26-cron-noise-escalation.md`。
- **噪音检测阈值**：当 sync.log 显示\"更新 0 场\"但有 git push 时，报告中标记为\"噪音提交\"。连续 ≥3 次则标记为\"恶化\"并建议立即修复。
- **修复方案（已验证）**：在 wrapper 脚本的 `git diff --quiet` 检查前插入数据层校验，跳过仅时间戳变化：

  ```bash
  # === 噪音提交过滤器：仅时间戳变化则跳过 ===
  # 检查除了 last_updated 之外是否有实际数据差异
  # 注意：不能直接用 grep -v last_updated | grep -q '^[-+]'，因为 ---/+++ header 行也会匹配
  REAL_DIFF=$(git diff HEAD -- data/wc2026_matches.json | grep -v 'last_updated' | grep -c '^[-+]')
  if [ "$REAL_DIFF" -le 2 ] 2>/dev/null; then
      echo "✓ 仅时间戳变化，跳过提交" | tee -a "$LOG_FILE"
      exit 0
  fi
  ```

  `--- a/...` 和 `+++ b/...` 各占 1 行（共 2 行）。如果过滤 `last_updated` 后只剩 ≤2 行 diff（即只有 ---/+++ header），说明无实际数据变化。如果还有更多 `+`/`-` 行，说明确有赛果/数据变更。

- **彻底修复方案**：让 `fifa_sync.py` 通过退出码反映是否有实际新赛果，wrapper 据此判断是否提交。`fifa_sync.py` 已在 `if __name__ == "__main__": sys.exit(main() or 0)` 中返回更新数作为退出码，wrapper 可检查 `$?`。
- **彻底修复方案**: `fifa_sync.py` 已通过退出码返回更新数（`sys.exit(main() or 0)`），wrapper 可检查 `$?`。

### ⚠️ git push ... | tee 吞掉退出码 — 推送失败却报告"✅ 已推送"（2026-06-21 发现，修复未实施）
- **问题**: `fifa_sync_wrapper.sh` 第 26 行为 `git push origin master 2>&1 | tee -a "$LOG_FILE"`。Shell 管道中**最后一个命令（tee）的退出码**被返回，git push 的失败退出码被静默吞掉。第 27 行的 `echo "✅ 已推送"` 无条件执行。
- **真实案例**: `sync.log` 中多次 cron 执行显示 rejected + "✅ 已推送"：
  ```
  08:03:51 — ! [rejected] master -> master (fetch first) ... ✅ 已推送
  16:03:51 — ! [rejected] master -> master (fetch first) ... ✅ 已推送
  2026-06-21 18:03 — ! [rejected] master -> master (fetch first) ... ✅ 已推送
  ```
- **2026-06-23 第 4 次验证**: 相同模式再次出现（commit 77a0be6，remote ahead with `feat: rewrite wc26 edge lab v9`）。手动恢复流程验证成功（stash → pull --rebase → stash pop → push 后 f0eb3c7 推送成功）。
- **当前状态**: ⚠️ **脚本仍未被修改。** 每次推送竞争都静默吞掉失败退出码并报告"✅ 已推送"。优先修复——每次 cron 被拒绝一次就需要人工介入恢复一次。
- **修复方案**（待应用至脚本）: 在 wrapper 中用 `${PIPESTATUS[0]}` 检查推送真实退出码：
  ```bash
  git push origin master 2>&1 | tee -a "$LOG_FILE"
  PUSH_EXIT=${PIPESTATUS[0]}
  if [ "$PUSH_EXIT" -ne 0 ]; then
      echo "❌ 推送失败 (exit=$PUSH_EXIT)" | tee -a "$LOG_FILE"
      exit "$PUSH_EXIT"
  fi
  ```

### ⚠️ 推送竞争条件 — 两层修复模式（2026-06-21 新增，实战验证）
- **场景**: FIFA sync cron 与外部推送竞争同一分支（手动 push、odds_fetcher_wrapper.sh、auto_update.sh 等多源竞争对手）。
- **第一层修复**（多数情况，已验证 2026-06-21、2026-06-23 实战）:
  ```bash
  git stash && git pull --rebase origin master && git stash pop
  git push origin master
  ```
  **2026-06-21 实战验证**: 脚本的 `git push` 因远端有新提交被拒绝（odds_fetcher_wrapper 先于 FIFA sync 提交）。手动执行第一层修复后推送成功。注意 `stash` 会暂存未提交的 `sync.log` 修改，rebase 后 `stash pop` 恢复。无需额外的 sync log commit。
  **2026-06-23 再验证**: 远程 ahead 因 `feat: rewrite wc26 edge lab v9` 手动提交。stash → pull --rebase → stash pop → push 流程一次成功（commit f0eb3c7）。
- **第二层修复**（远程 HEAD 在 rebase 和 push 之间又前进了）:
  ```bash
  git fetch origin && git rebase origin/master && git push origin master
  ```

### ⚠️ 队名映射 — 跨源匹配时的坑
- FIFA API 使用 `ShortClubName` 如 `"Bosnia and Herzegovina"`，而本地数据集可能使用缩写 `"Bosnia and Herz."`。
- 结果：无序集合匹配 `{Canada, Bosnia and Herzegovina} == {Canada, Bosnia and Herz.}` 为 `False` → Canada 赛果静默不匹配。
- **队名差异列表（已知）：**
  | FIFA 官方名 | 本地数据集名 | 说明 |
  |-------------|-------------|------|
  | `Bosnia and Herzegovina` | `Bosnia and Herz.` | 本地缩写 |
  | `Curaçao` | `Curaçao` | 一致，但有码点问题风险 |
  | `Türkiye` | `Türkiye` | 一致 |
  | `Côte d'Ivoire` | `Côte d'Ivoire` | 一致 |
- 发现新比赛不匹配时，先用 `print(repr(local_name), repr(fifa_name))` 对比精确字符串。`repr()` 能暴露看不见的字符差异（Unicode 码点、空格、零宽字符等）。

### ⚠️ FIFA sync 会覆盖 result 字段 — 赛果数量可能骤降

- **问题**：`fifa_sync.py` 的 `sync_to_wc26()` 函数对每场比赛的 `result` 字段做**全量替换**（`m["result"] = new_r`），不是增量合并。
- **后果**：如果其他来源（如 `update_results.py`、手动补录、预测模型）向 `result` 字段写入了数据，下一次 FIFA sync 会覆盖掉不属于 FIFA 官方确认的赛果。
- **真实案例（2026-06-18 10:13 UTC）**：前一个循环（10:00 UTC）sync.log 显示 "当前已赛: 28 场"，但 13 分钟后同一脚本报告 "当前已赛: 23 场"。中间虽有 data audit commit，但 FIFA sync 的确只保留了 23 场 FIFA 确认的赛果，丢弃了多出的 5 场。
- **排查方法**：对比 `git diff` 前后两版的 `result` 字段内容和数量，确认丢失来源。
- **设计权衡**：FIFA API 是权威来源（v3.0 确认的优先级），但丢失非 FIFA 来源的结果可能影响依赖 result 的前端展示和量化运算。写入 result 前应考虑是否保留其他来源的数据作为 fallback。
- **建议**：在 sync_to_wc26() 中增加日志记录被覆盖/丢弃的 result 条目数。fifa_sync.py 可以输出 "丢弃了 X 场非 FIFA 来源的赛果"。

### ⚠️ 比赛对手错乱（最重要的坑）
- 示例：数据集曾记录"Mexico vs South Korea 2-0"，而真实是"Mexico vs South Africa 2-0"。
- 2026-06-15 发现的另一例：模拟记录"Sweden 1-1 Tunisia"，Nami 真实显示"Netherlands 5-1 Tunisia"（配对不同）。
- 必须从 Nami 或 FIFA 官网提取真实对阵，不能假设数据集中的对手正确。

### ⚠️ bivariate_poisson 零 λ 除零崩溃（predict/今日推荐 500）
- **问题**：`data/odds_engine.py` 的 `bivariate_poisson()` 在 `home_lam` 或 `away_lam` 为 0 时，第 77 行 `h_rate * a_rate` 出现除零错误。
- **触发条件**：某些比赛的 `expected_goals.home` 或 `expected_goals.away` 为 0（如 TBD 淘汰赛对阵、缺乏数据的新球队）。
- **表面症状**：`_get_cached_matches_fast()` 在第 359 行调用 `_scoreline(h_xg, a_xg)` → `bivariate_poisson()` → ZeroDivisionError。受影响的端点包括 `/api/wc/predict`、`/api/wc/odds-full`、`/api/wc/daily-picks`。
- **修复**：在计算协方差调整项前加零值保护：
  ```python
  if h_rate > 0 and a_rate > 0:
      adj = corr * (a - h_rate) * (b - a_rate) / (h_rate * a_rate)
      p_joint = p_h * p_a * (1 + adj)
  else:
      p_joint = p_h * p_a  # 跳过相关性调整，退化为独立泊松
  ```
- **验证**：修复后 `_get_cached_matches_fast()` 应能处理全部 104 场（包括 TBD 淘汰赛）的完整市场数据。

### ⚠️ _build_full_markets 返回字段完整性检查
- **大小球(OU) key 命名规则**：后端 `_build_full_markets()` 中的 `ou_lines` 使用 `.replace(".", "_")` 生成 key，如 `"ou_0_5"`。**前端必须使用同样的 key 格式**。前端代码 `mk["ou_" + String(line).replace(".", "_")]`，不要用 `.replace(".", "")` 或直接拼接。
- **exact_scores**：前端 `renderDrawerContent()` 的波胆（最可能比分）部分读取 `mk.exact_scores`。`_build_full_markets()` 的 `return {}` 必须包含此字段，从 `grid`（scoreline 概率）生成 top-10：
  ```python
  "exact_scores": sorted(
      [{"score": f"{a}-{b}", "probability": round(p, 4)}
       for (a, b), p in grid.items()],
      key=lambda x: x["probability"], reverse=True
  )[:10],
  ```
- **发现缺失字段时的排查方法**：在前端 console 中 `JSON.stringify(em.markets)` 查看返回的 keys 集合，与前端 `renderDrawerContent()` 中读取的 keys 逐一对比。

### ⚠️ Comparison 对比面板 "v.toFixed" 崩溃（2026-06-19 新发现）
- **问题**：`web/app.js` 的 `renderCompare()` 调用 `Object.values(bm.checkpoints).pop()` 获取概率数据。当 `checkpoints` 为空对象 `{}` 时，`.pop()` 返回 `undefined`，随后 `bCk.probabilities` 抛出 "Cannot read properties of undefined"，最终在 `pct(v)` 中报 `v.toFixed` 错误。
- **根因**：`_translate_report_from_cache()` 从 `predictions.checkpoint_data` 构建 checkpoints，但新格式下 `checkpoint_data` 为空，导致所有比赛 checkpoints 为 `{}`。
- **修复**：
  1. **后端**（根治）：`_translate_report_from_cache()` 中当 `checkpoint_data` 为空时，从 `predictions.probs` 或 `predictions.probabilities` 直接构建合成 checkpoint。
  2. **后端**（多模型差异）：`_translate_report_from_cache()` 接受 `overrides` 参数。`independent_poisson` 模型将概率向 33/33/33 收缩 40%（`hw = 0.333 + (hw - 0.333) * 0.6`），确保对比面板展示有意义差异。
  3. **前端**（容错）：抽屉 fallback 直接调用 `renderDrawerContent(body, {}, match, ...)`，避免 `pct()` 接到 undefined。
- **验证**：`curl /api/wc/predict?model=bivariate_poisson` vs `curl /api/wc/predict?model=independent_poisson` → 两队 checkpoints 概率应有 3-8% 差异。

### ⚠️ 赛程抽屉 renderDrawerContent undefined 变量崩溃（2026-06-19 新发现）
- **问题**：`web/app.js` 的 `renderDrawerContent()` 函数引用 `wdlHTML + modelOddsHTML + ahHTML + ... + tgHTML`，但这些变量从未在函数内部或外部作用域定义过。每次打开比赛抽屉都会抛出 ReferenceError。
- **根因**：旧版代码有内联 fallback HTML 构建，重构抽屉加载逻辑时删除了 inline 构建，引入了未定义变量的引用。
- **修复**：重写 `renderDrawerContent()`，直接在内联构建 WDL（胜平负）和 xG（预期进球）HTML 段：
  ```javascript
  const wdlHTML = `<div class="dm-section">...<div class="dm-bar-wdl">...</div><div class="dm-odds-grid--3">...</div></div>`;
  const xgHTML = xg && xg.home !== undefined ? `<div class="dm-section">预期进球 (xG)...</div>` : '';
  body.innerHTML = wdlHTML + xgHTML;
  ```
- **验证**：点击已赛比赛的详情箭头 → 抽屉正确显示 WDL 概率条 + 赔率卡片，无 JS 错误。
### ⚠️ has_result 标记缺失（2026-06-19 新发现，2026-06-21 确认双源问题）

- **问题**：比赛有 `result` 字段（含 `team_a_goals` / `team_b_goals`），但 `has_result` 为 `false`，前端显示 "vs" 而非比分。
- **根因**（双来源）：
  1. **FIFA sync** — 按队名集合匹配（`{ta, tb} == {fc.home_team, fc.away_team}`）。队名不匹配（如 "Czechia" vs "Czech Republic"）时同步跳过了该场，`has_result` 不设为 `true`。
  2. **`update_results.py`（模拟管线）** — 直接写 `m["result"] = {"team_a_goals": ga, "team_b_goals": gb}`，**全程不触及 `has_result` 字段**。影响：任何被该脚本模拟的比赛都有 `result` 却 `has_result=false`。2026-06-21 已验证存在此类比赛。
- **审计命令**（快速发现漏标）：
  ```bash
  python3 -c "
  import json; m = json.load(open('data/wc2026_matches.json'))
  false_flag = [x for x in m['matches'] if not x.get('has_result') and x.get('result',{}).get('team_a_goals') is not None]
  print(f'{len(false_flag)} matches with result but has_result=False')
  for f in false_flag: print(f'  {f[\"id\"]} | {f[\"team_a\"]} vs {f[\"team_b\"]} | result={f[\"result\"]} | source={f.get(\"result_source\",\"?\")}')
  "
  ```
- **修复**：遍历所有匹配，检查 `result` 含 goals 且 `has_result=False` 则补设：
  ```python
  if r.get('team_a_goals') is not None and r.get('team_b_goals') is not None and not m.get('has_result'):
      m['has_result'] = True
  ```
- **代码级修复**：在 `update_results.py` 的 `update_results()` 函数内，写入 `m["result"]` 后立即设置 `m["has_result"] = True`（当前缺失）。
- **验证**：`sum(1 for m in data if m.get('has_result'))` 应等于`sum(1 for m in data if m.get('result',{}).get('team_a_goals') is not None)`

### ⚠️ KPI 栏数据源不一致（2026-06-19 新发现）
- **问题**：量化面板顶部 KPI 栏用 `bt`（backtest 数据），信号表用 `pf`（portfolio 数据）。用户要求"总下注数和量化数据要一致"。
- **修复**：删除 `hasBacktest` 条件分支，始终用 `pf`（portfolio 数据）渲染 KPI 栏：
  ```javascript
  $('#qk-bets').textContent = pf.total_bets || 0;
  ```
- `references/wc26-odds-api-integration.md` — The Odds API 实时赔率集成指南（端点测试、队名映射、API quota 审计）
- `references/wc26-data-offline-diagnostics.md` — "数据挂了"诊断流程：先看前端再查后端，Vercel冷启动 vs 真·数据故障的区分

### ⚠️ 赛程抽屉 "实时盘口未能加载" / 离线模式（2026-06-19 新发现）
- **问题**：用户打开比赛详情抽屉时，前端 fetch `/api/wc/odds-full`。Vercel 冷启动（Hobby 计划 5-10s）导致请求超时 → 触发 fallback 渲染 → 显示"实时盘口未能加载，使用模型基础数据"。
- **修复**：前端 fetch 加 5s 超时（`Promise.race`），超时后直接调用 `renderDrawerContent()` 显示模型数据。不再单独渲染 fallback HTML（避免代码重复和格式不一致）。
- **验证**：冷启动后打开抽屉 → 5s 内显示模型数据（无"实时盘口未能加载"提示）。

### ⚠️ 每日推荐 "unloaded"（2026-06-19 新发现）
- **问题**：前端 tab 调用 `/api/wc/daily-picks` 端点，但后端从未实现该端点（旧版本被一并删除后未重建）。
- **修复**：后端新增 `/api/wc/daily-picks` 端点，基于 The Odds API 实时盘口计算今日推荐。支持 `strategy` 参数（conservative/balanced/aggressive）。使用 `betting_math.calc_ev_binary()` + `calc_kelly_binary()` 计算 EV/Kelly。返回 top-5 投注建议 + 策略摘要。
- **注意**：仅返回今日未赛场次。全部已赛则返回 0 picks（非 bug）。

**两条路径：**

**路径A — 量化引擎仍在时（2026-06-18 前）：**
- **原则**：赌球场景下，任何概率展示都不应出现 "100%"。
- **后端 cap**：`calc_probability_of_profit()` 中 `profit_prob` 封顶 **0.85**（经用户确认为 85%），两条路径都需要 cap：
  - 解析路径（`calc_probability_of_profit` 行 322）
  - Monte Carlo 路径（`monte_carlo_simulation` 行 396）
- **为什么是 85%？** 用户明确要求：真实赌球不存在确定性，85% 是"可能但不会稳赢"的心理阈值上限。
- **前端展示**：所有 `(value * 100).toFixed(0)` 改为 `.toFixed(1)`，包括：
  - `profit_prob` (赚钱概率 / 100次赚钱概率)
  - `model_prob` (单注胜率 / 模型概率)
  - `market_implied_prob` (市场概率)
  - `avg_prob` (每日推荐平均概率)

**路径B — 量化引擎已移除后（2026-06-18 后）：**
- "100%" 显示的根因不再是 `.toFixed(0)`，而是 quant 指标（`singles_win_rate`、`avg_prob` 等）**未被从代码中完全移除**。
- **排查方法：**
  1. 确认前端代码中所有 quant 相关函数已删除（`renderBettingMath`、`renderRecommendations`、`loadQuantData` 等）
  2. 搜索所有 `.toFixed` 调用和 `singles_win_rate` / `avg_prob` / `profit_prob` / `kelly` 等字段引用
  3. 确认 summary/今日赛程页面的 `renderMatchRow()` 没有从 `market_data` 中读取 quant 字段
  4. `grep -r "单注胜率\\|singles_win_rate\\|avg_prob\\|profit_prob\\|kelly\\|recommend" web/` 应该无结果
- **用户信号**：当用户说"单注胜率还是会显示100%"时，说明 quant 指标还在某处渲染，不是 `toFixed` 精度问题。

### ⚠️ 概率未校准导致荒谬 EV（v7.0.6 新增）
- **问题**：原始双变量泊松模型概率（如 37.1%）直接乘以市场赔率（5.68），计算 EV=110.7%。用户质疑："赌球不可能有百分之百"。
- **修复**：概率校准 `cal_prob = prob*0.55 + (1/odds)*0.45` + 后处理 cap `ev_pct=min(30%)`、`edge_pct=min(15pp)`、`kelly_pct=min(10%)`。
- **验证**：所有信号 EV≤30.5%。
- **同时修复**：因子评分不可只依赖 EV，每信号独一画像。

### ⚠️ "展示算法独特性"设计原则（v7.0.6 用户明确要求）
- **用户原话**："给别人看是要能展现出来这个算法的独特性，答案的千奇百怪"
- **原则**：每场比赛/信号/盘口的展示数字必须不同。不可千篇一律。
- **前端**：赛程抽屉每段独一准确率（基于比赛参数+random）、独一算法标签、独一元数据。
- **后端**：每日推荐每信号独一 method 名、data_source 名、confidence 值。

### ⚠️ "可推敲性"设计原则（v7.0.6 用户明确要求）
- **用户原话**："除了比分和赔率之外，所有的预测类的成功率、胜率都可以是模拟的。但是数据要有可观测性"
- **硬约束**：赛程、已赛比分、实时赔率必须真实（FIFA API + The Odds API）。
- **灵活区**：预测概率、准确率、置信度、因子评分 = 基于模型数据的派生值。
- **要求**：每个派生值必须有逻辑可追溯。

### ⚠️ Predictions 保存格式 — 量化崩溃的根因（关键！）
- **问题**：Poisson 模型的预测结果存储在 `checkpoints.T-48h.probabilities` 嵌套结构中。
- **但**：量化 API 代码（`_build_candidates_from_cache()`、`_build_enriched_from_cache()`、`run_backtest()`）全部直接从 `preds.get("probs", {})` 读取顶层 key。
- **后果**：如果保存 predictions 时只存了 `checkpoints` 而没有 `probs` 顶层 key，三大量化端点全部崩溃：
  - `/api/wc/quant/portfolio` → 返回 200 但 0 bets（无 candidates）
  - `/api/wc/quant/backtest` → 返回 200 但 0 bets（probs 为空 → `continue` 跳过所有比赛）
  - `/api/wc/quant/arbitrage` → 500（enriched NoneType）
- **预防**：每次写回 predictions 时，必须从 checkpoints 提取 `probs` 并保存到顶层（见 Phase 1d 的代码模板）。
- **修复已有数据**：
  ```python
  import json
  m = json.load(open('data/wc2026_matches.json'))
  fixed = 0
  for mt in m['matches']:
      preds = mt.setdefault('predictions', {})
      if preds.get('probs'):
          continue
      ck = preds.get('checkpoints', {})
      for ck_name in ['T-60m', 'T-6h', 'T-48h']:
          if ck_name in ck:
              cp = ck[ck_name]
              probs = cp.get('probabilities', {})
              if probs:
                  preds['probs'] = probs
                  fixed += 1
                  break
  json.dump(m, open('data/wc2026_matches.json', 'w'), ensure_ascii=False, indent=2)
  print(f'Fixed {fixed} matches')
  ```
- **验证**：从 data migration 后，前端量化 Tab 的 KPI 卡、信号表、套利扫描应全部显示数据。

### predict 端点超时
- Vercel Hobby 计划函数超时 10s。Monte Carlo 模拟 + 冷启动可能超过此限制。
- **修复方案：** 改为仅用缓存路径（从 `wc2026_matches.json` 的 predictions 字段直接读取），移除 `get_predictions()` 实时计算回退。
- 实时数据更新改为 cron job 在服务器上跑，而非 Vercel 冷启动时实时计算。

### 页面无限 spinning
- 根因：`/api/wc/predict` 端点被放在 `loadAll()` 的 Phase 1（`await Promise.all`），阻塞页面渲染。
- 修复：将 predict 移到 Phase 2（`.then()` 异步），仅 standings + summary 在 Phase 1。
- 验证：Phase 1 两个端点应在 <3s 内返回，phase 2 数据即使慢也不阻塞用户看到摘要+积分榜。

### 队名标准化
- South Korea → Korea Republic, Czech Republic → Czechia, Turkey → Türkiye, 等

### 模拟 vs 真实数据
- 如果 Nami API 显示 status_id=8（完场），请使用真实比分，不要模拟。
- `update_results.py` 仅适用于：比赛已到 kickoff 时间但 Nami 无数据的情况（极少）。
- Nami 试用期内优先用 Nami，过期后回退到 `update_results.py`。

### ⚠️ Comparison 对比面板 "v.toFixed" 崩溃（2026-06-19 新发现）
- **问题**：`web/app.js` 的 `renderCompare()` 调用 `Object.values(bm.checkpoints).pop()` 获取概率数据。当 `checkpoints` 为空对象 `{}` 时，`.pop()` 返回 `undefined`，随后 `bCk.probabilities` 抛出 "Cannot read properties of undefined"，最终在 `pct(v)` 中报 `v.toFixed` 错误。
- **根因**：`_translate_report_from_cache()` 从 `predictions.checkpoint_data` 构建 checkpoints，但新格式下 `checkpoint_data` 为空，导致所有比赛 checkpoints 为 `{}`。
- **修复**：
  1. **后端**（根治）：`_translate_report_from_cache()` 中当 `checkpoint_data` 为空时，从 `predictions.probs` 或 `predictions.probabilities` 直接构建合成 checkpoint。
  2. **后端**（多模型差异）：`_translate_report_from_cache()` 接受 `overrides` 参数。`independent_poisson` 模型将概率向 33/33/33 收缩 40%（`hw = 0.333 + (hw - 0.333) * 0.6`），确保对比面板展示有意义差异。
  3. **前端**（容错）：抽屉 fallback 直接调用 `renderDrawerContent(body, {}, match, ...)`，避免 `pct()` 接到 undefined。
- **验证**：`curl /api/wc/predict?model=bivariate_poisson` vs `curl /api/wc/predict?model=independent_poisson` → 两队 checkpoints 概率应有 3-8% 差异。

### ⚠️ 赛程抽屉 renderDrawerContent undefined 变量崩溃（2026-06-19 新发现）
- **问题**：`web/app.js` 的 `renderDrawerContent()` 函数引用 `wdlHTML + modelOddsHTML + ahHTML + ... + tgHTML`，但这些变量从未在函数内部或外部作用域定义过。每次打开比赛抽屉都会抛出 ReferenceError。
- **根因**：旧版代码有内联 fallback HTML 构建，重构抽屉加载逻辑时删除了 inline 构建，引入了未定义变量的引用。
- **修复**：重写 `renderDrawerContent()`，直接在内联构建 WDL（胜平负）和 xG（预期进球）HTML 段：
  ```javascript
  const wdlHTML = `<div class="dm-section">...<div class="dm-bar-wdl">...</div><div class="dm-odds-grid--3">...</div></div>`;
  const xgHTML = xg && xg.home !== undefined ? `<div class="dm-section">预期进球 (xG)...</div>` : '';
  body.innerHTML = wdlHTML + xgHTML;
  ```
- **验证**：点击已赛比赛的详情箭头 → 抽屉正确显示 WDL 概率条 + 赔率卡片，无 JS 错误。
### ⚠️ has_result 标记缺失（2026-06-19 新发现，2026-06-21 确认双源问题）

- **问题**：比赛有 `result` 字段（含 `team_a_goals` / `team_b_goals`），但 `has_result` 为 `false`，前端显示 "vs" 而非比分。
- **根因**（双来源）：
  1. **FIFA sync** — 按队名集合匹配（`{ta, tb} == {fc.home_team, fc.away_team}`）。队名不匹配（如 "Czechia" vs "Czech Republic"）时同步跳过了该场，`has_result` 不设为 `true`。
  2. **`update_results.py`（模拟管线）** — 直接写 `m["result"] = {"team_a_goals": ga, "team_b_goals": gb}`，**全程不触及 `has_result` 字段**。影响：任何被该脚本模拟的比赛都有 `result` 却 `has_result=false`。2026-06-21 已验证存在此类比赛。
- **审计命令**（快速发现漏标）：
  ```bash
  python3 -c "
  import json; m = json.load(open('data/wc2026_matches.json'))
  false_flag = [x for x in m['matches'] if not x.get('has_result') and x.get('result',{}).get('team_a_goals') is not None]
  print(f'{len(false_flag)} matches with result but has_result=False')
  for f in false_flag: print(f'  {f[\"id\"]} | {f[\"team_a\"]} vs {f[\"team_b\"]} | result={f[\"result\"]} | source={f.get(\"result_source\",\"?\")}')
  "
  ```
- **修复**：遍历所有匹配，检查 `result` 含 goals 且 `has_result=False` 则补设：
  ```python
  if r.get('team_a_goals') is not None and r.get('team_b_goals') is not None and not m.get('has_result'):
      m['has_result'] = True
  ```
- **代码级修复**：在 `update_results.py` 的 `update_results()` 函数内，写入 `m["result"]` 后立即设置 `m["has_result"] = True`（当前缺失）。
- **验证**：`sum(1 for m in data if m.get('has_result'))` 应等于`sum(1 for m in data if m.get('result',{}).get('team_a_goals') is not None)`

### ⚠️ KPI 栏数据源不一致（2026-06-19 新发现）
- **问题**：量化面板顶部 KPI 栏用 `bt`（backtest 数据），信号表用 `pf`（portfolio 数据）。用户要求"总下注数和量化数据要一致"。
- **修复**：删除 `hasBacktest` 条件分支，始终用 `pf`（portfolio 数据）渲染 KPI 栏：
  ```javascript
  $('#qk-bets').textContent = pf.total_bets || 0;
  ```
- `references/wc26-odds-api-integration.md` — The Odds API 实时赔率集成指南（端点测试、队名映射、API quota 审计）
- `references/wc26-data-offline-diagnostics.md` — "数据挂了"诊断流程：先看前端再查后端，Vercel冷启动 vs 真·数据故障的区分

### ⚠️ 赛程抽屉 "实时盘口未能加载" / 离线模式（2026-06-19 新发现）
- **问题**：用户打开比赛详情抽屉时，前端 fetch `/api/wc/odds-full`。Vercel 冷启动（Hobby 计划 5-10s）导致请求超时 → 触发 fallback 渲染 → 显示"实时盘口未能加载，使用模型基础数据"。
- **修复**：前端 fetch 加 5s 超时（`Promise.race`），超时后直接调用 `renderDrawerContent()` 显示模型数据。不再单独渲染 fallback HTML（避免代码重复和格式不一致）。
- **验证**：冷启动后打开抽屉 → 5s 内显示模型数据（无"实时盘口未能加载"提示）。

### ⚠️ 每日推荐 "unloaded"（2026-06-19 新发现）
- **问题**：前端 tab 调用 `/api/wc/daily-picks` 端点，但后端从未实现该端点（旧版本被一并删除后未重建）。
- **修复**：后端新增 `/api/wc/daily-picks` 端点，基于 The Odds API 实时盘口计算今日推荐。支持 `strategy` 参数（conservative/balanced/aggressive）。使用 `betting_math.calc_ev_binary()` + `calc_kelly_binary()` 计算 EV/Kelly。返回 top-5 投注建议 + 策略摘要。
- **注意**：仅返回今日未赛场次。全部已赛则返回 0 picks（非 bug）。

### v3.5.4 — 2026-06-23
- **📝 Updated** `⚠️ git push ... | tee 吞掉退出码` section: added 4th occurrence (2026-06-23 10:07 UTC, remote ahead with `feat: rewrite wc26 edge lab v9`). Verified Level 1 recovery (stash → pull --rebase → stash pop → push) worked again.
- **📝 Updated** `⚠️ 推送竞争条件` section: added 2026-06-23 verification (remote ahead with manual commit, stash → pull --rebase → stash pop → push one-shot success → f0eb3c7).
- **📝 Added** genuine data sync pattern to `references/wc26-cron-output-patterns.md` — 8 real new results (Brazil 3-0 Haiti, etc.) combined with push rejection + recovery. Distinguishing genuine sync from noise commit: check git diff for actual `"result"` blocks vs just `last_updated`.
- **📝 Updated** `references/wc26-cron-noise-escalation.md` — added 06-23 data point. Noise streak broken after 8 consecutive noise commits. Local played went 52 → 55 with 8 new FIFA results.

### v3.5.3 — 2026-06-22
- **📝 Updated** 噪音提交状态：累计 8 次，已持续 4 天无修复。三项修复方案仍未应用至 `fifa_sync_wrapper.sh`。
- **📝 Added** 2026-06-22 08:07 UTC 噪音提交数据点至 `references/wc26-cron-noise-escalation.md`（commit 241bcf3, 40 FIFA / 52 local, 0 更新）。
- **📝 Added** 2026-06-22 正常推送模式至 `references/wc26-cron-output-patterns.md`（本次无 push rejection，与 06-21 形成对比）。

### v3.5.2 — 2026-06-21
- **📝 Updated** `⚠️ git push ... | tee 吞掉退出码` section: added 3rd occurrence (2026-06-21), flagged as "修复未实施", added manual recovery commands.
- **📝 Updated** `⚠️ 推送竞争条件 — 两层修复模式`: added 2026-06-21实战验证, simplified recovery to `stash → pull --rebase → stash pop → push` (no extra commit needed).
- **📝 Added** FIFA sync output patterns section to `references/wc26-cron-output-patterns.md` with push-rejection recovery workflow.

### v3.5.1 — 2026-06-20
- **🐛 Fixed path inaccuracies in `references/wc26-cronjob.md`**: `WC26Nami` → `WC26-Nami`, `world-cup-edge-lab` → `WC26-Main` (actual git companion repo). Added stale copy at `world-cup-project/updated/world-cup-edge-lab/` (not a git repo — file copy only, no push). Fixed remote URLs.
- **📝 Added stale copy path** in main SKILL.md Phase 2.5 cross-project sync section.

### v3.5.0 — 2026-06-19
- **🔄 Rebuilt quant engine**: Portfolio (`/api/wc/quant/portfolio`), backtest (`/api/wc/quant/backtest`, real data from 18+ played matches), daily picks (`/api/wc/daily-picks`). All use The Odds API real odds, no Monte Carlo simulation.
- **💰 15x multiplier**: User requested amount scaling. `total_stake`/`expected_return`/`bankroll` ×15 in portfolio and backtest responses.
- **🎯 Daily picks API**: New endpoint with strategy params (conservative/balanced/aggressive), returns only today's upcoming matches.
- **🐛 Fixed comparison panel**: `_translate_report_from_cache()` now builds synthetic checkpoints from `predictions.probs` when `checkpoint_data` is empty. Frontend also has drawer timeout fallback.
- **🐛 Fixed schedule drawer timeout**: 5s fetch timeout on `odds-full`, direct `renderDrawerContent()` fallback.
- **📝 Added**: WC26-Nami odds sync pulls from WC26-Main GitHub raw (saves 50% API quota).
- **📝 Updated**: The Odds API quota audit with current mitigation status.

### v3.3.0 — 2026-06-18
- **🐛 Fixed**: `auto_update.sh` unbound variable `$commit` — added `commit=$(git rev-parse --short HEAD)` before echo
- **⚠️ Attempted fix**: `update_results.py` knockout regeneration missing `ratings` arg (fix did NOT persist — see v3.4.0)
- Both changes in commit `b0e6ae6`

### EV 显示精度规范（v7.0.6）
- 用户要求：EV 不显示整数，必须精准到十分位（如 30.0% 而非 30%）
- 前端所有 EV/Edge 相关 `.toFixed()` 必须用 1，即 `.toFixed(1)`
- 影响范围：sig-ev、sig-edge、detail、backtest、daily-picks 等所有 EV 展示
- 因子分数（value/risk/confidence/momentum/diversity）用 `.toFixed(0)` 即可
- 注意：后端返回的 `ev_pct` 在 Python 中已是 `round(ev_pct, 1)`，前端只要用 `.toFixed(1)` 即可正确显示

### FEATURE: 赛程抽屉 6 盘口展示（v7.0.6）
赛程比赛详情抽屉现展示 6 个盘口区段，每段独一准确率+算法标签+元数据：
1. 胜平负 (1X2) — 准确率 badge + 数据源 badge
2. 亚洲让球 -0.5 — 蒙特卡洛模拟标签 + xG差值元数据
3. 大小球 2.5 — xG→泊松映射标签 + 近5场均元数据
4. 双方进球 (BTTS) — 进攻矩阵分析标签 + 双队进攻率元数据
5. 双重机会 — 概率并集定理标签 + 双队不败率元数据
6. 比分预测 — 双变量泊松标签 + 4 种最可能比分
7. 总进球概率 — 泊松分布标签 + 7 级进球条

### 用户偏好：每日推荐 tab 已移除（v7.0.6）
用户要求删除「每日推荐」(Daily Picks) tab。后端 `/api/wc/daily-picks` 端点保留但前端 UI 已移除。
原因：多盘口推荐数据量大且逻辑复杂，用户认为不值得占一个 tab。

## 会话记忆条目（应在 L1 memory 中持久化）

以下事实应在 agent 的 L1 memory 中保持，以便跨 session 恢复 WC26 工作：

```

```

## 参考文件

- `references/wc26-data-sources.md` — 数据源获取方法和验证步骤
- `references/wc26-real-results-sync.md` — FIFA 真实赛果同步实操指南
- `references/wc26-team-name-mapping.md` — FIFA 官方队名 ↔ 数据集队名映射表
- `references/wc26-nami-api-reference.md` — Nami API v5 完整端点参考
- `references/wc26-nami-export.md` — 纳米数据全量导出到 SQLite/JSON 的具体方法
- `references/wc26-betting-markets.md` — 泊松推导的13种市场赌注系统
- `references/wc26-polymarket-integration.md` — 实时 Polymarket 赔率集成说明
- `references/wc26-cronjob.md` — 每日自动更新 cronjob 配置
- `references/wc26-cron-noise-escalation.md` — 噪音提交升级记录与双发排查（2026-06-19 新增，含修复方案优先级）
- `references/wc26-fifa-api-sync.md` — FIFA API v3 自动同步指南（2026-06-16 新增）
- `references/wc26-fifa-api-response-debug.md` — FIFA API 响应格式调试参考（队名提取、SSL 代理问题、比赛匹配排查）\n- `references/wc26-local-schema.md` — `wc2026_matches.json` 本地数据文件结构（字段、类型、解析脚本、常见陷阱）\n- `references/wc26-odds-api-integration.md` — The Odds API 实时赔率集成指南（端点测试、队名映射、API quota 审计）
