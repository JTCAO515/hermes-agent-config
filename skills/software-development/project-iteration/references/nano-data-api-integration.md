# 纳米数据 API v5 接入记录

> 最后更新: 2026-06-15 | 项目: WC26Nami | 迭代: v6.0.0-v6.0.1

## 一、API 基础

| 项目 | 值 |
|------|-----|
| 基础 URL | `https://open.sportnanoapi.com/api/v5` |
| API 版本 | v5 (5.0.251204) |
| 认证方式 | **Query params**: `user` + `secret` |
| 响应格式 | `{code: 0, results: ..., query: {total, type}}` |
| 限速 | 1000次/分钟/IP |
| WebSocket | `wss://s.sportnanoapi.com:443` (MQTT over WebSocket) |

### 认证

❌ 以下方式不工作：
- `Authorization: Basic base64(user:secret)`
- `Authorization: Bearer <secret>`
- `X-NaMi-ACCESSKEY` / `X-NaMi-APPSECRET` headers
- POST JSON body

✅ **唯一有效方式**:
```bash
curl "https://open.sportnanoapi.com/api/v5/football/match/schedule/diary?user=USER&secret=SECRET&date=20260615"
```

### 3种错误码快速诊断

| 错误 | 含义 | 解决 |
|------|------|------|
| `产品权限受限` | 认证通过，套餐没激活该产品 | 找用户激活 |
| `url未授权访问` | 路径不存在或URL级别禁止 | 查路径/套餐范围 |
| `用户名或密钥错误` | 凭据或认证方式不对 | 换query params |

## 二、已验证的工作端点

### 赛程 / 实时

| 端点 | 请求频率 | 说明 | 状态 |
|------|---------|------|:----:|
| `/football/match/schedule/diary` | 当天10min/次, 未来30min/次 | **按日期查赛程赛果**(前后30天) | ✅ |
| `/football/match/live` | 2s/次 | 最近120min实时比赛+事件+统计+文字直播 | ✅ |
| `/football/match/live/history` | 120次/min | 历史比赛完整统计(30天), 查缺补漏用 | ✅ |

### 单场比赛详情

| 端点 | 限制 | 说明 | 状态 |
|------|------|------|:----:|
| `/football/match/analysis` | 前30天, 60次/min | 历史交锋/近期战绩/进球分布 | ✅ |
| `/football/match/trend/detail` | 前30天, 120次/min | 主客队趋势(按分钟) | ✅ |
| `/football/match/lineup/detail` | 前30天, 120次/min | 阵容(阵型/球员坐标/评分) | ✅ |
| `/football/match/team_stats/detail` | 前30天, 120次/min | 历史球队统计数据 | ✅ |
| `/football/match/player_stats/detail` | 前30天, 120次/min | 历史球员统计数据 | ✅ |
| `/football/match/player_stats/list` | 1min/次 | 实时球员统计变动(120s内) | ✅ |

### 赛事数据

| 端点 | 限制 | 说明 | 状态 |
|------|------|------|:----:|
| `/football/competition/table/detail` | 120次/min | **积分榜**(id=competition_id), 含分组/升降级 | ✅ |
| `/football/competition/stats/detail` | 120次/min | **赛事统计**(球员统计+射手榜+球队统计) | ✅ |
| `/football/competition/schedule/list` | — | 赛事完整赛程 | ✅ |
| `/football/deleted` | 1-5min/次 | 24h内删除数据同步 | ✅ |
| `/football/match/lineup/update` | 10s/次 | 阵容变动通知 | ✅ |

### 赔率/指数

| 端点 | 请求频率 | 说明 | 状态 |
|------|---------|------|:----:|
| `/football/odds/live` | 3s/次 | **实时赔率**(亚盘/欧赔/大小球/角球) | ✅ |
| `/football/odds/history` | 120次/min | 单场赔率历史(初盘→即时→滚球) | ✅ |
| `/football/odds/update` | 3s/次 | 赔率更新清单(比赛+公司ID) | ✅ |

### 不存在的端点（不要用）

```
football/season/list → 产品权限受限（正确路径但无权限）
football/team/list → 同上
football/league/list → url未授权访问（路径不存在）
football/match/list → url未授权访问
football/live/list → url未授权访问
football/odds/compare → url未授权访问
```

## 三、WC2026 配置

| 参数 | 值 |
|------|-----|
| competition_id | 1 |
| season_id (分组赛) | 13776 |
| 赛程范围 | 2026-06-08 ~ 2026-07-08 |
| 比赛总数(Nami数据) | 96场 (非104, 差异可能是数据源差异) |

