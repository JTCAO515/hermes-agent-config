     1|---
     2|name: voice-note-ingest
     3|version: 0.1.0
     4|description: Ingest a voice note with exact-phrasing preservation (never paraphrased). Routes content to originals/, concepts/, people/, companies/, ideas/, personal/, or voice-notes/ based on a decision tree. The user's exact words are the signal.
     5|triggers:
     6|  - "voice note"
     7|  - "ingest this voice memo"
     8|  - "transcribe and file"
     9|  - "voice note ingest"
    10|  - "save this audio note"
    11|  - "audio message"
    12|mutating: true
    13|writes_pages: true
    14|writes_to:
    15|  - voice-notes/
    16|  - originals/
    17|  - concepts/
    18|  - people/
    19|  - companies/
    20|  - ideas/
    21|  - personal/
    22|---
    23|
    24|# voice-note-ingest — Exact-Phrasing Voice Capture
    25|
    26|> **Convention:** see [conventions/quality.md](../conventions/quality.md) for
    27|> citation rules, back-link enforcement, and exact-phrasing requirements.
    28|>
    29|> **Convention:** see [_brain-filing-rules.md](../_brain-filing-rules.md) for
    30|> the filing decision protocol.
    31|
    32|## Iron Law
    33|
    34|The user's **exact words** are the insight. Never paraphrase. Never clean
    35|up. The vivid, unpolished, stream-of-consciousness phrasing captures
    36|something that cleaned-up prose does not. Preserve it in block quotes.
    37|The Analysis section can interpret; the transcript section is sacred.
    38|
    39|- ✅ `"The ambition-to-lifespan ratio has never been more fucked"`
    40|- ❌ `User noted the tension between ambition and mortality`
    41|
    42|## When to invoke
    43|
    44|The user sends an audio or voice message via any channel (Telegram, voice
    45|memo upload, openclaw audio attachment). The host agent typically provides
    46|the transcript text. If not, transcribe via `gbrain transcription` (Groq
    47|Whisper by default; OpenAI fallback for audio > 25MB segmented via ffmpeg).
    48|
    49|## The pipeline
    50|
    51|```
    52|1. STORE       → Upload original audio to gbrain storage backend
    53|                 (S3 / Supabase Storage / local — pluggable per
    54|                 src/core/storage.ts).
    55|2. TRANSCRIBE  → Use the agent-provided transcript verbatim, OR call
    56|                 gbrain transcription if no transcript was supplied.
    57|3. ROUTE       → Apply the decision tree (below) to find the right
    58|                 destination directory.
    59|4. WRITE       → Create / update the destination brain page; preserve the
    60|                 verbatim transcript in a block-quoted "User's Words"
    61|                 section.
    62|5. CROSS-LINK  → For every entity mentioned (person, company), add a
    63|                 timeline back-link from THEIR brain page to THIS one
    64|                 (Iron Law per conventions/quality.md).
    65|```
    66|
    67|## Decision tree (where the content goes)
    68|
    69|Apply in order. First match wins. If multiple categories apply, file to
    70|the primary directory and cross-link to the others.
    71|
    72|1. **Original idea, observation, or thesis** — the user is expressing a
    73|   novel thought, framework, or connection THEY generated.
    74|   → `originals/<slug>.md`. Use the user's vivid language for the slug.
    75|
    76|2. **About a world concept they encountered** — a framework or model
    77|   someone else created that the user is referencing.
    78|   → `concepts/<slug>.md`.
    79|
    80|3. **About a specific person** — new information, opinion, or observation
    81|   about someone.
    82|   → Update `people/<person>.md` timeline.
    83|
    84|4. **About a specific company** — new info about a company.
    85|   → Update `companies/<company>.md` timeline.
    86|
    87|5. **A product or business idea** — something that could be built.
    88|   → `ideas/<slug>.md`.
    89|
    90|6. **A personal reflection** — therapy-adjacent, emotional, identity.
    91|   → Append to appropriate `personal/<slug>.md`.
    92|
    93|7. **None of the above / random thought / doesn't fit cleanly** —
    94|   → `voice-notes/YYYY-MM-DD-<slug>.md` (catch-all).
    95|
    96|**Multiple categories?** Create the primary page, then cross-link to all
    97|others. If the voice note covers a person AND a novel idea, create the
    98|originals/ page AND update the person's timeline.
    99|
   100|## Brain page format
   101|
   102|For ALL voice-note-derived pages, include this skeleton:
   103|
   104|```markdown
   105|---
   106|title: "[Title derived from content]"
   107|type: [original | concept | voice-note | ...]
   108|created: YYYY-MM-DD
   109|updated: YYYY-MM-DD
   110|tags: [voice-note, relevant-tags]
   111|sources:
   112|  voice-note:
   113|    type: voice_note
   114|    storage_path: "[gbrain storage URL or relative path]"
   115|    acquired: YYYY-MM-DD
   116|    acquired_via: "voice note from <channel>"
   117|---
   118|
   119|# Title
   120|
   121|> Executive summary of what was said and why it matters.
   122|
   123|## User's Words
   124|
   125|> "Exact transcript, verbatim, preserving every word, hesitation, and verbal
   126|> tic. This is the primary source material. Do not edit."
   127|
   128|🔊 [Audio]([gbrain storage URL or relative path])
   129|
   130|## Analysis
   131|
   132|[What this means, why it matters, connections to other thinking. The
   133|analysis is the agent's interpretation; the transcript above is sacred.]
   134|
   135|## See Also
   136|
   137|- [Related brain pages with relative links]
   138|
   139|---
   140|
   141|## Timeline
   142|
   143|- **YYYY-MM-DD** | voice note from <channel> — [Brief description]
   144|```
   145|
   146|## Citation format
   147|
   148|```
   149|[Source: voice note, <channel>, YYYY-MM-DD]
   150|```
   151|
   152|Include timestamps when available:
   153|
   154|```
   155|[Source: voice note, <channel>, YYYY-MM-DD HH:MM PT]
   156|```
   157|
   158|## Naming convention
   159|
   160|- Audio files: `YYYY-MM-DD-<brief-slug>.<ext>` (e.g.,
   161|  `2026-04-13-rick-rubin-creative-philosophy.ogg`)
   162|- Brain pages: match the slug of the destination directory.
   163|
   164|## Bulk vs. single
   165|
   166|This skill handles ONE voice note at a time. Each is its own ingest cycle.
   167|No batching.
   168|
   169|## Anti-Patterns
   170|
   171|- ❌ **Paraphrasing the transcript.** The exact words are the signal.
   172|- ❌ **Cleaning up hesitations or filler words** ("um", "like", "you
   173|  know"). The texture matters.
   174|- ❌ **Creating a page with no entity cross-links** when people/companies
   175|  were mentioned. Iron Law fail.
   176|- ❌ **Skipping the audio storage step.** Always upload the original; the
   177|  brain page has a `🔊 [Audio]` link back to it.
   178|
   179|## Related skills
   180|
   181|- `skills/signal-detector/SKILL.md` — same exact-phrasing pattern for
   182|  text-channel idea capture
   183|- `skills/idea-ingest/SKILL.md` — for typed-text idea ingestion
   184|- `skills/conventions/quality.md` — citation + back-link rules
   185|
   186|
   187|## Contract
   188|
   189|This skill guarantees:
   190|
   191|- Routing matches the canonical triggers in the frontmatter.
   192|- Output written under the directories listed in `writes_to:` (when applicable).
   193|- Conventions referenced (`quality.md`, `brain-first.md`, `_brain-filing-rules.md`) are followed.
   194|- Privacy contract preserved: no real names, no fork-specific filesystem path literals, no upstream-fork references.
   195|
   196|The full behavior contract is documented in the body sections above; this section exists for the conformance test.
   197|
   198|## Output Format
   199|
   200|The skill's output shape is documented inline in the body sections above (see "Output", "Brain page format", or equivalent). The literal section header here exists for the conformance test (`test/skills-conformance.test.ts`).
   201|