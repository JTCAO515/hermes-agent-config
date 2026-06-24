#!/usr/bin/env python3
"""Track the self-interview day counter + manage report.
Stores count in ~/.hermes/cron/counter-interview.txt.
Creates report directory on first run.
Outputs: DAY=<N> WEEK=<week_theme>
"""
import os
import signal

# Ignore SIGPIPE so broken pipe on stdout doesn't kill the script
signal.signal(signal.SIGPIPE, signal.SIG_IGN)

COUNTER_FILE = os.path.expanduser("~/.hermes/cron/counter-interview.txt")
REPORT_DIR = os.path.expanduser("~/projects/self-interview")


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)

    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            try:
                day = int(f.read().strip())
            except ValueError:
                day = 0
        day = min(day + 1, 30)
    else:
        day = 1

    with open(COUNTER_FILE, "w") as f:
        f.write(str(day))

    # Determine week
    if day <= 7:
        week = "week1_daily"
        theme = "日常观察"
        desc = "最近发生了什么、感觉如何"
        style = "具体的日常事件和真实感受"
    elif day <= 14:
        week = "week2_pattern"
        theme = "行为模式"
        desc = "你发现自己什么重复行为"
        style = "具体的行为链和触发场景"
    elif day <= 21:
        week = "week3_values"
        theme = "核心价值"
        desc = "你真正在乎什么"
        style = "具体的取舍时刻和边界"
    else:
        week = "week4_fear"
        theme = "深层恐惧"
        desc = "你不敢承认的是什么"
        style = "具体的回避行为和沉默地带"

    print(f"DAY={day}")
    print(f"WEEK={week}")
    print(f"THEME={theme}")
    print(f"DESC={desc}")
    print(f"STYLE={style}")


if __name__ == "__main__":
    main()
