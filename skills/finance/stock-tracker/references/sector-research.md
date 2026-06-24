# Sector Research — Multi-Sector Stock Research

> Absorbed from standalone `sector-research` skill (2026-06-02). Use for tasks like "研究 AI/芯片/机器人/生物科技 四个热点板块" — parallel sector research across multiple industries.

## When to Use

- User asks for sector/板块/赛道 research across multiple industries
- User wants leader + emerging stock lists with analysis
- Task involves identifying ALL stocks in a sector then filtering to top 10 + 10

## Phase 1: Parallel Sector Search

Use `delegate_task` to research all sectors in parallel (max 3 concurrent per batch).

### Subagent Goal Template

```python
context: "Search ETF holdings (BOTZ/SMH/IBB etc), market reports."
goal: "Research ALL US-listed stocks in [SECTOR]. Identify 10 leaders (large-cap, established) + 10 emerging (smaller, high-potential)."
toolsets: ["web","search"]
```

### Pitfall: Subagent May Not Compile

Subagents sometimes return only search tool calls without compiling (~30% for complex sectors like Robotics). Fall back to manual compilation with known stocks.

## Phase 2: Stock Quote Enrichment

Pull real-time quotes for key tickers:
```bash
for ticker in NVDA MSFT GOOGL; do
  /venv/bin/python3 fetch.py $ticker --simple
done
```

**CRITICAL:** `--simple` only returns the FIRST ticker — loop individually or use `background=true`.

## Phase 3: Compile Report

Generate markdown with:
1. **Multi-Sector Overview** — Summary table (market size, CAGR, leader count, core driver)
2. **Per-Sector Chapters** — For each: market size + CAGR, core trends, top 10 leaders table, top 10 emerging table, catalysts + risks
3. **Cross-Sector Financial Analysis** — Valuation comparison, capital flow, correlation, allocation suggestions
4. **Risk Disclaimer** — "不构成投资建议"

All content in Chinese. Market cap in 万亿/亿. Tickers in UPPERCASE.

## Pitfalls

| Pitfall | Mitigation |
|---------|-----------|
| `delegate_task` max 3 concurrent | Split 4+ sectors into batches |
| Subagent doesn't compile results | Fall back to manual compilation |
| `fetch.py --simple` only returns first ticker | Loop individual tickers |
| Narrow sector (Robotics) has few ETF holdings | Use pre-built knowledge |
