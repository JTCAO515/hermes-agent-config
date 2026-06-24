---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Classify the PDF Type

PDFs fall into **three** categories — detect first before choosing the tool:

### How to Detect

```python
import pymupdf
doc = pymupdf.open("document.pdf")
print(f"Pages: {len(doc)}, Metadata: {doc.metadata}")
page = doc[0]
text = page.get_text().strip()
imgs = page.get_images(full=True)
blocks = page.get_text("dict")["blocks"]
print(f"Text length: {len(text)}, Images: {len(imgs)}, Blocks: {len(blocks)}")
for b in blocks:
    print(f"  Block type={b['type']}, bbox={b['bbox']}")  # type=0=text, type=1=image
```

- **Text-based PDF**: `len(text) > 0` and `blocks` contain type=0 text blocks → pymupdf works directly
- **Image-based PDF (WPS/PPT/Keynote export)**: `len(text) == 0`, each page = 1 type=1 image block; creator likely "WPS 演示" or "Microsoft PowerPoint" → **render + tesseract**
- **Scanned PDF**: `len(text) == 0`, pages may look like book scans with multiple images per page → marker-pdf (heavy OCR)

### Tool Comparison

| Feature | pymupdf (~25MB) | pymupdf + tesseract (~130MB) | marker-pdf (~3-5GB) |
|---------|-----------------|------------------------------|---------------------|
| **Text-based PDF** | ✅ | ✅ (unnecessary) | ✅ |
| **Image-based PDF (WPS/PPT export)** | ❌ (no text) | ✅ (render→OCR) | ✅ (overkill) |
| **Scanned PDF (OCR)** | ❌ | ⚠️ (works but less accurate) | ✅ (90+ languages) |
| **Chinese text** | ✅ (if embedded) | ✅ (chi_sim+chi_tra) | ✅ |
| **Tables** | ✅ (basic) | ⚠️ (OCR loses layout) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ❌ | ✅ |
| **Complex layout analysis** | ❌ | ❌ | ✅ |
| **Install size** | ~25MB | ~130MB (pymupdf + tesseract + lang data) | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~2-5s/page (CPU) | ~1-14s/page (CPU) |
| **No internet needed?** | ✅ | ✅ | ✅ (models cached) |

### Decision Tree

```
Is URL available? ─Yes→ web_extract (Firecrawl)
     │
     No
     │
     ▼
Is PDF text-based? ─Yes→ pymupdf (instant, no extra installs)
     │
     No
     │
     ▼
Is it WPS/PPT/Keynote export
(each page = 1 full-image block)? ─Yes→ pymupdf render + tesseract (lightweight OCR)
     │                                (creator="WPS 演示" or "Microsoft PowerPoint")
     No (scanned book/doc)
     │
     ▼
Has 5GB+ free disk? ─Yes→ marker-pdf (best OCR)
     │
     No
     │
     ▼
Fallback: pymupdf + tesseract (degrade gracefully)

---

## .doc (Old Word Format) Handling

> Old-format .doc files (Composite Document File V2) cannot be opened by `python-docx`.
> Use `antiword` for text extraction from .doc files.

```bash
# Install
sudo apt-get install -y antiword

# Basic text extraction (UTF-8)
antiword -m UTF-8 document.doc

# Redirect to file
antiword -m UTF-8 document.doc > extracted.txt
```

**Pitfalls:**
- `antiword` extracts text only (no images, no tables, no formatting)
- The file command can identify .doc vs .docx: `file document.doc` → "Composite Document File V2"
- `python-docx` will throw `PackageNotFoundError` on .doc files — check with `file` first before deciding the extraction tool
- For complex layout .doc files, try `catdoc` or LibreOffice headless conversion (`libreoffice --headless --convert-to docx`)

**Quick detection:**
```bash
if file "$DOC" | grep -q 'Composite Document File'; then
    antiword -m UTF-8 "$DOC"  # .doc format
else
    python3 -c "from docx import Document; ..."  # .docx format
fi
```

---

## pymupdf + tesseract OCR (lightweight image-based PDFs)

For **image-based PDFs** (WPS Presentation, PowerPoint, Keynote exports) where each page is a full-page image but you don't want to install marker-pdf's 3-5GB dependencies, render pages to images and OCR with tesseract.

### Install

```bash
sudo apt-get install -y tesseract-ocr \
    tesseract-ocr-chi-sim tesseract-ocr-chi-tra tesseract-ocr-jpn \
    tesseract-ocr-kor tesseract-ocr-rus
pip install pytesseract Pillow
```

### Workflow

```python
import pymupdf, pytesseract
from PIL import Image

