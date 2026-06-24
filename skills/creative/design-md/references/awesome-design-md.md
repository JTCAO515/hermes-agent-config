# awesome-design-md — 75 个品牌 DESIGN.md 文件集

> **本地路径**：`~/projects/awesome-design-md/`
> **源码**：https://github.com/VoltAgent/awesome-design-md (MIT, 83k+ stars)
> **在线浏览**：https://getdesign.md

## 是什么

由 VoltAgent 维护的 **DESIGN.md 文件集合**，每个文件提取自一个真实品牌的设计系统（Stripe、Linear、Vercel、Supabase 等）。扔进项目根目录，AI agent 就能按该品牌的视觉规范生成 UI。

## 仓库结构

```
~/projects/awesome-design-md/
├── design-md/              ← 75 个品牌目录
│   ├── stripe/DESIGN.md
│   ├── linear.app/DESIGN.md
│   ├── vercel/DESIGN.md
│   ├── supabase/DESIGN.md
│   ├── airbnb/DESIGN.md
│   ├── notion/DESIGN.md
│   ├── figma/DESIGN.md
│   ├── cursor/DESIGN.md
│   ├── claude/DESIGN.md
│   ├── apple/DESIGN.md
│   ├── tesla/DESIGN.md
│   └── ... 75 个
├── README.md
└── LICENSE (MIT)
```

## 如何与 design-md skill 配合使用

**场景 1：用户想快速给项目套一个成熟品牌的外观**
→ 从 `awesome-design-md/design-md/` 挑一个风格接近的，直接复制到项目根目录
→ 生成 UI 前用 `npx @google/design.md lint DESIGN.md` 验一下
→ 然后让 coding agent 按这个文件渲染

**场景 2：用户想创建自己的品牌 DESIGN.md**
→ 参考 awesome-design-md 中同类品牌的 token 结构
→ 参考 `templates/starter.md` 作为起点
→ 用 lint 验证通过

## 常用品牌速查

| 风格 | 推荐品牌 |
|------|----------|
| 深色极简 | linear.app、vercel、supabase |
| 深色科技 | cursor、raycast、sentry |
| 浅色编辑器 | notion、mintlify |
| 蓝色商务 | stripe、intercom |
| 旅行 | airbnb |
| 暗色金融 | revolut、mastercard |
| 橙色友好 | zapier、lovable |
| 紫色高端 | mistral.ai、linear.app |
