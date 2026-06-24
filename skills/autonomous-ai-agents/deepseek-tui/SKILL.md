---
name: deepseek-tui
description: "Install, configure, and use DeepSeek TUI — the Rust terminal coding agent optimized for DeepSeek V4 models."
version: 1.0.0
metadata:
  hermes:
    tags: [deepseek, tui, coding-agent, terminal, rust, installation, china-network]
    homepage: https://github.com/Hmbown/DeepSeek-TUI
    related_skills: [hermes-agent]
---

# DeepSeek TUI

A Rust-based terminal coding agent built specifically around DeepSeek V4 models (`deepseek-v4-pro` / `deepseek-v4-flash`). 1M-token context, streaming reasoning blocks, auto model selection, Linux Landlock sandbox, sub-agent concurrency, MCP support, and a skills system compatible with `.agents/skills/` convention.

**When to use DeepSeek TUI vs Hermes Agent:**

| | Hermes Agent | DeepSeek TUI |
|-|-------------|-------------|
| Multi-platform messaging (WeChat, Telegram...) | ✅ | ❌ |
| Cron jobs, webhooks | ✅ | ❌ |
| Terminal interactive coding | ✅ | ✅ (native TUI) |
| Streaming reasoning visibility | ❌ | ✅ |
| Auto model + thinking routing | ❌ | ✅ |
| LSP diagnostics after edits | ❌ | ✅ |
| OS-level sandbox | ❌ | ✅ (Landlock) |

Use both — Hermes for messaging/cron, DeepSeek TUI for interactive coding sessions.

## Installation (Linux x86_64, China)

### Download prebuilt binaries

Two binaries are required:
- `deepseek` — dispatcher CLI (18MB)
- `deepseek-tui` — TUI runtime (48MB)

**Latest release:** check `https://github.com/Hmbown/DeepSeek-TUI/releases/latest` for the current tag, then:

```bash
VERSION="v0.8.40"  # update from releases page

# Via ghproxy.net (China mirror — 26s for 18MB, 24s for 50MB)
curl -#L -o /tmp/deepseek-linux-x64 \
  "https://ghproxy.net/https://github.com/Hmbown/DeepSeek-TUI/releases/download/${VERSION}/deepseek-linux-x64"
curl -#L -o /tmp/deepseek-tui-linux-x64 \
  "https://ghproxy.net/https://github.com/Hmbown/DeepSeek-TUI/releases/download/${VERSION}/deepseek-tui-linux-x64"

sudo mv /tmp/deepseek-linux-x64 /usr/local/bin/deepseek
sudo mv /tmp/deepseek-tui-linux-x64 /usr/local/bin/deepseek-tui
sudo chmod +x /usr/local/bin/deepseek /usr/local/bin/deepseek-tui
```

GitHub direct downloads timeout (~2MB/120s from China); always use ghproxy.net.

Alternative install paths: `npm install -g deepseek-tui`, `cargo install deepseek-tui-cli --locked`, `brew install deepseek-tui`.

### Configure

```bash
# Save API key
deepseek auth set --provider deepseek
# → saves to ~/.deepseek/config.toml + secrets/

# Set Chinese locale (CNY cost display, Chinese UI)
echo 'locale = "zh-Hans"' >> ~/.deepseek/config.toml

# Verify
deepseek doctor
deepseek --version
```

Config file: `~/.deepseek/config.toml`. Secrets: `~/.deepseek/secrets/`.
Env var alternative: `DEEPSEEK_API_KEY` (config.toml takes precedence).

### Other providers

```bash
deepseek auth set --provider openrouter --api-key "sk-..."   # OpenRouter
deepseek auth set --provider nvidia-nim --api-key "..."     # NVIDIA NIM
deepseek auth set --provider openai --api-key "..."          # Generic OpenAI-compatible
```

## Usage Quickstart

```bash
deepseek                            # Interactive TUI
deepseek --model auto              # Auto-select model + thinking level
deepseek "explain this function"   # One-shot query
deepseek models                    # List available models
deepseek resume --last             # Resume most recent session
deepseek sessions                  # List saved sessions
deepseek serve --http              # HTTP/SSE API server
deepseek update                    # Check for binary updates
```

