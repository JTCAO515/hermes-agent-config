---
name: agent-maintenance
version: 1.1.0
version_date: 2026-06-21
description: |
  Hermes Agent 系统定期维护 — 三位一体清洁流程：
  记忆瘦身 (Memory compaction) + Profile去重 (Profile pruning) + Skills健康审计 (Skills audit)。
  不是被动修bug，而是主动防衰。
  当用户说"大扫除""清理""断舍离""瘦身""整理""维护"时触发。
trigger:
  keywords: [大扫除, 清理, 断舍离, 瘦身, 整理, 维护, maintenance, 记忆清理, 系统清洁, 记忆瘦身, 技能审计, 去重, profile整理, 记忆整理]
tags: [maintenance, cleanup, hygiene, memory, profile, skills, devops]
---
# Agent 三位一体维护流程

## 为什么要做定期维护

Hermes Agent 的 Memory 和 Profile 随时间膨胀：旧项目信息沉淀、已过时的事实残留、碎片化条目堆积。不清理会导致：
- 容量逼近上限（默认 2,200 chars for memory, 1,375 for profile，但实际值在 `config.yaml` 的 `memory.memory_char_limit` / `memory.user_char_limit` 中配置，**始终以 config.yaml 为准**）
- 关键信息被噪音淹没
- 每次会话都加载无用的旧数据

> ⚠️ 注意：memory_tool.py 代码中的默认值（2200/1375）不一定是实际生效的限制。必须在 `config.yaml` 中查 `memory.memory_char_limit` 和 `memory.user_char_limit`。当前生产环境值为 **4400/2750**。

## 维护三步骤

### Step 1: Memory 瘦身

**目标**：删除过期/不重要的记忆条目，合并相关的碎片，释放空间。

**检查清单**：
- [ ] 已完成的项目状态（VisePanda v3.0.1 已发布 → 只要全局信息，不要具体迭代日志）
- [ ] 已配置好的环境变量（配好了就不用每天记）
- [ ] 已被 skill 覆盖的知识（Vercel Python deployment → 有 vercel-python-deployment skill）
- [ ] 太基础的提醒（"每次修复后要git push" → 太明显不需要记）
- [ ] 可合并的条目（项目迭代偏好 + Vercel网络问题 → 一条搞定）

**判断标准**：这条信息如果6个月后用不上，就删。如果2条分开记但总是一起用，就合并。

**操作方式**：用 `memory` tool 的 `remove` 删除无用条目，`replace` 合并同类项。

### Step 2: Profile 去重 + 跨Agent画像

**目标**：压缩 User Profile，减少冗余。当用户要求"写一个我的记忆/画像给别的AI agent用"时，画像是写人的**工作风格和沟通习惯**，不是写项目详情。

**检查清单**：
- [ ] 把分散的多条合并为1-2条大的聚合条目
- [ ] 删除被合并后多余的旧条目
- [ ] 更新过时的事实（已见5天 → 认识3个月）
- [ ] 删除被 memory 覆盖的重复信息
- [ ] 合并个人背景（姓名+背景+项目 放一条）

**判断标准**：8-10条精品条目 > 14-15条碎片条目。每条都应该回答"这个信息会影响每次交互的行为"。

**操作方式**：`memory` tool → `target: "user"` 做 replace/remove。

#### ⚠️ 跨Agent画像写作（教训记录）

用户说"给别的AI agent写我的memory"时，**不要写项目拓扑**。其他AI需要知道的是：
- **工作风格**：指令解码（"继续"=直接做，"为什么卡住了"=给修复方案）
- **沟通习惯**：极简指令、先执行再汇报、并行优先
- **不喜欢什么**：长篇报告、连环追问、GUI教学、技术术语
- **汇报纪律**：git push后必须微信通知

项目信息一句带过即可。**典型错误**：写了36城知识库、SSE流式架构、Vercel部署 → 用户说"不是的，我要的是我这个人"。

**正确做法**：以"其他AI agent如何跟这个人配合工作"为中心。告诉AI：这个人的指令怎么解码、什么节奏、什么绝对不能做。

### Step 3: Skills 健康审计

**目标**：发现并修复破损、过时、描述为空的 skill。

**检查清单**：
- [ ] 遍历 `skills_list`，找 description 为空或异常的 skill
- [ ] 用 `skill_view` 检查可疑 skill 的内容
- [ ] 修复问题：
  - 空 description → 补上
  - content开头是"好的，这是根据您提供的…" → 这是AI生成摘要，不是真正的skill定义，需要重写
  - 缺失 trigger keywords → 补上
- [ ] 记录需要人工判断的问题（如：内容是否仍需要保留）

**判断标准**：description为空 = 破损。content以AI摘要开头 = 半成品。两者都修。

**操作方式**：`skill_manage` → `edit` 完整重写，或 `patch` 局部修复。

## 检查边界

