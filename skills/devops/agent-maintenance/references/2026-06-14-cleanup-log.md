# 2026-06-14 系统大扫除参考记录

## 执行概要

用户要求"给hermes agent做一次系统大扫除：记忆瘦身；工作流调序；memory断舍离"。

## Memory 变动

| 操作 | 原内容 | 原因 |
|------|--------|------|
| 🗑️ 删除 | Vercel Python handler 模式 (pydantic glibc 等) | 已有 skill vercel-python-deployment 覆盖 |
| 🗑️ 删除 | VisePanda v3.0.1 启动记录 | 项目已发布，无需每日记 |
| 🗑️ 删除 | DeepSeek V4 Flash 环境变量配置 | 已配好，不需要每天记 |
| 🗑️ 删除 | Vercel from China 网络问题 | 合并入项目迭代偏好条目 |
| 🔗 合并 | VisePanda/WC26 迭代偏好 + Vercel 网络 + VisePanda 配置 → 一条 | 同类信息合并 |

**结果**: 96% (11条) → 69% (7条), 释放605字符

## Profile 变动

| 操作 | 说明 |
|------|------|
| 🔗 合并 | 猪猪微身份+工作风格+GitHub+个人背景+项目列表 → 一条 |
| 🔗 合并 | 恋爱关系更新（已见5天→认识3个月） |
| 🗑️ 删除 | 代码修复后git push提醒（太基础） |
| 🗑️ 删除 | VisePanda迭代流程细节（已归Memory） |
| 🗑️ 删除 | 曹金涛个人信息（合入第一条） |
| 🗑️ 删除 | 工作风格独立条目（合入第一条） |

**结果**: 98% (12条) → 78% (8条), 精简23%

## Skills 审计发现

| Skill | 问题 | 修复 |
|-------|------|------|
| ljg-book | description为空, content是AI摘要"好的，这是根据您提供的…" | 已重写: 补description/triggers/tags, 删preamble |
| ljg-paper | description为空, content是AI摘要"好的，这是根据您提供的…" | 已重写: 同上 |
| impeccable | description为空 | 内容完整，只缺frontmatter description，标记但未修 |
| Machiavelli | description显示为"|" | YAML block indicator截断，不影响使用，标记 |