### Key shortcuts inside TUI

| Key | Action |
|-----|--------|
| `Tab` | Queue draft / cycle mode |
| `Shift+Tab` | Cycle reasoning: off → high → max |
| `Ctrl+K` | Command palette |
| `Ctrl+R` | Resume earlier session |
| `Esc` | Back / dismiss |
| `F1` | Help overlay |

### Modes

| Mode | Behavior |
|------|----------|
| **Plan** 🔍 | Read-only exploration |
| **Agent** 🤖 | Interactive with approval gates |
| **YOLO** ⚡ | Auto-approve all tools |

## Integration with Hermes Agent

### Option 1: Standalone (recommended)
Use DeepSeek TUI in its own terminal for interactive coding. Hermes handles messaging/cron.

### Option 2: Hermes spawns DeepSeek TUI
```bash
# One-shot task via Hermes terminal tool
deepseek exec --auto --output-format stream-json "fix this bug"

# Interactive via tmux
tmux new-session -d -s deepseek -x 120 -y 40 'deepseek --model auto'
```

### Option 3: MCP bridge
```bash
deepseek mcp-server              # DeepSeek TUI as MCP server
hermes mcp add deepseek-tui ...  # Hermes registers it
```

### Shared skills
Both tools read from `~/.agents/skills/`. Skills placed there work in both.

## Pitfalls

- **Two binaries required**: `deepseek` alone errors out — `deepseek-tui` must also be on PATH.
- **GitHub timeout in China**: Direct GitHub release downloads timeout at ~2MB/120s. Always use `ghproxy.net` prefix.
- **Config precedence**: `~/.deepseek/config.toml` beats env vars. If `DEEPSEEK_API_KEY` env var has a stale key but config.toml has the current one, config wins. Use `deepseek auth status` to debug.
- **Skills directory discovery order**: workspace `.agents/skills` → workspace `skills` → workspace `.opencode/skills` → `~/.agents/skills` → `~/.deepseek/skills`. The first one found with content wins.

## Reasonix — Alternative DeepSeek-Native Coding Agent

> Absorbed from `reasonix` (archived). NPM-based alternative to the Rust TUI.

Reasonix is a DeepSeek-only, cache-first coding agent installed via npm:
```bash
sudo npm install -g reasonix
```

### Key differences from DeepSeek TUI
| Dimension | DeepSeek TUI | Reasonix |
|-----------|-------------|----------|
| Platform | Rust binary | Node.js npm package |
| Providers | Multi (DeepSeek, OpenRouter, etc.) | DeepSeek only |
| Cache | General | Prefix-cache optimized (92-99% hit rate) |
| Cost display | N/A | Real-time ¥ spent in session |
| Shell env vars | Standard | `VAR=VALUE command` syntax NOT supported |

### Reasonix CLI commands
| Command | Purpose |
|---------|---------|
| `reasonix code [dir]` | Interactive coding mode |
| `reasonix run "task"` | One-shot non-interactive task |
| `reasonix doctor` | Health check (8/8 = ready) |
| `reasonix update` | Self-upgrade |

### Auto-iteration via tmux (Reasonix)
```bash
cd /path/to/project
tmux new-session -d -s reasonix-vp -x 120 -y 40 'reasonix code'
sleep 5
tmux send-keys -t reasonix-vp "Iter N: task description" Enter
```

**Reasonix approval flow:** Each diff pauses for y/Enter confirmation. Use `a` to apply all remaining. Send Enter for Run once prompts.

### Reasonix pitfalls
- `VAR=VALUE command` syntax doesn't work — use `--token` flags or `export VAR=VAL && command`
- Pasted commands stay in input buffer — send extra Enter
- Duplicate tmux session name → kill before recreate
- Each large edit spawns multiple diff confirmations — use `a` to skip all

Full details → `references/reasonix.md`

## Key Paths

```
~/.deepseek/config.toml     Main config
~/.deepseek/secrets/        API keys (file-based)
~/.deepseek/skills/         Global skills (fallback)
~/.agents/skills/           Shared skills (Hermes + DeepSeek TUI)
/usr/local/bin/deepseek     Dispatcher CLI
/usr/local/bin/deepseek-tui TUI runtime
```
