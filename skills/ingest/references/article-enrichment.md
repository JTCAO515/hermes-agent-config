     1|---
     2|name: article-enrichment
     3|version: 0.1.0
     4|description: Transform raw article text dumps in the brain into structured pages with executive summary, verbatim quotes, key insights, why-it-matters, and cross-references. Replaces walls-of-text with quotable, actionable brain pages.
     5|triggers:
     6|  - "enrich this article"
     7|  - "enrich the article"
     8|  - "enriching the article"
     9|  - "enrich brain pages"
    10|  - "batch enrich"
    11|  - "enrich pass"
    12|  - "make brain pages useful"
    13|mutating: true
    14|writes_pages: true
    15|writes_to:
    16|  - media/articles/
    17|---
    18|
    19|# article-enrichment — From Raw Dumps to Useful Brain Pages
    20|
    21|> **Convention:** see [conventions/quality.md](../conventions/quality.md) for
    22|> citation rules, verbatim-quote requirements, and back-link enforcement.
    23|>
    24|> **Convention:** see [_brain-filing-rules.md](../_brain-filing-rules.md) for
    25|> filing rules. Article pages live under `media/articles/` for raw ingest;
    26|> personalized one-of-one synthesis output uses the sanctioned
    27|> `media/articles/<slug>-personalized.md` exception.
    28|
    29|## What this does
    30|
    31|Takes an article brain page that's a wall of raw extracted text and rewrites
    32|it as a structured page with:
    33|
    34|- **Executive Summary** — 2-3 sentences, the ONE thing worth remembering
    35|- **Why It Matters** — connects to the user's specific projects + interests
    36|  (read from brain context, not assumed)
    37|- **Quotable Lines** — 3-5 VERBATIM quotes worth referencing in essays
    38|- **Key Insights** — actual insights, not topic labels
    39|- **Surprising or Counterintuitive** — what makes this content unique
    40|- **See Also** — standard markdown links to related brain pages
    41|
    42|Raw source content is preserved in a collapsed `<details>` section so the
    43|original is never lost.
    44|
    45|## When to invoke
    46|
    47|- New article page lands in the brain via media-ingest with `needs_enrichment: true`
    48|- Existing article page is a wall of text under a `## Content` header with
    49|  no synthesis
    50|- User says a brain page is useless, boring, or a dump
    51|- An LLM-judge brain-quality eval fails on quotability or actionability for
    52|  an article page
    53|
    54|## The pipeline
    55|
    56|```
    57|1. READ      → Open the article brain page; parse frontmatter + body.
    58|2. SCAN      → Look for ## Content (raw dump) and absence of ## Executive Summary.
    59|3. CONTEXT   → gbrain query the article's key entities to ground "Why It Matters".
    60|4. ENRICH    → Sonnet (default) or Opus (for high-value content) restructures.
    61|5. WRITE     → Replace ## Content with the structured sections; preserve raw
    62|               source in <details>; clear needs_enrichment in frontmatter.
    63|6. CROSS-LINK→ Add back-links from referenced people/companies pages
    64|               (Iron Law per conventions/quality.md).
    65|```
    66|
    67|## Invocation
    68|
    69|The skill itself is markdown instructions to the agent. It does NOT ship a
    70|deterministic CLI command in v0.25.1. The agent uses gbrain's existing
    71|operations:
    72|
    73|```bash
    74|# 1. Find candidate pages
    75|gbrain query "needs_enrichment: true type:article" --limit 50
    76|
    77|# 2. For each candidate, read the page
    78|gbrain get media/articles/<slug>
    79|
    80|# 3. Enrich via the agent's LLM (Sonnet by default; Opus for high-value)
    81|#    The agent reads the raw content + brain context + writes the structured page.
    82|
    83|# 4. Write the enriched page
    84|#    Use the put_page operation with the new structured markdown body.
    85|
    86|# 5. Cross-link entities
    87|#    For every person/company mentioned, add a timeline back-link.
    88|```
    89|
    90|## Quality bar
    91|
    92|An enriched page passes if it has:
    93|
    94|- ✅ `## Executive Summary` (2-3 sentences)
    95|- ✅ `## Quotable Lines` with ≥3 verbatim quotes (literal quotes, not paraphrase)
    96|- ✅ `## Key Insights` with ≥3 bullets (insights, not topic labels)
    97|- ✅ `## Why It Matters` connecting to specific brain context (not generic)
    98|- ✅ `## See Also` with standard markdown links (NOT `[[wiki-links]]`)
    99|- ✅ `<details>` block preserving the raw source content
   100|
   101|## Model selection
   102|
   103|| Model | Use when | Quote accuracy |
   104||-------|----------|----------------|
   105|| **Sonnet** (default) | Bulk enrichment, most articles | Good — occasionally paraphrases |
   106|| **Opus** | High-value content, original-thinking pieces, longreads | Excellent — respects "verbatim" instruction |
   107|
   108|Rule: for bulk enrichment, do a Sonnet draft pass and spot-check 5 with
   109|the LLM-judge brain-quality eval. If quotes are paraphrased, switch to
   110|Opus for that batch.
   111|
   112|## Link convention
   113|
   114|All cross-references use standard markdown links: `[Title](relative/path.md)`.
   115|NEVER use `[[wiki-links]]` — they don't render on GitHub.
   116|
   117|## Anti-Patterns
   118|
   119|- ❌ Paraphrasing quotes ("the author argues that…"). Quotes are verbatim
   120|  or they're not quotes.
   121|- ❌ Generic "Why It Matters" ("this is important because innovation").
   122|  Tie to specific brain context or remove the section.
   123|- ❌ Inventing topic labels and calling them insights. An insight is a
   124|  thing the article says that you didn't already know.
   125|- ❌ Discarding the raw source. Always wrap it in `<details>`.
   126|- ❌ Re-enriching non-idempotently — check the `needs_enrichment` flag in
   127|  frontmatter; skip if already false.
   128|
   129|## Related skills
   130|
   131|- `skills/media-ingest/SKILL.md` — creates the raw article pages this skill enriches
   132|- `skills/idea-ingest/SKILL.md` — link/article ingestion with author people-page enforcement
   133|- `skills/conventions/quality.md` — citation + back-link rules
   134|
   135|
   136|## Contract
   137|
   138|This skill guarantees:
   139|
   140|- Routing matches the canonical triggers in the frontmatter.
   141|- Output written under the directories listed in `writes_to:` (when applicable).
   142|- Conventions referenced (`quality.md`, `brain-first.md`, `_brain-filing-rules.md`) are followed.
   143|- Privacy contract preserved: no real names, no fork-specific filesystem path literals, no upstream-fork references.
   144|
   145|The full behavior contract is documented in the body sections above; this section exists for the conformance test.
   146|
   147|## Output Format
   148|
   149|The skill's output shape is documented inline in the body sections above (see "Output", "Brain page format", or equivalent). The literal section header here exists for the conformance test (`test/skills-conformance.test.ts`).
   150|