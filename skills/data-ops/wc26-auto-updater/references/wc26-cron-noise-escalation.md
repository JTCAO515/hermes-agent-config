# WC26 Cron 噪音提交升级记录

> 2026-06-19 验证：fifa_sync_wrapper.sh 噪音提交问题持续恶化。
> 连续 3 次 cron 执行产生空提交（仅时间戳更新），且出现同分钟双发。

## 噪音提交频率时间线

### 2026-06-19 凌晨

| Commit | 时间 (UTC) | 已赛场次 | 类型 | 说明 |
|--------|-----------|---------|------|------|
| b20bfef | 00:21 | 34 | ✅ 真更新 | 数据变化 |
| 79a7833 | 02:00 | 35 | ✅ 真更新 | 34→35 场，有实际新赛果 |
| cf77447 | 02:03 | 35 | ❌ 噪音 | 3分钟后，仅 last_updated 变化 |
| b4ac9f2 | 04:00 | 35 | ❌ 噪音 | 仅时间戳 |
| 47585c4 | 04:00 | 35 | ❌ 噪音 | **同分钟双发** |

### 2026-06-20 凌晨

| Commit | 时间 (UTC) | 已赛场次 | 类型 | 说明 |
|--------|-----------|---------|------|------|
| 89513fe | 18:00 | 44 | ✅ 真更新 | 数据变化 |
| f411ec0 | 18:00 | 44 | ❌ 噪音 | 2分钟后，仅 time delta 0.7s 时间戳变化 |

### 关键指标
- **噪音率**: 4/7 ≈ 57% 的 commits 是噪音
- **峰值频率**: 04:00 同一分钟 2 次推送（依然未修复）
- **最长无实质更新**: 35 场已赛数据曾维持 6+ 小时无变化
- **噪音修复状态**: 提案的噪音过滤器和 PID 互斥锁均未实施
- **新观察**: 2026-06-21 02:00 CST 运行再次产生噪音提交（f411ec0），44场已赛数据持续 2 天无变化

## 修复优先级

| 问题 | 影响 | 优先级 |
|------|------|--------|
| 时间戳噪音提交 | 浪费 Vercel 构建配额（Hobby 计划每月100次） | 🔴 高 |
| 同分钟双发 | 双倍浪费，可能触发速率限制 | 🔴 高 |

## 推荐修复方案

### 1. 立即修复：噪音提交过滤器

在 `fifa_sync_wrapper.sh` 的 git diff 检查前插入：

```bash
# === 噪音提交过滤器：仅时间戳变化则跳过 ===
REAL_DIFF=$(git diff HEAD -- data/wc2026_matches.json | grep -v 'last_updated' | grep -c '^[-+]')
if [ "$REAL_DIFF" -le 2 ] 2>/dev/null; then
    echo "✓ 仅时间戳变化，跳过提交" | tee -a "$LOG_FILE"
    exit 0
fi
```

`--- a/...` 和 `+++ b/...` 各占 1 行（共 2 行）。如果过滤 `last_updated` 后只剩 ≤2 行 diff，说明无实际数据变化。

### 2. 立即修复：PID 互斥锁防双发

在 `fifa_sync_wrapper.sh` 脚本开头加：

```bash
LOCKFILE=/tmp/fifa_sync.lock
if ! mkdir "$LOCKFILE" 2>/dev/null; then
    echo "⚠️ 已有同步进程在运行，跳过" | tee -a "$LOG_FILE"
    exit 0
fi
trap 'rm -rf "$LOCKFILE"' EXIT
```

### 3. 排查：cron 双发根因

04:00 同一分钟内出现两个不同 hash 的 commit（`b4ac9f2` 和 `47585c4`），说明两个 fifa_sync_wrapper.sh 进程并发执行。排查：

```bash
crontab -l                              # 用户 crontab
sudo crontab -l                         # root crontab（检查是否重复）
systemctl list-timers --all             # systemd timer（检查是否叠加）
grep -r fifa_sync /var/spool/cron/      # 其他 cron 路径
```

### 4. 彻底修复：fifa_sync.py 退出码驱动

`fifa_sync.py` 已返回更新数作为退出码（`sys.exit(main() or 0)`），wrapper 可检查 `$?`：

```bash
python3 data/fifa_sync.py
UPDATED=$?
if [ "$UPDATED" -eq 0 ]; then
    echo "✓ 无新赛果，跳过提交" | tee -a "$LOG_FILE"
    exit 0
fi
```

## 监控

每次 cron 执行后可检查：

```bash
git log --oneline -5 -- data/wc2026_matches.json | head -5
```

