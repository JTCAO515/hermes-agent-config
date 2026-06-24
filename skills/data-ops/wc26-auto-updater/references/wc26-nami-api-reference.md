# Nami Data API v5 — 完整参考

> 纳米数据 API 2.0 版。HTTP (REST) + WebSocket (MQTT)。WC26Nami 项目已集成于 `data/nami_client.py`。
> 文档来源：官方API接入指南PDF + 服务刊例PDF + 控制台产品页面 + 实际探测验证。
> 最后更新：2026-06-15

## 连接信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://open.sportnanoapi.com/api/v5` |
| 认证方式 | Query params: `user` + `secret` (GET请求唯一有效方法) |
| WS/MQTT | `wss://s.sportnanoapi.com:443` (使用 paho-mqtt websockets) |
| 限速 | 1000次/分钟/IP |
| 响应格式 | `{"code": 0, "results": ..., "query": {...}}` |
| 错误码 | 0=正常, 404=资源不存在, 9999=未知错误 |
| 错误诊断 | "url未授权访问"=路径不存在, "用户名或密钥错误"=认证失败, "产品权限受限"=套餐不含此产品 |
| 日期参数 | 使用 **CST (UTC+8)** 判定日期，非UTC。查询`date=20260612`返回北京时间6月12日全天的比赛。 |
| 请求频次 | 全局1000次/分钟/IP，单接口频次见各接口说明 |

## 全部工作端点 (17个)

### 🔵 赛程赛果

#### 1. 按日期查询 — schedule/diary
```
GET /football/match/schedule/diary?date=yyyymmdd
```
- **date**: yyyymmdd (CST, 前后30天限制)
- 建议频次: 当天10min/次, 未来30min/次
- 返回 `results.match[]` 数组

#### 2. 赛事赛程列表 — competition/schedule/list
```
GET /football/competition/schedule/list?id={competition_id}
```
- 参数: `id` = 赛事ID
- 返回该赛事完整赛程
- 120次/min

### 🟢 实时数据

#### 3. 实时比赛数据 — match/live
```
GET /football/match/live
```
- 返回最近120min内比赛的事件/技术统计/文字直播 (全量更新)
- 建议频次: **2s/次** (最高频端点)
- `results` 是 **数组** (不是对象)，每个元素 = 一个实时比赛
- 非120min内的比赛有更新也会同步返回
- 比赛分钟数公式: 上半场=(当前-开球)/60+1, 下半场=(当前-开球)/60+45+1

#### 4. 实时球员统计变动 — match/player_stats/list
```
GET /football/match/player_stats/list
```
- 返回最近120s内球员统计数据变动的比赛
- 建议频次: 1min/次
- 返回: `[{match_id, player_stats: [...]}]`

#### 5. 实时赔率数据 — odds/live
```
GET /football/odds/live
```
- 返回最近60秒变化的赔率数据 (无变动不返回)
- 范围: 初盘→即时盘→滚球盘
- 支持4种类型: `asia`(亚盘), `eu`(欧赔), `bs`(大小球), `cr`(角球)
- 建议频次: **3s/次**
- 返回结构: `results.{company_id}[ [matchId, type, [time, matchTime, oddsStr, status], scoreStr] ]`
- 赔率字符串格式: `"主胜,盘口,客胜,是否封盘"` (如 `"0.68,-1.25,1.15,0"`)
- 亚盘盘口: 正=主让客, 负=客让主
- 赔率含义: 亚盘/大小球/角球=赢率(不含本金), 欧赔=赢率+本金

#### 6. 赔率更新清单 — odds/update
```
GET /football/odds/update
```
- 返回最近60s内指数有更新的比赛ID+公司ID (倒序)
- 建议频次: 3s/次
- 返回: `[{id, company_id, update_time}]`
- 用途: 据此通过 odds/history 查缺补漏

#### 7. 阵容变动更新 — match/lineup/update
```
GET /football/match/lineup/update
```
- 返回最近60s内阵容有变动的比赛列表
- 建议频次: 10s/次

### 🟡 历史/分析数据

#### 8. 比赛分析 — match/analysis
```
GET /football/match/analysis?matchId={id}
```
- 历史交锋/近期战绩/未来赛程/进球分布
- 限制: 前30天比赛, 60次/min

#### 9. 比赛趋势详情 — match/trend/detail
```
GET /football/match/trend/detail?matchId={id}
```
- 主客队趋势变化 (按分钟数)
- 主队为正, 客队为负
- 限制: 前30天比赛, 120次/min
- 实时趋势在 match/live 获取，这个接口用于补漏

