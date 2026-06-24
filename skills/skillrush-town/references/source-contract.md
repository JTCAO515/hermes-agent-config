# Source Contract

Use this before changing ClawHub data ingestion.

## Canonical Ranking

Primary request:

```text
POST https://wry-manatee-359.convex.cloud/api/query
path=skills:listPublicPageV4
```

Args:

```json
{
  "sort": "downloads",
  "dir": "desc",
  "nonSuspiciousOnly": true,
  "highlightedOnly": false,
  "numItems": 25
}
```

Fetch 4 pages. For pages 2-4, pass the previous response `nextCursor` as
`cursor`.

## Non-Primary API

`GET https://clawhub.ai/api/v1/skills?sort=downloads&nonSuspicious=true` is
diagnostic only. If it returns empty `items`, do not conclude that the public
ranking page is empty.

## Required Snapshot Fields

Top level:

- `snapshot_date`
- `fetched_at`
- `source`
- `comparison_basis`
- `limitations`
- `items`

Each item:

- `rank`
- `name`
- `author`
- `slug`
- `downloads_raw`
- `downloads`
- `installs_raw`
- `installs`
- `stars_raw`
- `stars`
- `versions`
- `compare_key`
- `prev_rank`
- `download_delta`
- `star_delta`
- `rank_change`

## Failure Handling

Write limitations into both JSON and Markdown when:

- the source path changes
- expected fields are missing
- pagination fails
- fewer than 100 rows are fetched
- previous snapshot is missing
- comparison is not strict daily

