# Web UI 实现参考

## 整体架构

SPA 单页应用：**HTML + CSS + JS**，通过 `<script>` 标签内联所有逻辑，零外部依赖（无 React/Vue/jQuery）。

文件：`api/static/index.html`

## 牌编码方案（JS 端）

**必须**与服务端 Python `encode()` 完全一致。

### 正确公式

```javascript
function T(s, r) {
  const base = [0, 36, 72, 108, 120];  // 每花色偏移
  const per = [4, 4, 4, 3, 4];          // 每牌种张数（风牌 3 张）
  return base[s] + (r - 1) * per[s];
}
```

**⚠️ 历史坑：`s*28+(r-1)*4`（已废弃 — 见 bug-patterns.md 第7条）**
- ~~`function T(s,r) { return s*28+(r-1)*4 }`~~ → 所有非万花色编码错误、跨花色重叠
- 验证方法：首次实现时用 Python 对每个花色取首/中/尾三点做交叉校验

### ALL 数组

```javascript

## 关键函数

### `ts(c)` — 短名（选牌按钮显示）

```javascript
// ✅ 正确实现
function ts(c) {
  const t = ALL.find(x => x.code === c);
  if (!t) return '?';
  if (t.suit <= 2) return t.rank + ['万','条','饼'][t.suit];  // "1万" "2条"
  return '东南西北中发白'[t.rank - 1 + (t.suit === 3 ? 0 : 4)]; // "东" "中"
}
```

**⚠️ 历史坑**：
- ~~`['','万','条','饼'][t.suit]+t.rank`~~ → 显示"万1"而非"1万"，且 suit=0 时显示''（空，缺花色）
- `['','万','条','饼']` 索引偏移：suit=0→''(空) suit=1→'万'(错) suit=2→'条'(错) 
- 正确数组：`['万','条','饼']`，索引 0=万 1=条 2=饼

### `tn(c)` — 全名（结果展示）

```javascript
const NAMES[c] = s.id <= 2 ? (n[r-1] + s.name) : [...]; // "一万" "五万" "东风"
// n = ['一','二',...,'九','东','南','西','北','中','发','白']
```

## 交互模式

### 手牌选择

| 操作 | 行为 |
|------|------|
| 短按（< 400ms） | 加 1 张（上限 4 张/种） |
| 长按（≥ 400ms） | **清空**该牌所有副本 |
| 点手牌条 ✕ | 减 1 张 |

### 舍牌选择

与手牌**相同的交互模式**：
| 操作 | 行为 |
|------|------|
| 短按（< 400ms） | 加 1 张（上限 4 张/种） |
| 长按（≥ 400ms） | **清空**该牌所有副本 |
| 切换玩家 | 点玩家 pill，保留各玩家独立列表 |

**⚠️ 历史坑**：最早用 toggle 逻辑（点一下加，再点删），用户反馈无法选择多张相同牌。改为 ADD + long-press-remove 模式。

### 长按的实现

```javascript
// 通过 pointerdown / pointerup / pointerleave 实现
el.addEventListener('pointerdown', function(e) {
  const m = this.getAttribute('onclick');
  if (m) code = parseInt(m.match(/\d+/)[0]);
  timer = setTimeout(() => { removeFn(code); timer = null; }, 400);
});
el.addEventListener('pointerup',   () => { if (timer) { clearTimeout(timer); timer = null; } });
el.addEventListener('pointerleave',() => { if (timer) { clearTimeout(timer); timer = null; } });
```

注意：不能直接用 `ontouchstart`/`ontouchend`，要兼顾鼠标点击。

### 手牌条（hand strip）

合并相同牌显示，不重复渲染：

```javascript
// ❌ 旧：每张牌一个独立卡片 → "1万 1万 1万" 占3个位置
for (let i = 0; i < n; i++)
  hs += `<div>${ts(c)}<span class="x">✕</span></div>`;

