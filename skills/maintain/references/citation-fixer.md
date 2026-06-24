     1|---
     2|name: citation-fixer
     3|version: 1.1.0
     4|description: |
     5|  Audit and fix citation formatting across brain pages. Ensures every fact has
     6|  an inline [Source: ...] citation matching the standard format. Extended in
     7|  v0.25.1: scans for broken tweet/post references that lack actual URLs and
     8|  resolves them via the host's X / Twitter API integration.
     9|triggers:
    10|  - "fix citations"
    11|  - "fix broken citations"
    12|  - "citation audit"
    13|  - "check citations"
    14|  - "citation fixer"
    15|tools:
    16|  - search
    17|  - get_page
    18|  - put_page
    19|  - list_pages
    20|mutating: true
    21|---
    22|
    23|# Citation Fixer Skill
    24|
    25|> **Convention:** see [conventions/quality.md](../conventions/quality.md) for
    26|> the canonical citation format every fix should match.
    27|>
    28|> **Output rule:** all links MUST be deterministic (built from API data,
    29|> not composed by LLM). See [_output-rules.md](../_output-rules.md).
    30|
    31|## Contract
    32|
    33|This skill guarantees:
    34|
    35|- Every brain page is scanned for citation compliance.
    36|- Missing citations are flagged with specific location.
    37|- Malformed citations are fixed to match the standard format.
    38|- **(v0.25.1)** Tweet / post references without URLs are resolved via
    39|  X API and patched with deterministic `https://x.com/<handle>/status/<id>`
    40|  links.
    41|- Results reported with counts (scanned, fixed, remaining).
    42|
    43|## Phases
    44|
    45|1. **Scan pages.** List pages and read each one, checking for inline
    46|   `[Source: ...]` citations.
    47|2. **Identify issues:**
    48|   - Facts without any citation
    49|   - Citations missing date
    50|   - Citations missing source type
    51|   - Citations with wrong format
    52|   - **(v0.25.1)** Tweet references without `x.com` URLs
    53|3. **Fix format issues.** Rewrite malformed citations to match
    54|   `conventions/quality.md`.
    55|4. **(v0.25.1) Resolve tweet references** via the X API integration.
    56|5. **Report results.** Count: pages scanned, citations found, issues
    57|   fixed, tweets resolved, remaining gaps.
    58|
    59|## Tweet resolution pipeline (v0.25.1 extension)
    60|
    61|For each broken tweet reference, follow this chain. The actual API call
    62|goes through whatever X integration the host has configured (typical
    63|shape: a recipe under `recipes/x-api/` with handle / search-all
    64|endpoints).
    65|
    66|### Step 1: Identify broken references
    67|
    68|Scan the page for patterns that indicate tweet references without URLs:
    69|
    70|- Contains words like `tweeted`, `posted`, `said on X`, `RT`, `retweet`,
    71|  `X post`
    72|- Contains quoted text that looks like a tweet (short, punchy, often
    73|  starts with a quote)
    74|- Has `[Source: ... X/Twitter ...]` without an `x.com` URL
    75|- References engagement metrics (likes, impressions) without a link
    76|
    77|### Step 2: Extract searchable content
    78|
    79|From each broken reference, extract:
    80|
    81|- The **handle** (if mentioned: `@<username>`)
    82|- The **quoted text** (if available)
    83|- The **approximate date** (often present in surrounding timeline entries)
    84|
    85|### Step 3: Search for the actual tweet
    86|
    87|Use the host's X API integration. Query patterns:
    88|
    89|```
    90|# Handle + quoted text:
    91|from:<handle> "<exact quote fragment>"
    92|
    93|# Quoted text only:
    94|"<exact quote fragment>"
    95|
    96|# Original of a retweet:
    97|"<exact quote>" -is:retweet
    98|```
    99|
   100|### Step 4: Verify and extract metadata
   101|
   102|Once a candidate is found:
   103|
   104|- Confirm the text matches the quoted fragment.
   105|- Pull the tweet id, author handle, engagement metrics (likes / RTs /
   106|  impressions).
   107|- Construct the URL: `https://x.com/<handle>/status/<tweet_id>`.
   108|
   109|### Step 5: Patch the brain page
   110|
   111|Replace the broken citation with a proper one:
   112|
   113|**Before:**
   114|
   115|```
   116|"<quote fragment>" [Source: <some hand-wavy attribution>]
   117|```
   118|
   119|**After:**
   120|
   121|```
   122|"<full verified quote>" — <N> likes, <N> RTs, <N> impressions
   123|[Source: [X/<handle>, YYYY-MM-DD](https://x.com/<handle>/status/<tweet_id>)]
   124|```
   125|
   126|## Batch mode
   127|
   128|When sweeping many pages:
   129|
   130|### Find candidate pages
   131|
   132|```bash
   133|# Pages mentioning tweets but with no x.com links
   134|for f in $(find . -name "*.md" -not -path "./node_modules/*"); do
   135|  refs=$(grep -ci "tweet\|posted\|x post\|RT\|retweet\|said on X" "$f")
   136|  links=$(grep -c "x.com/.*/status/" "$f")
   137|  if [ "$refs" -gt 2 ] && [ "$links" -eq 0 ]; then
   138|    echo "$f"
   139|  fi
   140|done
   141|```
   142|
   143|### Priority order
   144|
   145|1. Recently created / updated pages — fresh broken refs are easiest to
   146|   resolve while context is fresh.
   147|2. High-traffic pages (frequent reads / writes from other skills).
   148|3. Everything else — bulk cleanup over time.
   149|
   150|### Rate limiting
   151|
   152|- X API: respect the host's tier limits; don't hammer.
   153|- Target ~50 pages per batch run.
   154|- 1-3 API calls per page (search + verify).
   155|- Batch-commit every 10-20 pages so a partial failure doesn't lose
   156|  progress.
   157|
   158|## Output format
   159|
   160|```
   161|Citation Audit Report
   162|=====================
   163|Pages scanned:        N
   164|Citations found:      N
   165|Issues fixed:         N
   166|Tweet links resolved: N
   167|Remaining gaps:       N (pages with uncitable facts)
   168|```
   169|
   170|## Anti-Patterns
   171|
   172|- ❌ Inventing citations for facts that have no source. Flag them.
   173|- ❌ Removing facts that lack citations (flag them; don't delete).
   174|- ❌ Fixing citations without reading the full page context.
   175|- ❌ Batch-fixing without checking quality on a sample first
   176|  (see `conventions/test-before-bulk.md`).
   177|- ❌ Composing tweet URLs by guessing the tweet id. Always go through
   178|  the X API; deterministic links only.
   179|
   180|## Integration
   181|
   182|This skill can be called:
   183|
   184|- **Manually** — "fix citations on this page"
   185|- **As a batch cron** — weekly sweep of pages with broken refs
   186|- **By other skills** — `enrich` or `media-ingest` can call citation-fixer
   187|  before commit to validate output
   188|
   189|## Metrics
   190|
   191|If running as a recurring batch, track state in a small JSON file under
   192|`~/.gbrain/citation-fixer-state.json`:
   193|
   194|```json
   195|{
   196|  "last_run": "2026-04-15T...",
   197|  "pages_scanned": 0,
   198|  "citations_fixed": 0,
   199|  "tweet_links_resolved": 0,
   200|  "citations_unresolvable": 0,
   201|  "pages_remaining": 1424
   202|}
   203|```
   204|
   205|
   206|## Output Format
   207|
   208|The skill's output shape is documented inline in the body sections above (see "Output", "Brain page format", or equivalent). The literal section header here exists for the conformance test (`test/skills-conformance.test.ts`).
   209|