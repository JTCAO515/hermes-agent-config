# WC26 真实赛果同步指南

> 基于 2026-06-14 手动同步实操记录。

## 步骤总览

```
FIFA.com web_extract → 解析比分 → 匹配本地比赛 → 写入双格式result → 重算积分榜 → 重生成预测 → 提交
```

## Step 1: 从 FIFA 拉取数据

```python
from hermes_tools import web_extract
result = web_extract(url="https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures")
# result.content 包含 markdown 格式的赛程表
```

返回内容结构示例：
```
| Date | Group | Home | Score | Away | Venue |
| Thu 11 Jun | A | Mexico | 2–0 | South Africa | Mexico City Stadium |
| Fri 12 Jun | A | Korea Republic | 2–1 | Czechia | Guadalajara |
```

关键观察：
- **比分使用 en-dash** `–` (U+2013)，不是 ASCII 连字符 `-`
- 已结束比赛显示比分 `"2–0"`，未赛显示时间 `"17:00"`
- 区分已赛/未赛：检查分数是否包含 `–`
- FIFA 主页使用 `"Korea Republic"`（与数据的 team name 一致）
- FIFA 使用 `"Bosnia and Herzegovina"`，数据集使用 `"Bosnia and Herz."` → 需要映射

## Step 2: 解析比分

```python
def parse_fifa_score(score_str):
    """Parse FIFA score string like '2–0' to (2, 0)."""
    if '–' not in score_str:
        return None  # 未赛（显示时间）
    parts = score_str.split('–')
    return int(parts[0]), int(parts[1])
```

## Step 3: 匹配本地比赛

```python
real_results = {
    ('Mexico','South Africa'): (2, 0),
    ('Korea Republic','Czechia'): (2, 1),
    # ... 所有已赛比赛
}

for mt in matches:
    key = (mt['team_a'], mt['team_b'])
    rev_key = (mt['team_b'], mt['team_a'])
    if key in real_results:
        score = real_results[key]
        # 更新
    elif rev_key in real_results:
        score = real_results[rev_key]
        # 更新（主客场翻转）
```

**⚠️ 队名映射检查表：**
| FIFA 官方名 | 数据集名 | 差异？ |
|-------------|---------|--------|
| Korea Republic | Korea Republic | ✅ 一致 |
| Czechia | Czechia | ✅ 一致 |
| Bosnia and Herzegovina | Bosnia and Herz. | ⚠️ 缩写差异 |
| Türkiye | Türkiye | ✅ 一致 |
| Cabo Verde | Cabo Verde | ✅ 一致 |
| Côte d'Ivoire | Côte d'Ivoire | ✅ 一致 |
| IR Iran | IR Iran | ✅ 一致 |

## Step 4: 写入双格式 result

```python
for mt in matches:
    if need_update:
        mt['has_result'] = True
        mt['result'] = {
            "home_score": home_goals,
            "away_score": away_goals,
            "team_a_goals": home_goals,    # backtest.py 需要
            "team_b_goals": away_goals,    # backtest.py 需要
        }
        mt['is_simulated'] = False
```

**为什么需要双格式？**  
- `home_score`/`away_score` — `odds_engine.py` 和前端使用  
- `team_a_goals`/`team_b_goals` — `backtest.py` 的 `_actual_wdl()` 和 `_actual_total()` 使用  
- 缺任一格式，`get_predictions()` → `run_backtest()` 会直接崩

## Step 5: 重新计算积分榜

```python
groups = {}
for mt in matches:
    g = mt.get('group', '?')
    if g == '?': continue  # 跳过淘汰赛
    # 初始化/累加每个队的 pts, gf, ga, p
    # 排序: (-pts, -(gf-ga), -gf)
    
m['groups'] = [{
    'name': g,
    'teams': [{'name': t, 'played': s['p'], 'points': s['pts'], 
               'gd': s['gf']-s['ga'], 'gf': s['gf'], 'ga': s['ga']} 
              for t, s in teams]
} for g, teams in sorted(groups.items())]
```

## Step 6: 重生成预测

```python
import sys; sys.path.insert(0, '.')
import importlib
import football_predictor.wc_api
importlib.reload(football_predictor.wc_api)
from football_predictor.wc_api import get_predictions

report = get_predictions(polymarket_weight=0.3)
matches_pred = report.get('matches', [])

predictions_dict = {}
for mt in matches_pred:
    mid = mt.get('id', f'wc2026-{mt["team_a"]}-{mt["team_b"]}')
    predictions_dict[mid] = {
        'team_a': mt['team_a'],
        'team_b': mt['team_b'],
        'probabilities': mt.get('probabilities', {}),
        'expected_goals': mt.get('expected_goals', {}),
        'scoreline_probabilities': mt.get('scoreline_probabilities', {}),
        'total_goals_prob': mt.get('total_goals_prob', {}),
        'btts': mt.get('btts', {}),
        'double_chance': mt.get('double_chance', {}),
        'asian_handicap': mt.get('asian_handicap', {}),
        'over_under': mt.get('over_under', {}),
        'has_result': mt.get('has_result', False),
        'result': mt.get('result', None),
    }

m['predictions'] = predictions_dict
m['last_updated'] = datetime.now().isoformat()
Path('data/wc2026_matches.json').write_text(json.dumps(m, indent=2, ensure_ascii=False))
```

**模块 reload 是必须的**：`football_predictor.wc_api` 在 import 时读取 JSON 文件并缓存到 `WC_MATCHES` 变量。修改 JSON 后必须 `importlib.reload()` 才能让新数据生效。

## 2026-06-14 同步结果

```
8 matches synced from FIFA.com
  Group A: Mexico 2-0 South Africa | Korea Republic 2-1 Czechia
  Group B: Canada 1-1 Bosnia/Herz. | Qatar 1-1 Switzerland  
  Group C: Brazil 1-1 Morocco | Haiti 0-1 Scotland
  Group D: USA 4-1 Paraguay | Australia 2-0 Türkiye
```
