#!/usr/bin/env python3
"""
天孚通信 300394 盘中监控
每30分钟运行一次，波动超2%报警
"""
import sys, os, json, urllib.request, re
from datetime import datetime

STOCK = "300394"
THRESHOLD = 2.0  # %
STATE_FILE = "/tmp/tfcc_monitor_state.json"

# ── 获取行情 ──
def fetch():
    url = "https://qt.gtimg.cn/q=sz300394"
    req = urllib.request.Request(url, headers={"Referer": "https://gu.qq.com/"})
    raw = urllib.request.urlopen(req, timeout=10).read()
    text = raw.decode("gbk", errors="replace")
    m = re.search(r'"([^"]*)"', text)
    if not m:
        return None
    f = m.group(1).split("~")
    if len(f) < 50:
        return None
    def _f(idx, cast=float, default=0):
        try:
            v = f[idx]
            return default if v in ("", " ") else cast(v)
        except:
            return default
    return {
        "name": f[1],
        "price": _f(3),
        "open": _f(5),
        "prev_close": _f(4),
        "change_pct": _f(32),
        "high": _f(33),
        "low": _f(34),
        "volume": _f(6, int),
        "amount": _f(37),
        "pe": _f(39),
        "timestamp": f[30] if len(f) > 30 else "",
    }

# ── 加载/保存状态 ──
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

# ── 主逻辑 ──
def main():
    now = datetime.now()
    data = fetch()
    if not data:
        print("[SKIP] 未获取到数据（可能非交易时间）")
        return

    state = load_state()
    open_price = state.get("open_price")
    alerted_before = state.get("alerted", False)
    prev_price = state.get("prev_price")

    # 首次运行：记录开盘价
    if open_price is None or data["open"] != 0 and abs(data["open"] - open_price) > 0.01:
        open_price = data["open"] if data["open"] != 0 else data["price"]
        state["open_price"] = open_price
        state["alerted"] = False
        state["start_time"] = now.isoformat()
        save_state(state)
        print(f"[INIT] 开盘价: ¥{open_price}  @ {now.strftime('%H:%M:%S')}")
        print(f"天孚通信 现价 ¥{data['price']}  涨跌 {data['change_pct']}%")
        return

    # 计算波动
    pct_from_open = (data["price"] - open_price) / open_price * 100
    pct_from_prev = (data["price"] - prev_price) / prev_price * 100 if prev_price else 0

    print(f"[{now.strftime('%H:%M:%S')}] 现价 ¥{data['price']}  "
          f"距开盘 {pct_from_open:+.2f}%  |  涨跌 {data['change_pct']}%")

    # 触发报警
    alert = ""
    if abs(pct_from_open) >= THRESHOLD and not alerted_before:
        direction = "📈拉升" if pct_from_open > 0 else "📉下挫"
        alert = (f"\n⚠️ **天孚通信 波动预警** ⚠️\n"
                 f"当前: ¥{data['price']}  距开盘: {pct_from_open:+.2f}%\n"
                 f"最高: ¥{data['high']}  最低: ¥{data['low']}\n"
                 f"PE: {data['pe']}  成交: {data['amount']}万")
        state["alerted"] = True
    elif abs(pct_from_open) < THRESHOLD and alerted_before:
        state["alerted"] = False  # 回落重置

    state["prev_price"] = data["price"]
    state["last_check"] = now.isoformat()
    save_state(state)

    if alert:
        print(alert)

if __name__ == "__main__":
    main()
