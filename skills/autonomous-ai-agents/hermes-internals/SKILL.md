---
name: hermes-internals
description: "Hermes Agent internal architecture, codebase navigation, design patterns, and contribution knowledge."
version: 1.0.0
---

# Hermes Internals

Knowledge base for understanding and modifying the Hermes Agent codebase at `~/.hermes/hermes-agent/`.

This skill is a companion to `hermes-agent` (which covers usage, config, and setup). It covers **internals**: how the system is structured, key design decisions, and the patterns you need to follow when contributing code.

## Codebase Topology

```
hermes-agent/
├── run_agent.py              # AIAgent — core conversation loop
├── model_tools.py            # Tool discovery and dispatch
├── toolsets.py               # Toolset definitions
├── cli.py                    # Interactive CLI
├── hermes_state.py           # SQLite session store
├── agent/                    # Agent runtime logic
│   ├── agent_init.py         # AIAgent.__init__ forwarding (~1700 lines)
│   ├── conversation_loop.py  # Turn loop (on_session_start, pre_llm_call etc.)
│   ├── turn_context.py       # Per-turn setup (plugin hooks fire here)
│   ├── shell_hooks.py        # Shell-script hook bridge
│   ├── agent_runtime_helpers.py  # Various AIAgent runtime helpers
│   ├── prompt_builder.py     # System prompt construction
│   └── ...
├── hermes_cli/
│   ├── plugins.py            # PluginManager + VALID_HOOKS + invoke_hook
│   └── ...
├── tools/
│   ├── delegate_tool.py      # Subagent creation (AIAgent for children)
│   ├── cronjob_tools.py      # Cron job create/update/delete
│   └── ...
├── cron/
│   └── scheduler.py          # Cron scheduler + run_job (AIAgent construction)
└── gateway/
    └── ...
```

## Key Architectural Patterns

### 1. PluginManager Singleton (hermes_cli/plugins.py)

Most of the hook/callback system funnels through a **module-level singleton** `get_plugin_manager()`:

```python
from hermes_cli.plugins import invoke_hook
results = invoke_hook("pre_llm_call", **kwargs)
```

This is **global** — every AIAgent instance shares the same PluginManager. There is NO instance-level hook isolation mechanism built yet.

**Current events (VALID_HOOKS):** `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `pre_api_request`, `post_api_request`, `on_session_start/end/finalize/reset`, `subagent_start/stop`, `pre_gateway_dispatch`, `pre_approval_request`, `post_approval_response`, `transform_*` variants.

### 2. Shell Hooks (agent/shell_hooks.py)

Shell hooks are a bridge between `config.yaml -> hooks:` and the PluginManager:
- `register_from_config(cfg)` parses the `hooks:` block and registers subprocess callbacks on the global PluginManager
- Each hook runs as a subprocess with an allowlist consent system (`~/.hermes/shell-hooks-allowlist.json`)
- Events are dispatched via PluginManager (same as Python plugin hooks)
- **Key**: shell hooks and Python plugin hooks compose through the same PluginManager — Python plugin blocks win priority ties

### 3. AIAgent Construction Chain

```
AIAgent.__init__(...)            # run_agent.py:343 — thin forwarder
  → init_agent(self, ...)        # agent/agent_init.py — ~1700 lines of setup
      → stores on self.*         # AIAgent is a mutable object
```

The constructor has ~50 optional parameters. There is **no `hook_overrides` parameter** — hooks are always global.

### 4. Cron Agent Construction (cron/scheduler.py:1726)

Cron jobs create an `AIAgent(...)` in `run_job()` with:
- Provider resolution, model config, reasoning config, toolsets
- **No hook injection mechanism** — cron jobs use the global PluginManager hooks

### 5. Subagent Construction (tools/delegate_tool.py:1210)

Subagents create an `AIAgent(...)` in `_build_child_agent()`:
- Inherits provider, model, API key, reasoning from parent
- **No hook inheritance** — subagents use the global PluginManager hooks

## Reference Files

| File | Topic |
|------|-------|
| `references/hook-system-architecture.md` | Detailed hook system code review, feasibility analysis for instance-level hooks |

## Common Investigation Patterns

When tracing how a feature flows through Hermes, follow this order:

1. **Config entry** — `config.yaml` or `cronjob` tool → what field stores it?
2. **Agent construction** — Does `run_agent.py:343` or `init_agent` mention it?
3. **Runtime hook** — Does `conversation_loop.py` or `turn_context.py` invoke it?
4. **Global singleton** — Does PluginManager own it, or is it on `self.*`?

This pattern catches 90% of integration points.
