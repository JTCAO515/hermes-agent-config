# Server Performance Triage & Disk Cleanup — 2026-06-16

## 问题诊断流程

当用户反映"长任务卡顿"或"项目跑到一半不对话"，按以下顺序排查：

### 1. 服务器资源检查

```bash
# 一键诊断
echo "=== CPU ===" && nproc && lscpu | grep "Model name"
echo "=== RAM ===" && free -h
echo "=== SWAP ===" && swapon --show 2>/dev/null || echo "no swap"
echo "=== DISK ===" && df -h /
echo "=== LOAD ===" && uptime
echo "=== TOP PROC ===" && ps aux --sort=-%mem | head -8
```

**阈值告警：**
| 指标 | 正常 | 警戒 | 严重 |
|------|------|------|------|
| RAM 可用 | >2GB | <1GB | <500MB |
| Swap 使用 | 0 | >0 | >1GB |
| 磁盘占用 | <70% | >80% | >90% |
| Load | <CPU核数 | ≈CPU核数 | >CPU核数 |

### 2. 根因链

```
RAM 不足 → 系统使用 Swap (磁盘当内存用) →  Disk I/O 慢1000倍 → 卡顿
                                              ↓
上下文膨胀 → Context Compaction → 丢弃前面对话 →  Agent 丢失用户意图 → "不说话了"
```

Two separate problems that amplify each other.

### 3. 上下文中断的深层原因

用户说"项目跑到一半不对话了"有三个可能原因（按频率排序）：

1. **Context Compaction**（最常见）— 对话太长时系统将早期内容压缩为摘要，摘要可能丢失用户意图线索。Agent 基于过时版本继续工作，看起来就像"不管用户了"。
2. **DeepSeek V4 Flash 上下文窗口较小** — worker/browser 角色用 Flash 模型，窗口比 Pro 小，更容易触发 compaction。
3. **每日会话重置** — 系统定时重置会话，如果任务跨过重置点，新会话没有上文。

**缓解措施：**
- 任务完成后主动生成 HANDOFF.md 保存状态快照
- 大任务拆分为多个子阶段，每阶段完成后通知用户"继续"
- 关键决策写进记忆而非依赖长对话上下文

## 磁盘清理指南

### 大件排查

```bash
du -sh /home/ubuntu/* 2>/dev/null | sort -rh | head -10
du -sh /home/ubuntu/.* 2>/dev/null | sort -rh | head -15
```

### 安全清理清单（按优先级）

| 目录 | 典型大小 | 用途 | 能否删 | 清理命令 |
|------|---------|------|--------|---------|
| `~/.npm` | 1-2.2GB | npm 缓存 | ✅ 安全 | `npm cache clean --force` |
| `~/.rustup` | 1-1.4GB | Rust 工具链 | ✅ 不用Rust开发可删 | `rustup self uninstall -y` |
| `~/.cargo` | 150-180MB | Rust 包 | ✅ 同上 | `rm -rf ~/.cargo` |
| `~/.bun` | 200-240MB | Bun 运行时 | ✅ 没用过可删 | `rm -rf ~/.bun` |
| `~/.deno` | 100-110MB | Deno 运行时 | ✅ 没用过可删 | `rm -rf ~/.deno` |
| `~/.cache/pip` | 15-25MB | pip 缓存 | ✅ 安全 | `pip3 cache purge` |
| `/var/cache/apt` | 可清理部分 | apt 缓存 | ✅ 安全 | `sudo apt-get clean` |
| `~/.npm-global` | 200-250MB | 全局 npm 包 | ✅ 不用可删 | `rm -rf ~/.npm-global` |
| `~/.npm` 剩余 | ~224MB | npm 注册缓存 | ⚠️ 留少量 | 清理后剩200MB左右正常 |
| `~/.cache/camoufox` | 1.2-1.5GB | Agent 浏览器引擎 | ❌ Agent 浏览器功能需要 | 不清 |
| `~/.cache/ms-playwright` | 600-700MB | Playwright 浏览器 | ❌ 测试/浏览器功能需要 | 不清 |
| `~/.hermes/sessions` | 200-260MB | 历史会话 | ⚠️ 可清理旧会话 | 保留最近50个 `ls -t \| tail -n +51 \| xargs rm` |

### 系统级清理

```bash
sudo journalctl --vacuum-time=3d   # 保留3天日志
sudo apt-get clean -y               # 清 apt 缓存
rm -rf /tmp/*                       # 临时文件
```

### 升级建议阈值

当前配置 4C/3.6GB RAM/40GB 磁盘时，如果满足以下任一条件建议升级：
- Swap 持续 >500MB（内存不足）
- 磁盘 >80%（空间紧张）
- 用户经常并行跑多个项目或长任务

推荐目标配置：4C/8GB RAM/120GB 磁盘 — 可消除 Swap，内存充裕，10M 带宽提升拉取速度。
