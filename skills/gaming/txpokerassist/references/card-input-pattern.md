# Card Input Pattern — TXPokerAssist 选牌交互演进

## v4.5: 13×4 牌面网格（当前方案）

### 动机
v4.2 的 rank→suit 两步选牌需要点两次才能选1张牌，且无视觉反馈哪些牌已被选。

市面调研（Equilab/PokerCruncher/Odds Calculator for Poker）一致采用 **13×4 网格点选**，
1次点击=1张牌，比两步法少 50% 操作。详见 `references/poker-card-ui-research.md`。

### 结构

```html
<!-- 起手牌快速预设 -->
<div class="hand-presets" id="qPresets"></div>
<!-- 13×4 牌面网格 -->
<div class="card-grid" id="qGrid"></div>
```

```css
.card-grid{display:grid;grid-template-columns:repeat(13,1fr);gap:2px}
.card-cell{padding:5px 0;border-radius:4px;text-align:center;font-size:.68rem;font-weight:700}
.card-cell.used{opacity:0.2;pointer-events:none}
.card-cell.red{color:#ef5350}
.card-cell.black{color:var(--text)}
```

### JS 生成逻辑

```javascript
function buildGrid(prefix){
  const grid=document.getElementById(prefix+'Grid');
  SUITS.forEach(suit=>{
    RANKS.forEach(rank=>{
      const card=rank+suit.c;
      const div=document.createElement('div');
      div.className=`card-cell ${suit.cls}`;
      div.dataset.card=card;
      div.innerHTML=`${rank}<span class="mini-suit">${suit.sym}</span>`;
      div.addEventListener('click',()=>pickCard(prefix,card));
      grid.appendChild(div);
    });
  });
}
```

### 智能分配

```javascript
function pickCard(prefix,card){
  const st=getState(prefix);
  if(st.hero.length<2) st.hero.push(card);
  else if(st.board.length<5) st.board.push(card);
  else { status('❌ 已选满7张牌'); return; }
  renderCards(prefix);
  updateGridUsed(prefix);  // 灰掉已选牌
}
```

### 已选牌灰掉

```javascript
function updateGridUsed(prefix){
  const st=getState(prefix);
  const all=[...st.hero,...st.board];
  document.querySelectorAll(`#${prefix}Grid .card-cell`).forEach(cell=>{
    cell.classList.toggle('used',all.includes(cell.dataset.card));
  });
}
```

### 起手牌预设

```javascript
const HAND_PRESETS=[
  {label:'AA',cards:['As','Ah']},
  {label:'KK',cards:['Ks','Kh']},
  {label:'AKs',cards:['As','Ks']},
  {label:'AKo',cards:['As','Kh']},
  {label:'QQ',cards:['Qs','Qh']},
];
```

---

## v4.2: 文本输入 + rank→suit 两步选牌（已废弃）

### 问题
- 需要点两次（先 rank 后 suit）才能选1张牌
- 无已选牌灰掉机制，容易选重复
- suit 按钮在选 rank 前不可用，但无视觉提示

### 保留部分
- **文本输入框**仍保留为辅助输入方式
- **已选小卡片**渲染 + 点击移除 仍使用

### 文本解析（保留）

```javascript
function parseCards(str){
  const cleaned=str.replace(/[,\s]+/g,' ').trim();
  if(!cleaned)return[];
  const tokens=cleaned.split(/\s+/);
  const result=[];
  for(let t of tokens){
    let rank,suit;
    if(t.startsWith('10')){rank='T';suit=t[2]||'';}
    else{rank=t[0];suit=t[1]||'';}
    rank=rank.toUpperCase();
    const sChar=SUIT_MAP[suit.toLowerCase()];
    if(!RANK_MAP[rank]||!sChar)continue;
    result.push(rank+sChar);
  }
  return result;
}
```

自动分离：前 2 张为手牌，后面的为公共牌。

### 已选卡牌展示（保留）

```html
<div class="mini-card red">
  <span class="r">A</span>
  <span class="s">♥</span>
</div>
```

- 每张卡牌 44×62px，Georgia 字体
- 花色颜色：#c62828（红）/ #1a1a1a（黑）
- 点击移除：添加 .removing class → 180ms 后 splice → renderCards

---

## 坑点记录

### ❗ board 空字符串 split 陷阱
JS 中 `''.split(' ')` 返回 `['']` 而非 `[]`。发送到后端时 `board: ['']` 可能导致 parse_card("") 报错。

```javascript
// ❌ 错误
const board = boardStr.split(' ');

// ✅ 正确
const board = boardStr ? boardStr.split(' ').filter(c => c.trim()) : [];
```

### ❗ 中英文 action 值匹配
后端返回中文 action（"加注"/"跟注"/"弃牌"），前端 CSS 类判断需兼容：

```javascript
const act = d.action.toLowerCase();
banner.className = act.includes('加注') || act === 'raise' ? 'raise' : 'fold';
```
