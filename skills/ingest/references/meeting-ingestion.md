     1|---
     2|name: meeting-ingestion
     3|version: 1.0.0
     4|description: |
     5|  Ingest meeting transcripts into brain pages with attendee enrichment, entity
     6|  propagation, and timeline merge. A meeting is NOT fully ingested until the
     7|  enrich skill has processed every entity.
     8|triggers:
     9|  - "meeting transcript"
    10|  - "process this meeting"
    11|  - "meeting notes"
    12|  - meeting transcript received
    13|tools:
    14|  - search
    15|  - query
    16|  - get_page
    17|  - put_page
    18|  - add_link
    19|  - add_timeline_entry
    20|mutating: true
    21|writes_pages: true
    22|writes_to:
    23|  - meetings/
    24|  - people/
    25|  - companies/
    26|---
    27|
    28|# Meeting Ingestion Skill
    29|
    30|> **Filing rule:** Read `skills/_brain-filing-rules.md` before creating any new page.
    31|
    32|## Contract
    33|
    34|This skill guarantees:
    35|- Meeting page created with attendees, summary, key decisions, action items
    36|- EVERY attendee gets a people page (created or updated)
    37|- EVERY company discussed gets entity propagation
    38|- Timeline entries on ALL mentioned entities (timeline merge)
    39|- Meeting is NOT fully ingested until enrich runs for every entity
    40|- Back-links created bidirectionally
    41|
    42|> **Convention:** See `skills/conventions/quality.md` for Iron Law back-linking.
    43|
    44|Every attendee and company mentioned MUST get a back-link from their page to
    45|the meeting page. An unlinked mention is a broken brain.
    46|
    47|## Phases
    48|
    49|### Phase 1: Parse the transcript
    50|
    51|Extract from the transcript:
    52|- Attendees (names, roles if available)
    53|- Date, time, duration
    54|- Key topics discussed
    55|- Decisions made
    56|- Action items with owners
    57|- Companies and projects mentioned
    58|
    59|### Phase 2: Create meeting page
    60|
    61|```markdown
    62|# {Meeting Title} — {Date}
    63|
    64|**Attendees:** {list with links to people pages}
    65|**Date:** {YYYY-MM-DD}
    66|**Duration:** {if available}
    67|
    68|## Summary
    69|{3-5 bullet key outcomes}
    70|
    71|## Key Decisions
    72|{Decisions with context}
    73|
    74|## Action Items
    75|{Tasks with owners and deadlines}
    76|
    77|## Discussion Notes
    78|{Structured notes by topic}
    79|```
    80|
    81|### Phase 3: Attendee enrichment (MANDATORY)
    82|
    83|For EACH attendee:
    84|1. `gbrain search "{name}"` — does a people page exist?
    85|2. If NO → create via enrich skill (this is mandatory, not optional)
    86|3. If YES → update compiled truth with meeting context
    87|4. Add timeline entry on the person's page:
    88|   `gbrain timeline-add <person-slug> <date> "Attended <meeting-title>"`
    89|
    90|**Note (v0.10.1):** Once the meeting page is written via `gbrain put`, the
    91|auto-link post-hook automatically creates `attended` links from the meeting
    92|to each attendee whose page is referenced as `[Name](people/slug)`. You don't
    93|need to call `gbrain link` for attendees. You DO still need `gbrain timeline-add`
    94|for dated events (auto-link only handles links, not timeline entries).
    95|
    96|### Phase 4: Entity propagation (MANDATORY)
    97|
    98|For each company, project, or concept discussed:
    99|1. Check brain for existing page
   100|2. Create/update as needed
   101|3. Add timeline entry referencing the meeting
   102|4. Back-link from entity page to meeting page
   103|
   104|### Phase 5: Timeline merge
   105|
   106|The same event appears on ALL mentioned entities' timelines. If Alice met Bob at
   107|Acme Corp, the event goes on Alice's page, Bob's page, AND Acme Corp's page.
   108|
   109|### Phase 6: Sync
   110|
   111|`gbrain sync` to update the index.
   112|
   113|## Output Format
   114|
   115|Meeting page created. Report: "Meeting ingested: {N} attendees enriched, {N} entities
   116|updated, {N} action items captured."
   117|
   118|## Anti-Patterns
   119|
   120|- Creating the meeting page without enriching attendees
   121|- Skipping entity propagation ("I'll do that later")
   122|- Not merging timelines across all mentioned entities
   123|- Creating attendee stubs without meaningful content
   124|- Filing meeting pages without cross-linking to all participants
   125|