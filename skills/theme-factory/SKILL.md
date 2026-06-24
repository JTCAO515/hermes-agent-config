---
name: theme-factory
description: >
  为 PPT/Word/网页/图表统一应用主题配色。触发词：主题/配色/换肤/风格统一/dark mode/品牌色。
version: 1.0.0
---

# 主题工厂

## 内置主题
| 主题 | 主色 | 辅色 | 适用 |
|------|------|------|------|
| ocean | #1a73e8 | #0d47a1 | 科技/金融 |
| forest | #2e7d32 | #1b5e20 | 环保/健康 |
| sunset | #e65100 | #bf360c | 创意/餐饮 |
| royal | #6a1b9a | #4a148c | 奢侈品/高端 |
| mono | #212121 | #757575 | 极简/商务 |

## 应用方式
- **网页**: CSS `:root` 变量注入
- **PPT**: `python-pptx` 主题色设置
- **Word**: `python-docx` 样式集修改
- **图表**: matplotlib `rcParams` 配色

## 自定义
用户提供 HEX 色值 → 自动生成完整调色板（50-900色阶）+ 对比度检查。
