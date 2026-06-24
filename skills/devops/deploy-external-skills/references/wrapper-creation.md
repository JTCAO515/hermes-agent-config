# Wrapper Skill Creation Templates

Templates for creating Hermes SKILL.md files around non-Hermes tools (pip packages, npm CLIs, etc.).

## pip Library Wrapper (e.g. RAG-Anything)

```yaml
---
name: <skill-name>
description: <one-line: what this is>
---

# <Title>

`pip install <pkg>` (已安装)

## 快速使用

### Basic Usage

```python
from <module> import <Class>

# Core usage examples
# Keep concise — this is a reference, not full docs
```

### 支持的格式 / Limitations
- Format A: supported
- Format B: needs LibreOffice
- Format C: requires API key

### 配置
- Environment variables needed
- API keys required
```

## npm CLI Wrapper (e.g. westock-data)

```yaml
---
name: <skill-name>
description: <one-line: what this CLI does>
---

# <Title>

Data source: <source>
Supported markets: <markets>

## Quick Start

```bash
npx -y <pkg>@<version> <subcommand>
```

## Core Commands

### 1. Search
```bash
npx -y <pkg>@<version> search <query>
```

### 2. Data Query
```bash
npx -y <pkg>@<version> query <param> --option <value>
```

## Batch Queries
All commands (except search/minute) support comma-separated multi-input:
```bash
npx -y <pkg>@<version> command <input1>,<input2>
```

## Known Limitations
| Limitation | Details |
|------------|---------|
| Feature A | Only works on market X |
| Feature B | Requires flag Y |
```

## Key Principles for Wrapper Skills

1. **The wrapper is documentation, not automation.** It teaches the agent how to use the tool, it doesn't replace the tool.
2. **Include all subcommands** with example invocations so the agent knows what's possible.
3. **Flag limitations explicitly** — the agent can't discover them by trial.
4. **Specify the exact version** you installed (e.g., `@1.0.3`) to avoid drift.
5. **Currency units matter** — for financial CLIs, remind the agent to show currency symbols.