#### 10. 单场赔率历史 — odds/history
```
GET /football/odds/history?id={matchId}
```
- 单场比赛所有指数公司的全历史赔率变化 (初盘→请求时刻)
- 范围: 初盘→即时盘→滚球盘
- 120次/min
- 返回: `results.{company_id}.{asia|eu|bs|cr}[ [time, matchTime, home, handicap, away, status, closed, score] ]`

### 🟠 比赛详情

#### 11. 比赛阵容详情 — match/lineup/detail
```
GET /football/match/lineup/detail?matchId={id}
```
- 需要先检查赛程接口中 `coverage.lineup == 1`
- 返回: 阵型(home_formation/away_formation), 教练, 球衣颜色, 球员列表(含坐标/球衣号/队长/评分)
- 坐标: 主队左上→右下, 客队右下→左上, 共100
- 限制: 前30天比赛, 120次/min

#### 12. 历史比赛完整统计 — match/live/history
```
GET /football/match/live/history?id={matchId}
```
- 已完结比赛 (30天内) 的完整统计 (事件+技术统计+文字直播)
- 120次/min
- 用于 match/live 的查缺补漏

### 🔴 球队/球员统计

#### 13. 历史比赛球队统计 — match/team_stats/detail
```
GET /football/match/team_stats/detail?id={matchId}
```

#### 14. 历史比赛球员统计 — match/player_stats/detail
```
GET /football/match/player_stats/detail?id={matchId}
```
- `rating`: 10分满分×100 (760 = 7.60)
- 含: goals, assists, shots, passes, fouls, tackles, dribble, saves, rating等30+字段

### 🟣 赛事数据 (积分榜+统计)

#### 15. 赛事积分榜 — competition/table/detail
```
GET /football/competition/table/detail?id={competition_id}
```
- **WC2026 积分榜关键端点!** `id=1` 返回世界杯12组积分榜
- 120次/min
- 返回结构:
  ```
  results.promotions[] — 升降级
  results.tables[] — 积分榜列表
    .group — 0=汇总/1=A/2=B...
    .stage_id — 阶段ID
    .rows[] — 球队排行
      .team_id, .points, .position, .total, .won, .draw, .loss
      .goals, .goals_against, .goal_diff
      .home_*, .away_* — 主客场细分
      .deduct_points — 扣分
      .promotion_id — 升降级关联
  ```
- WC2026 的 `competition_id=1`, group 1-12 对应 A-L 组
- 注: `group=0` 的行是汇总/所有球队总排名

#### 16. 赛事统计 — competition/stats/detail
```
GET /football/competition/stats/detail?id={competition_id}
```
- 返回: 球员统计(players_stats), **射手榜(shooters)**, 球队统计(teams_stats)
- 120次/min
- **shooters**: position, player_id, team_id, goals, penalty, assists, minutes_played
- **teams_stats**: team_id, matches, goals, shots, ball_possession, passes, fouls, etc.
- 球员可能存在转会，同一球员多行数据可按team_id合并

### ⚪ 数据同步

#### 17. 删除数据同步 — deleted
```
GET /football/deleted
```
- 最近24h内删除的数据ID (比赛/球队/球员/教练/赛事/赛季/阶段)
- 建议频次: 1-5min/次
- 返回: `{match:[id], team:[id], ...}`

## WC2026 专用配置

| 参数 | 值 | 说明 |
|------|-----|------|
| competition_id | **1** | 2026世界杯赛事ID |
| season_id (group) | **13776** | 小组赛赛季ID |
| 赛程范围 | 2026-06-11 ~ 2026-07-08 | 开幕→决赛 |
| 球队数 | 48 (12组×4队) | Nami系统中对应48个team_id |
| 小组赛 | 6/12~6/24 (48场) | 每天4场 (Nami CST日期算法下首日2场) |
| R32 | 6/25~6/28 (16场) | 每天4-6场 |
| R16 | 6/29~7/04 (8场) | 每天1-3场 |
| QF | 7/05~7/06 (4场) | 每天2场 |
| SF | 7/07 (2场) | — |
| 决赛+季军 | 7/08 (2场) | —

## 状态码大全 (2026-06更新)

### 比赛状态 (status_id)
| 码 | 含义 |
|----|------|
| 0 | 异常 (建议隐藏) |
| 1 | 未开赛 |
| 2 | 上半场 |
| 3 | 中场 |
| 4 | 下半场 |
| 5 | 加时赛 |
| 7 | 点球决战 |
| 8 | **完场** |
| 9 | 推迟 |
| 10 | 中断 |
| 11 | 腰斩 |
| 12 | 取消 |
| 13 | 待定 |