### 团队ID映射

通过**时间交叉比对**从 Nami 的 team_id → 项目中的 team_name (48支球队)。

方法: 对 Nami `schedule/diary` 的比赛时间戳 与 WC26项目 `wc2026_matches.json` 的 kickoff ISO时间做逐场匹配 → 建立 `{nami_team_id: team_name}` 映射。

结果: `/home/ubuntu/projects/WC26Nami/data/nami_team_map.json`

### CST日期偏移

`schedule/diary` 的 `date` 参数使用 **中国标准时间(CST, UTC+8)** 作为日切点:
- `date=20260612` → 2026-06-11 16:00:00Z ~ 2026-06-12 15:59:59Z
- 查询时应比UTC日期早一天

Proxy中 `_today()` 实现:
```python
from datetime import datetime, timezone, timedelta
dt = datetime.now(timezone.utc) + timedelta(hours=8)
return dt.strftime("%Y%m%d")
```

## 四、状态码表

### 比赛状态

| code | 描述 |
|:----:|------|
| 0 | 异常(腰斩/取消, 建议隐藏) |
| 1 | 未开赛 |
| 2 | 上半场 |
| 3 | 中场 |
| 4 | 下半场 |
| 5 | 加时赛 |
| 6 | 加时赛(弃用) |
| 7 | 点球决战 |
| 8 | **完场** |
| 9 | 推迟 |
| 10 | 中断 |
| 11 | 腰斩 |
| 12 | 取消 |
| 13 | 待定 |

### 技术统计事件类型

| code | 描述 | code | 描述 |
|:----:|------|:----:|------|
| 1 | 进球 | 2 | 角球 |
| 3 | 黄牌 | 4 | 红牌 |
| 5 | 越位 | 8 | 点球 |
| 9 | 换人 | 15 | 两黄变红 |
| 16 | 点球未进 | 17 | 乌龙球 |
| 18 | 助攻 | 21 | 射正 |
| 22 | 射偏 | 23 | 进攻 |
| 24 | 危险进攻 | 25 | 控球率 |
| 28 | VAR | 37 | 射门被阻挡 |

### 比分数组结构

`home_scores` / `away_scores` 数组 `[6个元素]`:
```
[0]: 常规时间比分
[1]: 半场比分
[2]: 红牌
[3]: 黄牌
[4]: 角球(-1表示无数据)
[5]: 加时比分(加时赛才有)
[6]: 点球比分(点球大战才有)
```

## 五、Python 客户端模式（Vercel stdlib-only）

### 核心模式

```python
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

class ApiClient:
    def _request(self, endpoint: str, params: dict | None = None) -> dict:
        query = {"user": self.username, "secret": self.secret}
        if params:
            query.update(params)
        url = f"{self.base_url}/{endpoint}?{urlencode(sorted(query.items()))}"

        req = Request(url, method="GET")
        req.add_header("Accept", "application/json")
        resp = urlopen(req, timeout=self.timeout)
        return json.loads(resp.read().decode("utf-8"))
```

### 查询参数构建注意

- `urlencode(sorted(query.items()))` — 参数排序确保缓存key一致
- params 中的 `None` 值需要用 `{k: str(v) for k, v in kwargs.items() if v is not None}` 过滤
- 所有参数转为 `str()` 类型

## 六、Vercel WSGI 代理子模块模式

### 架构

```
api/index.py (main WSGI app)
  └── nami_config_endpoint(environ) → returns (body, headers) or None
      └── _respond(payload) → ([body_bytes], [headers])
```

### 返回值约定

子代理模块返回 `(body_bytes_list, headers_list)` 元组，由主 WSGI handler 调用 `start_response("200 OK", headers)`:
```python
# index.py
result = nami_config_endpoint(environ)
if result is not None:
    body, headers = result
    start_response("200 OK", headers)
    return body
```

### 子模块实现

```python
def _respond(payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return [body], [("Content-Type", "application/json; charset=utf-8")]

def nami_config_endpoint(environ):
    path = environ.get("PATH_INFO", "/")
    if not path.startswith("/api/nami/"):
        return None
    ep = path[len("/api/nami/"):]
    if ep == "health":
        return _respond(health_check())
    ...
```

## 七、WC26Nami 代码架构

