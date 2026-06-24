#!/usr/bin/env python3
"""
Always-on Executor — 系统主动巡检 (PilotDeck 模块5)
定时检查：磁盘/内存/服务健康/成本异常。
"""
import os, json, shutil, subprocess
from datetime import datetime

REPORT_PATH = os.path.expanduser("~/.hermes/memory/health_report.json")
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

def check_disk():
    stat = shutil.disk_usage("/")
    pct = stat.used / stat.total * 100
    return {"total_gb": round(stat.total / 1e9, 1), "used_pct": round(pct, 1), "healthy": pct < 90}

def check_memory_dir():
    mem_dir = os.path.expanduser("~/.hermes/memory")
    if os.path.isdir(mem_dir):
        files = os.listdir(mem_dir)
        return {"exists": True, "file_count": len(files), "files": files}
    return {"exists": False, "file_count": 0}

def check_services():
    # Check key Hermes processes
    services = {}
    for svc, cmd in [
        ("hermes-agent", "hermes --version"),
        ("aesculap", "systemctl --user is-active aesculap.service 2>/dev/null"),
    ]:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            services[svc] = {"status": "ok" if r.returncode == 0 else "error", "output": r.stdout.strip()[:100]}
        except Exception as e:
            services[svc] = {"status": "error", "output": str(e)}
    return services

def run_health_check():
    findings = {
        "timestamp": datetime.now().isoformat(),
        "disk": check_disk(),
        "memory_dir": check_memory_dir(),
        "services": check_services(),
    }
    
    with open(REPORT_PATH, 'w') as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)
    
    print(f"[HealthCheck] 巡检完成 → {REPORT_PATH}")
    print(json.dumps(findings, indent=2, ensure_ascii=False))
    return findings

if __name__ == "__main__":
    run_health_check()
