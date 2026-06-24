# WC26 Odds Pipeline — Reference Configuration

## Project Paths
- Main: `/home/ubuntu/projects/WC26-Main` → `worldcup.jtcao.space` (Vercel)
- Nami: `/home/ubuntu/projects/WC26-Nami` → `wc26nami.jtcao.space` (Vercel)

## API Key
`7bd3207b09a2b09053a7df453b33623d` (free tier, ~1000 req/mo)

## Cron Schedule
```
*/30 * * * * /home/ubuntu/projects/WC26-Main/data/odds_fetcher_wrapper.sh    # Primary
*/30 * * * * /home/ubuntu/projects/WC26-Nami/data/odds_fetcher_wrapper.sh    # Pulls from Main
```

## Git Remotes
```bash
# Main: HTTPS PAT
git remote set-url origin https://github.com/JTCAO515/WC26-Main.git
# Nami: HTTPS PAT
git remote set-url origin https://github.com/JTCAO515/WC26-Nami.git
```

## FIFA Sync (separate pipeline)
Blocked from China VPS — uses Xray HTTP proxy:
```bash
export https_proxy=http://127.0.0.1:10809
```
Cron: `0 */2 * * * .../fifa_sync_wrapper.sh`

## Version
v7.0.0 — deployed 2026-06-19
Key files: `api/index.py`, `data/odds_fetcher.py`, `data/odds_fetcher_wrapper.sh`, `data/live_odds.json`
