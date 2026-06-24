     1|---
     2|name: idea-ingest
     3|version: 1.0.0
     4|description: |
     5|  Ingest links, articles, tweets, and ideas into the brain. Fetch content, save
     6|  to brain with analysis, create author people page, and cross-link. Use when the
     7|  user shares a link or says "read this", "save this", "think about this".
     8|triggers:
     9|  - shares a link or URL
    10|  - "read this"
    11|  - "save this"
    12|  - "think about this"
    13|  - "put this in brain"
    14|tools:
    15|  - search
    16|  - query
    17|  - get_page
    18|  - put_page
    19|  - add_link
    20|  - add_timeline_entry
    21|  - file_upload
    22|mutating: true
    23|writes_pages: true
    24|writes_to:
    25|  - people/
    26|  - concepts/
    27|  - sources/
    28|---
    29|
    30|# Idea Ingest Skill
    31|
    32|> **Filing rule:** Read `skills/_brain-filing-rules.md` before creating any new page.
    33|
    34|## Contract
    35|
    36|This skill guarantees:
    37|- Every ingested item has a brain page with genuine analysis (not just a summary)
    38|- The author gets a people page (MANDATORY for anyone whose thinking is worth ingesting)
    39|- Cross-links created bidirectionally (source ↔ author, source ↔ mentioned entities)
    40|- Raw source preserved for provenance via `gbrain files upload-raw`
    41|- Every fact has an inline `[Source: ...]` citation
    42|- Filing follows primary subject rules (not format-based)
    43|
    44|> **Convention:** See `skills/conventions/quality.md` for Iron Law back-linking.
    45|
    46|Every mention of a person or company with a brain page MUST create a back-link.
    47|Format: `- **YYYY-MM-DD** | Referenced in [page title](path) — brief context`
    48|
    49|## Phases
    50|
    51|1. **Fetch the content.** Use appropriate tools for the content type (web fetch for articles, API for tweets, PDF reader for documents).
    52|
    53|2. **Upload raw source.** Save the fetched content for provenance: `gbrain files upload-raw <file> --page <slug>`
    54|
    55|3. **Identify the author — MANDATORY people page.** Anyone whose thinking is worth ingesting is worth tracking.
    56|   - Search brain for existing author page
    57|   - If no page → CREATE ONE with compiled truth + timeline format
    58|   - If page exists → update timeline with this new publication
    59|   - Cross-link both directions
    60|
    61|4. **Save to brain.** File by PRIMARY SUBJECT (read `skills/_brain-filing-rules.md`):
    62|   - About a person → `people/`
    63|   - About a company → `companies/`
    64|   - A reusable framework → `concepts/`
    65|   - Raw data dump → `sources/`
    66|
    67|5. **Analyze for the user.** Reply with analysis that connects the content to what the brain knows. Think about:
    68|   - Active projects — is this relevant?
    69|   - Contradictions — does this challenge existing brain knowledge?
    70|   - Connections — does this involve known people/companies?
    71|   - Don't just summarize. Tell the user things they wouldn't have noticed.
    72|
    73|6. **Sync.** `gbrain sync` to update the index.
    74|
    75|## Output Format
    76|
    77|```markdown
    78|# {Title} — {Author}
    79|
    80|**Source:** {URL}
    81|**Author:** {Author}, {role}
    82|**Published:** {date}
    83|**Ingested:** {date}
    84|
    85|## Context
    86|{Why this matters now, connected to brain knowledge}
    87|
    88|## Summary
    89|{3-5 bullet core arguments}
    90|
    91|## Key Data / Claims
    92|{Specific facts, numbers, quotes}
    93|
    94|## Analysis
    95|{How this connects to existing brain knowledge. What's new. What contradicts.}
    96|```
    97|
    98|## Anti-Patterns
    99|
   100|- Just summarizing without connecting to brain knowledge
   101|- Filing everything in `sources/` (sources is for raw data dumps only)
   102|- Skipping the author people page
   103|- Not cross-linking to mentioned entities
   104|- Ingesting without checking brain first for existing coverage
   105|