// ✅ 新：合并显示 ×N → "1万×3" 占1个位置
hs += `<div>${ts(c)}${n > 1 ? `×${n}` : ''}<span class="x">✕</span></div>`;
```

## 布局演进

### 版本 1：单 Tab（初始版）
- 纯手牌输入 + 分析按钮
- 无牌局状态输入

### 版本 2：双 Tab（Session 重构）
- Tab「手牌」— 点选手牌
- Tab「牌局」— 三家舍牌 + 对面副露 + 对方出牌 + 设置
- 问题：Tab 切换破坏输入流，用户需要来回切

### 版本 3：单页合并（当前版，Session-006）
- **顶部**：手牌预览条（实时显示已选牌，长按清除）
- **中部**：完整牌选择网格（花色分组，9列网格）
- **设置行**：座风/圈风/摸牌模式（紧凑一行）
- **折叠区1**：三家舍牌（默认展开，玩家 pill 切换）
- **折叠区2**：他家副露（默认折叠）
- **折叠区3**：对方打牌（默认折叠，用于吃碰杠判断）
- **分析按钮**：手牌≤12张→普通金色，≥13张→亮金色脉冲提示
- **结果区**：操作英雄卡（最大的建议）→ 统计卡片 → 详情表格 → 防守信息

### 版本 4：统一牌网格（当前版，Session-007）

**核心改动**：手牌和三家舍牌共用一个牌选择网格（不再有"手牌网格"和"舍牌网格"两个独立网格）。通过**模式 selector** 切换操作目标。

**布局**：

```
[手牌预览条]              ← 始终显示你的手牌
[MODE PILLS]              ← 🧩手牌 🔴下家 🔵对家 🟢上家 点选切换
[统一牌网格]               ← 唯一的选择网格，高亮当前模式的已选牌
[对手摘要行]              ← 下家/对家/上家各自已出牌的摘要（点击直达）
[设置行]                  ← 座风/圈风/自摸/出牌
[分析按钮]                ← 单按钮
[结果区]                  ← 全面分析
```

**交互规则**（全模式统一）：
| 元素 | 短按 | 长按 |
|------|------|------|
| 牌网格按钮 | 当前模式+1张（上限4） | 清空当前模式该牌 |
| 手牌条 tile | -1张 | — |
| 对手摘要行 | 自动切到该玩家模式 | — |
| 结果"打X"卡 | 从手牌移除该张牌 | — |

**出牌人选择**：点击"出牌"按钮 → 牌网格切换为选牌模式 → 点选对方的牌 → 自动确认并恢复到正常模式。

**注意**：三个模式（手牌/下家/对家/上家）的数据完全独立，互不影响。切模式不会丢失各玩家的数据。

## 花色配色方案

```css
/* 选牌颜色 */
.tile.sel.wan  { background: rgba(232,197,74,0.18);  color: #e8c54a; }  /* 金色 */
.tile.sel.tiao { background: rgba(106,191,122,0.18); color: #8adf9a; }  /* 绿色 */
.tile.sel.bing { background: rgba(74,159,223,0.18);  color: #7abfef; }  /* 蓝色 */
.tile.sel.feng { background: rgba(232,160,64,0.15);  color: #f0b050; }  /* 橙色 */
.tile.sel.jian { background: rgba(212,85,85,0.15);   color: #e07070; }  /* 红色 */
```

## 结果展示层次

分析结果从上到下递减重要性：

1. **胡牌卡**（如果有）→ 大金牌，显示胡哪张+多少番
2. **最佳出牌卡** → 蓝色卡，可点击（点击自动从手牌移除该张）
3. **吃碰杠卡** → 红色卡
4. **向听/进张统计** → 两列卡片
5. **进张牌列表** → chips 展示
6. **出牌对比表** → 所有出牌选项
7. **听牌分析** → 最佳听牌 + 番种明细 + 所有选项
8. **防守信息** → 危险牌 + 安全牌

## 关于卡片点击行为

最佳出牌卡可点击自动执行：

```javascript
onclick="rmOne(${bestDisc.tile.code}); renderHand(); document.getElementById('resultArea').classList.remove('show')"
```

效果：点「打 1万」→ 手牌移除 1 张 1 万 → 页面刷新 → 结果区收起 → 手牌自动更新显示移除后状态。

## 手牌上限：14 张

手牌模式（target=0）下，点选手牌时做硬限制：

```javascript
function tapTile(code, target) {
  if (target === 0 && totalHand() >= 14) return;  // 最多14张
  // ...
}
```

选满 14 张后点按无反应（不会报错/卡死），手牌条右上角 count 实时显示当前张数。
用户需先出牌（点✕或点分析结果中的「打 X 卡」）后才能继续添加。

## 最优打法英雄卡

分析结果顶部最显眼位置，以大金色分隔线引导视觉焦点：

```html
<div style="text-align:center;font-size:.55rem;font-weight:700;color:var(--gold);letter-spacing:2px;margin:4px 0 2px">
  ━━  👉 最优打法  👈  ━━
</div>
```

卡片特征：
- tile 图标尺寸 42×52px（大于普通卡片 38×46）
- 危险等级着色：`var(--green)` 🟢 / `var(--orange)` 🟡 / `var(--red)` 🔴
- 可点击：点完后自动 `rmOne(code)` + 重渲染手牌 + 收起结果区
- 位于所有结果卡片之上，独立成行

## 设计系统（Session-007 最终版）

### 字体

```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;800;900&display=swap');
body {
  font-family: 'Noto Sans SC', -apple-system, 'PingFang SC', ...;
}
```

### CSS 变量体系

```css
:root {
  --bg: #16281e;            /* 深绿桌面背景 */
  --felt: #0f1f16;          /* 墨绿桌面 */
  --gold: #dbb42c;          /* 金色主色 */
  --rose: #c0392b;          /* 删除/危险 */
  --radius: 10px;           /* 卡片圆角 */
  --radius-sm: 6px;         /* 小圆角 */
  --shadow: 0 2px 16px rgba(0,0,0,0.5);  /* 卡片阴影 */
}
```

### 动画

```css
.result-area {
  animation: fadeIn .2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.analyze-btn.ready {
  background: linear-gradient(135deg, rgba(219,180,44,0.18), rgba(219,180,44,0.08));
  box-shadow: 0 0 20px rgba(219,180,44,0.06);
  /* 手牌≥13张时自动添加 → 金色脉冲吸引点击 */
}
```

### Tile 样式

```css
.tile {
  aspect-ratio: .8;          /* 纵向比 0.8 → 更像真实麻将牌 */
  border-radius: 5px;
  transition: all .1s ease;
}
.tile:active { transform: scale(.82); }

/* 选中态：淡金渐变 + 半透明金边 + 光晕 */
.tile.hand {
  background: linear-gradient(135deg, rgba(219,180,44,0.12), rgba(219,180,44,0.04));
  border-color: rgba(219,180,44,0.2);
  box-shadow: 0 0 8px rgba(219,180,44,0.06);
}
```

### 卡片样式

```css
.sec {
  background: linear-gradient(135deg, rgba(0,0,0,0.04), rgba(0,0,0,0.02));
  border-radius: var(--radius-sm);
  border: 1px solid rgba(219,180,44,0.02);
}
```

### 响应式

```css
@media (max-width: 420px) {
  .tile { font-size: .7rem; }         /* 极窄屏缩小字号 */
}
```
