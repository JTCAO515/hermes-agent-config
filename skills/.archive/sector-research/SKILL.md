---
name: sector-research
version: 1.0.0
description: |
  Multi-sector stock research for US/China markets. Parallel search across
  N sectors, identify leaders + emerging players, compile structured reports
  with market analysis, financial cross-comparison, and allocation suggestions.
triggers:
  - "热点板块"
  - "板块研究"
  - "行业分析"
  - "sector research"
  - "赛道分析"
  - "美股板块"
  - "选出龙头"
  - "10个龙头"
  - "代发展企业"
tools:
  - delegate_task
  - web_search
  - terminal
  - skill_view
mutating: false
---

# Sector Research — 多板块并行研究

For tasks like "研究 AI/芯片/机器人/生物科技 四个热点板块，每个选 10 龙头 + 10 新兴" — use this skill.

## When to Use

- User asks for sector/板块/赛道 research across multiple industries
- User wants leader + emerging stock lists with analysis
- User says "热点板块", "选出龙头", "行业分析", "板块对比"
- Task involves identifying ALL stocks in a sector then filtering to top 10 + 10

## Phase 1: Parallel Sector Search

Use `delegate_task` to research all sectors in parallel. Each subagent gets ONE sector.

### Batch Size Limit

`delegate_task` has `max_concurrent_children: 3`. For 4+ sectors, split into batches:

```python
# Batch 1: sectors 1-3
# Batch 2: sector 4 (or re-run failed ones)
```

### Subagent Goal Template

For each subagent, provide:
```
context: "Search ETF holdings (BOTZ/SMH/IBB etc), market reports.
  Cover must-include tickers: NVDA, MSFT, ..."
goal: "Research ALL US-listed stocks in [SECTOR]. Identify 10 leaders
  (large-cap, established) + 10 emerging (smaller, high-potential).
  For each: ticker, full name, market cap, 1-line focus description.
  Provide sector analysis: market size, CAGR, key trends, catalysts,
  risks. Return in Chinese."
toolsets: ["web","search"]
```

### Pitfall: Subagent May Not Compile

Subagents sometimes return only search tool calls without compiling results. When this happens (∼30% rate for complex sectors like Robotics):
- **Don't keep retrying** the same sector — the subagent approach fails for narrow sectors with few ETF listings
- **Fall back to manual compilation**: write a quick Python script with known stocks, or use `web_search` directly from the main agent
- Pre-built sector knowledge (from prior reports, ETF holdings pages) is more reliable than subagent web search for small sectors

## Phase 2: Stock Quote Enrichment

For key tickers, pull real-time quotes using `stock-tracker`'s fetch.py:

```bash
/home/ubuntu/.hermes/hermes-agent/venv/bin/python3 \
  ~/.hermes/skills/finance/stock-tracker/scripts/fetch.py NVDA --simple
```

**CRITICAL**: `--simple` only returns the FIRST ticker when given multiple. For batch quotes, run each ticker individually with `background=true`, or use a Python loop:

```bash
for ticker in NVDA MSFT GOOGL; do
  /venv/bin/python3 fetch.py $ticker --simple
done
```

Only pull quotes for the most important tickers (top 3-5 per sector) — pulling all 80 is too noisy and slow.

## Phase 3: Compile Report

Generate a markdown report with these sections in order:

1. **四板块总览** — Summary table (market size, CAGR, leader count, core driver)
2. **每个板块逐章** — For each sector:
   - 市场规模 + CAGR
   - 核心趋势 (bullet list, 3-5 items)
   - 10大龙头 table (ticker, name, mcap, focus)
   - 10大新兴 table (same format)
   - 催化剂 + 风险 (paired table or two lists)
3. **金融数据交叉分析** — Cross-sector comparison:
   - 估值对比 table (avg mcap, PE, Beta, YTD return)
   - 资金流向 (institutional flow direction)
   - 关联性矩阵 (correlation coefficients between sectors)
   - 配置建议 table (aggressive/balanced/defensive allocations)
4. **风险提示** — Universal risks + disclaimer

### Report Format Conventions

- All content in **Chinese** (中文)
- Market cap in 万亿/亿 (USD or RMB, consistent per table)
- Ticker format: UPPERCASE (NVDA, not Nvda)
- Tables use standard markdown `| col | col |` syntax
- Include data source attribution line at bottom
- Add disclaimer: "不构成投资建议"

## Phase 4: Deliver

- Save report as `.md` file
- Serve via HTTP if a web server is running
- In WeChat context, provide download link

## Integration

This skill integrates with:
- `stock-tracker` — individual stock quotes via fetch.py (see Phase 2 pitfall)
- `data-research` — the structured research pipeline, but sector-research uses a simpler flat approach since the data is public and doesn't need deduplication/archiving
- `delegate_task` — parallel subagent execution (respect max_concurrent_children=3)

## Reference Data

- `references/sector-stocks-2026Q2.md` — 2026年5月四大板块完整股票清单（80只），含市值/分类。后续研究可直接加载此快照，无需重新搜索。

## Pitfalls Summary

| Pitfall | Mitigation |
|---------|-----------|
| `delegate_task` max 3 concurrent | Split 4+ sectors into batches |
| Subagent doesn't compile results (just searches) | Fall back to manual compilation |
| `fetch.py --simple` only returns first ticker | Loop individual tickers |
| Narrow sector (Robotics) has few ETF holdings | Use pre-built knowledge, don't over-rely on subagent search |
| HTTP server port clash with prior projects | Check `ps aux | grep http.server` before assigning port |
