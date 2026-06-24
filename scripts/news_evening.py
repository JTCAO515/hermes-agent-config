#!/usr/bin/env python3
"""Wrapper: run evening news briefing and deliver to Weixin directly."""
import sys, subprocess

r = subprocess.run(
    [sys.executable, "/home/ubuntu/.hermes/scripts/news_briefing.py", "evening"],
    capture_output=True, text=True, timeout=60
)
news = r.stdout.strip()
if r.stderr: print(r.stderr, file=sys.stderr)

if news:
    send_r = subprocess.run(
        [sys.executable, "/home/ubuntu/.hermes/scripts/weixin_send.py"],
        input=news, capture_output=True, text=True, timeout=20
    )
    if send_r.returncode == 0:
        print(f"[OK] Evening news delivered to Weixin", file=sys.stderr)
    else:
        print(f"[FAIL] Delivery failed: {send_r.stderr}", file=sys.stderr)
    print(news)
else:
    print("[WARN] No evening news content", file=sys.stderr)
