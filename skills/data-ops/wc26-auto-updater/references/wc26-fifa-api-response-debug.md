# FIFA API v3 Response Debugging & Field Reference

> 发现的现场调试技巧和字段格式确认，避免重复踩坑。

## 快速调试命令

### 拉取 FIFA 原始数据并打印已赛赛果

```bash
cd ~/projects/world-cup-edge-lab
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
python3 -u -c "
import json, urllib.request

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Origin': 'https://www.fifa.com',
    'Referer': 'https://www.fifa.com/',
}
req = urllib.request.Request(
    'https://api.fifa.com/api/v3/calendar/matches?idSeason=285023&count=104&language=en',
    headers=headers
)
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read())
results = data.get('Results', [])
completed = [r for r in results if r.get('MatchStatus') == 0]
print(f'Total: {len(results)}, Completed: {len(completed)}')
for r in completed:
    date = r.get('Date', '?')[:10]
    home = r.get('Home', {}).get('ShortClubName', '?')
    away = r.get('Away', {}).get('ShortClubName', '?')
    hs = r.get('HomeTeamScore', '?')
    aws = r.get('AwayTeamScore', '?')
    def desc(lst):
        if lst and isinstance(lst, list) and len(lst) > 0:
            return lst[0].get('Description', '?')
        return '?'
    group = desc(r.get('GroupName', []))
    print(f'  [{date}] {home} {hs}-{aws} {away}  ({group})')
"
```

### 对比本地 vs FIFA 数据（找不匹配的比赛）

```python
# 在 ~/projects/world-cup-edge-lab/ 下运行
import json, sys
sys.path.insert(0, 'data')
from fifa_sync import fetch_fifa, parse_completed

data = fetch_fifa()
completed = parse_completed(data)

m = json.load(open('data/wc2026_matches.json'))
matches = m['matches']

for fc in completed:
    fc_set = {fc["home_team"], fc["away_team"]}
    found = False
    for mt in matches:
        if {mt.get("team_a",""), mt.get("team_b","")} == fc_set:
            found = True
            break
    status = "✅" if found else "❌"
    print(f'{status}: {fc["home_team"]} {fc["home_score"]}-{fc["away_score"]} {fc["away_team"]}')
```

## FIFA API Response 字段确认

| JSON 路径 | 类型 | 示例值 | 说明 |
|-----------|------|--------|------|
| `MatchStatus` | int | `0` | 0=已赛, 1=未赛, 2=进行中 |
| `Home.ShortClubName` | str | `"Mexico"` | **纯字符串**，不是列表 |
| `Away.ShortClubName` | str | `"South Africa"` | 同上 |
| `Home.TeamName` | list[dict] | `[{"Locale":"en-GB","Description":"Mexico"}]` | 结构化队名，包含语言标签 |
| `HomeTeamScore` | int | `2` | 主队比分 |
| `AwayTeamScore` | int | `0` | 客队比分 |
| `Home.IdTeam` | str | `"43911"` | FIFA 内部球队 ID |
| `GroupName` | list[dict] | `[{"Locale":"en-GB","Description":"Group A"}]` | 组别信息 |
| `Date` | str | `"2026-06-11T19:00:00Z"` | ISO 8601 |
| `StageName` | list[dict] | `[{"Locale":"en-GB","Description":"Group stage"}]` | 阶段名称 |

## 常见错误及排查

### SSL: UNEXPECTED_EOF_WHILE_READING

**原因**：`http_proxy` 环境变量导致 urllib 通过代理连接 FIFA API。代理处理 SSL 证书失败。

**解法**：运行前 unset 代理变量，或用 `--noproxy '*'` 等效方式。

### 运行 fifa_sync.py 无任何输出

**原因 1**（2026-06-17）：`sys.exit(0)` 没有调用 `main()`。修正为 `sys.exit(main() or 0)`。

**原因 2**：输出被缓冲。加 `-u` 参数运行：`python3 -u data/fifa_sync.py`。

### 比赛配对被静默跳过

**原因**：本地数据集队名与 FIFA 官方名不一致。无序集合匹配 `{ta, tb} == {fc_home, fc_away}` 要求完全字符串相等。

**排查**：用 `repr(local_name)` 和 `repr(fifa_name)` 比较精确 Unicode 码点。
