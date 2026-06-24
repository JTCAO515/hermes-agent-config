#!/usr/bin/env python3
"""
Stock Tracker — A股 + 美股行情数据抓取脚本
用法: python3 fetch.py <code_or_name>
"""

import sys
import json
import urllib.request
import re
from datetime import datetime

def http_get(url, headers=None, timeout=10, decode=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    if decode:
        return raw.decode(decode)
    for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
        try: return raw.decode(enc)
        except UnicodeDecodeError: continue
    return raw.decode('utf-8', errors='replace')

def http_get_raw(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def is_a_share(code):
    return bool(re.match(r'^\d{6}$', code))

def is_us_stock(code):
    return bool(re.match(r'^[A-Za-z]{1,5}$', code))

def normalize_a_code(code):
    code = code.strip().zfill(6)
    return f'sh{code}' if code.startswith(('60', '68')) else f'sz{code}'

# ── A股：腾讯财经 API ────────────────────────────────

def fetch_a_share_full(code):
    """腾讯财经API — 单次请求获取行情+估值
    字段: [1]名称 [2]代码 [3]当前价 [4]昨收 [5]今开
    [6]成交量(手) [30]时间 [31]涨跌额 [32]涨跌幅%
    [33]最高 [34]最低 [37]成交额(万) [38]换手率%
    [39]PE动态 [43]振幅% [44]流通市值(亿) [45]总市值(亿)
    [46]PB [47]涨停 [48]跌停 [61]板块 [72]总股本 [73]流通股本"""
    tc_code = normalize_a_code(code)
    url = f'https://qt.gtimg.cn/q={tc_code}'
    headers = {'Referer': 'https://gu.qq.com/'}
    raw = http_get_raw(url, headers=headers)
    text = raw.decode('gbk', errors='replace')
    m = re.search(r'"([^"]*)"', text)
    if not m:
        return {'error': '无数据'}
    f = m.group(1).split('~')
    if len(f) < 50:
        return {'error': f'字段不足({len(f)})'}
    def _f(idx, cast=float, default=0):
        try:
            val = f[idx]
            return default if val in ('', ' ') else cast(val)
        except: return default
    price = _f(3)
    prev_close = _f(4)
    return {
        'name': f[1], 'code': f[2].replace('sz','').replace('sh',''),
        'exchange': '上交所' if tc_code.startswith('sh') else '深交所',
        'sector': f[61] if len(f)>61 else '',
        'price': price, 'open': _f(5), 'prev_close': prev_close,
        'high': _f(33), 'low': _f(34),
        'volume': _f(6,int), 'amount': _f(37),
        'change_pct': _f(32), 'change_amt': round(price-prev_close,2),
        'amplitude': _f(43), 'pe_dynamic': _f(39), 'pb': _f(46),
        'market_cap': _f(45), 'float_cap': _f(44),
        'turnover_rate': _f(38),
        'total_shares': _f(72,int), 'float_shares': _f(73,int),
        'limit_up': _f(47), 'limit_down': _f(48),
        'timestamp': f[30] if len(f)>30 else '',
    }

# ── A股：K线技术指标 ─────────────────────────────────

def fetch_a_technicals(code):
    tc_code = normalize_a_code(code)
    url = (f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/'
           f'CN_MarketData.getKLineData?symbol={tc_code}&scale=240&ma=5,10,20,60&datalen=120')
    headers = {'Referer': 'https://finance.sina.com.cn'}
    try:
        data = http_get(url, headers=headers, timeout=10)
        klines = json.loads(data)
        if not klines or len(klines) < 5: return {}
        last = klines[-1]; close = float(last['close'])
        ma5 = last.get('ma_price5','?'); ma10 = last.get('ma_price10','?')
        ma20 = last.get('ma_price20','?'); ma60 = last.get('ma_price60','?')
        if ma5!='?' and ma10!='?' and ma20!='?':
            m5,m10,m20 = float(ma5),float(ma10),float(ma20)
            if close>m5>m10>m20: trend='📈多头排列'
            elif close<m5<m10<m20: trend='📉空头排列'
            elif close>m20: trend='→偏多震荡'
            else: trend='→偏空震荡'
        else: trend='数据不足'
        rsi='?'
        if len(klines)>=15:
            gains=losses=0.0
            for i in range(-14,0):
                chg=float(klines[i]['close'])-float(klines[i-1]['close'])
                if chg>0: gains+=chg
                else: losses-=chg
            rsi=round(100-100/(1+gains/losses),1) if losses>0 else 100
        all_lows=sorted([float(k['low']) for k in klines[-60:]])
        all_highs=sorted([float(k['high']) for k in klines[-60:]],reverse=True)
        support=round(sum(all_lows[:5])/5,2) if len(all_lows)>=5 else '?'
        resistance=round(sum(all_highs[:5])/5,2) if len(all_highs)>=5 else '?'
        return {'MA5':ma5,'MA10':ma10,'MA20':ma20,'MA60':ma60,
                'trend':trend,'RSI_14':rsi,'close':close,
                'support':support,'resistance':resistance}
    except Exception as e:
        return {'error':str(e)}

# ── 美股 (CNBC 优先, Yahoo 备选) ───────────────────

def fetch_us_stock_cnbc(symbol):
    """CNBC API — 稳定，字段全"""
    symbol=symbol.upper()
    url=(f'https://quote.cnbc.com/quote-html-webservice/restQuote/'
         f'symbolType/symbol?symbols={symbol}&requestMethod=itv'
         f'&noForm=1&partnerId=2&fund=1&exthrs=0&output=json&events=1')
    headers={'User-Agent':'Mozilla/5.0'}
    try:
        data=http_get(url,headers=headers,timeout=8)
        d=json.loads(data)
        q=d['FormattedQuoteResult']['FormattedQuote'][0]
        p=float(q['last']); pc=float(q.get('previous_day_closing',p))
        return {
            'name':q.get('name',symbol),'symbol':symbol,
            'exchange':q.get('exchange',''),
            'price':p,'prev_close':pc,
            'open':float(q.get('open',0)),'high':float(q.get('high',0)),
            'low':float(q.get('low',0)),
            'volume':q.get('volume','?'),
            'change_pct':round((p-pc)/pc*100,2) if pc else 0,
            'change_amt':round(p-pc,2),
            'pe':q.get('pe','?'),'eps':q.get('eps','?'),
            'market_cap':q.get('mktcapView','?'),'beta':q.get('beta','?'),
            '52w_high':q.get('yrhiprice','?'),'52w_low':q.get('yrloprice','?'),
            'shares':q.get('sharesout','?'),'avg_vol_10d':q.get('tendayavgvol','?'),
            'source':'CNBC',
        }
    except Exception as e:
        return {'error':f'CNBC: {e}','symbol':symbol}

def fetch_us_stock_yahoo(symbol):
    """Yahoo Finance API — 备选"""
    symbol=symbol.upper()
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
    headers={'User-Agent':'Mozilla/5.0'}
    try:
        data=http_get(url,headers=headers,timeout=8)
        d=json.loads(data); meta=d['chart']['result'][0]['meta']
        p=meta.get('regularMarketPrice',0); pc=meta.get('previousClose',0)
        return {
            'name':meta.get('longName',symbol),'symbol':meta.get('symbol'),
            'exchange':meta.get('exchangeName',''),
            'price':p,'prev_close':pc,'open':meta.get('regularMarketOpen'),
            'high':meta.get('regularMarketDayHigh'),'low':meta.get('regularMarketDayLow'),
            'volume':meta.get('regularMarketVolume'),'market_cap':meta.get('marketCap'),
            '52w_high':meta.get('fiftyTwoWeekHigh'),'52w_low':meta.get('fiftyTwoWeekLow'),
            'pe':meta.get('trailingPE','?'),
            'change_pct':round((p-pc)/pc*100,2) if pc else 0,
            'change_amt':round(p-pc,2),'source':'Yahoo',
        }
    except Exception as e:
        return {'error':f'Yahoo: {e}','symbol':symbol}

def fetch_us_stock(symbol):
    """美股：CNBC 优先，失败则 Yahoo"""
    result=fetch_us_stock_cnbc(symbol)
    if 'error' not in result:
        return result
    return fetch_us_stock_yahoo(symbol)

# ── 搜索 ──────────────────────────────────────────────

def search_stock_code(name):
    """腾讯智能搜索 → 股票代码"""
    import urllib.parse
    encoded=urllib.parse.quote(name,encoding='utf-8')
    url=f'https://smartbox.gtimg.cn/s3/?t=all&q={encoded}&fmt=json'
    try:
        raw=http_get_raw(url,headers={'Referer':'https://gu.qq.com/'},timeout=5)
        text=raw.decode('gbk',errors='replace')
        m=re.search(r'v_hint="([^"]*)"',text)
        if m:
            items=m.group(1).split('^')
            results=[]
            for item in items:
                parts=item.split('~')
                if len(parts)>=4:
                    code=parts[1]
                    results.append({'code':code.replace('sh','').replace('sz',''),'name':parts[2]})
            return results
    except: pass
    return []

# ── 格式化 ────────────────────────────────────────────

def format_output(data, simple=False):
    q=data.get('quote',{}); t=data.get('technicals',{})
    cur='¥' if data.get('market')=='A股' else '$'
    name=q.get('name','?'); code=data.get('query','?')
    exch=q.get('exchange',''); sector=q.get('sector','')
    chg=data.get('change_pct',0)
    chg_sign='+' if chg>0 else ''
    if data.get('market')=='A股':
        pe_key='pe_dynamic'
    else:
        pe_key='pe'
    if simple:
        return (f"**{name}** ({code}) | {exch}\n"
                f"现价 {cur}{q.get('price','?')}  {chg_sign}{chg}% | "
                f"PE {q.get(pe_key,q.get('pe','?'))} | "
                f"{'趋势 '+t.get('trend','?') if data.get('market')=='A股' else '52w '+str(q.get('52w_low','?'))+'—'+str(q.get('52w_high','?'))}")
    lines=[f"📊 **{name}** ({code}) — {exch} | {sector}", "",
           "━━━ 💰 实时行情 ━━━",
           f"现价: {cur}{q.get('price','?')}  涨跌: {chg_sign}{chg}% ({data.get('change_amt','?')})",
           f"开: {q.get('open','?')}  昨收: {q.get('prev_close','?')}  "
           f"高/低: {q.get('high','?')}/{q.get('low','?')}",
           f"量: {q.get('volume','?')}  额: {q.get('amount','?')}"]
    lines.append(f"换手: {q.get('turnover_rate','?')}%  PE: {q.get(pe_key,q.get('pe','?'))}  "
                 f"PB: {q.get('pb','?')}  市值: {q.get('market_cap','?')}{'亿' if data.get('market')=='A股' else ''}")
    eps=q.get('eps',''); beta=q.get('beta','')
    if eps or beta:
        extras=[]
        if eps: extras.append(f"EPS: {eps}")
        if beta: extras.append(f"Beta: {beta}")
        lines.append('  '.join(extras))
    if data.get('market')=='A股':
        lines.extend(["","━━━ 📈 技术面 ━━━",
            f"MA5:{t.get('MA5','?')} MA10:{t.get('MA10','?')} "
            f"MA20:{t.get('MA20','?')} MA60:{t.get('MA60','?')}",
            f"RSI(14):{t.get('RSI_14','?')}  趋势:{t.get('trend','?')}"])
        if t.get('support')!='?':
            lines.append(f"支撑:{t.get('support')}  压力:{t.get('resistance')}")
    else:
        h52=q.get('52w_high','?'); l52=q.get('52w_low','?')
        src=q.get('source','?')
        lines.extend(["",f"━━━ 📊 美股数据 (来源: {src}) ━━━",
            f"52周区间: {l52} — {h52}"])
        avgvol=q.get('avg_vol_10d','?')
        if avgvol and avgvol!='?':
            lines.append(f"10日均量: {avgvol}")
    ts=q.get('total_shares',0); fs=q.get('float_shares',0)
    if ts and int(ts)>0:
        lines.append(f"总股本:{int(ts)//100000000}亿  流通:{int(fs)//100000000}亿")
    lu=q.get('limit_up',0); ld=q.get('limit_down',0)
    if lu and float(lu)>0:
        lines.extend(["","━━━ ⚠️ 风控 ━━━",f"涨停:{lu}  跌停:{ld}"])
    return '\n'.join(lines)

# ── 主入口 ────────────────────────────────────────────

def main():
    args=[a for a in sys.argv[1:] if a!='--simple']
    simple='--simple' in sys.argv
    if not args:
        print(json.dumps({'error':'Usage: fetch.py <code> [--simple]'},ensure_ascii=False))
        return
    query=args[0].strip()
    if not is_a_share(query) and not is_us_stock(query):
        results=search_stock_code(query)
        if results:
            query=results[0]['code']
            if not simple:
                print(f"🔍 '{sys.argv[1]}' → {results[0]['name']} ({query})",file=sys.stderr)
        else:
            print(json.dumps({'error':f'未找到"{args[0]}"'},ensure_ascii=False))
            return
    if not simple:
        print(f"⏳ 获取 {query}...",file=sys.stderr)
    if is_a_share(query):
        quote=fetch_a_share_full(query)
        if 'error' in quote:
            print(json.dumps(quote,ensure_ascii=False)); return
        tech=fetch_a_technicals(query)
        result={'query':query,'market':'A股','timestamp':datetime.now().isoformat(),
                'quote':quote,'change_pct':quote.get('change_pct',0),
                'change_amt':quote.get('change_amt',0),'technicals':tech}
    else:
        us=fetch_us_stock(query)
        if 'error' in us:
            print(json.dumps(us,ensure_ascii=False)); return
        result={'query':query,'market':'美股','timestamp':datetime.now().isoformat(),
                'quote':us,'change_pct':us.get('change_pct',0),
                'change_amt':us.get('change_amt',0)}
    if simple: print(format_output(result,simple=True))
    else: print(format_output(result))

if __name__=='__main__':
    main()
