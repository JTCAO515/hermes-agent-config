# hindsight-mcp — Hindsight AI Memory MCP Server

## Overview
`hindsight-mcp` is an MCP server that bridges Hermes Agent with the Hindsight AI Memory Service (https://hindsight-ai.com). It provides persistent cross-session memory with semantic search, conversation retrieval, agent management, and feedback loops — a more powerful alternative to the built-in `memory` tool.

## Tools Provided
| Tool | Description |
|------|-------------|
| `create_memory_block` | Create a new memory block (requires content + lessons_learned) |
| `create_agent` | Create a new agent identity |
| `retrieve_relevant_memories` | Semantic/keyword search across memories |
| `retrieve_all_memory_blocks` | Paginate through all memory blocks |
| `retrieve_memory_blocks_by_conversation_id` | Filter by conversation |
| `report_memory_feedback` | Positive/negative/neutral feedback on memories |
| `get_memory_details` | Metadata + content for one memory block |
| `search_agents` | Search agent names by query |
| `show_capture_checklist` | Operating loop guidance |
| `advanced_search_memories` | Full-text + semantic hybrid search with tuning |
| `whoami` | Return authenticated user and memberships |

## Installation
```bash
sudo npm install -g hindsight-mcp
```
Requires Node.js ≥ 18. Verify: `which hindsight-mcp` → `/usr/bin/hindsight-mcp`

## Hermes Config
Requires user to obtain credentials from https://hindsight-ai.com dashboard (API Settings → Personal Access Token).

```yaml
# In ~/.hermes/config.yaml
mcp_servers:
  hindsight:
    command: "hindsight-mcp"
    env:
      HINDSIGHT_API_TOKEN: "hs_pat_xxxxxxxxxxxx"
      DEFAULT_AGENT_ID: "00000000-0000-0000-0000-000000000000"
    timeout: 60
```

Optional env vars:
- `HINDSIGHT_API_BASE_URL` — defaults to `https://api.hindsight-ai.com`
- `DEFAULT_CONVERSATION_ID` — fixed conversation UUID for all requests
- `HINDSIGHT_ACTIVE_SCOPE` — `personal` / `organization` / `public`
- `HINDSIGHT_ORGANIZATION_ID` — org override (avoid if token is org-scoped)

Scope: read tokens can search/retrieve; write tokens required for create/update/feedback.

## Prerequisites
- `mcp` Python package already installed (v1.27.0+): `pip install mcp`
- Token from Hindsight dashboard
- An existing agent created in Hindsight (use `create_agent` tool after config if none exists)