- ❌ 不要修改 core system skills（hermes-agent, soul-audit 等）
- ❌ 不要删除 user 明确安装的 skill（即使不常用）
- ⚠️ 发现技能重叠只记录不合并（由 curator 做规模化合并）

## 典型输出格式

```
## 🧹 维护报告

### Memory: XX% → XX% ✅
- 🗑️ 删除: X条 (原因)
- 🔗 合并: X条 (合并成一条)
- **结果**: N条→M条, 释放N字符

### Profile: XX% → XX% ✅
- 🔗 合并: N条背景信息
- 🗑️ 删除: X条 (原因)
- **结果**: N条→M条

### Skills: 发现X处问题 ⚠️
- skill-A: description为空, 已修复
- skill-B: content是AI摘要, 已重写
```

## PilotDeck 增强：记忆推理链

从 PilotDeck 借鉴的实践 — 存储记忆时附带推理链，提高检索关联性。

**为什么需要推理链：**
- 传统记忆只存事实（"服务器是腾讯云122.51.121.116"），不存"为什么这个值得记"
- 推理链帮 LLM 快速判断"这条记忆和当前任务有没有关系"

**记忆条目格式规范：**

每条记忆应包含两部分：
```
[事实描述] ... 【→推理: 这条信息为什么重要, 什么时候会用到】
```

**分类标签前缀：**
```
[环境] — 系统配置、API端点、工具路径
[规则] — 用户明确要求的行为准则
[规则-HARD] — 不可违背的硬规则
[用户] — 用户个人背景信息
[项目] — 项目状态、目录、URL
[工具] — 常见坑、workaround
[L1索引] — 第一行：全局导航索引
```

**示例：**
```
[环境] 生图=Seedream 5.0(0.22元/张）. 【→推理: 火山引擎是默认图像服务, 报价敏感】
[规则-HARD] 每次推送必须WeChat汇报. 【→推理: 用户通过微信跟踪进度, 跳过=失职】
```

## PilotDeck 增强：Dream Mode + Always-on Cron 维护

超越手动维护 — 设置自动 cron 定期执行记忆健康检查和系统巡检。

### Step 1: 创建脚本

**记忆自检脚本** `~/.hermes/scripts/memory-dream-mode.py`：

> ⚠️ **重要：此脚本必须做真实记忆文件检查，不能只是占位输出。** 实际记忆存储在 `~/.hermes/memories/MEMORY.md` 和 `USER.md` 中，条目用 `§` 分隔。容量限制在 `~/.hermes/config.yaml` 的 `memory.*` 下配置。

```python
#!/usr/bin/env python3
"""
Memory Dream Mode — 记忆系统自检 (真正读取记忆文件)
每天/每周自动运行，检查记忆健康度、去重、过期清理。
"""
import json, os, re, yaml
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.hermes/memories")
CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")
REPORT_DIR = os.path.expanduser("~/.hermes/memory")
REPORT_PATH = os.path.join(REPORT_DIR, "dream_report.json")
os.makedirs(REPORT_DIR, exist_ok=True)

def read_config_limits():
    """从 config.yaml 读取真实容量限制，而非使用代码默认值"""
    try:
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        mem_cfg = cfg.get("memory", {})
        return {
            "memory_char_limit": int(mem_cfg.get("memory_char_limit", 2200)),
            "user_char_limit": int(mem_cfg.get("user_char_limit", 1375)),
        }
    except Exception:
        return {"memory_char_limit": 2200, "user_char_limit": 1375}

def parse_entries(path):
    """读取记忆文件，按 § 分隔解析条目"""
    if not os.path.exists(path):
        return [], 0
    raw = open(path, "r", encoding="utf-8").read()
    entries = [e.strip() for e in raw.replace("\u00a7", "\nDELIM\n").split("\nDELIM\n") if e.strip()]
    return entries, len(raw)

def run_dream_mode():
    limits = read_config_limits()
    
    mem_entries, mem_chars = parse_entries(os.path.join(MEMORY_DIR, "MEMORY.md"))
    user_entries, user_chars = parse_entries(os.path.join(MEMORY_DIR, "USER.md"))
    
    mem_limit = limits["memory_char_limit"]
    user_limit = limits["user_char_limit"]
    mem_pct = round(mem_chars / mem_limit * 100, 1) if mem_limit else 0
    user_pct = round(user_chars / user_limit * 100, 1) if user_limit else 0
    
    # 检查重复（前60字符相同视为潜在重复）
    mem_prefixes = {}
    for i, e in enumerate(mem_entries):
        mem_prefixes.setdefault(e[:60], []).append(i)
    dup_groups = sum(1 for v in mem_prefixes.values() if len(v) > 1)
    
    # 检查过时/任务进度条目（不应存在于持久记忆）
    stale_patterns = ["Day ", "cron", "已完Day", "每晚"]
    stale_count = sum(1 for e in mem_entries if any(p in e[:120] for p in stale_patterns))
    
    recommendations = []
    if mem_pct > 85:
        recommendations.append(f"MEMORY.md {mem_chars}/{mem_limit} ({mem_pct}%) — 超过85%容量门限，建议压缩")
    if user_pct > 85:
        recommendations.append(f"USER.md {user_chars}/{user_limit} ({user_pct}%) — 超过85%容量门限，建议压缩")
    if dup_groups > 0:
        recommendations.append(f"发现 {dup_groups} 组可能重复条目")
    if stale_count > 0:
        recommendations.append(f"{stale_count} 条任务进度记忆建议移除（不符合持久记忆规范）")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "metrics": {
            "memory": {
                "total_entries": len(mem_entries),
                "total_chars": mem_chars,
                "char_limit": mem_limit,
                "usage_pct": mem_pct,
                "over_capacity": mem_pct > 85,
            },
            "user_profile": {
                "total_entries": len(user_entries),
                "total_chars": user_chars,
                "char_limit": user_limit,
                "usage_pct": user_pct,
                "over_capacity": user_pct > 85,
            },
            "duplicates": dup_groups,
            "stale_task_progress": stale_count,
            "consistency_ok": True,
        },
        "recommendations": recommendations,
    }
    
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"[DreamMode] 记忆自检完成 → {REPORT_PATH}")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == "__main__":
    run_dream_mode()
```

