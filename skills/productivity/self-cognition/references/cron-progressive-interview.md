# Cron-Based Progressive Interview (30-Day Pattern) — 完整实现

## 文件清单

| 文件 | 说明 |
|------|------|
| `~/.hermes/scripts/interview-tracker.py` | 天数计数器脚本 |
| `~/.hermes/cron/counter-interview.txt` | 计数器持久文件 |
| `~/projects/self-interview/report.md` | 累积报告 |

## interview-tracker.py 完整代码

```python
#!/usr/bin/env python3
"""Track the self-interview day counter + manage report.
Stores count in ~/.hermes/cron/counter-interview.txt.
Creates report directory on first run.
Outputs: DAY=<N> WEEK=<week_theme>
"""

import os

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
```

## Cron 配置

```yaml
schedule: "0 21 * * *"      # 每日21:00
deliver: origin               # 发回微信
script: interview-tracker.py  # 相对 ~/.hermes/scripts/
```

## Prompt 模板（含变量注入）

```markdown
30天自我访谈计划，每天晚上执行一次。

请扮演一位资深的存在主义心理咨询师。根据下面的天数阶段，问3个具体的问题。

规则：
- 问题要具体，不要抽象飘忽
- 问题由浅入深递进，第一个最轻，第三个最深
- 只说问题，不要安慰，不要给建议，不要评价
- 用简体中文，语言自然

当前是第 DAY 天，阶段「THEME」— DESC。风格要求：STYLE。

在问完3个问题之后，用以下格式记录到报告文件：
1. 先写一段今天的问题和我的预期分析
2. 等用户回答后，下一次执行时读取报告更新

报告路径：~/projects/self-interview/report.md

如果报告文件已存在，先读取之前的报告了解进度和之前的回答，再问今天的问题。
如果 report.md 的累计分析中有提到今天需要注意的方向，把今天的问题往那个方向调整。

最后更新报告时，每天追加以下内容：
- 今天的日期和第 N 天
- 今天问了哪3个问题
- 用户的回答摘要
- 今天的小分析（从回答中看到了什么模式/信号）
- 截止今天的整体分析（累计趋势、重复出现的主题、变化方向）
```

## 重置方法

```bash
# 重置计数器（从头开始）
echo 0 > ~/.hermes/cron/counter-interview.txt

# 或删除计数器文件（下次执行自动从第1天开始）
rm ~/.hermes/cron/counter-interview.txt

# 手动触发立即执行
hermes cron run --job-id <job-id>
```
