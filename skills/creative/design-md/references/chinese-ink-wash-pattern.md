# 中国水墨风格 DESIGN.md 示例 — VisePanda (熊猫行)

> **项目**: VisePanda — AI China Travel Planner
> **文件**: `~/projects/vise-panda-2/DESIGN.md` (完整 token spec)
> **线上**: https://go2china.space
> **效果**: 深色底 + 水墨山水背景 + 朱砂红印章Logo + 金色点缀

## 设计思路

结合中国传统水墨画（ink-wash painting）与现代暗色 UI，营造「东方意境 × 现代产品」的气质。

| 元素 | 来源 | 在 UI 中的角色 |
|------|------|----------------|
| 水墨山峦 | 国画 | 三层 SVG 轮廓作为背景，5px 模糊，0.008-0.016 透明度 |
| 圆月 | 中秋/山水画 | 右上角径向渐变辉光 `rgba(255,233,196,.04)` |
| 朱砂红 (#BC3A2C) | 印章/国画落款 | CTA、发送按钮、头像框、品牌标识 |
| 金色 (#C9A96E) | 皇家/庙宇装饰 | 中文副标题、hover 顶线、导航点缀 |
| 天蓝 (#7DD3FC) | 青花瓷/旅行 | 气泡、地图、链接（保留原有旅行感） |
| 印章 (seal) | 传统篆刻 | 方形红色边框微旋转 -2°，宋体「熊」字 |

## 色彩体系

```
主色:     #0E0B14  (深紫黑画布)
点缀红:  #BC3A2C  (朱砂 — 印章/CTA)
金色:    #C9A96E  (标题/导航)
天蓝:    #7DD3FC  (地图/气泡/链接)
底色:    #05070B  (最底层)
文字:    #EBEBED
暗文:    #8A8A9A
线框:    rgba(255,255,255,.07)
```

## 背景 SVG 生成方式

三层层叠山峦 SVG，用 `path` 绘制渐变透明轮廓：

```svg
<!-- 第1层 (远景, 透明度0.016) -->
<path d="M0 520 Q120 370 260 420 ... L1400 800 L0 800Z" fill="%23fff" opacity=".016"/>
<!-- 第2层 (中景, 0.012) -->
<path d="M0 580 Q180 440 320 490 ... L1400 800 L0 800Z" fill="%23fff" opacity=".012"/>
<!-- 第3层 (近景, 0.008) -->
<path d="M0 640 Q200 520 400 560 ... L1400 800 L0 800Z" fill="%23fff" opacity=".008"/>
<!-- 右上月亮 -->
<circle cx="1050" cy="140" r="48" fill="%23ffe9c4" opacity=".12"/>
```

CSS 中通过 `url('data:image/svg+xml,...')` 嵌入，配合 `filter: blur(5px)` 和 `opacity: .2` 实现朦胧感。

## 印章 Logo 实现

```html
<a href="/" class="logo-seal">
  <span class="seal">熊</span>
  <span class="name">VisePanda<span class="name-ch">熊猫行</span></span>
</a>
```

```css
.logo-seal .seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1.5px solid #BC3A2C;
  border-radius: 6px;
  background: linear-gradient(135deg, rgba(188,58,44,.08), rgba(188,58,44,.02));
  font-size: 14px;
  color: #BC3A2C;
  font-weight: 700;
  font-family: 'Songti SC', 'STSong', 'Georgia', serif;
  transform: rotate(-2deg);
}
```

## Token 特点（本模式与标准 DESIGN.md 的差异）

1. **CSS 用渐变背景** — `backgroundColor` 映射为 `linear-gradient(...)` 而非纯色
2. **透明度/模糊** — 标准 token 不支持 `opacity`/`blur`，需在 components 的描述文字中说明
3. **SVG 背景** — DESIGN.md 的 token 不直接描述背景 SVG 内容，需在 Overview 中以文字描述
4. **动画** — `hover` 状态的 `translateY`/`boxShadow` 写在 component 变体名称中（`card-hover`）

## 应用到现有项目的步骤

1. 读取现有前端文件（CSS/HTML）
2. 在项目根创建 `DESIGN.md`
3. 从 DESIGN.md 提取颜色/圆角/间距值，替换到 CSS 变量中
4. 调整组件样式（按钮、卡片、气泡）匹配 token
5. 添加背景 SVG 元素
6. 更新品牌标识（Logo）
7. 用 `npx @google/design.md lint DESIGN.md` 验证
8. 部署确认效果
