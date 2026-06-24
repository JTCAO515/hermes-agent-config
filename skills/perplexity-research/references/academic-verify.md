     1|---
     2|name: academic-verify
     3|version: 0.1.0
     4|description: Verify a research claim or academic citation by tracing it through publication → methodology → raw data → independent replication. Routes through perplexity-research for the actual web lookup, then formats results as a citation-checked brain page. Use when a book/article/conversation cites a study and you want to confirm the claim is real, replicated, and accurately characterized.
     5|triggers:
     6|  - "verify this academic claim"
     7|  - "check this study"
     8|  - "academic verify"
     9|  - "validate citation"
    10|  - "is this study real"
    11|  - "Retraction Watch"
    12|mutating: true
    13|writes_pages: true
    14|writes_to:
    15|  - concepts/
    16|---
    17|
    18|# academic-verify — Trace Claims to Source Data
    19|
    20|> **Convention:** see [conventions/quality.md](../conventions/quality.md) for
    21|> citation rules; every verdict cites the source data, not just the
    22|> author's claim about the source data.
    23|>
    24|> **Convention:** see [conventions/brain-first.md](../conventions/brain-first.md)
    25|> for the lookup chain. This skill enforces brain-first by checking
    26|> existing brain pages before issuing a fresh web search.
    27|
    28|## What this is
    29|
    30|A claim-verification flow for academic / research statements. When a
    31|book, article, or speaker cites a study or quotes a number, this skill
    32|traces the claim through:
    33|
    34|```
    35|claim → publication → methodology section → raw data source → independent verification
    36|```
    37|
    38|At each step, it answers:
    39|
    40|- **Where does this number come from?** (Self-generated? Survey? Government data?)
    41|- **What's the baseline?** (Reduction from what? Over what time period?)
    42|- **Is the raw data available?** (Public? Proprietary? "Available on request"?)
    43|- **Has anyone independently verified it?** (Replication study? Government audit?)
    44|- **Are there confounding factors?** (Other interventions, policy changes, COVID, sampling bias?)
    45|- **Is the comparison fair?** (Cherry-picked comparison group? Survivorship bias?)
    46|
    47|The output is a brain page under `concepts/<claim-slug>.md` that records
    48|the claim, the trace, and the verdict — so future references to the
    49|same claim can re-use the verified analysis.
    50|
    51|## When to use this
    52|
    53|- A book quotes a study and you want to confirm it's real and not
    54|  miscited
    55|- An article makes a quantified claim ("X reduced Y by 40%") that you
    56|  want traced to the source data
    57|- You're writing something that depends on a piece of research and you
    58|  want to verify the underlying paper holds up
    59|- You're updating a brain page that cites a research claim and you want
    60|  to record the verification status alongside
    61|
    62|## What this skill is NOT
    63|
    64|- Not adversarial / oppo work. The point is rigor, not takedown.
    65|- Not generic web research — use `perplexity-research` directly for
    66|  open-ended topic exploration.
    67|- Not a brain-only lookup — that's `gbrain query`.
    68|
    69|## How it works (D7/α: pure routing through perplexity-research)
    70|
    71|academic-verify is a thin orchestrator. The actual web search is done
    72|by [perplexity-research](../perplexity-research/SKILL.md). academic-verify's
    73|job is the *workflow*: scoping the claim precisely, sending it through
    74|perplexity-research with citation-mode, then formatting the response
    75|into a verdict-shaped brain page.
    76|
    77|```
    78|Step 1: Scope the claim
    79|  Pin down EXACTLY what's being claimed:
    80|    • Quote: who said what?
    81|    • Source: which paper / dataset / survey?
    82|    • Number: what specific quantity is claimed?
    83|    • Period: over what time range?
    84|
    85|Step 2: Brain-first lookup
    86|  gbrain query "<paper title> OR <author name> OR <claim keywords>"
    87|  If the brain has prior verification of this claim, reuse it.
    88|
    89|Step 3: Invoke perplexity-research with citation-mode prompt
    90|  Send the claim + brain context to perplexity-research with a prompt
    91|  that explicitly asks for:
    92|    • Original publication (title, authors, journal, year, DOI)
    93|    • Methodology section summary
    94|    • Raw data availability (public repo? proprietary?)
    95|    • Independent replication status (Retraction Watch / PubPeer hits)
    96|    • Citations of the paper that critique or contextualize it
    97|
    98|Step 4: Format the verdict
    99|  Write the result to concepts/<claim-slug>.md. The verdict is one of:
   100|    • Verified — claim is accurate; raw data available; replication exists
   101|    • Partially verified — claim correct on the underlying paper but
   102|      methodology has known limits; record limits explicitly
   103|    • Unverifiable — no public data, no replication; not enough to act
   104|    • Misattributed — the claim cites a paper but the paper doesn't say that
   105|    • Retracted / disputed — paper has known retraction or
   106|      well-documented critique
   107|
   108|Step 5: Cross-link to original sources
   109|  Add the paper authors to people/ if they have brain pages, or create
   110|  one if notable. Iron Law per conventions/quality.md.
   111|```
   112|
   113|## Output: brain page format
   114|
   115|```markdown
   116|---
   117|title: "[Claim summary] — Verified"
   118|type: research
   119|date: YYYY-MM-DD
   120|verdict: "verified|partial|unverifiable|misattributed|retracted"
   121|brain_context_slugs: ["pages cited as context"]
   122|---
   123|
   124|# [Claim summary] — Verified
   125|
   126|> One-line: the verdict + the bottom-line reason.
   127|
   128|## The Claim
   129|
   130|> Exact quote, exactly as stated, with source attribution.
   131|
   132|## Trace
   133|
   134|| Step | Finding | Source |
   135||------|---------|--------|
   136|| Original publication | [Title, authors, year, DOI] | [URL] |
   137|| Methodology | [1-line summary; flag obvious limits] | [URL] |
   138|| Raw data | [Public repo / proprietary / available-on-request] | [URL] |
   139|| Independent replication | [Replication studies and their results] | [URL] |
   140|| Critical citations | [Papers that critique this work] | [URL] |
   141|
   142|## Verdict
   143|
   144|[Verified / Partially verified / Unverifiable / Misattributed / Retracted]
   145|
   146|[1-2 paragraphs explaining WHY the verdict, with specific evidence.]
   147|
   148|## Caveats
   149|
   150|[Honest limits: what we couldn't verify, what would change the verdict.]
   151|
   152|## See Also
   153|
   154|- Original paper: [Title](DOI URL)
   155|- Authors' brain pages: [Author 1](people/author-1.md), ...
   156|- Related claims (verified or otherwise): [...]
   157|```
   158|
   159|## Useful databases (the agent uses these via perplexity-research)
   160|
   161|| Database | What it has | URL pattern |
   162||----------|-------------|-------------|
   163|| Retraction Watch | Retractions, corrections, expressions of concern | retractionwatch.com/?s=NAME |
   164|| PubPeer | Anonymous post-publication peer review | pubpeer.com/search?q=NAME |
   165|| OSF | Pre-registrations, open data, open materials | osf.io/search/?q=QUERY |
   166|| Semantic Scholar | Citation analysis, paper metadata | api.semanticscholar.org |
   167|| OpenAlex | Open citation data, institutional affiliations | api.openalex.org |
   168|| Many Labs | Replication results for social psychology | osf.io/wx7ck/ |
   169|
   170|## Standards (the rigor bar)
   171|
   172|- **Verified** — only when the underlying paper exists, raw data is
   173|  public OR an independent lab has confirmed the result, and the citing
   174|  source represents the claim accurately.
   175|- **Partial** — paper is real and findings stand, but the citation
   176|  context oversells (e.g., "X causes Y" when the paper shows
   177|  correlation, or "all studies find X" when it's one underpowered study).
   178|- **Unverifiable** — the underlying number can't be traced to source
   179|  data, no replication has been done, no independent confirmation
   180|  exists. Not the same as "wrong" — say "we couldn't verify."
   181|- **Misattributed** — the citation points to a paper, but the paper
   182|  doesn't actually say what the citation claims. Common in policy briefs.
   183|- **Retracted / disputed** — paper has been retracted, has a major
   184|  expression-of-concern, or has well-documented critique that
   185|  contradicts the headline finding.
   186|
   187|Never claim a problem without evidence. The verification document
   188|itself is the artifact — if the claim holds up, say so plainly. If it
   189|doesn't, the trace speaks for itself.
   190|
   191|## Anti-Patterns
   192|
   193|- ❌ Skipping the brain-first lookup. Re-doing verification we've
   194|  already done is wasted Perplexity spend.
   195|- ❌ Bypassing perplexity-research and inventing the lookup. The
   196|  citations from Perplexity are the evidence — without them, the
   197|  verdict is just opinion.
   198|- ❌ Stating "Verified" without confirming raw data availability.
   199|  Replication trumps any single paper.
   200|- ❌ Stating "Unverifiable" when you simply didn't look hard enough.
   201|  The verdict is on the source, not on your search effort.
   202|
   203|## Related skills
   204|
   205|- `skills/perplexity-research/SKILL.md` — the actual web-search engine
   206|  this skill routes through (D7/α: pure routing, no new infrastructure)
   207|- `skills/citation-fixer/SKILL.md` — fixes citation FORMATTING; this
   208|  skill checks whether the cited claim is true
   209|- `skills/conventions/quality.md` — citation + back-link rules
   210|
   211|
   212|## Contract
   213|
   214|This skill guarantees:
   215|
   216|- Routing matches the canonical triggers in the frontmatter.
   217|- Output written under the directories listed in `writes_to:` (when applicable).
   218|- Conventions referenced (`quality.md`, `brain-first.md`, `_brain-filing-rules.md`) are followed.
   219|- Privacy contract preserved: no real names, no fork-specific filesystem path literals, no upstream-fork references.
   220|
   221|The full behavior contract is documented in the body sections above; this section exists for the conformance test.
   222|
   223|## Output Format
   224|
   225|The skill's output shape is documented inline in the body sections above (see "Output", "Brain page format", or equivalent). The literal section header here exists for the conformance test (`test/skills-conformance.test.ts`).
   226|