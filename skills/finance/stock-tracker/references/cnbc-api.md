# CNBC Quote API

Stable, no-auth REST API for US stock quotes — works from servers where Yahoo Finance is rate-limited.

## Endpoint

```
GET https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol
```

## Parameters

| Param | Value | Notes |
|-------|-------|-------|
| `symbols` | `INTC` | Uppercase ticker |
| `requestMethod` | `itv` | Required |
| `noForm` | `1` | |
| `partnerId` | `2` | |
| `fund` | `1` | Include fundamental data |
| `exthrs` | `0` | No extended hours |
| `output` | `json` | |
| `events` | `1` | |

## Full URL

```
https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=INTC&requestMethod=itv&noForm=1&partnerId=2&fund=1&exthrs=0&output=json&events=1
```

## Response Fields

Root: `FormattedQuoteResult.FormattedQuote[0]`

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `name` | str | `Intel Corp` | |
| `symbol` | str | `INTC` | |
| `exchange` | str | `NASDAQ` | |
| `last` | str | `104.93` | Current price |
| `previous_day_closing` | str | `108.17` | Prev close |
| `open` | str | `106.98` | |
| `high` | str | `109.43` | |
| `low` | str | `102.40` | |
| `change` | str | `-3.24` | Dollar change |
| `change_pct` | str | `-3.00%` | Includes % sign |
| `volume` | str | `50,314,385` | **Includes commas** |
| `pe` | str | `-167.49` | Can be negative |
| `eps` | str | `-0.63` | |
| `beta` | str | `2.20` | |
| `mktcapView` | str | `527.378B` | With suffix (B, M) |
| `yrhiprice` | str | `132.75` | 52-week high |
| `yrloprice` | str | `18.97` | 52-week low |
| `tendayavgvol` | str | `157.28M` | 10-day avg volume |
| `sharesout` | str | `5.03B` | Shares outstanding |

## Parsing Notes

- `volume`: strip commas before `int()` conversion
- `change_pct`: strip `%` suffix
- Market cap / sharesout / avgvol include suffix (B, M) — keep as display strings
- `pe` can be negative (loss-making companies) — don't filter
- All numeric fields come as strings

## Usage in fetch.py

```python
def fetch_us_stock_cnbc(symbol):
    url = f'https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={symbol}&requestMethod=itv&noForm=1&partnerId=2&fund=1&exthrs=0&output=json&events=1'
    data = http_get(url, headers={'User-Agent': 'Mozilla/5.0'})
    q = json.loads(data)['FormattedQuoteResult']['FormattedQuote'][0]
    return {
        'name': q.get('name', symbol),
        'price': float(q['last']),
        'prev_close': float(q.get('previous_day_closing', q['last'])),
        'pe': q.get('pe', '?'),
        'eps': q.get('eps', '?'),
        'beta': q.get('beta', '?'),
        'market_cap': q.get('mktcapView', '?'),
        '52w_high': q.get('yrhiprice', '?'),
        '52w_low': q.get('yrloprice', '?'),
        'avg_vol_10d': q.get('tendayavgvol', '?'),
        # ...
    }
```
