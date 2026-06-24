# External Service Status Watchdog

> Poll an external status API (statuspage.io or similar), track state transitions, only alert on change.

## Use Cases

- Monitor a SaaS service (Claude, OpenAI, Vercel, GitHub) for outage → recovery transitions
- Track component-level status (e.g., "Claude Code" specifically, not the whole platform)
- Get notified when a service comes back online without human checking

## Architecture

```
cron (every 5m)
  └── check-service-status.py (no_agent=True)
        ├── GET /api/v2/components.json (or similar status API)
        ├── Compare current status with saved state file
        ├── If changed: print notification → delivered to user
        └── If same: silent (no output = no delivery)
```

## Script Template

```python
#!/usr/bin/env python3
"""Monitor an external service status and notify on transitions."""
import json, os, urllib.request

STATUS_URL = "https://status.example.com/api/v2/components.json"
STATE_FILE = os.path.expanduser("~/.hermes/cron/states/service-status.txt")
TARGET_COMPONENT_ID = "abc123"  # specific component to monitor

# Required: strip proxy — statuspage APIs are global and direct-accessible
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

# Find target component
current_status = "unknown"
for c in data.get("components", []):
    if c["id"] == TARGET_COMPONENT_ID:
        current_status = c["status"]
        break

# Read previous state
prev = ""
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        prev = f.read().strip()

# Status values: operational, degraded_performance, partial_outage, major_outage
NON_OK = {"degraded_performance", "partial_outage", "major_outage"}

if current_status == "operational" and prev in NON_OK:
    print(f"✅ ServiceName 已恢复！状态从 {prev} → operational\n  https://status.example.com")
elif current_status != prev and prev:  # any other transition
    print(f"⚠️ ServiceName 状态变更: {prev} → {current_status}\n  https://status.example.com")
elif current_status in NON_OK:
    # Still degraded — silent (no repeat alerting)
    pass
# Save current state
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w") as f:
    f.write(current_status)
```

## Cron Setup

```bash
cronjob action=create \
  schedule="5m" \
  script="check-service-status.py" \
  no_agent=true \
  name="ServiceName Status Monitor" \
  deliver="origin"
```

## Key Design Decisions

1. **State transitions, not every-tick alerts** — Only notify when status actually changes. If it's still degraded, skip. Avoids notification fatigue.
2. **Recovery-first** — The primary value is knowing "it's back." Secondary is "status changed."
3. **Proxy must be unset** — statuspage.io and similar global services are available without proxy. The proxy (if set) may introduce timeouts ("The read operation timed out").
4. **State file** — One file per monitored service, saved under `~/.hermes/cron/states/service-name-status.txt`.
5. **no_agent=True** — Script output IS the message. Empty output = silent.

## Pitfalls

- **Proxy interference**: If `http_proxy` is set globally, the status API call routes through it and may timeout. Always unset proxy env vars at script start.
- **Component ID changes**: If the status page provider reconfigures, component IDs may change. Validate periodically or catch "not found" gracefully.
- **Rate limits**: Most statuspage.io instances allow unauthenticated requests. If hitting limits, add a longer interval (10-15m instead of 5m).
- **False recovery**: Some services go "operational" briefly before crashing again. Consider adding a "sustained operational" check (2 consecutive OK checks before notification).
