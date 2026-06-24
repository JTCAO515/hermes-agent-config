# Seedream App Icon Prompts（已验证有效）

> 本会话中生成的两个 App 图标 Prompt，Seedream 5.0 均成功产出可用图标。

## WC26 — 足球 + 金钱（体育金融）

```text
Mobile app icon for a World Cup 2026 prediction platform. Square 1:1 format. Clean composition: a golden football/soccer ball integrated with a dollar currency symbol $, surrounded by subtle glowing circuit board traces and data graph lines. Dark background (#08090a), neon accent colors (cyan #5e6ad2 and gold). Professional fintech sports style. Vector-quality flat design. No text. High contrast, suitable for app launcher icon.
```

**VLM 评价：** 中心金色立体足球 + 嵌入美元符号，外围青蓝科技行情折线环绕，深色背景居中构图。

## VisePanda — 熊猫 + 指南针（AI旅行）

```text
Mobile app icon for an AI China travel planner. Square 1:1 format. A cute panda face integrated with a compass or map pin, glowing cyan and purple neon tech lines, dark navy background (#0e0b14), clean flat vector style, professional travel tech app icon. No text. High contrast, suitable for Android launcher icon.
```

## Prompt 结构解析

| 部分 | 内容 | 作用 |
|------|------|------|
| 项目类型 | "Mobile app icon for [项目]." | 定义用途 |
| 格式 | "Square 1:1 format." | Seedream 默认可能不是 1:1 |
| 主体 | "a cute panda face integrated with..." | 精确语义关系（integrated with 比 "and" 更佳） |
| 背景 | "Dark background (#HEX)" | 指定品牌色 |
| 风格 | "professional fintech style", "high contrast" | 控制输出品质 |
| 约束 | "No text." | 避免文字被裁剪 |
| 用途 | "suitable for app launcher icon." | 引导输出适合图标裁剪 |

## 关键技巧

1. **指定品牌色 HEX** — Seedream 能理解十六进制颜色代码
2. **`integrated with` 比 `and` 好** — 语义更精确，元素融合更强
3. **`No text` 必须加** — 否则 Seedream 会在图标上写字（中文可能乱码）
4. **`app launcher icon` 引导裁剪** — 确保主体居中、留白足够
5. **用 VLM 检查结果** — 生图后用 Doubao-Seed-2.0-Lite VLM 确认布局和风格
