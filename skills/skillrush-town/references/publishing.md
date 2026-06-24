# Publishing

Skillrush Town is designed for GitHub Pages.

## Public Site Files

- `index.html`
- `assets/app.js`
- `assets/styles.css`
- `data/dates.json`
- `data/latest.json`
- `data/snapshots/YYYY-MM-DD.json`
- `data/reports/YYYY-MM-DD.md`

The page supports:

```text
/?date=YYYY-MM-DD
```

## GitHub Actions

Use `.github/workflows/update.yml` for daily updates:

1. checkout
2. setup Python
3. run `python scripts/clawhub_daily.py`
4. commit changed `data/*`
5. deploy Pages

The project does not need API keys for the default ClawHub public ranking.

## Release Checklist

- GitHub Pages opens on mobile.
- Latest date loads by default.
- `?date=YYYY-MM-DD` loads a historical snapshot.
- First-run reports do not claim strict daily deltas.
- README says both "read my page" and "fork your own town".
- Skill validator passes.

