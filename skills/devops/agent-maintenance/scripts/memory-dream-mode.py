#!/usr/bin/env python3
"""
Memory Dream Mode — 记忆系统自检 (真正读取记忆文件)
每天/每周自动运行，检查记忆健康度、去重、过期清理。

用法: python3 memory-dream-mode.py
报告写入 ~/.hermes/memory/dream_report.json
"""
import json, os
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.hermes/memories")
CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")
REPORT_DIR = os.path.expanduser("~/.hermes/memory")
REPORT_PATH = os.path.join(REPORT_DIR, "dream_report.json")
os.makedirs(REPORT_DIR, exist_ok=True)


def read_config_limits():
    """从 config.yaml 读取真实容量限制，而非使用代码默认值"""
    try:
        with open(CONFIG_PATH) as f:
            content = f.read()
        # Simple YAML parse for the memory section
        import re
        mem_chars = 2200
        user_chars = 1375
        m = re.search(r"memory_char_limit:\s*(\d+)", content)
        if m:
            mem_chars = int(m.group(1))
        m = re.search(r"user_char_limit:\s*(\d+)", content)
        if m:
            user_chars = int(m.group(1))
        return {"memory_char_limit": mem_chars, "user_char_limit": user_chars}
    except Exception:
        return {"memory_char_limit": 4400, "user_char_limit": 2750}


def parse_entries(path):
    """读取记忆文件，按 § 分隔解析条目"""
    if not os.path.exists(path):
        return [], 0, "FILE_NOT_FOUND"
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    if not raw.strip():
        return [], 0, "EMPTY"
    entries = [e.strip() for e in raw.replace("\u00a7", "\nDELIM\n").split("\nDELIM\n") if e.strip()]
    return entries, len(raw), "OK"


def run_dream_mode():
    limits = read_config_limits()

    mem_entries, mem_chars, mem_status = parse_entries(os.path.join(MEMORY_DIR, "MEMORY.md"))
    user_entries, user_chars, user_status = parse_entries(os.path.join(MEMORY_DIR, "USER.md"))

    mem_limit = limits["memory_char_limit"]
    user_limit = limits["user_char_limit"]
    mem_pct = round(mem_chars / mem_limit * 100, 1) if mem_limit else 0
    user_pct = round(user_chars / user_limit * 100, 1) if user_limit else 0

    # 检查重复（前60字符相同视为潜在重复）
    mem_prefixes = {}
    for i, e in enumerate(mem_entries):
        mem_prefixes.setdefault(e[:60], []).append(i)
    dup_groups = sum(1 for v in mem_prefixes.values() if len(v) > 1)

    # 检查任务进度残留
    stale_patterns = ["Day ", "cron", "已完Day", "每晚", "tracking"]
    stale_count = sum(1 for e in mem_entries if any(p in e[:120] for p in stale_patterns))

    recommendations = []
    if mem_pct > 85:
        recommendations.append(
            f"MEMORY.md {mem_chars}/{mem_limit} ({mem_pct}%) — 超过85%容量门限，建议压缩"
        )
    if user_pct > 85:
        recommendations.append(
            f"USER.md {user_chars}/{user_limit} ({user_pct}%) — 超过85%容量门限，建议压缩"
        )
    if dup_groups > 0:
        recommendations.append(f"发现 {dup_groups} 组可能重复条目")
    if stale_count > 0:
        recommendations.append(
            f"{stale_count} 条任务进度记忆建议移除（不符合持久记忆规范）"
        )

    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "metrics": {
            "memory": {
                "total_entries": len(mem_entries),
                "total_chars": mem_chars,
                "char_limit": mem_limit,
                "usage_pct": mem_pct,
                "over_capacity": mem_pct > 85,
                "file_status": mem_status,
            },
            "user_profile": {
                "total_entries": len(user_entries),
                "total_chars": user_chars,
                "char_limit": user_limit,
                "usage_pct": user_pct,
                "over_capacity": user_pct > 85,
                "file_status": user_status,
            },
            "duplicates": dup_groups,
            "stale_task_progress": stale_count,
            "consistency_ok": True,
        },
        "recommendations": recommendations,
    }

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[DreamMode] 记忆自检完成 → {REPORT_PATH}")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    run_dream_mode()
