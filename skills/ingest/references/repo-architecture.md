     1|---
     2|name: repo-architecture
     3|version: 1.0.0
     4|description: |
     5|  Where new brain files go. Decision protocol for filing brain pages by primary
     6|  subject, not by format or source. Reference for all brain-writing skills.
     7|triggers:
     8|  - "where does this go"
     9|  - "filing rules"
    10|  - "create new page"
    11|  - "which directory"
    12|tools:
    13|  - search
    14|  - get_page
    15|  - list_pages
    16|mutating: false
    17|---
    18|
    19|# Repo Architecture — Filing Rules
    20|
    21|> **Full filing rules:** See `skills/_brain-filing-rules.md`
    22|
    23|## Contract
    24|
    25|This skill guarantees:
    26|- Every new page is filed by primary subject (not format, not source)
    27|- The decision protocol is followed for ambiguous cases
    28|- Common misfiling patterns are caught
    29|
    30|## Phases
    31|
    32|1. **Identify the primary subject.** What would you search for to find this page?
    33|2. **Walk the decision tree:**
    34|   - About a person → `people/{name-slug}.md`
    35|   - About a company → `companies/{name-slug}.md`
    36|   - A reusable concept/framework → `concepts/{slug}.md`
    37|   - An original idea → `originals/{slug}.md`
    38|   - A meeting → `meetings/{slug}.md`
    39|   - Media content → `media/{type}/{slug}.md`
    40|   - Raw data import → `sources/{slug}.md`
    41|3. **Cross-link.** Link from related directories.
    42|4. **Check notability.** See `skills/conventions/quality.md` notability gate.
    43|
    44|## Output Format
    45|
    46|Advisory: "File this at `{type}/{slug}.md` because the primary subject is {reason}."
    47|
    48|## Anti-Patterns
    49|
    50|- Filing by format ("it's a PDF so it goes in sources/")
    51|- Filing by source ("it came from email so it goes in sources/")
    52|- Creating pages without checking if one already exists
    53|- Using `sources/` for anything except raw data dumps
    54|