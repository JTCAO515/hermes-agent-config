# 参考案例: VisePanda HANDOFF.md (v3.0.1)

> 完整文件见 `~/projects/vise-panda-2/HANDOFF.md`
> 当前实际版本已迭代到 v3.0.5，handoff 需从工作目录读取最新状态

## 结构示范

```
# [项目名称] v[版本号] — Handoff Document

> **Last Updated:** [日期]
> **Status:** ✅ 状态
> **Repo:** SSH地址
> **Live URL:** 生产环境地址
> **Agent Memory Key:** 记忆关键词

---

## 1. Product Overview
一句话产品描述 + 核心哲学 + 目标用户

## 2. Architecture
架构ASCII图 + 关键设计决策表（Decision | Choice | Why）

## 3. Current State
功能清单（按Phase/模块分组，✅/🔄标记）+ Known Quirks / Gotchas

## 4. File Structure
项目目录树 + 每个文件/目录的作用标注

## 5. API / Interface
所有API端点（Method | Endpoint | Description | Auth）

## 6. Key Config
环境变量表 + 部署配置

## 7. Core Logic / Data Flow
核心流程ASCII图

## 8. Frontend / UI Component Map
前端组件树

## 9. Dependencies
技术栈 + 版本

## 10. Next Steps
待办事项（Priority | Feature | Complexity | Notes）

## 11. Troubleshooting
常见问题（Problem | Cause | Fix）

## 12. References
相关文档链接
```

## 关键要点

1. **Section 3 Current State 必须包含 Known Quirks/Gotchas** — 这是手写handoff最有价值的部分，记录所有踩过的坑
2. **Section 4 File Structure 标注 "ACTIVE" vs "LEGACY"** — 避免误改旧文件
3. **Section 6 Key Config 不写敏感值** — 只写变量名和说明
4. **Section 10 Next Steps 用 🔴🟡🟢 标注优先级**
5. **版本号必须在文件名和 header 中保持一致**
