---
name: stock-tracker
version: 1.0.0
description: |
  Track A-shares (A股) and US stocks (美股) by ticker or name.
  Returns: real-time quotes, financials, capital flow, technical indicators,
  news/sentiment, and risk alerts. Works via web scraping + Python.
triggers:
  - "stock"
  - "股票"
  - "A股"
  - "美股"
  - "股价"
  - "行情"
  - "财报"
  - "ticker"
  - "AAPL"
  - "TSLA"
  - "000001"
  - "600519"
  - "查一下"
tools:
  - terminal
  - web_search
  - browser
  - multi-search-engine
mutating: false
---

# Stock Tracker — A股 + 美股行情追踪

输入股票代码或名称，返回八维度的完整股票画像。

## 识别规则

| 代码格式 | 市场 | 数据源 |
|----------|------|--------|
| 6位纯数字 (000xxx, 002xxx, 300xxx, 600xxx, 688xxx) | A股 | 腾讯财经 (行情+估值) + 新浪K线 (技术面) |
| 1-5位字母 (AAPL, TSLA, INTC, BABA...) | 美股 | CNBC API (主) → Yahoo Finance (备) |
| 中文名称 (茅台, 比亚迪...) | 先搜索确认代码再查 | 腾讯智能搜索 → A股流程 |

## Pitfalls

- **Yahoo Finance 在国内服务器/容器极易429限流** — 不要作为美股首选，CNBC 更稳定
- **东方财富 push2 API 从此服务器不可达** — 返回空响应，不要尝试
- **雪球 API 需要登录态** — `stock.xueqiu.com/v5/stock/quote.json` 返回 400016 认证错误
- **Chrome browser 在容器环境不可用** — 无 sandbox，`browser_navigate` 会失败，用 web_fetch/web_search 代替
- **Python 依赖路径**：脚本需要用 `/home/ubuntu/.hermes/hermes-agent/venv/bin/python3` 运行（yfinance/akshare 装在此 venv 中）
- **CNBC volume 字段带逗号**（如 `"48,669,475"`）— 脚本中 `int(q.get('volume','0').replace(',',''))` 处理
- **`--simple` 多代码只返回第一只** — `fetch.py NVDA AAPL MSFT --simple` 仅输出 NVDA。批量行情需逐只调用或用 `background=true` 并行跑，不要一次传多个 ticker 期望批量输出
- **`--simple` 美股格式**: `**公司名** (TICKER) | 交易所\n现价 $XX.XX  ±X% | PE XX | 52w $low—$high` — 单行输出，适合嵌入报告

## Phase 1: 执行 fetch.py

直接跑脚本，一条命令搞定 A股：

```bash
/venv/bin/python3 ~/.hermes/skills/finance/stock-tracker/scripts/fetch.py <code_or_name> [--simple]
```

- 自动识别A股代码(6位数字)、英文代码(美股)、中文名称
- `--simple` 输出极简版一行

**数据来源：**
- A股行情+估值：腾讯财经 API (`qt.gtimg.cn`) — 单请求返回价格/PE/PB/市值/换手率/股本
- A股技术指标：新浪K线 API — MA5/MA10/MA20/MA60/RSI/支撑压力
- 名称搜索：腾讯智能搜索 (`smartbox.gtimg.cn`)
- 美股行情：**CNBC API 优先** (`quote.cnbc.com`) — 含 PE/EPS/Beta/52周区间/10日均量
- 美股备选：Yahoo Finance Chart API（此服务器极易429限流）
- CNBC API 完整字段参考 → `references/cnbc-api.md`

## Phase 2: 根据结果回答

脚本输出已包含格式化报告，直接展示给用户。如需补充：

- **资金流向/北向资金**：用 `web_fetch` 搜 "东方财富 {code} 资金流向"
- **公告新闻**：用 `web_fetch` 或 `multi-search-engine` 搜 "{name} 最新公告"
- **美股**：用 `web_fetch` 或 `browser` 访问 Yahoo Finance / CNBC

## 输出格式

脚本自动生成：

```
📊 **平安银行** (000001) — 深交所 | GP-A

━━━ 💰 实时行情 ━━━
现价: ¥10.86  涨跌: 0.0% (0.0)
开: 10.83  昨收: 10.86  高/低: 10.92/10.83
量: 793529  额: 86256.0
换手: 0.41%  PE: 4.89  PB: 0.45  市值: 2107.48亿

━━━ 📈 技术面 ━━━
MA5:10.98 MA10:11.146 MA20:11.172 MA60:?
RSI(14):44.2  趋势:📉空头排列
支撑:10.61  压力:11.53
总股本:194亿  流通:194亿

━━━ ⚠️ 风控 ━━━
涨停:11.95  跌停:9.77
```

极简版 (`--simple`)：

```
**贵州茅台** (600519) | 上交所
现价 ¥1324.3  +0.1% | PE 20.05 | 趋势 📉空头排列
```

## Absorbed Sub-Skills

### Sector Research (`references/sector-research.md`)
Multi-sector stock research: parallel sector search via delegate_task, stock quote enrichment, and report compilation. Use when the user asks about sector/板块/赛道 analysis across multiple industries. Includes pitfall mitigations for subagent failures and fetch.py limitations.

### THS Advanced Analysis (`references/ths-advanced-analysis.md`)
Deep-dive stock analysis via thsdk: minute K-lines (1m/5m/15m/30m/60m/120m), sector/index data (CSI indices/Shenwan sectors/concept blocks), multi-stock batch comparison (tables + normalized charts + correlation heatmaps), depth-of-book, big order flow, call auction anomalies, intraday tick data, Wencai NLP natural-language stock screening, Hong Kong/US/forex/futures market data, and real-time news feeds. Use when the user needs tick-level analysis, sector rotation tracking, cross-asset comparison, or natural-language stock screening (e.g. "连续3日主力净流入, 换手率大于5%"). Requires `pip install --upgrade thsdk`.
