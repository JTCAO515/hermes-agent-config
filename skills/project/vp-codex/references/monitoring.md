# VP-Codex Monitoring Script

Location: `~/.hermes/scripts/monitor-vp-codex-web.sh`

## What it does

Silent watchdog that checks both VP-Codex-Web and VP-Codex-APK GitHub repos for new commits every 2 hours.

## How it works

1. Calls GitHub API `GET /repos/JTCAO515/VP-Codex-Web/commits` and `GET /repos/JTCAO515/VP-Codex-APK/commits`
2. Compares latest SHA against stored state files in `~/.hermes/cron/states/`
3. If SHA changed: prints change summary (commit messages, dates, authors) to stdout
4. If no change: silent exit (watchdog pattern)

## Cron job

Created via `cronjob` tool:
- `no_agent=True` (script runs without LLM)
- `deliver=weixin` (sends to WeChat)
- Runs every 2 hours

## Manual run

```bash
bash ~/.hermes/scripts/monitor-vp-codex-web.sh
```

## State files

- `~/.hermes/cron/states/state-JTCAO515-VP-Codex-Web.txt` — last known SHA for Web
- `~/.hermes/cron/states/state-JTCAO515-VP-Codex-APK.txt` — last known SHA for APK
