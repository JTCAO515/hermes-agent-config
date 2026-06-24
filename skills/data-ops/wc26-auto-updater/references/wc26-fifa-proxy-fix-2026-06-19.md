# FIFA API 代理修复记录 — 2026-06-19

## 背景

`api.fifa.com` 从 2026年6月中旬起，从中国 VPS 直连被 Cloudflare 拦截。
- **阶段 1 (~6月16日)**: 直连可用，只需加 `Origin`/`Referer` headers
- **阶段 2 (6月17-18日)**: 间歇性 SSL 超时/EOF，重试有时成功
- **阶段 3 (6月19日起)**: 完全封锁，直连永远超时

## 修复方案

通过 Xray HTTP 代理（127.0.0.1:10809）走新加坡中继节点。

### 代理配置

```
Xray VLESS+REALITY
中继: Vultr Singapore (64.176.82.81)
分流: fifa.com 走代理（通过 export https_proxy 实现）
HTTP proxy: 127.0.0.1:10809
SOCKS5: 127.0.0.1:10808
```

### 脚本修改

`fifa_sync_wrapper.sh` 在 sync 命令前添加:
```bash
export https_proxy=http://127.0.0.1:10809
export http_proxy=http://127.0.0.1:10809
python3 data/fifa_sync.py
```

## 并发问题

FIFA API 返回 28 场已赛，但本地数据有 36 场。差异原因是 `update_results.py` 模拟了 Nami 来源的额外 8 场结果，FIFA API 尚未确认。同步逻辑正确（只更新匹配到的比赛）。

## 代理下 timeout 不足的静默失败（2026-06-19 追加）

### 问题
`fifa_sync.py` 的 `urlopen(req, timeout=15)` 在直连时够用，但通过 HTTP 代理走新加坡中继时，SSL 握手阶段可能耗时超过 15 秒：

```
TimeoutError: _ssl.c:999: The handshake operation timed out
```

后果：Python 脚本异常退出（exit 1）→ `fifa_sync_wrapper.sh` 的 `set -e` + `tee` 管道 → wrapper 继续执行 `git diff` → 无变更 → STDOUT 显示"✓ 无新赛果" → cron job 认为一切正常。**这是一个静默失败。**

### 修复
`fifa_sync.py` 第 36 行：`timeout=15` → `timeout=30`

### 排查方法
如果 cron 日志显示 `The handshake operation timed out`：
1. 先测代理连通性：`curl -s --proxy http://127.0.0.1:10809 --max-time 15 'https://api.fifa.com/api/v3/calendar/matches?language=en&count=1&idSeason=285023' -o /dev/null -w '%{http_code}\n'`
2. 如果代理正常但 `urlopen` 仍超时，调大 timeout
3. 验证修复：修复后 `python3 data/fifa_sync.py` 应在 4-7 秒内返回，无超时异常

### 教训
通过代理的 SSL 握手延迟不可忽略。脚本中所有通过代理调用的 `urlopen` 应使用 ≥30 秒 timeout，或使用 `retry` 模式（首次 15s → 重试 30s → 重试 60s）。

## 同步管道验证

```bash
# 通过代理测试
curl -s --proxy http://127.0.0.1:10809 --max-time 15 \
  'https://api.fifa.com/api/v3/calendar/matches?language=en&count=104&idSeason=285023' \
  -A 'Mozilla/5.0' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Results: {len(d.get(\"Results\",[]))}')"
# → Results: 104
```

## 被修复的 cron 任务清单

| Cron | 类型 | 旧路径 | 新路径 |
|------|------|--------|--------|
| WC26 FIFA 赛果自动同步(每2h) | 系统 crontab | `world-cup-edge-lab/data/fifa_sync_wrapper.sh` | `WC26-Main/data/fifa_sync_wrapper.sh` |
| wc26-daily-update (10:00) | Hermes cron | `workdir=world-cup-edge-lab` | `workdir=WC26-Main` |
| WC26 每日赛果自动更新 (23:30) | Hermes cron | 同上 | 同上 |
| WC26 赛时赛果更新 (13/16/19/22:00) | Hermes cron ×4 | 同上 | 同上 |
| WC26Nami 每日数据更新 (13:00) | Hermes cron | `workdir=WC26Nami` | `workdir=WC26-Nami` |
