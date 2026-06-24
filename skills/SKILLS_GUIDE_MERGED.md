# 🧭 Skills Guide — 猪猪微 Hermes

> 收录：382 skills（系统技能 v1 + 已安装 v379 + 新装 3）
> 更新：2026-06-22

---

## 一、新安装的技能

| 技能 | 来源 | 说明 |
|------|------|------|
| ✅ `humanizer-zh` | op7418/humanizer-zh | 中文文本去 AI 腔。修正夸张象征/三段式/AI词汇/连接性短语 |
| ✅ `gh-fix-ci` | davila7/claude-code-templates | GitHub Actions CI 故障诊断与修复 |
| ✅ `internal-comms` | anthropics/skills | 内部沟通文档模板（状态汇报/FAQ/事故通报） |

**未安装的剩余缺失技能及原因：**

| 缺失技能 | 原因 | 建议替代 |
|----------|------|----------|
| `ui-ux-pro-max` | 不存在于任何公开仓库 | `design-taste-frontend` + `web-design-review` |
| `hyperframes` | 同上 | `manim-video` / `p5js` |
| `motion-graphics` | 同上 | 需要时手动创建 |
| `gsap-core/react/scrolltrigger` | 同上 | 需要时手动创建 |
| `website-to-hyperframes` | 同上 | 浏览器工具直接操作 |
| `yeet` | 同上 | `coding-workflow` 全流程替代 |
| `gitnexus-pr-swarm-review` | 同上 | `adversarial-code-review-orchestrator` |
| `web-access` / `playwright` / `webapp-testing` | 已有浏览器工具 | browser tool 原生替代 |
| `screenshot` | 同上 | `terminal` 截图命令 |
| `hindsight-*` 细分 | `hindsight` 已装 | 覆盖全部功能 |
| `mcp-builder` | `native-mcp` 已装 | 覆盖全部功能 |
| `planning-with-files` | `planning` 已装 | 覆盖全部功能 |

---

## 二、分类目录（去重后）

### 🎨 设计与前端（22）
| 技能 | 用途 | 去重说明 |
|------|------|----------|
| `design-taste-frontend` | 反模版/高品味前端设计 | 替代 `frontend-design` |
| `claude-design` | 高保真 HTML 原型 |  |
| `web-design-engineer` | 精美浏览器可交付 |  |
| `web-design-review` | UI/UX 规范审查 | 替代 `ui-ux-pro-max` |
| `web-design-guidelines` | 设计准则参考 |  |
| `sketch` | 一次性 HTML mockup（多方案对比） |  |
| `architecture-diagram` | 暗色 SVG 架构图（HTML） |  |
| `excalidraw` | 手绘风格图表 Excalidraw JSON | 替代 `drawio-skill` |
| `drawio-skill` | drawio 图表文件 |  |
| `p5js` | p5.js 生成艺术/3D | 替代 `hyperframes` |
| `pixel-art` | 像素画（NES/GameBoy/PICO-8） |  |
| `ascii-art` | pyfiglet/cowsay ASCI 艺术 |  |
| `ascii-video` | 视频→彩色 ASCII MP4/GIF |  |
| `popular-web-designs` | 54 个真实设计系统（Stripe/Linear） |  |
| `pretext` | @chenglou/pretext 浏览器 demo |  |
| `baoyu-comic` | 知识漫画（信息图风格） |  |
| `baoyu-infographic` | 信息图：21 布局×21 风格 |  |
| `show-widget` | 可视化卡片/仪表盘/KPI |  |
| `theme-factory` | PPT/Word/网页统一主题配色 |  |
| `manim-video` | 3Blue1Brown 风格教学动画 |  |
| `figma-*`（5 skills） | Figma 设计系统/生成/代码连接 |  |
| `touchdesigner-mcp` | TouchDesigner MCP 控制 |  |

