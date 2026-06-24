# Consumer Browser Fetch Guide

When `curl` to GitHub Pages times out (exit 28/124), fetch all three data files
via the browser console. This guide shows the exact sequence used and validated
in production.

## Why a separate guide

The main SKILL.md "curl timeout" section documents the single-file technique.
This guide extends it to three files (latest.json, dates.json, prev snapshot),
which require navigating to different URLs and storing each result in a separate
DOM element so they don't overwrite each other.

## Prerequisites

- Hermes Agent with `browser_navigate` and `browser_console` tools.
- Browser-based agent (not headless curl environment).

## Step-by-step: Fetch All Three Files

### 1. Fetch latest.json

Navigate to the URL, then inject the raw JSON into the DOM:

```text
browser_navigate(url='https://learnprompt.github.io/skillrush-town/data/latest.json')

browser_console(expression="
  fetch('https://learnprompt.github.io/skillrush-town/data/latest.json')
    .then(r => r.text())
    .then(t => {
      let p = document.createElement('pre');
      p.id = 'latest_json_data';
      p.textContent = t;
      document.body.appendChild(p);
    })
")
```

Read it back:

```text
browser_console(expression="
  document.getElementById('latest_json_data').textContent
")
```

### 2. Fetch dates.json

Navigate to the dates.json URL — the DOM elements from step 1 are lost after
navigation. Use a new element ID:

```text
browser_navigate(url='https://learnprompt.github.io/skillrush-town/data/dates.json')

browser_console(expression="
  fetch('https://learnprompt.github.io/skillrush-town/data/dates.json')
    .then(r => r.text())
    .then(t => {
      let p = document.createElement('pre');
      p.id = 'dates_json_data';
      p.textContent = t;
      document.body.appendChild(p);
    })
")

# Read it back:
browser_console(expression="
  document.getElementById('dates_json_data').textContent
")
```

The result includes `latest` (the most recent snapshot date) and `dates`
(array of all available dates). Use `result.latest` to determine which
snapshot to fetch next.

### 3. Fetch the previous day's snapshot

The previous snapshot date is `latest - 1 day` from dates.json. Navigate to:

```text
browser_navigate(
  url='https://learnprompt.github.io/skillrush-town/data/snapshots/<PREV_DATE>.json'
)

browser_console(expression="
  fetch('https://learnprompt.github.io/skillrush-town/data/snapshots/<PREV_DATE>.json')
    .then(r => r.text())
    .then(t => {
      let p = document.createElement('pre');
      p.id = 'prev_json_data';
      p.textContent = t;
      document.body.appendChild(p);
    })
")

# Read it back:
browser_console(expression="
  document.getElementById('prev_json_data').textContent
")
```

### 4. Extract key fields for analysis (skip file-saving, go straight to data)

If write_file is available and you need disk copies for re-analysis, paste the
JSON from the console into a write_file call. Otherwise extract all needed
fields in a single expressive query:

```text
browser_console(expression="
  fetch('https://learnprompt.github.io/skillrush-town/data/latest.json')
    .then(r => r.json())
    .then(d => {
      let out = [];
      out.push('SNAPSHOT_DATE|' + d.snapshot_date);
      out.push('FETCHED_AT|' + d.fetched_at);
      out.push('');
      out.push('=== LIMITATIONS ===');
      (d.limitations || []).forEach(l => out.push('LIM|' + l));
      out.push('');
      out.push('=== TOP10 ===');
      d.items.slice(0,10).forEach(i => {
        let rc = i.rank_change ?? '';
        let dd = i.download_delta ?? '';
        let sd = i.star_delta ?? '';
        out.push('T10|' + i.rank + '|' + i.name + '|' + i.author + '|rc=' + rc + '|dd=' + dd + '|sd=' + sd);
      });
      out.push('');
      out.push('=== ALL ITEMS ===');
      d.items.forEach(i => {
        let rc = i.rank_change ?? '';
        let dd = i.download_delta ?? '';
        let sd = i.star_delta ?? '';
        let dl = i.downloads ?? '';
        out.push('ALL|' + i.rank + '|' + i.slug + '|rc=' + rc + '|dd=' + dd + '|sd=' + sd + '|dl=' + dl);
      });
      return out.join('\\n');
    })
")
```

## Loading the data into a Python script for analysis

After fetching via browser, the data is in the console output as a dict.
The most reliable approach for analysis is:

1. Extract the full JSON dict from the browser_console result (it's the
   `result` field).
2. Write a Python script to `/tmp/` using the `write_file` tool with the
   data hardcoded or saved to a JSON file.
3. Execute via `terminal` with `python3 /tmp/script.py`.

**Alternative** (when data is too large to hardcode): Save JSON to disk as
shown in the main skill's "curl timeout" section (Step 3-5), then have the
Python script `json.load(open('/tmp/...'))`.

## Known pitfalls

- **DOM elements per navigation**: Each `browser_navigate` reloads the page,
  destroying previous DOM elements. Always read your data before navigating
  to the next URL, or use a single fetch-all approach (see single-shot
  extraction in the main skill).
- **Result size limits**: The browser_console result field may truncate very
  large JSON blobs (100+ items). If this happens, use the DOM-injection
  technique (steps 1-3 above) and read back via `textContent`.
- **Unicode in pipe output**: Arrow characters (↗ / ↘) and emoji from the
  console may not survive through terminal or cron delivery. Keep the
  extraction using numeric values only, and add decorations only in the
  final report output.