```
WC26Nami/
├── data/
│   ├── nami_client.py       — HTTP客户端 (stdlib-only)
│   ├── nami_team_map.json   — 48支球队 ID→名称映射
│   └── wc2026_*             — 原有硬编码数据(待替换)
├── api/
│   ├── index.py             — WSGI主路由(注册nami路由)
│   └── nami_proxy.py        — 纳米数据代理(14+个端点)
└── web/                     — 前端
```

### 代理端点汇总

```
通用数据:
  /api/nami/health, schedule, live, analysis, trend, lineup,
  team-stats, player-stats, player-stats-live, match-history,
  lineup-updates, deleted

赛事数据:
  /api/nami/competition/schedule, competition/table, competition/stats

赔率:
  /api/nami/odds/live, odds/history, odds/update

WC2026快捷:
  /api/nami/wc/schedule, live, team-map, range, standings, stats

管理:
  /api/nami/cache/clear (POST)
```

## 八、常用测试命令

```bash
# 赛程
curl -s "https://open.sportnanoapi.com/api/v5/football/match/schedule/diary?user=naofpmibbn&secret=<SECRET>&date=20260615" | python3 -m json.tool

# 积分榜(世界杯)
curl -s "https://open.sportnanoapi.com/api/v5/football/competition/table/detail?user=naofpmibbn&secret=<SECRET>&id=1" | python3 -m json.tool

# 射手榜
curl -s "https://open.sportnanoapi.com/api/v5/football/competition/stats/detail?user=naofpmibbn&secret=<SECRET>&id=1" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f\"#{s['position']} Player {s['player_id']}: {s['goals']}g\") for s in d.get('results',{}).get('shooters',[])]"
```

## 九、中继代理服务器（Vercel IP 白名单绕过）

### 问题

Vercel Serverless 函数使用 AWS/GCP 动态 IP，无法加入 Nami API IP 白名单。从 Vercel 访问 Nami API 均返回 `{"err": "ip未授权访问"}`。

### 架构

```
Vercel (动态IP)
  ↓ HTTP → http://64.176.82.81:8080/api/v5/...
Vultr 服务器 64.176.82.81 (端口8080, 纳米白名单已加)
  ↓ HTTP + user+secret
纳米数据 API (open.sportnanoapi.com)
```

**⚠️ 拓扑更正:**
- **实际中继** 运行在 Hermes agent 所在的 **Vultr 新加坡** (64.176.82.81)。此IP已在纳米数据API白名单中，可直接从本机curl纳米API。
- **之前的 122.51.121.116**（阿里云）是另一台不相关的服务器，中继从未在那台运行过。
- **端口 8080 被 Vultr 云防火墙阻断** — Vultr 默认只开放 22/8000/5055/8502 四个端口。`iptables` 规则无法覆盖云防火墙。需要登录 `my.vultr.com` → Firewall 控制台放行才能对外暴露。**Docker 端口映射也不能穿透云防火墙**——Docker 容器暴露的端口在 OS 层 bind 到了 0.0.0.0 但 Vultr 云防火墙在 VM 外拒绝入站 SYN，所以连 Docker 的服务也会被挡。**例外：** 如果在创建 Vultr 云防火墙规则时已经放行了某个端口（如 5055），Docker 映射到该端口就能通。
- **Vercel 端配置：** `NAMI_RELAY=http://64.176.82.81:8080` 作为 Vercel 环境变量

### 中继文件

`~/projects/WC26Nami/nami_relay.py` — 约80行纯 stdlib

- HTTP Server 监听 `0.0.0.0:8080`
- 只转发 `/api/v5/*` 路径
- 认证凭据硬编码（服务器本地运行安全）
- 30s 内存 LRU 缓存
- CORS 全开（Vercel→服务器跨域）
- log_message 静默（不刷崩溃日志）

### systemd 服务

```
/etc/systemd/system/nami-relay.service
```

### Vultr 云防火墙诊断

当 relay 端口无法从外网访问时，按以下步骤排查：

| 步骤 | 命令 | 预期结果 | 故障诊断 |
|------|------|---------|---------|
| 1. 检查relay进程 | `systemctl status nami-relay` | active (running) | 未运行 → 启动服务 |
| 2. 本地回环测试 | `curl -s --noproxy '*' http://127.0.0.1:8080/health` | `{"ok":1,...}` 1ms响应 | 失败 → relay进程挂了 |
| 3. 本机公网IP测试 | `curl -s --connect-timeout 3 http://64.176.82.81:8080/health` | hang → 超时 | **Vultr云防火墙阻断** |
| 4. 检查开放端口 | `ss -tlnp \| grep 8080` | LISTEN | 进程在监听，但云防火墙在VM外拦截 |
| 5. 确认开放端口 | `curl -s http://64.176.82.81:5055/health` | 应返回内容 | 5055已知开放(验证云防火墙规则) |

