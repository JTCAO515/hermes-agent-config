# WC26 Service Worker Cache Bust 模式

## 问题

WC26/WC26Nami 使用 Service Worker 的 cache-first 策略缓存静态资源（app.js, app.css, index.html）。部署 JS 修复后，浏览器仍使用 SW 缓存的旧版本，表现为：
- 页面加载标题和 loading spinner
- app.js 不执行 / 页面一直转圈圈
- `browser_console` 中 `typeof init !== 'undefined'` 返回 `'init NOT found'`
- 但通过 `fetch('/app.js?_=' + Date.now())` 手动拉取并 eval 却能正常工作

## 根因

SW 的 `fetch` 事件处理：
```javascript
self.addEventListener("fetch", (e) => {
  // API calls → network only
  if (e.request.url.includes("/api/")) { ... return; }
  // Static assets → cache first
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request))
  );
});
```

由于 cache-first，浏览器永远从缓存读取 app.js，不会请求网络。即使服务器上的 app.js 已更新，SW 仍返回缓存中的旧版本。

## 修复步骤

### 1. 定位问题

```javascript
// browser_console 中执行
caches.keys()                                    // 查看活跃缓存名称
navigator.serviceWorker.getRegistrations()       // 检查 SW 注册状态

// 检查 app.js 语法
curl -s "https://example.com/app.js" | node --check /dev/null 2>&1
// 注: node --check /dev/stdin 不可用，必须保存到文件
curl -s "https://example.com/app.js" -o /tmp/app_check.js
node --check /tmp/app_check.js
```

### 2. 修复 SW 缓存名称

在 `sw.js` 中更改缓存版本字符串：

```javascript
// Before
const CACHE = "wc26-v1";

// After (任何内容变化都会触发 SW update)
const CACHE = "wc26-v2";
```

**原理：** SW 的 `install` 事件会在新 SW 检测到时触发。SW 的字节变化（即使一行注释）也会让浏览器检测到新版本。新的 `install` 事件打开新缓存名称 → 所有静态资源被重新缓存。旧的 `activate` 事件会删除旧缓存。

### 3. 浏览器端强制刷新

```javascript
// browser_console 中执行
(async function() {
  // 清除所有缓存
  var keys = await caches.keys();
  await Promise.all(keys.map(k => caches.delete(k)));
  // 注销所有 SW
  var regs = await navigator.serviceWorker.getRegistrations();
  await Promise.all(regs.map(r => r.unregister()));
  // 强制刷新
  window.location.href = '/?_=' + Date.now();
})();
```

### 4. 验证

```javascript
// 确认 app.js 执行
typeof init !== 'undefined' ? 'init FOUND' : 'init NOT found'
// 或检查 dashboard 可见性
document.getElementById('dashboard').style.display
// 应为 'block'
```

## Pitfalls

1. **只改 app.js 不改 sw.js 修复无效** — SW 不会自动检测 app.js 变化，即使 app.js 已修复。必须同时修改 sw.js 触发重新安装
2. **HTML 中无 SW 注册脚本也可能有 SW** — SW 一旦注册，即使 HTML 中的注册代码被移除，SW 仍存活。必须显式 unregister
3. **修改 sw.js 后需要清除浏览器的 SW 缓存** — 新的 SW 使用新缓存名，但旧的 SW/cache 可能仍存活。在 browser_console 中清除所有 cache + 注销所有 SW 是最可靠的方式
4. **`location.reload(true)` 不影响 SW 缓存** — 强制刷新跳过 HTTP 缓存但不跳过 SW。必须通过 DevTools 或 `caches.delete()` 清除 SW 缓存

## 诊断命令速查

| 目的 | 命令 |
|------|------|
| 查看活跃缓存 | `caches.keys()` |
| 查看 SW 注册 | `navigator.serviceWorker.getRegistrations()` |
| 清除所有缓存 | `caches.keys().then(ks => Promise.all(ks.map(k => caches.delete(k))))` |
| 注销所有 SW | `navigator.serviceWorker.getRegistrations().then(rs => Promise.all(rs.map(r => r.unregister())))` |
| 检查 deployed app.js 语法 | `curl -s URL -o /tmp/f.js && node --check /tmp/f.js` |
| 搜索 "truncated" 确认文件是否损坏 | `grep -c "truncated" /tmp/f.js` |
