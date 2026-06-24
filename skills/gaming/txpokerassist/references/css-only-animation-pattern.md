# CSS-Only Animation Pattern for TXPokerAssist

## 核心原则

所有动画使用纯 CSS + vanilla JS，不引入任何外部库。零额外 HTTP 请求。

| 原则 | 原因 |
|------|------|
| 只使用 `transform` / `opacity` | GPU 合成，不触发布局重排 |
| `cubic-bezier()` 弹性曲线 | 模拟物理弹簧，无需 JS 动画库 |
| 动画时长 150ms–600ms | 人眼最佳感知区间 |
| `backface-visibility: hidden` | 3D 翻转防止 Firefox 闪烁 |
| 不使用 `@property` | 兼容性不足（Chrome only），用 JS setTimeout 模拟 |

## 动画清单

| 动画 | 实现 | 触发表述 |
|------|------|---------|
| 页面淡入 | `body { animation: pageIn .4s ease-out }` | 页面加载 |
| 卡牌 3D 翻转 | `rotateY(90→0deg) + spring easing + stagger delay` | 选牌时渲染 |
| 卡牌移除 | `scale(1→0.5) + rotate(10deg) + fade` | 点击卡牌 → 先加 `.removing` class → 180ms 后 splice |
| 按钮金色流光 | `background-position 200% 200%` 渐变位移 | 静态持续 |
| 按钮悬停发光 | `box-shadow` 增强 + `translateY(-1px)` | 悬停 |
| 结果面板弹性弹入 | `translateY(24→-4→0) + scale(0.95→1.01→1)` spring | 接口返回 |
| 结果子元素分步渐入 | `stepIn` + `animation-delay` 递增 (100ms/150ms/200ms/250ms/300ms) | 面板 show |
| 横幅脉冲光晕 | `box-shadow` 内阴影呼吸 | 面板 show 后持续 |
| Equity 环弹性填充 | `stroke-dasharray` + `cubic-bezier(.34,1.56,.64,1)` | 数值更新 |
| 数字滚动 | `setTimeout` 20 帧 × 600ms | 面板 show |
| 胜负条展开 | `width` + spring easing | 数值更新 |
| 标签滑动指示器 | `translateX` + `.tab-indicator` 绝对定位 | 切换标签 |
| Range chip 回弹 | `scale(0.92)` + spring transition | 点击 |

## Easing 变量

```css
:root {
  --spring: cubic-bezier(.34,1.56,.64,1);    /* 弹性弹入 */
  --ease-out: cubic-bezier(.22,1,.36,1);     /* 平滑减速 */
  --ease-in-out: cubic-bezier(.65,0,.35,1);  /* 标准过渡 */
}
```

## 关键模式：Tab 滑动指示器

```html
<div class="tabs" style="position:relative">
  <div class="tab active" data-tab="quick">⚡ 快速决策</div>
  <div class="tab" data-tab="gt">🎯 博弈分析</div>
  <div class="tab-indicator" style="position:absolute;top:3px;bottom:3px;border-radius:7px;transition:transform .25s var(--spring);z-index:0;pointer-events:none"></div>
</div>
```

```javascript
function updateTabIndicator(tab){
  const ind=document.getElementById('tabIndicator');
  const tabs=document.querySelectorAll('.tab');
  const idx=Array.from(tabs).indexOf(tab);
  const tabW=100/tabs.length;
  ind.style.transform=`translateX(${idx*100}%)`;
  ind.style.width=tabW+'%';
}
```

## 关键模式：Tab 滑动指示器

```html
<div class="tabs" style="position:relative">
  <div class="tab active" data-tab="quick">⚡ 快速决策</div>
  <div class="tab" data-tab="gt">🎯 博弈分析</div>
  <div class="tab-indicator" style="position:absolute;top:3px;bottom:3px;border-radius:7px;transition:transform .25s var(--spring);z-index:0;pointer-events:none"></div>
</div>
```

```javascript
function updateTabIndicator(tab){
  const ind=document.getElementById('tabIndicator');
  const tabs=document.querySelectorAll('.tab');
  const idx=Array.from(tabs).indexOf(tab);
  const tabW=100/tabs.length;
  ind.style.transform=`translateX(${idx*100}%)`;
  ind.style.width=tabW+'%';
}
```

## 关键模式：数字滚动

```javascript
const targetEq=eq, targetEv=d.ev;
const dur=600, steps=20;
for(let i=0;i<=steps;i++){
  const t=i/steps;
  setTimeout(()=>{
    eqEl.textContent=Math.round(targetEq*t)+'%';
    const ev=targetEv*t;
    evEl.textContent=(ev>=0?'+':'')+ev.toFixed(2);
  }, t*dur);
}
```

20 帧 × 30ms 间隔 = 600ms 滚动。帧数不是关键（20 帧够平滑），关键是 `t*dur` 的 `setTimeout` 调度模拟匀速滚动。
