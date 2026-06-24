# Frontend Security & Performance Checklist

## XSS 防护

### `esc()` 转义函数（必须）
Vanilla JS 项目必须包含此函数，用于所有 `innerHTML` 赋值的 API 数据：

```javascript
function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
```

### innerHTML 审计
审查时逐行检查所有 `.innerHTML =` 赋值，以下场景必须用 `esc()` 包裹：
- API 响应的 `d.error`, `d.message` — 错误消息可能被滥用为 XSS payload
- 团队名、球员名等用户可影响字段
- `b.selection`, `b.market_type` 等投注选择字段
- 赔率字符串、百分比（虽然纯数字安全，但保持一致性）

### textContent 优于 innerHTML
能用 `textContent` 设置文本的字段，绝不用 `innerHTML`：
```javascript
// ✅ 安全 — 纯文本
el.textContent = `$${bankroll.toLocaleString()}`;
// ❌ 危险 — API 数据直接 innerHTML
el.innerHTML = `${d.error}`;
```

### style 直接设置，不拼接字符串
```javascript
// ✅ 安全且类型安全
refs.pret.style.color = ret >= 0 ? '#34d399' : '#f87171';
// ❌ 危险 — style 字符串拼接
el.style.cssText = 'color: ' + color;
```

## DOM 性能优化

### DOM 选择器缓存（懒加载模式）
在 render 函数内缓存静态度 DOM 引用，避免每次调用都 querySelector：

```javascript
let _pkRefs = null;
function pkRefs() {
  if (!_pkRefs) _pkRefs = {
    subtitle: $('#picks-subtitle'),
    body: $('#picks-body'),
    bankroll: $('#pk-bankroll'),
    stake: $('#pk-stake'),
    // ... cached once
  };
  return _pkRefs;
}
```

可节省 5-10 次 querySelector/渲染周期。

### 事件监听器合并
将多个独立的 click listener 合并为一个代理监听器，通过 `e.target.closest()` 分发：

```javascript
// ❌ 4个独立监听器
document.addEventListener('click', handlerA);
document.addEventListener('click', handlerB);
document.addEventListener('click', handlerC);
document.addEventListener('keydown', handlerD);

// ✅ 1个代理监听器（click）+ 1个keydown
document.addEventListener('click', (e) => {
  if (e.target.closest('.btn-a')) { handlerA(); return; }
  if (e.target.closest('.btn-b')) { handlerB(); return; }
  if (e.target.closest('.btn-c')) { handlerC(); }
});
```

### AbortController 防竞争
对重复触发的 API 调用（输入框 Enter、快速点击），用 AbortController 取消前一次请求：

```javascript
let abortCtrl = null;

function fetchData() {
  if (abortCtrl) abortCtrl.abort();
  abortCtrl = new AbortController();
  
  fetch('/api/data', { signal: abortCtrl.signal })
    .then(r => r.json())
    .then(d => render(d))
    .catch(err => {
      if (err.name === 'AbortError') return; // 静默忽略
      showError(err);
    });
}
```

## JavaScript 陷阱

### 0 || 默认值陷阱
`0 || "?"` 在 JS 中求值为 `"?"`（0 是 falsy），导致合法比分 0 显示为问号。

```javascript
// ❌ 0 被吞 — 比分 2-0 显示为 2-?
const score = `${result.home || "?"}–${result.away || "?"}`;

// ✅ 显式 null/undefined 检查
function _val(v) { return v != null ? v : "?"; }
const score = `${_val(result.home)}–${_val(result.away)}`;
```

**防御原则**：
- 数字 0、空字符串 `""`、布尔 `false` 是有效值时，用 `!= null` 检查
- 提取成 `_val()` 或 `_gs()` 辅助函数

### Null-safe chaining
API 响应中可能缺失的数组/对象字段，用 `?.` 保护：

```javascript
// ❌ 若 d.bets 为 undefined → TypeError
d.bets.forEach(b => ...);

// ✅ 安全
if (d.bets) d.bets.forEach(b => ...);
// 或
(d.bets || []).forEach(b => ...);
```

## 验证命令

```bash
# JS 语法检查
node --check web/app.js

# 查找所有 innerHTML 赋值（需逐行人工审计）
grep -rn '\.innerHTML\s*=' web/app.js

# 查找 0 || 默认值陷阱
grep -rn '|| "\|"?' web/app.js

# 查找未受保护的 forEach
grep -rn '\.forEach' web/app.js | grep -v 'if\|?\.\|\.bets\b'
```