### 技术统计/事件类型 (type 字段)
| 码 | 含义 | 类别 |
|----|------|------|
| 1 | 进球 | 事件 |
| 2 | 角球 | 事件/统计 |
| 3 | 黄牌 | 事件/统计 |
| 4 | 红牌 | 事件/统计 |
| 5 | 越位 | 统计 |
| 6 | 任意球 | 统计 |
| 8 | 点球 | 事件 |
| 9 | 换人 | 事件 |
| 10 | 比赛开始 | 事件 |
| 11 | 中场 | 事件 |
| 12 | 结束 | 事件 |
| 15 | 两黄变红 | 事件 |
| 16 | 点球未进 | 事件 |
| 17 | 乌龙球 | 事件 |
| 18 | 助攻 | 事件 |
| 19 | 伤停补时 | 事件 |
| 21 | 射正 | 统计 |
| 22 | 射偏 | 统计 |
| 23 | 进攻 | 统计 |
| 24 | 危险进攻 | 统计 |
| 25 | **控球率** | 统计 (百分比) |
| 28 | VAR | 事件 |
| 37 | 射门被阻挡 | 统计 |
| 38 | 补水 | 事件 |

### 事件发生方 (position)
| 值 | 含义 |
|----|------|
| 0 | 中立 |
| 1 | 主队 |
| 2 | 客队 |

### 比分数组 (home_scores / away_scores)
下标数组 (7个元素): `[全场, 半场, 红牌, 黄牌, 角球, 加时比分, 点球比分]`
- `index[0]`: 常规时间比分
- `index[1]`: 半场比分
- `index[4]`: 角球 (-1=无数据)
- `index[5]`: 加时比分 (120min含常规时间)
- `index[6]`: 点球比分 (不含常规/加时)

### 实时数据 score 数组 (match/live 接口)
数组 (6个元素): `[matchId, status, homeScoresArr, awayScoresArr, kickoffTimestamp, note]`
- `index[2]` = 主队 [全场,半场,红牌,黄牌,角球,加时,点球]
- `index[3]` = 客队同上
- `index[4]` = 开球时间戳 (上/下半场根据status)

### 指数公司ID
| ID | 公司 |
|----|------|
| 2 | BET365 |
| 3 | 皇冠 |
| 5 | 立博 |
| 6 | 明陞 |
| 7 | 澳彩 |
| 9 | 威廉希尔 |
| 10 | 易胜博 |
| 17 | 18Bet |
| 19 | **竞彩官方** |
| 22 | 平博 |
| 136 | 马会 |

### 事件原因 (红黄牌/换人)
| 码 | 含义 |
|----|------|
| 1 | 犯规 |
| 11 | 手球犯规 |
| 14 | 阻挡进球机会 |
| 15 | 拖延时间 |
| 31 | 非体育道德行为 |
| 33 | 假摔 |
| 0 | 未知 |

## 球队ID映射

48支世界杯球队ID→名称映射见 `data/nami_team_map.json`。生成方法:
1. 从Nami拉取所有 `competition_id=1` 比赛 (6/12~7/08)
2. 从现有WC26项目读取硬编码比赛数据 (含球队名)
3. 通过 **比赛时间戳精确匹配** (Unix timestamp UTC) 建立 team_id↔team_name 关联
4. 验证: 团队名 + 分组赛48个独立team_id 全部匹配成功 ✅

## 开发注意事项

### 认证方式
- 只有 `GET + query params` 能通过认证。POST/Basic Auth/Bearer/header 方式都失败。
- 参数名: `user` 和 `secret` (小写，不含下划线)

### 时区陷阱
- `schedule/diary` 的 `date` 参数使用 **CST (UTC+8)**。查询 `20260612` 会返回北京时间6月12日03:00~次日03:00 (即UTC 6/11 19:00 ~ 6/12 19:00) 的比赛。
- 返回的 `match_time` 是 **UTC** 时间戳。前端格式化时注意。

### 数据更新策略
- 列表接口: 首次用 `id` 循环全量 → 记录最大 `updated_at` → 后续用 `time` (updated_at+1) 增量更新
- 增量更新: 1min/次, 用 `time` 参数查询 (可返回超过limit的数据量，因同一时间多数据同步返回)
- 实时: match/live 2s/次, odds/live 3s/次
- 补漏: live/history, odds/history, trend/detail 用于查缺补漏

### 不可用的端点
以下端点存在且在文档中，但账号套餐无权访问 (返回"产品权限受限"):
- `team/list`, `player/list`, `season/list`, `league/list`, `season/info`

### Vercel 代理设计模式
- WSGI 函数 `nami_config_endpoint(environ)` 返回 `(body_bytes_list, headers_list)` 元组
- 不使用 `start_response` 参数 (index.py 负责调用)
- 所有 JSON 响应通过 `_respond(payload)` 辅助函数生成
