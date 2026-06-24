---
name: web-design-review
description: >
  UI/UX 规范审查：可访问性、响应式、性能、设计一致性。触发词：设计审查/UI review/UX/可访问性/a11y。
version: 1.0.0
---

# Web 设计规范审查

## 审查清单
### 可访问性 (WCAG 2.1 AA)
- [ ] 色彩对比度 ≥ 4.5:1 (正文) / 3:1 (大字)
- [ ] 所有 img 有 alt
- [ ] 表单有 label
- [ ] 键盘可导航 (Tab/Enter/Esc)
- [ ] focus-visible 样式

### 响应式
- [ ] 320px / 768px / 1024px / 1440px 无横向滚动
- [ ] 触摸目标 ≥ 44x44px
- [ ] 图片使用 srcset/loading=lazy

### 性能
- [ ] LCP < 2.5s
- [ ] 字体使用 font-display: swap
- [ ] 关键 CSS 内联

### 设计一致性
- [ ] 颜色来自统一调色板
- [ ] 间距使用 4px 倍数
- [ ] 字体层级 ≤ 4 级