doc = pymupdf.open("document.pdf")

# 1. Check if it's image-based (no text layer)
page0 = doc[0]
has_text = len(page0.get_text().strip()) > 0

# 2. Render each page at 2x DPI for better OCR
for i, page in enumerate(doc):
    mat = pymupdf.Matrix(2, 2)    # 2x zoom = 144 DPI → good balance
    pix = page.get_pixmap(matrix=mat)
    img_path = f"/tmp/pdf_pages/page_{i+1}.png"
    pix.save(img_path)
    
    # 3. OCR (Chinese + English)
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    print(f"--- Page {i+1} ---")
    print(text)
```

### Key Parameters

| Aspect | Recommended | Reason |
|--------|-------------|--------|
| Matrix zoom | `Matrix(2, 2)` (144 DPI) | 1x too blurry, 3x+ too slow |
| Tesseract lang | `chi_sim+eng` for Chinese docs | Falls back to English for mixed content |
| File format | PNG (lossless) | JPEG artifacts confuse OCR |

### Pitfalls

- **WPS 演示 exports**: Creator metadata shows `WPS 演示` — this is a strong signal the PDF is image-only. Check `doc.metadata.get("creator")` before deciding.
- **pymupdf 1.27.x API changes**: `page.extract_image()` is removed. Use `page.get_pixmap(matrix=...)` + `pix.save()` instead. To check for images, use `page.get_image_info()` or `page.get_images(full=True)`.
- **Filename edge cases**: PDF filenames with trailing spaces or special unicode characters (like `（2026 ）.pdf` with a space before the parenthesis) can cause `FileNotFoundError` in pymupdf. Verify the exact filename with `os.path.exists()` before opening.
- **No `fitz` module**: In pymupdf 1.27.x, import via `import pymupdf`, not `import fitz` (the old name is not guaranteed).
- **Large PDFs**: Batching helps — OCR 4-5 pages at a time to avoid context overflow.
- **Tesseract not installed**: Check with `which tesseract` before relying on it. If absent, fall back to marker-pdf or inform user.

---

## pymupdf (text-based PDFs)

For text-based PDFs — no rendering or OCR needed, instant extraction.

### Install

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Verifying Tabular Data (Critical)

When extracting **pricing tables, product comparisons, or any structured tabular data**, the most common failure mode is **misattributing table labels or headers**. Follow this verification protocol:

### 1. Map Labels to Tables First
- **Don't assume** the order of table labels in the raw text matches their visual position. Use positional data (x,y coordinates from `page.get_text('dict')`) to determine which label sits above/below which table.
- **Read every label line** in the document — product names like "原生IP", "住宅IP", "动态住宅" often appear as section headers or footers near their respective tables.
- **CRITICAL: Labels can be FOOTERS, not headers.** In many PDF pricing tables, the product name label appears at the **bottom** of a table (as a footer/colophon), not above it. If you find labels scattered across the document (e.g. between table data blocks), extract ALL label positions first, sort by y-coordinate, then use a zone-mapping approach: find each table's bounding box and see which label falls within or adjacent to it.
- **When users correct your table assignment**, always check whether you misread which label maps to which table by examining positional data — this is the single most common PDF table extraction error.

### 2. Never Invent Category Names
- Use only the **exact product names** from the document. "Standard 档", "经济档", "基本款" etc. are invented — they mislead the user.
- If a table doesn't have an explicit label nearby, say "未标注名称" rather than making one up.

### 3. Cross-Reference Every Claimed Data Point
- Before presenting, verify each row/price/value actually exists in the extracted text. Common mistakes:
  - Adding a country/region that only appears in one table to the wrong table
  - Confusing unit prices vs. bulk prices vs. total prices
  - Swapping the monthly-consumption columns (e.g., 10k IPS vs 100k IPS)

### 4. Use Positional Extraction for Ambiguous Layouts
```python
import fitz
doc = fitz.open('document.pdf')
blocks = page.get_text('dict')['blocks']
for block in blocks:
    if block['type'] == 0:  # text block
        for line in block['lines']:
            text = ''.join([span['text'] for span in line['spans']])
            y = line['bbox'][1]
            x = line['bbox'][0]
            print(f'({x:.0f},{y:.0f}) {text}')
```
This reveals the actual visual layout (top-to-bottom, left-to-right) and prevents misordering.

### 5. When Corrected
If the user says you got a price/value wrong:
- **Don't just re-read the same text** — change your extraction method (use positional layout, or render as image and analyze visually)
- Check labels first, then numbers. Labels are the most common error.
- Present the corrected version alongside a clear "what I got wrong" note so the user trusts the fix.

---

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
