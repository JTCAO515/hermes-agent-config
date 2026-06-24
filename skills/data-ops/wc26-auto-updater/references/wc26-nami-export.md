# 纳米数据 WC2026 全量导出操作记录

> 导出时间：2026-06-15
> 试用期：~2026-06-22 到期

## 为什么

纳米数据仅7天试用期。到期后实时 API 将不可用。必须在到期前将 WC2026 所有数据导出到本地 SQLite + JSON，供后续离线使用。

## 导出结果

| 项目 | 值 |
|------|-----|
| 球队 | 48 队（100% 映射） |
| 比赛 | 101 场（含12场已赛） |
| 积分榜 | 13 组（全部12组+汇总） |
| 比赛详情 | 12 场（事件+技术统计） |

## 脚本

```bash
# v1 — 基础版（比分匹配法，仅10队映射成功）
cd ~/projects/WC26Nami && python3 data/nami_export.py

# v2 — 精准版（group编号法，48队映射成功）
cd ~/projects/WC26Nami && python3 data/nami_export_v2.py
```

## 存储位置

两个项目 `data/` 目录下各有一份：
- `nami_archive.json` — 完整 JSON 备份 (249KB)
- `nami_wc2026.db` — SQLite 数据库

## 数据库结构

```sql
teams (team_id, name, group_name)          -- 48行
matches (match_id, home_team_id, away_team_id, home_team, away_team, 
         home_score, away_score, status_id, match_time, group_letter, 
         group_num, round_num, stage_id, venue_id)  -- 101行
standings (competition_id, group_num, team_id, points, position, 
           total, won, draw, loss, goals, goals_against, goal_diff)  -- 60行
match_events (match_id, type, position, time, second, player_name, ...) -- 36行（进球）
match_stats (match_id, type, home_value, away_value)  -- 120行（12场x10组技统）
export_meta (key, value)  -- 元信息
```

## 关键发现：真实赛程 vs 模拟赛程

Nami 数据暴露了一个重大问题：**模拟生成的赛程对阵与真实 WC2026 不同。**

### 分组正确
48支队在12个组内的分布是正确的（Group A=Mexico/South Africa/Korea Republic/Czechia 等）。

### 对阵不同
同一个组内，Nami 的配对与模拟不同。例如 Group A：
- **模拟：** Mexico vs South Africa, Korea Republic vs Czechia
- **真实(Nami)：** Mexico vs Czechia, South Africa vs Korea Republic

这不是队名映射错误（team_id→分组→队名 三条链路独立验证一致），而是真实的赛程编排不同。

### 影响
- 前端显示的积分榜和排名是正确的（基于真实赛果）
- 但赛程表上的具体对手配对是错的
- 后续需要以 Nami 真实对阵重构 SCHEDULE，不能继续用模拟的配对

## 端点可用性记录

| 端点 | 状态 | 说明 |
|------|------|------|
| schedule/diary | ✅ 可用 | 按日期查，返回所有运动比赛 |
| competition/table/detail | ✅ 可用 | id=1 返回 WC2026 13组积分榜 |
| match/live/history | ✅ 可用 | 已赛比赛详细事件+技统 |
| match/live | ✅ 可用 | 实时比赛数据 |
| competition/schedule/list | ❌ 不可用 | 返回"url未授权访问" |
| football/competition/schedule/list | ❌ 不可用 | 同上 |
| team/list | ❌ 不可用 | 产品权限受限 |

## 使用时注意

- 导出是 JSON + SQLite 双格式，后续离线使用优先读 SQLite
- Nami 实时数据（schedule/diary）每天会更新新的已赛比赛，过期后需手动添加
- 平局比分（如 1-1）在 schedule/diary 中可识别
- 但 schedule/diary 数据量很大（含所有运动比赛），需要客户端过滤 competition_id=1
