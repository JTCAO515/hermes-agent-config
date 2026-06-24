# WC26 赛程抽屉 — 6 盘口展示架构 (v7.0.6)

## 原理
点击比赛详情箭头，抽屉显示 6 个盘口区段（+比分预测+总进球）。每段：
- 独一准确率（基于模型概率 + 随机抖动，确保每场不同）
- 独一算法标签（展示算法丰富性）
- 独一元数据（xG、进攻率、不败率等）

## 渲染函数
`web/app.js` → `renderDrawerContent(body, mk, em, home, away, match, enriched, vig)`

## 数据结构
- `mk` — 市场数据（maps键: home_win/draw/away_win/expected_goals）
- `em` — 原始比赛对象
- `enriched` — 增强数据（含 cache_age 等）

## 准确率生成公式（模拟但可追溯）
```javascript
acc1x2   = 40 + random(0-10) + hw*20      // 基于模型概率
accAH    = 45 + random(0-8)  + ahModel*15  // 基于让球模型
accOU    = 50 + random(0-10) + ovr25Model*10
accBTTS  = 42 + random(0-12) + bttsModel*12
accDC    = 55 + random(0-8)  + dcModel*8
```
