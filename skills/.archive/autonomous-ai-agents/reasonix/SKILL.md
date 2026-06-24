---
name: reasonix
description: "DeepSeek-native AI coding agent — install, configure, and automate coding iterations via tmux. Single-provider (DeepSeek), cache-first architecture. Trigger words: reasonix, coding agent, auto iterate, auto iteration, multi-turn coding."
version: 1.0.0
---

# Reasonix — DeepSeek-Native Coding Agent

> 单提供商（DeepSeek）、前缀缓存优化的终端编码 agent。用于自动化迭代、大规模重构、持续部署。

## 安装

```bash
# 前置要求：Node ≥ 22
node --version  # v22.22.2 ✓

# 全局安装
sudo npm install -g reasonix  # /usr/lib/node_modules 需要 root

# 验证
reasonix doctor  # 8/8 pass = 安装成功
```

### 中国 npm 镜像

自动使用已配置的腾讯镜像：
```bash
npm config get registry  # https://mirrors.tencentyun.com/npm
```

## 配置

### `~/.reasonix/config.json`

```json
{
  "apiKey": "sk-...",
  "model": "deepseek-v4-flash",
  "reasoning": false,
  "tools": {
    "interpreter": true,
    "webSearch": true,
    "mcp": true
  },
  "shell": {
    "allowlist": ["*"]
  },
  "skills": {
    "dirs": ["~/.agents/skills"]
  }
}
```

配置优先级：`~/.reasonix/config.json` > `DEEPSEEK_API_KEY` 环境变量 > 无配置（报错）。

### 验证配置

```bash
reasonix doctor
# ✓ api key from ~/.reasonix/config.json
# ✓ api reach  /user/balance ok — ¥37.36 CNY
# ✓ tokenizer  /usr/lib/node_modules/reasonix/data/deepseek-tokenizer.json.gz
# 8 ok · 1 warn · 0 fail = 就绪
```

### 切换模型

修改 `~/.reasonix/config.json` 的 `"model"` 字段。已验证：
- `deepseek-v4-flash` ✅
- `deepseek-v4-pro` ✅
- `deepseek-chat` (V3) ✅

## CLI 命令速查

| 命令 | 用途 |
|------|------|
| `reasonix code [dir]` | 进入编码模式（交互式） |
| `reasonix run "task"` | 一键任务（非交互，流式输出到 stdout） |
| `reasonix chat` | 纯聊天（无文件/Shell 工具） |
| `reasonix doctor` | 健康检查 |
| `reasonix update` | 升级自身 |

## 自动化迭代工作流（tmux + reasonix code）

当需要连续执行多个编码迭代时，使用 tmux 持久化 reasonix 会话：

### 启动

```bash
cd /path/to/project
tmux new-session -d -s reasonix-vp -x 120 -y 40 'reasonix code'
sleep 5  # 等待 reasonix 启动
```

### 下发任务

```bash
tmux send-keys -t reasonix-vp "Iter N: 任务描述" Enter
```

### 等待完成

```bash
sleep 120 && tmux capture-pane -t reasonix-vp -p | tail -20
```

### 提交 + 部署

Reasonix 内运行命令时需要单独发送 Enter 提交到 input buffer：

```bash
# 如果命令被粘贴到 input buffer 但未执行（光标 ▌在末尾）：
tmux send-keys -t reasonix-vp Enter
```

### 批准命令/编辑

Reasonix 对以下操作会交互式确认（需要 approval）：

| 提示类型 | 确认方式 |
|----------|----------|
| 编辑 diff (`[y/Enter] apply`) | `tmux send-keys -t reasonix-vp y` |
| 多个 diff 批处理 | `tmux send-keys -t reasonix-vp a` — apply all/rest，跳过所有剩余 |
| 命令执行 (`▸ Run once`) | `tmux send-keys -t reasonix-vp Enter` 选择默认选项 |
| `Always allow` — git add | `tmux send-keys -t reasonix-vp Enter` 选 Run once |
| `Always allow` — Vercel | `tmux send-keys -t reasonix-vp Enter` |

**注意**：每次 `send-keys` 后需 `sleep` 等待 reasonix 处理。工具链太快会导致确认菜单未渲染就已发 Enter，反而误选。

### 验证 + 提交 + 部署链

```bash
# 1. 等 reasonix 完成编辑
sleep 60 && tmux capture-pane -t reasonix-vp -p | tail -20

# 2. 如果在 diff 确认界面 → a 应用剩余
tmux send-keys -t reasonix-vp a && sleep 10

# 3. 下发 Git 提交 + Vercel 部署
#    注意：VERCEL_TOKEN 用 --token flag，VAR=VALUE 在 reasonix shell 不工作
tmux send-keys -t reasonix-vp \
  "git add -A && git commit -m 'Iter N: description' && \
   vercel deploy --prod --yes --no-color --token vcp_..." Enter

# 4. 等 Reasonix 处理 → 弹出 Run once 确认 → Enter 批准
sleep 10
tmux capture-pane -t reasonix-vp -p | grep -q "Run once" && \
  tmux send-keys -t reasonix-vp Enter

# 5. 等部署完成
sleep 40 && tmux capture-pane -t reasonix-vp -p | tail -10
```

### 链式迭代

```bash
# Iter N 完成后，在 "ask anything" 提示下直接发 Iter N+1
tmux send-keys -t reasonix-vp "Iter N+1: 任务描述" Enter
```

### 清理

```bash
tmux send-keys -t reasonix-vp '/exit' Enter
sleep 2
tmux kill-session -t reasonix-vp 2>/dev/null
```

## 陷阱

### `VAR=VALUE command` 语法在 Reasonix Shell 中不工作

Reasonix 的 shell 工具使用参数解析器而非 Unix shell，不支持内联环境变量。应当：
```bash
# ❌ 不行
VERCEL_TOKEN=xxx vercel deploy

# ✅ 用 --token flag（支持的话）
vercel deploy --prod --yes --no-color --token xxx

# 或先 export 再一条命令（注意 && 连接）
export TOKEN=xxx && vercel deploy --prod --yes --no-color --token "$TOKEN"
```

### 粘贴的命令在 input buffer 中未执行

Reasonix 的消息输入框粘贴命令后不会自动提交。需要额外发送 Enter：
```bash
tmux send-keys -t reasonix-vp "git add -A && git commit -m 'N'" Enter
# 注意：上面最后有 Enter，但 tool 可能把整行当 paste
# 保险做法：分两步
tmux send-keys -t reasonix-vp "git add -A && git commit..."
sleep 1
tmux send-keys -t reasonix-vp Enter  # 单独提交
```

### 恢复旧会话

如果 tmux 会话名已存在，reasonix 会显示 `duplicate session` 错误。先 kill 再重建：
```bash
tmux kill-session -t reasonix-vp 2>/dev/null
tmux new-session -d -s reasonix-vp ...
```

### 编辑 diff 确认累积

Reasonix 的自动模式可能将大型改动拆为多个 diff。每个 diff 都会暂停等待确认。用 `a` (apply all / apply rest) 跳过所有剩余 diff 而非逐个按 y。

## 成本监控

Reasonix 编码模式实时显示当前会话花费：
```
¥0.04 spent  /  left¥36.10
```

- 一次编码迭代（读取文件 + 修改 + 写入）约 ¥0.02–0.08
- 每次对话都有独立会话，互不影响
- cache hit 率通常在 92-99%（DeepSeek 前缀缓存优化）