**关键发现：** Vultr 云防火墙在 VM 实例外部。`ss` 显示端口 LISTEN 不代表外网可访问。必须登录 `my.vultr.com` → Firewall 控制台添加规则。

**绕过方案 (如不开放端口)：**
- **使用其他允许的端口** — 将 relay 改为 8000（已知开放，但可能被其他服务占用）
- **使用 SSH 隧道转发** — `ssh -L 8080:localhost:8080 user@64.176.82.81 -N`（不暴露端口，需SSH保持连接）
- **使用 bore/ngrok/boringtun** — 内网穿透工具（需验证可用性）
- **Hermes cron 定时推送** — 不需要实时 API 时，用 cron 拉取数据写到静态 JSON

### ⚡ 连通性探测与快速回退（v6.1.3+）

**问题：** 阿里云安全组拦截 8080 端口时，relay 的每个 TCP SYN 都被丢弃。Python `urllib.request.urlopen(url, timeout=10)` 会等满 10s 的超时，因为 TCP 层在超时前会重试多次（1s+3s+7s）。导致 `live-broadcast` 端点从 Vercel 调用耗时 12s+。

**方案：** 使用 relay 前做 socket 级别连通性探测：

```python
import socket
import urllib.parse

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
    # relay 可达 → 使用中继地址
    base_raw = relay_url.rstrip("/") + "/api/v5"
    auth_str = ""
else:
    # relay 不通 → 直接返回空数据（回退直连也会超时）
    return {"code": 0, "matches": [], "upcoming": [],
            "note": "数据中继不可用", "relay_status": "unreachable"}
```

**为什么不像普通 API 故障那样回退到直连？** Vercel 的 IP 段未被纳米数据白名单，纳米 API 在网络层丢弃来自非白名单 IP 的 SYN 包，产生同样的 TCP 超时问题。回退直连只是把 12s 失败变成 8s 失败，不值得。

**端到端诊断：**
1. `curl http://127.0.0.1:8080/health` → 1ms 响应 → relay 进程正常
2. `curl http://<公网IP>:8080/health --connect-timeout 3` → hang 2s → 安全组拦截
3. `curl https://wc26nami.jtcao.space/api/nami/live-broadcast` → 耗时 6-12s → relay 不可达
4. 响应体 `relay_status: "unreachable"` → 端口未开放；`relay_status: "ok"` → 中继正常工作

### Vercel 侧配置

在 Vercel Dashboard → WC26Nami → Settings → Environment Variables 添加：

| Name | Value |
|------|-------|
| `NAMI_RELAY` | `http://122.51.121.116:8080` |

nami_proxy.py 中的代码支持：
```python
relay = os.environ.get("NAMI_RELAY", "")
if relay and relay.startswith("http"):
    base_raw = relay.rstrip("/")
    auth_str = ""  # 中继自带认证
```

**改动文件：** `api/nami_proxy.py`（新增 `import os` + 中继检测逻辑在 live-broadcast handler 内）

### 验证

```bash
curl -s --noproxy '*' http://127.0.0.1:8080/health
# → {"ok": 1, "base": "https://open.sportnanoapi.com/api/v5", "user": "naofpmibbn", "cache": N}

curl -s --noproxy '*' "http://127.0.0.1:8080/api/v5/football/match/live"
# → {"code": 0, "results": [...]}
```

注意：服务器上 `http_proxy` 环境变量可能导致 curl 测试走代理而非直连中继。必须用 `--noproxy '*'` 绕过。

1. **文档解析** — API文档可能以 DOCX/PDF 图片形式由用户提供，需用 python-docx 或 OCR 提取
2. **时间偏移** — `schedule/diary` 日期参数用 CST (UTC+8) 而非 UTC
3. **认证格式** — v5 API 唯一有效认证是 query params `user` + `secret`
4. **积分榜端点** — 用 `competition/table/detail?id=X` 而非 `season/standings`
5. **Team ID映射** — 无 `team/list` 时，可用时间交叉比对法从多日赛程匹配队名
6. **WSGI子模块** — 不能调 `start_response`，应返回 `(body, headers)` 由主 handler 处理
7. **Nami 比赛数 vs 项目预期** — Nami返回96场世界杯比赛，项目预期104场(差异可能是数据源差异)
