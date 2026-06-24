# WC26 Team Name Mapping (FIFA Official → Dataset)

**Rule:** All internal data must use FIFA official names. The `FLAGS` map in `web/app.js` must use the same names.

## Standard Mapping

| Old Name (Dataset) | FIFA Official Name | Flag | Found In |
|-------------------|-------------------|------|----------|
| South Korea | Korea Republic | 🇰🇷 | teams.json, matches.json, FLAGS |
| Czech Republic | Czechia | 🇨🇿 | teams.json, matches.json, FLAGS |
| Turkey | Türkiye | 🇹🇷 | teams.json, matches.json, FLAGS |
| Bosnia/Herz. | Bosnia and Herz. | 🇧🇦 | teams.json, matches.json, FLAGS |
| Cape Verde | Cabo Verde | 🇨🇻 | teams.json, matches.json, FLAGS |
| Iran | IR Iran | 🇮🇷 | teams.json, matches.json, FLAGS |
| Ivory Coast | Côte d'Ivoire | 🇨🇮 | teams.json, matches.json, FLAGS |
| Curacao | Curaçao | 🇨🇼 | teams.json, matches.json, FLAGS |
| DR Congo | Congo DR | 🇨🇩 | teams.json, matches.json, FLAGS |
| United States | USA | 🇺🇸 | teams.json, matches.json, FLAGS |

## Files That Need Updating When Names Change

1. **`data/wc2026_teams.json`** — `team_ratings` dict keys
2. **`data/wc2026_matches.json`** — `team_a`, `team_b` fields in every match object
3. **`data/generate_wc2026.py`** — `GROUPS` dict, `KNOWN_RESULTS` keys
4. **`web/app.js`** — `FLAGS` const mapping
5. **`football_predictor/wc_api.py`** — `_normalize_team()` mapping
6. **`football_predictor/tournament_sim.py`** — `GROUPS` dict (mirrors generator)
7. **`football_predictor/chat_engine.py`** — `TEAM_NAME_MAP` (chat display names)

## Pitfall: Wrong Opponents

In the original dataset, Mexico's result was recorded as vs South Korea but the real match was vs South Africa. Always verify the **pairing** not just the name:
- Check GROUP_MATCHUPS ordering vs FIFA schedule
- Verify MD1 pairings produce the real-world matchups
- Check that the winning/losing teams make sense with the scores

## Pitfall: Flag Emoji Consistency

Some flags use special Unicode (England 🏴󠁧󠁢󠁥󠁮󠁧󠁿, Scotland 🏴󠁧󠁢󠁳󠁣󠁴󠁿). These are multi-codepoint sequences and must be stored as literal strings, not composed.
