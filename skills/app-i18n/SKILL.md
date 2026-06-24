---
name: app-i18n
description: Systematically localize a web app to English-native. Scan for Chinese text, categorize files, translate with proper-noun formatting, sync version numbers, and deploy-verify.
---

# App i18n — English-Native Localization Workflow

## When to use
- User asks to make an app English-native（将所有中文翻译成英文）
- App has mixed Chinese/English content that needs systematic translation
- Building an English-native product that references Chinese proper nouns

## Workflow

### 1. Full Scan
Scan all source files for Chinese characters:

```bash
cd /project && python3 -c "
import re, os
for root, dirs, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root: continue
    for f in files:
        if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.html') or f.endswith('.css')):
            continue
        fpath = os.path.join(root, f)
        cn = 0
        with open(fpath, 'r', errors='ignore') as fh:
            for line in fh:
                if re.search(r'[\u4e00-\u9fff]', line):
                    cn += 1
        if cn > 0:
            print(f'{cn:4d}  {fpath}')
"
```

### 2. Categorize Files
Group results by type — each type gets different treatment:

| Category | Treatment | Example |
|----------|-----------|---------|
| **UI text** (HTML, frontend strings) | Pure English → translate entirely | `web/index.html` |
| **Data files** (Python data dicts) | "English (中文)" format | `data/tools/*.py` |
| **Proper-noun fields** (`name_zh`, place names) | Keep as bilingual reference | `data/knowledge/cities.py` |
| **JS pattern matching** (Chinese keywords) | Keep — detects user input language | `web/app.js` keywords |
| **i18n/zh section** (language toggle) | Keep as backup language option | `static/i18n.js` |

### 3. Translation Format (Hard Rule)
- **Non-proper-noun text**: Pure English only
- **Chinese proper nouns** (places, food, landmarks, brands, currency units): `"English text (中文)"`
- **Examples**:
  - `"Forbidden City (故宫)"`
  - `"¥13 starting fare (起步价)"`
  - `"Alipay (支付宝)"`
  - `"Peking duck (北京烤鸭)"`
- **Document comments / docstrings**: Translate to English
- **API response field keys** (like `"高铁_每100km"` → `"HSR_per_100km (高铁_每100km)"`): English first, Chinese in parens

### 4. File-by-File Strategy

**Small files (< 50 lines of Chinese)**: Use `patch` for targeted replacements

**Large files with structural data** (city/attraction/hotel databases, 50–200+ lines): Use `write_file` with fully translated content in one pass. This is faster and safer than 15+ sequential patches.

**F-string + multi-line content** (CSS/SVG embedded in Python f-strings): Use `python3 << 'PYEOF'` heredoc via terminal → read full content, replace, write back in one operation. Avoid patch for these (see `coding-workflow` pitfalls).

### 5. Version Number Sync
Before deployment, ensure version numbers match across all locations:

```bash
# grep all version references
grep -n 'v[0-9]\.[0-9]\.[0-9]' web/index.html web/app.js api/index.py
```

Sync locations:
- HTML: `<span id="version-badge">vX.Y.Z</span>`
- API health endpoint: `"version": "X.Y.Z"`
- API timestamp: `"build": "YYYY-MM-DD"`

### 6. Deployment Verification
```bash
# Push → Vercel auto-deploys
git add -A && git commit -m "vX.Y.Z: i18n description" && git push

# Wait for cold start (10–30s on Vercel Hobby)
sleep 15

# Verify API version
curl -sL https://domain.com/api/health

# Verify page loads
curl -sL https://domain.com/ | grep -o 'v[0-9]\.[0-9]\.[0-9]'
```

## Common Pitfalls

### ❌ Don't translate these
- `name_zh` fields in structured data — they are intentionally bilingual
- `zh` section in i18n files — it supports the language toggle feature
- JS pattern-matching keywords — they detect user input regardless of language
- City/place names in travel-knowledge data — foreign users NEED the Chinese name to navigate

### ✅ Do translate these
- All docstrings and code comments
- API response descriptions and user-facing strings
- Examples in AI system prompts (Beijing itinerary examples, etc.)
- Dropdown options and button labels

### Version Number Staleness
The HTML fallback version and API health-endpoint version can drift apart if only one is updated. Always update both simultaneously. Use `grep` to confirm no old version remains before committing.

### Vercel Cold Start
Vercel Hobby plan Serverless Functions take 10–30s to cold-start. When verifying after deploy, add a `sleep 15` before the first curl check. If it times out, retry after 30s rather than assuming the deploy failed.

## Related Skills
- `coding-workflow` — Full-stack coding workflow (auth UI patterns, patch pitfalls, f-string handling)
- `book-to-skill` — Knowledge extraction and skill creation methodology
