# wc2026_matches.json — 本地数据文件结构

> 用途：供 cron job、报告生成、数据校验脚本读取本地数据。
> 本文件描述 `world-cup-edge-lab/data/wc2026_matches.json` 和 `WC26Nami/data/wc2026_matches.json` 的数据结构。
>
> 区分：本文件描述**本地存储的 JSON 结构**（含预测/赔率/积分榜），而非 FIFA API v3 或 Nami API 的原始响应格式。FIFA API 原始响应见 `references/wc26-fifa-api-sync.md`。

---

## 顶层 keys

```python
{
  "competition": str,          # e.g. "World Cup 2026"
  "season": str,               # e.g. "2026"
  "notes": str,                # 任意备注
  "knockout": list | dict,     # 淘汰赛对阵结构
  "matches": [Match, ...],     # 104 场比赛（72小组 + 32淘汰）
  "last_updated": str,         # ISO 8601 timestamp, e.g. "2026-06-18T06:09:41.811246+00:00"
  "groups": [Group, ...],      # 12 个小组积分榜
  "predictions": dict,         # (全局级别, 赛事预测)
  "generated_at": str,         # Poisson 模型生成时间
  "predictions_timestamp": str,# 预测时间戳
  "data_source": str,          # e.g. "fifa_official"
}
```

---

## Match 对象

### 全部字段

| 字段 | 类型 | 说明 | 所有场次均有？ |
|------|------|------|:------------:|
| `id` | int | 唯一 ID（104 场递增） | ✅ |
| `phase` | str | `"group"` / `"R32"` / `"R16"` / `"QF"` / `"SF"` / `"3rd-Place"` / `"Final"` | ✅ |
| `group` | str | 如 `"A"`–`"L"`；淘汰赛为空字符串 | ✅ |
| `match_day` | int | 比赛日编号（1–?） | ✅ |
| `team_a` | str | **纯字符串**，非对象。FIFA 官方队名 | ✅ |
| `team_b` | str | **纯字符串**，非对象。FIFA 官方队名 | ✅ |
| `kickoff` | str | ISO 8601 datetime，如 `"2026-06-13T14:00:00Z"` | ✅ |
| `has_result` | bool | 是否有真实/模拟赛果 | ✅ |
| `result` | dict | 比分对象（见下），仅在 `has_result=true` 时有 | 仅已赛 |
| `predictions` | dict | Poisson 模型预测 | 大部分 |
| `checkpoints` | dict | 多时间点预测快照（含 `T-60m` / `T-6h` / `T-48h`） | 大部分 |
| `base_xg` | dict | 基础预期进球：`{home: float, away: float}` | 大部分 |
| `odds_snapshots` | dict | 赔率快照 | 部分 |
| `lineup_updates` | dict | 阵容更新 | 部分 |
| `injury_updates` | list | 伤病更新 | 部分 |

### `result` 对象 — 关键：双格式键名

Predictions 端和前端/quant 端读取不同格式的键名，两者**必须同时存在**：

```python
result = {
    # 前端/odds_engine 使用
    "home_score": int,          # team_a 的进球数
    "away_score": int,          # team_b 的进球数
    # backtest/quant 使用
    "team_a_goals": int,        # 与 home_score 相同
    "team_b_goals": int,        # 与 away_score 相同
}

# ⚠️ 缺失任一格式键名会静默导致对应功能失效。
#   脚本 audit_integrity.py --fix 可自动补全缺失格式。
```

### `predictions` 对象

```python
predictions = {
    "team_a_win": float,        # 百分比，如 0.45
    "draw": float,              # 百分比
    "team_b_win": float,        # 百分比
    "probs": dict,              # ⚠️ 量化端依赖的顶层 key，如 {home_win: 0.45, draw: 0.25, away_win: 0.30}
    "probabilities": dict,      # 兼容写法，与 probs 同内容
    "expected_goals": {
        "home": float,          # 主队预期进球
        "away": float,          # 客队预期进球
    },
    "checkpoints": {            # 嵌套 — 前端 T-60m 倒计时依赖
        "T-60m": { "probabilities": {...}, "generated_at": str },
        "T-6h":  { "probabilities": {...}, "generated_at": str },
        "T-48h": { "probabilities": {...}, "generated_at": str },
    },
}
```

### `checkpoints` 字段（冗余但独立）

`predictions.checkpoints` 与顶层 `checkpoints` 字段内容相同，均为多时间点预测快照。

---

## Group 对象

```python
group = {
    "name": str,                # 如 "A"–"L"
    "teams": [TeamInfo, ...],   # 48 队分散在 12 组
}

# TeamInfo 字段
team_info = {
    "name": str,                # FIFA 官方队名
    "played": int,              # 已赛场数
    "wins": int,
    "draws": int,
    "losses": int,
    "goals_for": int,
    "goals_against": int,
    "goal_diff": int,
    "points": int,
}
```

---

## 常用解析脚本

### 提取所有有赛果的比赛（用于 cron 报告）

```python
import json
with open("data/wc2026_matches.json") as f:
    data = json.load(f)

results = [
    m for m in data["matches"]
    if m.get("has_result") and m.get("result")
]

for m in sorted(results, key=lambda x: x.get("kickoff", "")):
    r = m["result"]
    d = m.get("kickoff", "")[:10]
    print(f"{d}  {m['team_a']:20s} {r['home_score']}-{r['away_score']}  {m['team_b']:20s}  {m.get('phase', '')}")
```

### 检查 predictons/checkpoints 完整性

```python
import json
with open("data/wc2026_matches.json") as f:
    data = json.load(f)

for m in data["matches"]:
    preds = m.get("predictions", {})
    if not preds.get("probs"):
        print(f"[MISSING probs] match {m['id']}: {m['team_a']} vs {m['team_b']}")
    if not preds.get("checkpoints"):
        print(f"[MISSING checkpoints] match {m['id']}: {m['team_a']} vs {m['team_b']}")
```

### 提取预测统计

```python
import json
with open("data/wc2026_matches.json") as f:
    data = json.load(f)

matches_with_preds = sum(
    1 for m in data["matches"]
    if m.get("predictions", {}).get("probs")
)
print(f"Matches with predictions: {matches_with_preds} / {len(data['matches'])}")
```

---

## 常见陷阱

1. **`team_a` / `team_b` 是字符串，不是对象。** 不要用 `.get("name")` 或 `["ShortClubName"]` — 直接 `m["team_a"]`。
2. **`result` 双格式必须一致。** `home_score` 必须等于 `team_a_goals`。`audit_integrity.py` 可校验+修复。
3. **`probs` 必须存在于 `predictions` 顶层。** 仅存 `checkpoints` 是不够的 — 量化端（portfolio/backtest/arbitrage）全部依赖 `preds.get("probs", {})`。
4. **`kickoff` 是 ISO 时间字符串。** 排序时直接用字符串比较（ISO 8601 自然顺序）。
5. **淘汰赛场次没有 `group` 字段。** `group` 为空字符串，`phase` 区分轮次。
6. **`last_updated` 每次同步都变。** 即使赛果没变，这个字段也会更新，是噪音提交的根因。
