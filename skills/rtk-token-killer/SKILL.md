---
name: rtk-token-killer
description: rtk (Rust Token Killer) — 高性能 CLI 代理，过滤/压缩命令输出以减少 LLM token 消耗 60-90%
version: 1.0.0
---

# rtk (Rust Token Killer) — Hermes Agent 集成

rtk 安装在 `~/.local/bin/rtk`，版本 0.40.0。在 Hermes Agent 的 terminal 工具中，优先使用 `rtk <cmd>` 代替原始命令，以减少 token 消耗。

## 支持的命令

### 文件操作
| 命令 | 替代 | Token 节省 |
|------|------|-----------|
| `rtk ls .` | `ls` | -80% |
| `rtk read <file>` | `cat` / `read` | -70% |
| `rtk find <pattern> .` | `find` | -70% |
| `rtk grep <pattern> .` | `grep` / `rg` | -80% |

### Git
| 命令 | 替代 | Token 节省 |
|------|------|-----------|
| `rtk git status` | `git status` | -80% |
| `rtk git log -n <N>` | `git log` | -80% |
| `rtk git diff` | `git diff` | -75% |
| `rtk git add|commit|push` | `git add/commit/push` | -92% |

### 测试
| 命令 | Token 节省 |
|------|-----------|
| `rtk cargo test` | -90% |
| `rtk pytest` | -90% |
| `rtk jest` | -85% |
| `rtk vitest` | -85% |
| `rtk go test` | -90% |

### 构建 & Lint
| 命令 | Token 节省 |
|------|-----------|
| `rtk cargo build` | -80% |
| `rtk cargo check` | -75% |
| `rtk cargo clippy` | -70% |
| `rtk ruff check` | -80% |
| `rtk lint` | -80% |

### 容器
| 命令 | Token 节省 |
|------|-----------|
| `rtk docker ps` | -70% |
| `rtk docker logs <id>` | -70% |
| `rtk kubectl pods` | -70% |

## 何时使用 rtk

**推荐**：任何 github/git/cargo/npm/pnpm/npx/pip/pytest/go/docker/kubectl 相关的 terminal 调用，优先加 `rtk` 前缀。

**不适用**：命令输出需要完整保留的场景（如精确的行号定位、完整错误栈）。

## 验证安装

```bash
rtk --version    # 应显示 rtk 0.40.0
rtk gain         # 查看 token 节省统计
```

## 源代码

- 仓库：`~/projects/rtk/` (本地) / `git@github.com:JTCAO515/rtk.git` (GitHub fork)
- 上游：`git@github.com:rtk-ai/rtk.git`
