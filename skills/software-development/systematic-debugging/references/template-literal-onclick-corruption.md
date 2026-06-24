# Template Literal → onclick Corruption

A recurring frontend bug pattern where complex JavaScript embedded in `onclick` attributes inside template literals produces broken HTML.

## Symptom

The rendered HTML shows the raw JavaScript source code of the click handler instead of the expected UI element. Clicking does nothing. The page may show fragments like:

```
Loading...
'; fetch('/api/...') .then(r => r.json()) ...
```

## Root Cause

Nested template literals (backticks `` ` ``) inside template-generated HTML. When you have:

```javascript
function render() {
  const html = `
    <button onclick="
      var x = '${someValue}';
      fetch('${API}/...')
        .then(...)
    ">Click</button>
  `;
}
```

...the JavaScript engine sees the **first backtick after `onclick="` as closing the outer template literal**, not as starting an inner string. This corrupts the entire template, producing broken HTML with visible JS code.

## The Fix: Event Delegation

**Never put complex JS in onclick (or onchange, onmouseover, etc.) attributes of HTML generated inside template literals.** Use event delegation instead:

```javascript
// ❌ WRONG — will corrupt
function render() {
  return `
    <div class="session" onclick="
      fetch('/api/' + id).then(r => r.json()).then(d => { ... });
    ">...</div>
  `;
}

// ✅ CORRECT — event delegation
function render() {
  return `
    <div class="session" data-id="${id}">...</div>
  `;
}

// Separate click handler
document.getElementById('container').addEventListener('click', function(e) {
  const el = e.target.closest('.session');
  if (!el) return;
  const id = el.getAttribute('data-id');
  fetch('/api/' + encodeURIComponent(id))
    .then(r => r.json())
    .then(d => { /* render */ });
});
```

## Rules

1. **Inline onclick OK for** — simple calls like `onclick="toggle()"` where `toggle` is a named function with no arguments. Even here, avoid template-variable interpolation in the call.
2. **Inline onclick NOT OK for** — any handler with fetch, template variables (`${...}`), multiple statements, or arrow functions.
3. **Use `data-*` attributes** to pass data from template to click handler.
4. **Use `e.target.closest()`** to handle clicks on child elements of the target.
5. **Cache the container** — `document.getElementById('container')` once, not on every click.

## Detection

If rendered HTML looks like it contains JS source code:
- Check the onclick attribute value in the rendered HTML (browser dev tools)
- Look for backtick characters (`` ` ``) appearing inside onclick= strings
- Look for `${...}` inside onclick attributes — this is the telltale sign

## Prevention

When writing template-literals-generated HTML, always ask:
- Does this HTML contain any dynamic behavior (clicks, onChange, onSubmit)?
- If yes: move that behavior to a delegated event listener
- Keep the template literal only for static HTML structure + data-* attributes