**健康巡检脚本** `~/.hermes/scripts/alwayson-executor.py`：
```python
#!/usr/bin/env python3
# 检查磁盘/记忆目录/服务状态
import os, json, shutil, subprocess
from datetime import datetime

def check_disk():
    stat = shutil.disk_usage("/")
    pct = stat.used / stat.total * 100
    return {"used_pct": round(pct, 1), "healthy": pct < 90}

def run_health_check():
    findings = {
        "timestamp": datetime.now().isoformat(),
        "disk": check_disk(),
        "memory_dir": {"exists": os.path.isdir(os.path.expanduser("~/.hermes/memory"))},
        "services": {},
    }
    report_path = os.path.expanduser("~/.hermes/memory/health_report.json")
    with open(report_path, 'w') as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)
```

### Step 2: 创建 cron 任务

```bash
# 记忆自检 — 每周日10:00
hermes cron create --name "memory-dream-mode" --schedule "0 10 * * 0" --prompt "Run ~/.hermes/scripts/memory-dream-mode.py" --deliver local

# 健康巡检 — 每天02:00
hermes cron create --name "alwayson-health-check" --schedule "0 2 * * *" --prompt "Run ~/.hermes/scripts/alwayson-executor.py" --deliver local
```

> 💡 **增强版脚本**已包含在本 skill 中：`scripts/memory-dream-mode.py`。需要时复制到 `~/.hermes/scripts/` 替换原有占位脚本。此版本真正读取 `~/.hermes/memories/MEMORY.md` 和 `USER.md` 文件、从 config.yaml 读取容量限制、检查重复和任务进度残留。

### Step 3: 内存压缩流程（Dream Mode 手动执行）

当存储空间 >85% 时，执行以下流程：

1. **批量移除** — 用唯一子串逐个 `memory(action='remove', old_text='...')`
2. **分类压缩** — 每条控制在 80-150 字符，加分类标签 + 推理链
3. **合并同类项** — 同一项目的多个版本信息合并为一条
4. **L1索引** — 第一条是全局导航，标注整体使用率和条目数

**常见压缩点：**
| 类型 | 改造前 | 改造后 |
|------|--------|--------|
| 项目状态 | 3-4行冗余版本信息 | 1行：活跃/暂停 + 目录 + URL |
| GitHub认证 | 2条重复PAT信息 | 1条：user + 认证方式 |
| 环境配置 | 整段API端点描述 | 端点URL + key提示 + 【→推理】 |

## 扩展诊断：Server Performance Triage

当用户反映"卡顿"或"任务中断"时，按 `references/2026-06-16-performance-triage.md` 的流程排查：
1. 检查 RAM/Swap/Disk 阈值
2. 判断是内存瓶颈还是上下文问题
3. 按安全清理清单回收磁盘空间

## Hermes Agent 版本升级

当需要升级 Hermes Agent 到最新版本时，见 `references/hermes-upgrade-workflow.md`。

**关键坑：** `hermes update` 在有本地改动时会跳过上游合并（提示"Your fork has 1 commit(s) not on upstream"）。此时必须手动：
1. `git fetch upstream --tags`
2. `git stash` 保存本地改动
3. `git merge upstream/main --no-edit`
4. `git stash pop` 恢复本地改动
5. `hermes --version` + `hermes doctor` 验证

版本 tag 是日期格式（v2026.6.19），`hermes --version` 显示语义版本（v0.17.0）。升级后务必检查 git status 确认本地改动无冲突。

## 频率建议

- **常规维护**：每2-4周一次（或每次 session 空间即将满时）
- **深度维护**：项目阶段切换后 + 重要关系更新后
- **版本升级**：有新版发布时，或用户主动要求时