若连续 ≥3 条记录显示相同场次数且间隔 < 2.5h，说明噪音提交仍在发生。

## 新发现：2026-06-21 — 推送竞争条件 + 退出码吞掉

### 噪音提交持续
2026-06-21 又有 2 次噪音提交（08:03 和 16:03 UTC）。两次都是纯 `last_updated` 时间戳变更——FIFA API 返回 36 场已赛，本地已录 48 场，更新数为 0。

## 2026-06-22 — 噪音提交第 8 次，修复仍未实施

### 噪音提交
Hermes cron 2026-06-22 08:07 UTC 再次触发噪音提交 commit `241bcf3`。输出模式与前 7 次完全一致：
```
📡 40 场已赛 (FIFA)
📊 更新 0 场, 当前已赛: 52 场
🔄 检测到新赛果! 共 52 场已赛
```
git diff 确认仅 `last_updated` 时间戳变化（08:00:05 → 08:07:03）。实际比分数据无任何变更（仍为 51 场有 team_a_goals/team_b_goals 的完赛结果）。

### 修复状态：仍未实施
已连续 4 天（06-19 → 06-22）共 8 次噪音提交。SKILL.md 中记录的三项修复方案均未应用至 `fifa_sync_wrapper.sh`：
1. ❌ 噪音提交过滤器（`grep -v last_updated | grep -c '^[-+]'`）
2. ❌ PID 互斥锁（`mkdir LOCKFILE`）
3. ❌ PIPESTATUS 检查（`PUSH_EXIT=${PIPESTATUS[0]}`）

**调用链：** Hermes cron → `fifa_sync_wrapper.sh` → 脚本没有噪音过滤逻辑 → 时间戳变化触发 git commit → push → Vercel 部署。每 2 小时一次空部署，Hobby 计划每月 100 次构建配额已浪费约 12 次（截至 06-22）。

### 赛果数量变化
| 日期 | 完赛比分 | 说明 |
|------|---------|------|
| 06-19 02:00 | 35 | 最后有实际新赛果的 sync |
| 06-20 18:00 | 44 | group G/H 新增 9 场 |
| 06-21 | 48 | 持续增加 |
| 06-22 | 52 | 本地累计 51 场有比分，1 场 has_result 但缺 goals |
| **06-23** | **55** | **✅噪音中断！8场真实新赛果** (Brazil 3-0 Haiti 等) |

注：FIFA API 报告 40 场已赛，本地 51/52 场——差值来自 update_results.py（模拟/补录）和 scores_no_fifa 来源，FIFA sync 不覆盖这些数据。

### Push 被拒但脚本报告 "✅ 已推送"
两次噪音提交的 git push 全部被拒绝（远程有新的提交），但 `sync.log` 显示：

```
08:03 — ! [rejected] master -> master (fetch first) ... ✅ 已推送
16:03 — ! [rejected] master -> master (fetch first) ... ✅ 已推送
```

**根因**: `fifa_sync_wrapper.sh` 的 `git push ... 2>&1 | tee -a "$LOG_FILE"` 管道吞掉了 push 的退出码。Shell 管道只保留最后一个命令（tee）的退出码，`echo "✅ 已推送"` 无条件执行。

**影响**: cron 执行者（Hermes cron / 运维）看到 "✅" 以为推送成功，但实际上数据未被部署到 Vercel。

### 修复步骤（已验证）

对于 `[rejected] master -> master (fetch first)` 错误，采用两层修复：

**第一层（大多数情况）:**
```bash
git stash
git pull --rebase origin master
git stash pop
git add data/sync.log data/update_log.json
git commit -m "chore: sync log post-rebase $(date +%Y-%m-%dT%H:%M)"
git push origin master
```

**第二层（远程 HEAD 在 rebase 和 push 之间又前进了）:**
```bash
git fetch origin
git rebase origin/master
git push origin master
```

**验证**: 2026-06-21 16:04 UTC 成功推送 `207a0c5`（`96ede8e..207a0c5 master -> master`）。

### 建议修复（wrapper 脚本）

在 `fifa_sync_wrapper.sh` 中用 PIPESTATUS 检查推送真实退出码：

```bash
git push origin master 2>&1 | tee -a "$LOG_FILE"
PUSH_EXIT=${PIPESTATUS[0]}
if [ "$PUSH_EXIT" -ne 0 ]; then
    echo "❌ 推送失败 (exit=$PUSH_EXIT)" | tee -a "$LOG_FILE"
    exit "$PUSH_EXIT"
fi
echo "✅ 已推送" | tee -a "$LOG_FILE"
```
