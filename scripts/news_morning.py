#!/usr/bin/env python3
"""Wrapper: run morning/evening news briefing and deliver to Weixin directly."""
import sys, subprocess

mode = sys.argv[1] if len(sys.argv) > 1 else "morning"

# Generate the news briefing
r = subprocess.run(
    [sys.executable, "/home/ubuntu/.hermes/scripts/news_briefing.py", mode],
    capture_output=True, text=True, timeout=60
)
news = r.stdout.strip()
if r.stderr:
    print(r.stderr, file=sys.stderr)

if news:
    # Send to Weixin directly via REST API (bypasses Hermes async gateway bug)
    send_r = subprocess.run(
        [sys.executable, "/home/ubuntu/.hermes/scripts/weixin_send.py"],
        input=news, capture_output=True, text=True, timeout=20
    )
    if send_r.returncode == 0:
        print(f"[OK] News delivered to Weixin ({mode})", file=sys.stderr)
    else:
        print(f"[FAIL] Weixin delivery failed: {send_r.stderr}", file=sys.stderr)
    # Also output for cron logging
    print(news)
else:
    print(f"[WARN] No news content generated for {mode}", file=sys.stderr)
