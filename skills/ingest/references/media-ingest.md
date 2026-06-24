     1|---
     2|name: media-ingest
     3|version: 1.0.0
     4|description: |
     5|  Ingest video, audio, PDF, book, screenshot, and GitHub repo content into the brain.
     6|  Multi-format handling with entity extraction and backlink propagation. Covers
     7|  video-ingest, youtube-ingest, and book-ingest subtypes.
     8|triggers:
     9|  - "watch this video"
    10|  - "process this YouTube link"
    11|  - "ingest this PDF"
    12|  - "save this podcast"
    13|  - "process this book"
    14|  - "PDF book"
    15|  - "summarize this book"
    16|  - "ingest it into my brain"
    17|  - "what's in this screenshot"
    18|  - "check out this repo"
    19|tools:
    20|  - search
    21|  - query
    22|  - get_page
    23|  - put_page
    24|  - add_link
    25|  - add_timeline_entry
    26|  - file_upload
    27|mutating: true
    28|writes_pages: true
    29|writes_to:
    30|  - concepts/
    31|  - people/
    32|  - companies/
    33|  - sources/
    34|---
    35|
    36|# Media Ingest Skill
    37|
    38|Ingest video, audio, PDF, book, screenshot, and GitHub repo content into the brain.
    39|
    40|> **Filing rule:** Read `skills/_brain-filing-rules.md` before creating any new page.
    41|
    42|## Contract
    43|
    44|This skill guarantees:
    45|- Every ingested media item has a brain page with analysis (not just a transcript dump)
    46|- Transcripts (video/audio) saved in raw and human-readable formats
    47|- Entity extraction: every person and company mentioned gets back-linked
    48|- Raw source files preserved via `gbrain files upload-raw`
    49|- Filing by primary subject, not by media format
    50|
    51|> **Convention:** See `skills/conventions/quality.md` for Iron Law back-linking.
    52|
    53|Every mention of a person or company with a brain page MUST create a back-link.
    54|
    55|## Phases
    56|
    57|### Phase 1: Identify format and fetch
    58|
    59|| Format | Action |
    60||--------|--------|
    61|| YouTube/video URL | Fetch transcript (Whisper, transcription service, or captions) |
    62|| Audio file | Transcribe with available STT service |
    63|| PDF | Extract text (OCR if needed) |
    64|| Book PDF | Extract text, identify chapters/sections |
    65|| Screenshot/image | OCR via vision model, extract text and entities |
    66|| GitHub repo | Clone, read README + key files, summarize architecture |
    67|
    68|### Phase 2: Upload raw source
    69|
    70|Save the original file for provenance: `gbrain files upload-raw <file> --page <slug>`
    71|
    72|### Phase 3: Create brain page
    73|
    74|File by primary subject (not format). Use this template:
    75|
    76|```markdown
    77|# {Title}
    78|
    79|**Source:** {URL or file path}
    80|**Format:** {video/audio/PDF/book/screenshot/repo}
    81|**Created:** {date}
    82|
    83|## Summary
    84|{Key points, not a transcript dump}
    85|
    86|## Key Segments / Highlights
    87|{For video/audio: timestamped highlights. For books: chapter summaries.}
    88|
    89|## People Mentioned
    90|{List with links to brain pages}
    91|
    92|## Companies Mentioned
    93|{List with links to brain pages}
    94|```
    95|
    96|### Phase 4: Entity extraction and propagation
    97|
    98|For every person and company mentioned:
    99|1. Check brain for existing page
   100|2. Create/enrich if needed (delegate to enrich skill)
   101|3. Add back-link from entity page to this media page
   102|4. Add timeline entry on entity page
   103|
   104|A media item is NOT fully ingested until entity propagation is complete.
   105|
   106|### Phase 5: Sync
   107|
   108|`gbrain sync` to update the index.
   109|
   110|## Output Format
   111|
   112|Brain page created with summary, highlights, and entity cross-links. Report to user:
   113|"Ingested {title}: {N} entities detected, {N} pages updated."
   114|
   115|## Anti-Patterns
   116|
   117|- Dumping raw transcripts without analysis
   118|- Skipping entity extraction ("I'll do that separately")
   119|- Filing **raw ingest** by format (all videos in `media/videos/`) instead of by subject. Note: format-prefixed paths under `media/<format>/<slug>` ARE sanctioned for **synthesized one-of-one output** like book-mirror's `media/books/<slug>-personalized.md`. The anti-pattern is for raw ingest, not for sui generis synthesis. See `skills/_brain-filing-rules.md` "Sanctioned exception: synthesis output is sui generis."
   120|- Not preserving raw source files
   121|- Creating stub pages without meaningful content
   122|