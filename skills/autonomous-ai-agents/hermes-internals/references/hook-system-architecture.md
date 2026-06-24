# Hook System Architecture

> Code review conducted 2026-06-20 during feasibility assessment of "instance-level hook injection" refactoring.
> Relevant files under `~/.hermes/hermes-agent/`.

## Overview

The hook system provides lifecycle callbacks at key points in the agent loop:
- **Global hooks** via `PluginManager` singleton (current, only mechanism)
- **Instance hooks** — proposed but not yet implemented (`hook_overrides` parameter on AIAgent)

## Architecture Diagram (Current)

```
config.yaml
  hooks:
    pre_llm_call:
      - command: python hook.py
```

```
shell_hooks.py:register_from_config(cfg)
  → parses config's "hooks:" block
  → registers callbacks on global PluginManager._hooks[event]

PluginManager (hermes_cli/plugins.py)
  └── invoke_hook(event, **kwargs)
        ├── calls all registered callbacks for event
        └── returns list of non-None results

Every AIAgent instance shares the SAME PluginManager singleton.
No instance-level isolation.
```

## Event Flow Per Agent Lifecycle

### Session Start
```
AIAgent.__init__(...)           # run_agent.py:343
  → init_agent(self, ...)       # agent/agent_init.py
    → build_turn_context(...)   # agent/turn_context.py
        → invoke_hook("pre_llm_call", ...)  # Plugin hook: context injection
```

### Each Turn (conversation_loop.py)
```
run_conversation(prompt):
  1. Build system prompt
  2. Loop:
     a. Call LLM
     b. If tool_calls → invoke_hook("pre_tool_call", ...) → dispatch → invoke_hook("post_tool_call", ...)
     c. If text → return
  3. invoke_hook("post_llm_call", ...)
```

### Session End
```
invoke_hook("on_session_finalize", ...)
invoke_hook("on_session_reset", ...)  # on /reset
```

## Plugin Hooks vs Shell Hooks

| Aspect | Plugin Hooks | Shell Hooks |
|--------|-------------|-------------|
| Registration | `discover_and_load()` → Python plugin modules | `register_from_config()` → config.yaml `hooks:` |
| Callback type | Python functions | Subprocess (spawned per event) |
| Shared via | PluginManager singleton | PluginManager singleton (same as plugins) |
| Allowlist | Not needed (code trust) | `~/.hermes/shell-hooks-allowlist.json` |
| Priority | Python plugins run before shell hooks | Shell hooks after Python plugins |

Both flow through the SAME `invoke_hook()` — they compose naturally.

## Key Files

| File Path | Role | Lines |
|-----------|------|-------|
| `agent/shell_hooks.py` | Shell hook bridge: parse, register, spawn, parse response | 847 |
| `agent/turn_context.py` | `pre_llm_call` hook fires during build_turn_context | 390 |
| `agent/conversation_loop.py` | Main loop: `on_session_start`, `pre_tool_call`, `post_tool_call`, `post_llm_call` | 4480 |
| `run_agent.py` | `AIAgent.__init__()` — forwarder to `init_agent()` | 5493 |
| `agent/agent_init.py` | `init_agent()` — actual construction logic | 1746 |
| `hermes_cli/plugins.py` | PluginManager: `VALID_HOOKS`, `invoke_hook()`, `discover_and_load()` | 2046 |
| `cron/scheduler.py` | `run_job()` → creates `AIAgent(...)` for cron tasks | 2213 |
| `tools/delegate_tool.py` | `_build_child_agent()` → creates `AIAgent(...)` for subagents | 3126 |

## Hook Event Schema (VALID_HOOKS at plugins.py:128)

```
pre_tool_call                    # Before tool execution. Can block.
post_tool_call                   # After tool execution.
pre_llm_call                     # Before LLM call. Can inject context into user message.
post_llm_call                    # After LLM response.
pre_api_request / post_api_request / api_request_error  # HTTP-level lifecycle
transform_tool_result            # Transform tool output before agent sees it.
transform_terminal_output        # Transform terminal output.
transform_llm_output             # Transform LLM output before user sees it.
on_session_start / end / finalize / reset  # Session lifecycle
subagent_start / stop            # Subagent lifecycle
pre_gateway_dispatch             # Inbound message before auth
pre_approval_request / post_approval_response  # Approval lifecycle
```

## Identified Gap: No Instance-Level Hook Isolation

**Problem:**
- Cron jobs (`scheduler.py:1726`) create `AIAgent(...)` with no way to inject job-specific hooks
- Subagents (`delegate_tool.py:1210`) create `child = AIAgent(...)` with no hook inheritance
- All hooks are global via PluginManager — changing one affects every instance

**Proposed Fix (assessed 8/10 feasible):**
Modify 6 files:

| File | Change | Complexity |
|------|--------|------------|
| `shell_hooks.py` | Add `register_instance_hooks()` + `invoke_instance_hooks()`. Reuses existing parse/spawn logic. | ~80 lines |
| `run_agent.py` | Add `hook_overrides` to `AIAgent.__init__()` signature | ~5 lines |
| `agent/agent_init.py` | Forward `hook_overrides` through to AIAgent state | ~5 lines |
| `agent/conversation_loop.py` | Fire instance hooks alongside global hooks. Must not break prompt caching. | ~20 lines |
| `cron/scheduler.py` | Parse `hooks` field from job config, pass as `hook_overrides` | ~50 lines |
| `tools/delegate_tool.py` | Inherit parent's `hook_overrides`, pass to child AIAgent | ~5 lines |

**Unresolved Design Decisions (from review):**
1. **Merge strategy** — Instance hooks APPEND to global hooks (recommended). Instance cannot REPLACE global. For replacement, clear the global `hooks:` config.
2. **Plugin hooks** — Python plugin hooks remain global. Instance hooks only affect shell hooks. Full plugin per-instance isolation is a v2.
3. **Cron allowlist** — Cron has no TTY. Instance shell hooks for cron must use `accept_hooks=True` / `HERMES_ACCEPT_HOOKS=1` path.
4. **Job storage** — Need to confirm cron job schema (`cronjob_tools.py`) supports arbitrary `hooks:` field without migration.
