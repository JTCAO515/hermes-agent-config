# LLM Content Persistence Pattern

> Save, view, load, and share LLM-generated content (itineraries, plans, analyses) directly in the browser — zero backend changes.

## Architecture

```
User Chat → LLM generates structured content
  ↓ (auto-detection in JS)
  "💾 Trip saved! View all trips →" note appears
  ↓ (localStorage)
Trips list view → Load (restores to chat) → Share (clipboard)
```

## When to use

- LLM generates structured, reusable content (itineraries, meal plans, workout routines, study schedules)
- Content is valuable enough to keep across sessions
- You want zero backend/database changes
- Vercel/stdlib project where localStorage is the simplest persistence layer

## Implementation

### 1. Trip/Content data structure

```javascript
{
  id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
  city: city || '',                    // contextual identifier
  title: firstLine of content,         // auto-extracted
  content: rawText,                    // the full LLM response
  days: detectedDayCount || '?',       // parsed from pattern Day N
  created: new Date().toISOString(),   // ISO date for sorting
}
```

### 2. Auto-detection heuristic

Detect if bot response looks like "save-worthy" content:

```javascript
function autoSaveContent(contextKey, content) {
  const hasDayPattern = /\*\*Day \d+|Day \d+:/i.test(content);
  const hasListItem = /^\- /m.test(content);
  const hasStructureIcons = /[🕐🍽️🏨💡🎯💰⭐]/i.test(content);
  
  // Save if: has day structure, OR has list + enough length + structure icons
  if ((hasDayPattern || (hasListItem && content.length > 300)) && content.length > 200) {
    return saveContent(contextKey, content);  // returns saved item
  }
  return null;
}
```

Call this after each bot response in the SSE stream handler.

### 3. Save indicator (subtle, non-blocking)

```javascript
const saved = autoSaveContent(currentCity, botContent);
if (saved) {
  const note = document.createElement('div');
  note.className = 'save-note';
  note.innerHTML = '💾 Saved! <a href="#" onclick="VP.navigate(\'list-view\');return false">View all →</a>';
  chatContainer.appendChild(note);
}
```

CSS:
```css
.save-note{
  text-align:center;padding:8px;margin:4px 0;
  font-size:12px;color:var(--accent-gold);
  background:var(--accent-gold-soft);
  border-radius:6px;
  animation:slideUp .25s ease;
}
```

### 4. List view

Grid of saved items with:
- Context icon (city emoji or generic)
- Title (first line)
- Meta (days · date)
- Preview snippet (120 chars)
- Action buttons: Load / Copy / Delete

### 5. Load action (restore to chat)

```javascript
function loadContent(id) {
  const items = getAllItems();
  const item = items.find(t => t.id === id);
  if (!item) return;

  // Push into conversation history
  messages.push({role: 'user', content: 'Show me my saved item: ' + item.title});
  messages.push({role: 'assistant', content: item.content});
  saveMessages();

  // Navigate to chat view
  navigate('chat');

  // Re-render all messages from history
  renderMessages();
}
```

### 6. Share action (clipboard)

```javascript
function shareContent(id) {
  const items = getAllItems();
  const item = items.find(t => t.id === id);
  if (!item) return;

  // Strip markdown for clean text
  const clean = item.content
    .replace(/\*\*/g, '')
    .replace(/#/g, '')
    .replace(/---+/g, '')
    .trim();

  const text = '🌏 Title: ' + item.title + '\n'
    + '─────────────────\n\n'
    + clean
    + '\n\n─────────────────\n'
    + 'Created with App 🐼';

  navigator.clipboard.writeText(text).then(() => {
    showToast('✅ Copied to clipboard!');
  });
}
```

### 7. Toast notification

```javascript
const toast = document.getElementById('toast') || (() => {
  const el = document.createElement('div');
  el.id = 'toast';
  el.className = 'toast';
  document.body.appendChild(el);
  return el;
})();
toast.textContent = message;
toast.classList.add('show');
setTimeout(() => toast.classList.remove('show'), 2000);
```

```css
.toast{
  position:fixed;bottom:80px;left:50%;transform:translateX(-50%);
  background:var(--bg-secondary);
  border:1px solid var(--border-default);
  color:var(--text-primary);
  padding:10px 20px;border-radius:8px;
  font-size:13px;font-weight:500;
  z-index:300;opacity:0;transition:opacity .3s;
  pointer-events:none;
  box-shadow:0 8px 30px rgba(0,0,0,.5);
}
.toast.show{opacity:1}
```

## Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| **localStorage quota** (5-10MB) | Saving large itinerary content + chat history | Cap saved items at 20; chat history at 50 messages; `.slice(0, 20)` |
| **Stale data after delete** | List view not re-rendered | Call `renderListView()` after every delete |
| **Load duplicates** | User clicks Load multiple times | Use `messages.push()` both user + assistant messages to reconstruct conversation naturally |
| **Clipboard API fails on HTTP** | `navigator.clipboard` requires HTTPS/localhost | Fallback: `alert('Copied!\n\n' + text.slice(0, 200) + '...')` |
| **EscHtml injection** | Content may contain HTML | Always escape with `escHtml()` before inserting into innerHTML |