### ✍️ 写作与内容（16）
| 技能 | 用途 | 去重说明 |
|------|------|----------|
| `humanizer` | 英文文本去 AI 腔 |  |
| `humanizer-zh` | ⭐中文文本去 AI 腔 | 新装 |
| `internal-comms` | ⭐内部沟通模板（状态/FAQ/事故） | 新装 |
| `writing-plans` | 实施计划书写 |  |
| `writing-beats` | 文章节奏编排（choose-your-own-adventure） |  |
| `writing-fragments` | 碎片→结构化写作 |  |
| `writing-shape` | Markdown 整型（段落级打磨） |  |
| `writing-great-skills` | Skills 写作规范 |  |
| `writing-skills` | Skills 写作指南 | 重复？可与 writing-great-skills 合并 |
| `writing-guidelines` | 通用写作指南 |  |
| `grammar-check` | 语法/逻辑/流畅性检查 |  |
| `book-mirror` | 书→个性化章节摘要 |  |
| `release-notes` | 用户面向的发版说明 |  |
| `youtube-content` | YouTube 字幕→摘要/推文/博客 |  |
| `research-paper-writing` | 论文写作辅助 |  |
| `beautiful-article` | 文章排版美化 |  |

### 💰 金融与投资（48）
- **财务模型：** `3-statement-model` / `dcf-model` / `lbo-model` / `merger-model`
- **可比分析：** `comps-analysis` / `fsi-strip-profile` / `tear-sheet`
- **研究报告：** `equity-research` / `initiating-coverage` / `earnings-coverage`
- **交易文档：** `cim-builder` / `ic-memo` / `pitch-deck` / `deal-workflow` / `teaser` / `process-letter` / `buyer-list`
- **交易分析：** `returns-analysis` (IRR/MOIC) / `unit-economics` / `value-creation-plan`
- **资产配置：** `portfolio-monitoring` / `portfolio-rebalance` / `thesis-tracker` / `tax-loss-harvesting`
- **固定收益：** `bond-relative-value` / `bond-futures-basis` / `fixed-income-portfolio` / `swap-curve-strategy`
- **衍生品：** `option-vol-analysis` / `fx-carry-trade`
- **月结/对账：** `accrual-schedule` / `gl-recon` / `break-trace` / `roll-forward` / `nav-tieout` / `variance-commentary`
- **模型维护：** `model-update` / `audit-xls` / `clean-data-xls` / `deck-refresh`
- **数据工具：** `futuapi`（富途） / `westock-data`（腾讯自选股） / `stock-tracker` / `football-odds`
- **宏观：** `macro-rates-monitor` / `catalyst-calendar` / `news-briefing` / `briefing` / `morning-note`
- **风控/合规：** `kyc` / `draft-nda` / `privacy-policy` / `contract-review` / `financial-plan`

### 🔧 软件开发（36）
- **工作流：** `coding-workflow`（全流程） / `subagent-driven-development` / `tdd` / `test-driven-development`
- **调试：** `diagnose`（6阶段） / `systematic-debugging`（4阶段） / `python-debugpy` / `node-inspect-debugger` / `gh-fix-ci` → ⭐新装
- **代码审查：** `requesting-code-review` / `receiving-code-review` / `adversarial-code-review-orchestrator` / `review`
- **架构：** `improve-codebase-architecture` / `backend-modularization` / `intended-vs-implemented`
- **Git/GitHub：** `github-auth` / `github-issues` / `github-pr-workflow` / `github-code-review` / `github-repo-management` / `git-guardrails-claude-code` / `using-git-worktrees`
- **原型：** `prototype` / `spike` / `sketch`
- **执行：** `executing-plans` / `verification-before-completion` / `using-superpowers` / `finishing-a-development-branch`
- **平台：** `claude-code` / `codex` / `opencode` / `deepseek-tui`
- **其他：** `app-i18n` / `migrate-to-shoehorn` / `simplify-code` / `scaffold-exercises`

### 🤖 AI/ML（16）
- **推理：** `llama-cpp` / `serving-llms-vllm` / `outlines`（结构化输出）
- **微调：** `axolotl` / `unsloth` / `fine-tuning-with-trl`
- **评估：** `evaluating-llms-harness` / `cross-modal-review`
- **框架：** `dspy` / `swarm` / `raganything`（RAG） / `self-improvement`
- **语音/图像：** `qwen-voice` / `audiocraft-audio-generation` / `segment-anything-model` / `obliteratus`
- **工具链：** `huggingface-hub` / `weights-and-biases` / `rtk-token-killer`

