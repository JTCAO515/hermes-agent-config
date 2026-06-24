#!/usr/bin/env python3
"""Monitor Claude Code status and notify when recovered."""
import json, os, urllib.request, time

STATUS_URL = "https://status.claude.com/api/v2/components.json"
STATE_FILE = os.path.expanduser("~/.hermes/cron/states/claude-code-status.txt")
CLAUDE_CODE_ID = "yyzkbfz2thpt"

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

def get_status():
    req = urllib.request.Request(STATUS_URL, headers={
        "Accept": "application/json",
        "User-Agent": "hermes-status-monitor/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

data = get_status()
if "error" in data:
    print(f"STATUS_CHECK_ERROR: {data['error']}")
    exit(1)

# Find Claude Code
cc_status = "unknown"
for c in data.get("components", []):
    if c["id"] == CLAUDE_CODE_ID:
        cc_status = c["status"]
        break

# Read previous state
prev = ""
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        prev = f.read().strip()

# Check if it's recovering: was degraded/outage -> now operational
non_ok_states = {"degraded_performance", "partial_outage", "major_outage"}
if cc_status == "operational" and prev in non_ok_states:
    print(f"✅ Claude Code 已恢复！\n  状态已从 {prev} 变更为 operational\n  https://status.claude.com")
elif cc_status in non_ok_states:
    print(f"⚠️ Claude Code 仍受影响\n  当前状态: {cc_status}\n  上次检查: {prev if prev else '首次检查'}")
# else: nothing changed, silent

# Save current state
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w") as f:
    f.write(cc_status)
