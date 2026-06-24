---
name: hermes-migration
description: Migrate Hermes Agent configuration (SOUL.md, skills, memories, harness, cron) between servers. Package → transfer → setup in 3 steps.
trigger: 迁移/换服务器/新机器/搬家/迁移配置/migrate/move server/new machine
---

# Hermes Agent 服务器迁移

将 Hermes Agent 的全部配置从旧服务器迁移到新服务器。

## 触发条件

用户提到换服务器、新机器、迁移配置、搬家等关键词。

## 迁移清单

### 自动迁移（打包进 tar.gz）

| 路径 | 内容 | 说明 |
|------|------|------|
| `~/.hermes/SOUL.md` | 行为宪法 | 最高优先级 |
| `~/.hermes/AGENTS.md` | 项目级 Agent 指令 | 全局工作流 |
| `~/.hermes/config.yaml` | hermes 配置 | 模型/provider/skills 路径 |
| `~/.hermes/skills/` | 全部 skill 文件 | 含 SKILL.md + references/templates/scripts |
| `~/.hermes/harness/` | Harness Engineering 模板 | PLAN/IMPLEMENT/AGENTS/CHECKLIST |
| `~/.hermes/memories/` | 持久记忆 | 用户偏好/环境事实 |
| `~/.hermes/cron/` | 定时任务 | 如有 |

### 手动迁移（安全原因）

| 项目 | 操作 |
|------|------|
| `~/.hermes/.env` | **手动复制** API Keys（不打包进 tar.gz） |
| 平台重连 | 微信/元宝需重新扫码登录 |
| SSH Key | 自动生成，需重新添加到 GitHub |
| 第三方 API Key | DeepSeek/Futu/GLM 等需在新服务器设置 |

## 执行步骤

### Step 1: 旧服务器打包

```bash
cd ~
tar czf /tmp/hermes-migration.tar.gz \
  .hermes/config.yaml \
  .hermes/SOUL.md \
  .hermes/AGENTS.md \
  .hermes/skills/ \
  .hermes/harness/ \
  .hermes/memories/ \
  .hermes/cron/ 2>/dev/null
```

同时生成 setup 脚本（见 `templates/setup.sh`），写入 `/tmp/hermes-setup.sh`。

### Step 2: 传输到新服务器

```bash
scp /tmp/hermes-migration.tar.gz /tmp/hermes-setup.sh 用户名@新服务器IP:/tmp/
```

### Step 3: 新服务器解压 + 安装

```bash
bash /tmp/hermes-setup.sh
```

脚本自动完成：
1. 创建 `~/.hermes/` 目录结构
2. 解压配置文件
3. 生成新 SSH Key
4. 输出验证结果

### Step 4: 手动补全

1. **API Keys**：把旧服务器 `~/.hermes/.env` 内容复制到新服务器
2. **SSH Key**：`cat ~/.ssh/id_ed25519.pub` 添加到 GitHub
3. **平台重连**：微信扫码、元宝重新登录

### Step 5: 验证

```bash
hermes --version && cat ~/.hermes/SOUL.md | head -3
```

应输出 `# SOUL.md - 猪猪微`（或对应 Agent 名）。

## 常见项目迁移

如果用户在新服务器也需要跑之前部署过的项目（如 VisePanda），参考 `references/project-clone-pattern.md`。

## 注意事项

- **不要**把 `.env` 或含 API Key 的文件打包进 tar.gz
- 如果旧服务器磁盘空间紧张，迁移完成后清理 `/tmp/hermes-migration.tar.gz`
- 新服务器需要先安装 hermes agent 本身（不在迁移范围内）
- cron 任务路径可能需要调整（如果用户名或 home 目录变了）
