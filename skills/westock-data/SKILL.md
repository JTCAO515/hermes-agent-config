---
name: westock-data
description: 腾讯自选股数据工具 — 查询 A股/港股/美股 实时行情、K线、财务报表、技术指标、资金流向等。数据源：腾讯自选股行情接口，基于 npm 包 westock-data-skillhub。
---

# 腾讯自选股数据工具 (WeStock Data)

数据源：腾讯自选股行情数据接口
支持市场：A股（沪深/科创/北交所）、港股、美股

## 快速开始

```bash
# 搜索股票
npx -y westock-data-skillhub@1.0.3 search 腾讯控股

# 查询K线
npx -y westock-data-skillhub@1.0.3 kline sh600000 --period day --limit 20

# 查询财务报表
npx -y westock-data-skillhub@1.0.3 finance sh600000
```

## 核心命令

### 1. 股票搜索
```bash
npx -y westock-data-skillhub@1.0.3 search <关键词>
npx -y westock-data-skillhub@1.0.3 search <板块名> --sector  # 搜索板块
```

### 2. K线
支持个股、指数、板块、ETF。
参数：`--period day/week/month/season/year`；`--fq qfq/hfq/bfq`；`--limit` 最大2000条。
```bash
npx -y westock-data-skillhub@1.0.3 kline sh600000 --period day --limit 20
npx -y westock-data-skillhub@1.0.3 kline hk00700 --period week --limit 10
npx -y westock-data-skillhub@1.0.3 kline sz000001 --period day --limit 60 --fq qfq
npx -y westock-data-skillhub@1.0.3 kline sh000001 --period day --limit 20    # 指数
```

### 3. 分时
```bash
npx -y westock-data-skillhub@1.0.3 minute sh600000              # 1日
npx -y westock-data-skillhub@1.0.3 minute sh600000 --days 5
```

### 4. 财务报表
默认返回最新1期，`--num` 指定期数，`--type` 指定报表类型。
- A股：`lrb`(利润表) / `zcfz`(资产负债表) / `xjll`(现金流量表)
- 港股：`zhsy`(综合损益表) / `zcfz` / `xjll`
- 美股：`income` / `balance` / `cashflow`

```bash
npx -y westock-data-skillhub@1.0.3 finance sh600000               # 最新1期
npx -y westock-data-skillhub@1.0.3 finance sh600000 --num 4       # 最近4期
npx -y westock-data-skillhub@1.0.3 finance sh600000 --type lrb --num 8
npx -y westock-data-skillhub@1.0.3 finance hk00700 --num 4
npx -y westock-data-skillhub@1.0.3 finance usBABA --type income --num 4
```

⚠️ 港股返回港元/美元，美股返回美元，展示时需标注货币单位。

### 5. 公司简况
```bash
npx -y westock-data-skillhub@1.0.3 profile sh600000
npx -y westock-data-skillhub@1.0.3 profile sh600000,hk00700,usAAPL  # 支持批量
```

### 6. 资金与交易分析
```bash
npx -y westock-data-skillhub@1.0.3 hkfund hk00700     # 港股资金流向
npx -y westock-data-skillhub@1.0.3 asfund sh600000     # A股资金流向
npx -y westock-data-skillhub@1.0.3 usfund usAAPL       # 美股卖空数据
npx -y westock-data-skillhub@1.0.3 lhb sz000001         # 龙虎榜（仅沪深）
npx -y westock-data-skillhub@1.0.3 blocktrade sz000001  # 大宗交易（仅沪深）
npx -y westock-data-skillhub@1.0.3 margintrade sz000001 # 融资融券（仅沪深）
```

### 7. 技术指标
支持分组：`ma`、`macd`、`kdj`、`rsi`、`boll`、`bias`、`wr`、`dmi`、`all`
```bash
npx -y westock-data-skillhub@1.0.3 technical sh600000                   # 全部指标
npx -y westock-data-skillhub@1.0.3 technical sh600000 --group macd      # 特定分组
npx -y westock-data-skillhub@1.0.3 technical sh600000 --group ma,rsi    # 多分组
npx -y westock-data-skillhub@1.0.3 technical sh600000 --group macd --start 2026-02-01 --end 2026-03-01
```

### 8. 筹码成本（仅沪深A股）
```bash
npx -y westock-data-skillhub@1.0.3 chip sh600519
npx -y westock-data-skillhub@1.0.3 chip sh600519 --start 2026-02-01 --end 2026-03-01
```

### 9. 股东结构（仅A股和港股）
```bash
npx -y westock-data-skillhub@1.0.3 shareholder sh600519
npx -y westock-data-skillhub@1.0.3 shareholder hk00700
```

### 10. 分红数据
```bash
npx -y westock-data-skillhub@1.0.3 dividend sh600519
npx -y westock-data-skillhub@1.0.3 dividend sh600519 --years 5
npx -y westock-data-skillhub@1.0.3 dividend sh600519,hk00700,usAAPL  # 批量
```

### 11. ETF 基金数据
```bash
npx -y westock-data-skillhub@1.0.3 etf sh510300           # ETF详情
npx -y westock-data-skillhub@1.0.3 etf-holdings sh510300  # ETF持仓
npx -y westock-data-skillhub@1.0.3 etf-nav sh510300 --start 2026-01-01 --end 2026-03-31  # ETF净值
```

## 批量查询
所有查询类命令（除 `search` 和 `minute` 外）均支持逗号分隔多股代码：
```bash
npx -y westock-data-skillhub@1.0.3 kline sh600000,sh600519 --period day --limit 20
```

## 股票代码前缀
| 市场 | 前缀 | 示例 |
|------|------|------|
| 上海A股 | sh | sh600519 |
| 深圳A股 | sz | sz000001 |
| 北交所 | bj | bj830799 |
| 港股 | hk | hk00700 |
| 美股 | us | usAAPL |