### 🚀 产品与商业（20）
- **战略：** `product-strategy` / `market-analysis` / `competitive-analysis` / `ansoff-matrix` / `go-to-market` / `business-model`
- **定价：** `pricing-strategy` / `monetization-strategy` / `unit-economics`
- **需求：** `user-stories` / `analyze-feature-requests` / `prioritization-frameworks` / `wwas` / `create-prd` / `to-prd` / `to-issues`
- **指标：** `north-star-metric` / `metrics-dashboard` / `cohort-analysis` / `sentiment-analysis` / `signal-detector`
- **规划：** `brainstorming` / `decision-mapping` / `making-decisions` / `outcome-roadmap` / `product-management` / `sprint-plan`

### ⚡ 前端框架（15）
- **Vue 全家桶：** `vue` / `vue-best-practices` / `vue-router-best-practices` / `vue-testing-best-practices` / `vueuse-functions` / `nuxt` / `vitepress` / `pinia`
- **React/Vite：** `vite` / `vercel-react-best-practices` / `vercel-react-view-transitions` / `vercel-react-native-skills`
- **工具链：** `unocss` / `turborepo` / `pnpm` / `tsdown` / `vitest` / `slidev`

### ☁️ DevOps 与部署（14）
- **Vercel：** `vercel-python-deployment` / `vercel-vps-hybrid-deployment` / `deploy-to-vercel` / `vercel-cli-with-tokens`
- **远程/VPS：** `remote-desktop`（Xvfb+noVNC） / `xray-smart-routing`（智能分流）
- **移动端：** `pwa-android-deployment`（PWA→APK/AAB）
- **备份/同步：** `cloud-sync`（rclone） / `webhook-subscriptions`
- **维护：** `agent-maintenance`（记忆瘦身） / `hermes-migration`（配置迁移） / `setup-pre-commit`
- **其他：** `deploy-external-skills` / `cron-scheduler`

### 🗂️ 工具与集成（14）
- **设计协作：** `figma-*`（5 skills）
- **项目管理：** `notion` / `linear` / `airtable`
- **办公套件：** `docx` / `xlsx` / `powerpoint` / `pptx-author` / `nano-pdf`
- **通讯/娱乐：** `himalaya`（邮件） / `spotify` / `xurl`（推特） / `openhue`（灯光）
- **地图/位置：** `maps` / `travel-planner`

### 🔍 搜索与研究（10）
| 技能 | 用途 | 去重说明 |
|------|------|----------|
| `tavily-search` | AI 优化搜索（主要搜索后端） | 与 `web_search` 互补 |
| `web-tools-guide` | 搜索工具使用指南 |  |
| `xcrawl` | 网络数据抓取 | 与 `data-research` 互补 |
| `data-research` | 结构化数据调研 |  |
| `document-grounded-research` | 文档驱动的调研（先读后搜） |  |
| `arxiv` | 学术论文搜索 |  |
| `wiki-search` | 百度百科/Wikipedia |  |
| `blogwatcher` | RSS/Atom 博客监控 |  |
| `agent-reach` | 全平台搜索（Twitter/Reddit/小红书/抖音等） |  |
| `polymarket` | 预测市场查询 |  |

### 💬 教练与沟通（8）
- **恋爱教练：** `qingsheng`（全流程） / `relationship-coaching`（异地恋/暧昧）
- **沟通训练：** `communication-coach` / `humanizer`（去AI腔）
- **人生教练：** `sage-coach-career` / `sage-coach-crisis` / `sage-coach-spiritual` / `sage-coach-startup`
- **社交洞察：** `tong-jincheng-perspective`（童锦程视角） / `hinge-profile-optimizer`（Hinge资料优化）
- **自我认知：** `self-cognition` / `guided-interview`

