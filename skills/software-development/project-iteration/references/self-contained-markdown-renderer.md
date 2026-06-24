# Self-Contained Markdown Renderer for LLM Chat

## When to use

Build a minimal markdown-to-HTML renderer (no external library) when:
- You want zero pip/npm dependencies (stdlib-only Vercel)
- LLM output contains only basic markdown: `**bold**`, lists, `inline code`, code blocks, horizontal rules
- You don't need full GFM (tables, links, images, headings beyond bold)

## The renderer (~30 lines)

```javascript
function renderMD(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks (```...```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // Horizontal rules
  html = html.replace(/^-{3,}$/gm, '<hr>');

  // Unordered lists: - item → <li>item</li> → <ul><li>...</li></ul>
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Ordered lists: 1. item → <li>item</li> → <ol>
  html = html.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(?<!<ul>)((<li>.*<\/li>\n?)+)(?!<\/ul>)/g, '<ol>$1</ol>');

  // Paragraphs (split by double newlines)
  const parts = html.split(/\n\n+/);
  return parts.map(p => {
    p = p.trim();
    if (!p) return '';
    if (p.startsWith('<')) return p;  // already wrapped
    return `<p>${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');
}
```

## CSS companion (~40 lines)

```css
.msg-text p{margin-bottom:8px;line-height:1.7}
.msg-text p:last-child{margin-bottom:0}
.msg-text strong{color:var(--accent-gold);font-weight:600}  /* gold emphasis */
.msg-text ul{margin:4px 0 8px;padding-left:20px;list-style:none}
.msg-text ul li{position:relative;padding-left:4px;margin-bottom:3px}
.msg-text ul li::before{content:'•';position:absolute;left:-14px;color:var(--accent-red)}  /* red bullets */
.msg-text ol{margin:4px 0 8px;padding-left:20px}
.msg-text ol li{margin-bottom:3px}
.msg-text hr{margin:12px 0;border:none;border-top:1px solid var(--border-default)}
.msg-text code{font-family:'JetBrains Mono',monospace;font-size:12px;
  background:var(--bg-hover);padding:1px 5px;border-radius:4px;color:var(--accent-blue);}
.msg-text pre{margin:8px 0;background:var(--bg-tertiary);
  border:1px solid var(--border-subtle);border-radius:6px;padding:12px;overflow-x:auto;}
.msg-text pre code{background:none;padding:0;color:var(--text-secondary);font-size:12px;}
```

## Using with SSE streaming

When receiving tokens one at a time via SSE, render incrementally:

```javascript
// In the SSE stream loop, when receiving a token:
botContent += parsed.token;
updateTyping(typingId, botContent);
// The updateTyping function calls renderMD():
function updateTyping(el, content) {
  const textDiv = el.querySelector('.msg-text');
  if (textDiv && content) {
    textDiv.innerHTML = renderMD(content) + '<span class="cursor-blink">▌</span>';
  }
}
```

## Why not marked.js / showdown?

| Library | Size | Issue |
|---------|------|-------|
| `marked.js` | ~18KB min | Adds npm/tag dependency; overkill for simple bold+lists output |
| `showdown` | ~21KB min | Same problem |
| Self-built | ~1KB | Zero dependencies, perfectly tailored to LLM output |

LLM output from DeepSeek/GPT/Claude typically only uses: `**bold**`, `- lists` (unordered), `1. lists` (ordered), `inline code`, code blocks, horizontal rules, and paragraph breaks. The self-built renderer covers all of these.

## Pitfalls

- **Ordered list detection**: The regex `^\d+\.\s(.+)$` matches `1. item`, `10. item`, etc. It may conflict with decimal numbers at start of line — rare in LLM output.
- **Nested lists**: Not supported. LLMs rarely output nested lists in travel itineraries.
- **Tables**: Not supported. If needed, add a simple pipe-to-HTML-table converter.
- **Headers**: The LLM output uses `**bold**` for headings (like `**Day 1:**`) rather than `##` headers, so no `#` handling is needed.
