# 参考案例：VisePanda AGENT_MEMORY.md — 面向其他AI的入职文档

> 完整文件见 `~/projects/VP-Hermes-Web/AGENT_MEMORY_VisePanda.md`

## 背景

用户在会话中说「你需要给别的ai agent写一个我的memory。注重在visepanda项目」。这不是写HANDOFF.md（项目状态快照），而是写一份**给其他AI Agent用的用户+项目入职指南**。

## 产出品结构示范

```markdown
# VisePanda 用户记忆 — 给其他 AI Agent

> 面向来华外国人的 AI 中国旅行规划平台
> 最后更新：2026-06-21

---

## 用户画像

- 非技术背景决策者（投资人/创始人），判断力在业务层
- 用业务语言提需求，不说技术术语
- 沟通节奏：我分析 → 给方案 → 他拍板 → 我执行
- 极简指令风格：说"继续"=不要问下一步直接做
- 遇到问题直接诊断+修复，不要只诊断不修复
- Git push后必须微信汇报

## 项目拓扑

### VP-Hermes-Web — SPA全栈版
| 项目 | 值 |
|------|-----|
| GitHub | github.com/JTCAO515/VP-Hermes-Web (HTTPS PAT, branch: main) |
| 在线地址 | https://www.go2china.space |
| 技术栈 | Vanilla JS SPA + Python WSGI (stdlib only) + DeepSeek V4 Flash |
| 核心功能 | AI聊天(SSE) / 36城知识库 / 行程规划器 / 登录 / 工具箱 / 管理后台 |
| i18n | English-native，中文专有名词括号标注 |

### VP-Hermes-APK — Android原生版
| 项目 | 值 |
|------|-----|
| GitHub | github.com/JTCAO515/VP-Hermes-APK (SSH, branch: master) |
| 在线地址 | https://hermesapp.go2china.space |
| 技术栈 | Android Jetpack Compose + FastAPI (Docker) + React Admin (Vercel) |
| APK编译 | Windows本地 gradlew.bat assembleDebug |

## 设计约定
- 界面语言：全部英文（专有名词括号标中文）
- 视觉风格：熊猫中国风，竹绿+金色，暗/亮双主题
- PM文档规约：PRD_PRODUCT_ANALYSIS.md + PLAN.md + README.md + HANDOFF.md

## 已知边界
- ESTIMATE_DATA只有7/36城有估价
- MAP_DATA POIs只覆盖8城
- Admin不能用Google OAuth

## 沟通模式
```
用户说 "做X"           → 直接做，不问"你确定吗"
用户说 "继续"          → 自动下一步
用户说 "为什么卡住了"  → [原因+修复方案]，不要长篇错误日志
用户说 "两个一起写"    → 并行执行
用户给GitHub链接       → 诊断+修复，不只诊断
用户给链接说"改成这个" → 直接改配置
```

*End of Agent Memory*
```

## 关键要点

1. **先读用户的memory** — 从User Profile里提取用户的背景、沟通风格、偏好。这些已经存在Hermes记忆里
2. **读HANDOFF.md** — 获取项目最新状态（架构、API、已知问题）
3. **项目拓扑分两类写** — 如果项目有多个子系统（Web/APK/Backend），分别列表
4. **沟通模式是核心价值** — 其他AI最需要知道的是"这个用户怎么和我对话"，而不是项目功能细节
5. **不要push到GitHub** — AGENT_MEMORY是AI之间的上下文文档，不是项目交付物