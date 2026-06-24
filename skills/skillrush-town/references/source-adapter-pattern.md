# Source Adapter Pattern

Use this when extending Skillrush Town beyond the default ClawHub Top100 source.

Skillrush Town is not just a static page. The page is the public surface; the Skill is the maintenance workflow that teaches future agents how to monitor changing public sources safely.

## Source Families

### Cursor or pagination leaderboard

Examples:

- ClawHub Top100 Skills
- Any marketplace ranking that needs page-by-page traversal

Required contract:

- canonical endpoint or page URL
- sort order
- page size
- pagination rule
- stable item key
- required numeric fields
- failure and partial-fetch behavior

### Changelog or release feed

Examples:

- Claude Code changelog at `https://code.claude.com/docs/en/changelog`
- Product docs pages that publish dated release notes

Required contract:

- canonical changelog URL
- entry boundary rule
- date extraction rule
- title extraction rule
- body or summary extraction rule
- stable entry key, usually date plus normalized title
- diff rule for new, updated, and removed entries

### Dynamic model or product leaderboard

Examples:

- Artificial Analysis model leaderboard at `https://artificialanalysis.ai/leaderboards/models`
- Model speed, price, intelligence, or benchmark ranking tables

Required contract:

- canonical leaderboard URL
- whether data is available in HTML, embedded JSON, API calls, or browser runtime
- stable model key
- metric fields and units
- rank and metric comparison rules
- known limitations if the page requires browser rendering

## Adapter Rules

Before adding a new source adapter, create a source-specific contract file:

```text
skills/skillrush-town/references/source-contract-<source>.md
```

The adapter must define:

- source name
- canonical URL or request
- extraction method
- stable keys
- snapshot schema
- diff semantics
- limitations
- headless validation strategy

## Output Rules

Every source should still follow the town workflow:

1. fetch public source
2. normalize rows or entries
3. write dated snapshot
4. compare with previous snapshot
5. write human-readable report
6. update latest pointer and date index
7. expose public page or readable artifact
8. optionally send an Agent reminder

## Testing Rules

Do not make browser automation a required CI dependency unless the source truly cannot be tested headlessly.

Preferred tests:

- mock network responses
- fixture HTML or JSON
- source contract lock tests
- stable-key and diff tests
- partial-fetch limitation tests

Browser checks can exist as optional manual validation.

## Privacy Boundary

Only monitor public sources by default. Do not commit tokens, cookies, private inbox content, private API payloads, or user-specific data.

If a future adapter needs credentials, it must be disabled by default and must not publish private artifacts to GitHub Pages.