### 🧠 认知与学习（8）
- `structured-thinking`（答题前结构化分析）
- `ljg`（16 认知工具方法论）
- `strategic-reading` / `zoom-out` / `teach`
- `knowledge-extractor`（文档/会议→结构化知识）
- `grill-me` / `grilling`（压力面试式方案打磨）
- `grill-with-docs`（含领域建模的压力面试）

### 📊 数据分析（4）
- `data-analysis`（CSV/Excel 统计透视可视化）
- `sql-queries`（自然语言→SQL）
- `dummy-dataset`（模拟数据集生成）
- `jupyter-live-kernel`（交互式 Jupyter 环境）

### 🎮 娱乐（5）
- `mahjong-engine`（国标麻将决策引擎）
- `txpokerassist`（德州扑克数学辅助）
- `minecraft-modpack-server`（MC 模组服务器）
- `pokemon-player`（宝可梦模拟器）
- `songwriting-and-ai-music`（AI 音乐+Suno 提示词）

### 📋 项目文档（6）
- `handoff`（项目交接文档）
- `shipping-artifacts`（AI 项目的持久文档集）
- `project-iteration`（迭代管理框架）
- `release-notes`
- `changelog`（位于 WC26 等项目中）
- `standup` / `weekly-digests` / `timeline-report`

### ♻️ 记忆与系统（6）
- `brain-ops`（知识库读写循环）
- `enrich`（Brain 页面分层增强）
- `maintain`（知识库健康检查）
- `query`（三层提问→知识检索）
- `soul-audit`（6阶段人格生成面试）
- `testing`（技能验证框架）

---

## 三、去重说明

以下技能功能重叠，**每次只用一个即可：**

| 保留 | 去重（替代或合并） |
|------|-------------------|
| `planning` | ~~`planning-with-files`~~（同一套东西） |
| `hindsight` | ~~`hindsight-architect/local/cloud/self-hosted/docs`~~（合并为一个） |
| `design-taste-frontend` | ~~`frontend-design`、`ui-ux-pro-max`~~（未安装） |
| `tdd` | ~~`test-driven-development`~~（同一套 RED-GREEN-REFACTOR，分别保留但推荐用 `tdd`） |
| `native-mcp` | ~~`mcp-builder`~~ |
| `browser tools` | ~~`web-access`、`playwright`、`webapp-testing`、`screenshot`~~ |
| `adversarial-code-review-orchestrator` | ~~`gitnexus-pr-swarm-review`~~ |
| `coding-workflow` | ~~`yeet`~~（全流程 ship） |
| `excalidraw` / `drawio-skill` | 两者不同格式，按需用 |
| `writing-skills` | 与 `writing-great-skills` 高度重复，建议保留后者 |

---

## 四、使用场景搭配

### 🧑‍💻 日常开发
```
grill-with-docs → decision-mapping → planning → tdd/diagnose → review → verification-before-completion
```

### 📦 新项目启动
```
design-taste-frontend → sketch → figma-generate-design → create-prd → to-issues → coding-workflow
```

### 🔒 CI 故障
```
gh-fix-ci + diagnose
```

### 📝 写作
```
writing-fragments → writing-beats → writing-shape → humanizer/humanizer-zh → grammar-check
```

### 📊 数据分析
```
data-analysis + sql-queries + show-widget
```

### 💰 投行/投资
```
deal-workflow → cim-builder/ic-memo → dcf-model/lbo-model → pitch-deck
```

### 🚀 产品设计
```
brainstorming → assumptions-prioritization → user-stories → create-prd → sprint-plan
```

### 🎨 前端设计
```
design-taste-frontend → popular-web-designs → sketch/mockup → figma-design-system → code
```

### 🤖 AI 微调
```
dspy (prototype) → axolotl/unsloth (train) → evaluating-llms-harness (eval)
```

### 💬 社交/关系
```
self-cognition → qingsheng/relationship-coaching → hinge-profile-optimizer
```

---

*参考：原 SKILLS_GUIDE.md（npx skills 生态）+ Hermes 当前 382 skills*
