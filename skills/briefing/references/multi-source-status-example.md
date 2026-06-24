# Multi-Source Status Compilation — 实操案例

> 记录 2026-06-14 "汇报" 会话的完整数据源与操作流程。
> 作为 Phase 0b 无 gbrain 环境下的参考示例。

## 数据源清单

| 序号 | 数据源 | 工具/命令 | 获取内容 |
|------|--------|-----------|----------|
| 1 | 活跃会话 | `session_search()` 无参数 | 最新3个会话的 title/preview/message_count |
| 2 | 定时任务 | `cronjob(action='list')` | 4个 cron job 的名称、调度、enabled、最近执行、next_run、delivery_error |
| 3 | 项目目录 | `ls ~/projects/` | 全部项目清单 |
| 4 | 迭代日志 | `read_file(.../ITERATION_LOG.md)` | 各项目的最近迭代记录 |
| 5 | PLAN.md | `read_file(.../PLAN.md)` | WC26 的迭代路线图 |
| 6 | Git 日志 | `git log --oneline -3` | 最近3次 commit 信息 |
| 7 | Git 状态 | `git status --short` | 未暂存/未提交的变更 |
| 8 | 技能状态 | `skill_view(name)` | 确认 last30days-skill 已安装可调用 |
| 9 | 部署状态 | `ls -la web/` | 确认 WC26 前端文件存在 |

## 操作流程

### Step 1: 全局扫描（3条命令并行）
```
session_search()                  → 活跃会话
cronjob(action='list')            → 定时任务
ls ~/projects/                    → 项目清单
```

### Step 2: 关键项目深读
对每个活跃项目执行：
```
read_file(.../ITERATION_LOG.md)   → 最近迭代记录
read_file(.../PLAN.md)            → 路线图
git log --oneline -3              → 近期变更
git status --short                → 未提交变更
```

### Step 3: 构建汇报
按 Phase 0b 格式组织。关键判断：
- **项目活动期**：ITERATION_LOG 最近更新时间 + git log 最近 commit → 判断活跃/冻结
- **任务即将执行**：cron next_run_at 在今天内 → 标注"今天X点首次执行"
- **项目状态**：git status 干净 + 已 git push + Vercel 可访问 → ✅ 正常
- **错误报警**：cron last_delivery_error 有内容 → ⚠️ 标注

### Step 4: 开放式提问
汇报结尾附 3-5 个选择性问题，让用户可以快速决定下一步方向。

## 典型问题

- **项目暂停超2周**：Query "要不要继续迭代？"
- **Cron 首次执行在即**：Query "要做什么准备？"
- **恋爱/元宝会话在活跃列表**：Query "有进展需要调整策略？"
