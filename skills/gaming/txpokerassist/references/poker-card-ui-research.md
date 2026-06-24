# Poker Calculator Card Selection UI — 竞品调研 (2026-06)

## 市面主流产品选牌交互对比

| 产品 | 选牌方式 | 交互步骤 | 移动端 | 亮点 |
|------|----------|----------|--------|------|
| **Equilab** | 13×4 牌面网格（行=suit, 列=rank） | 点1次选1张 | ❌ 桌面 | 经典，最直觉 |
| **Flopzilla** | 13×13 起手牌矩阵（对角线=pair） | 点1次选组合 | ❌ 桌面 | 范围分析专用 |
| **OpenPokerTools** | 13×13 矩阵 + 具体牌弹窗 | 选组合→弹窗选花色 | ⚠️ 勉强 | 范围+具体牌双模式 |
| **Fast Poker Odds** (iOS) | 拖拽式（solitaire 风格） | 拖1次 | ✅ 移动优先 | 最少步骤 |
| **Odds Calculator for Poker** (iOS/Android) | 简洁点选网格 | 点1次 | ✅ 移动优先 | **最佳移动端** |
| **Enterra Poker Calculator** | 语音/拍照/点选 | 语音1次 | ✅ | 语音输入创新 |
| **PokerCruncher** | 牌面网格 + 手牌范围对角矩阵 | 点1次 | ✅ iOS/Android | 最强大，范围编辑器 |
| **SnapShove** | 快速选择起手牌（仅翻前全下） | 点1次 | ✅ | 极简场景专用 |
| **Poker Odds Camera** | 摄像头识别 + 点选 | 拍1次 | ✅ | OCR 创新 |

## 关键发现

### 最佳实践 = 13×4 牌面网格，点1次出1张牌
- Equilab、PokerCruncher、Odds Calculator 等顶级产品的**共同选择**
- 比 rank→suit 两步选牌少 50% 操作
- 手机上 13 列可接受（每格 ~28px，配合小字体 rank+mini-suit）

### 移动端特有优化
1. **即时计算（Instant Results）** — 加牌后自动重算，不需要点"计算"按钮
2. **快速起手牌预设** — AA/KK/AKs 等一键填入
3. **已选牌灰掉** — 防重复 + 视觉反馈
4. **拖拽模式**（Fast Poker Odds 独创）— 实现复杂，不推荐

### 不推荐方案
- ❌ 13×13 矩阵：范围分析专用，不适合具体牌选择
- ❌ rank→suit 两步：多一步操作，用户需记忆当前选了什么 rank
- ❌ 纯文本输入：作为主要交互太慢，但适合快速复制粘贴场景

## TXPokerAssist 方案

### 选定：13×4 牌面网格 + 快速起手牌预设

```
4行（♠♥♦♣）× 13列（A K Q J T 9 8 7 6 5 4 3 2）
每格显示 rank + 小花色符号
已选牌 → .used 类灰掉（opacity:0.2 + pointer-events:none）
```

### 交互流程
1. 点网格 → 1次选出1张牌
2. 智能分配：hero 先填2张 → 剩余进 board → 满7张提示
3. 点击已选小卡片 → 移除（带动画）
4. 起手牌预设：AA / KK / QQ / AKs / AKo 一键填入

### CSS 关键样式
```css
.card-grid{display:grid;grid-template-columns:repeat(13,1fr);gap:2px}
.card-cell{padding:5px 0;border-radius:4px;text-align:center;font-size:.68rem;font-weight:700}
.card-cell.used{opacity:0.2;pointer-events:none;text-decoration:line-through}
.card-cell.red{color:#ef5350}
.card-cell.black{color:var(--text)}
```

### 保留文本输入
文本输入框作为辅助，支持快速粘贴 "Ah Ks Qd Jh 2c" 格式。
