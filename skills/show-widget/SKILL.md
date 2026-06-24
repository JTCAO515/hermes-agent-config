---
name: show-widget
description: >
  可视化图表/组件生成：卡片、仪表盘、KPI面板、信息图。触发词：组件/卡片/widget/仪表盘/可视化/信息卡。
version: 1.0.0
---

# ShowWidget — 可视化组件

单文件 HTML 组件，可直接嵌入页面。

## 组件类型
- **stat-card**: 数字+标签+趋势箭头
- **progress-bar**: 进度条+百分比
- **comparison-card**: AB对比卡
- **timeline**: 时间线
- **pricing-card**: 定价卡
- **feature-grid**: 功能网格
- **review-card**: 评价卡(头像+星级+引述)
- **kpi-dashboard**: 4-KPI面板
- **chart-mini**: 迷你柱状/折线图(纯CSS)

## 生成规范
```html
<!-- 单组件 -->
<div class="widget stat-card">
  <div class="stat-value">€8,500</div>
  <div class="stat-label">人均预算</div>
  <div class="stat-trend up">↑12%</div>
</div>
```
所有组件带: dark/light 双模式 CSS 变量，可直接复用。
