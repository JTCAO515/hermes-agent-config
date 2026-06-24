# Figma Official MCP Skills — Deployment Reference

**Source:** `https://github.com/figma/mcp-server-guide`
**Session:** 2026-06-16

## Structure

The repo has 9 skills under `skills/`, each with its own `SKILL.md` and a `references/` directory:

```
skills/
├── figma-use/              # Core Plugin API skill
│   ├── SKILL.md
│   └── references/         # Plugin API typing docs, design system guides
├── figma-use-figjam/       # FigJam whiteboard operations
├── figma-use-slides/       # Slides deck operations
├── figma-code-connect/     # Component → code mapping
├── figma-create-new-file/  # Blank file creation
├── figma-generate-design/  # Code → Figma screen translation
├── figma-generate-diagram/ # Mermaid → FigJam diagram
├── figma-generate-library/ # Design system library building
└── figma-swiftui/          # SwiftUI ↔ Figma bidirectional
```

## Deployment Steps

```bash
# 1. Download repo
curl -sL "https://github.com/figma/mcp-server-guide/archive/refs/heads/main.zip" -o /tmp/figma-skills.zip
cd /tmp && unzip -q figma-skills.zip

# 2. Copy all skills (including references/) to ~/.hermes/skills/
for s in mcp-server-guide-main/skills/figma-*; do
  name=$(basename "$s")
  target=~/.hermes/skills/"$name"
  mkdir -p "$target"
  cp -r "$s"/* "$target"/
done
```

## Critical Details

- **Always copy `references/` directories** — Figma skills have non-trivial typed API docs, gotcha files, and design system references that SKILL.md imports.
- **The proxy issue**: On this server, `http_proxy=http://127.0.0.1:10809` is set. Use `--noproxy '*'` on all localhost curl/wget calls, or `unset http_proxy` before the download.
- **No API key needed for the skill files themselves.** But to actually USE `figma-use` / `generate_diagram` etc., Hermes needs a Figma MCP server connection (`https://mcp.figma.com/mcp` over Streamable HTTP) plus a Figma API token (Personal Access Token or OAuth).

## Prerequisites for Actual Usage

| Component | Required | How |
|-----------|----------|-----|
| Figma MCP client | Yes | Hermes needs `mcpServers.figma.type=http` in config.yaml |
| Figma PAT token | Yes | From Figma Dev Settings → Personal Access Token |
| Figma file URL | Yes | Must have `node-id` in URL for context operations |
| Rate limit | Starter plan: 6 calls/month | Dev/Full seat: unlimited (Tier 1 REST API) |
