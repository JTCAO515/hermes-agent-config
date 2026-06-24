# Categorization Keywords

Keyword-based classification buckets for skills. Each bucket has a list of
substrings that, when matched against `name + description`, classify the skill.

```
设计与前端     : design, figma, ui, ux, sketch, css, html, frontend, motion,
               animation, gsap, pixel, ascii, excalidraw, p5js, web-design,
               claude-design, drawio, architecture-diagram, baoyu, pretext

写作与内容     : writing, humanizer, article, editor, fragment, beat, shape,
               grammar, release-notes, internal-comms, book-mirror,
               research-paper, beautiful-article

金融与投资     : model, finance, bond, swap, option, equity, portfolio,
               lbo, dcf, merger, comps, accrual, recon, earnings, valuation,
               pitch, cim, deal, stock, futu, macro, rates, fx, carry,
               returns, irr, sector, audit-xls, clean-data, kyc

编程与开发     : tdd, test, debug, diagnose, codereview, python, typescript,
               git, github, pr, refactor, architect, prototype, coding,
               workflow, modulariz, backend, simplify, scaffold, review,
               triage, gh-fix

产品与商业     : product, prd, user-stories, feature, roadmap, north-star,
               metrics, analytics, cohort, pricing, gtm, competitive,
               business-model, monetiz, signal-detector, wwas

AI/ML         : llm, dspy, vllm, llama, unsloth, axolotl, fine-tun, rag,
               swarm, image-generation, qwen-voice, huggingface, outlines,
               obliteratus, audiocraft, comfyui, evaluating-llms

DevOps        : deploy, vercel, cloud, remote-desktop, pwa, android, xray,
               cron, webhook, sync, cloud-sync, pre-commit

前端框架      : vue, react, nuxt, vitepress, vite, pinia, vueuse, unocss,
               turborepo, pnpm, tsdown, vitest, slidev

工具集成      : notion, linear, airtable, obsidian, docx, xlsx, powerpoint,
               maps, spotify, himalaya, openhue, xurl, yuanbao, weread

搜索与研究    : search, arxiv, tavily, wiki, blogwatcher, perplexity,
               agent-reach, xcrawl

教练与沟通    : coach, qingsheng, relationship, hinge, sage, self-cognition,
               guided-interview, tong-jincheng

认知与学习    : structured-thinking, ljg, strategic-reading, teach,
               knowledge-extractor, zoom-out, planning

数据与可视化  : data-analysis, sql, show-widget, timeline, report
娱乐与游戏    : mahjong, poker, minecraft, pokemon, songwriting
法律与合规    : legal, contract, nda, privacy
项目文档      : handoff, changelog, release-notes, shipping-artifacts, standup
自检与系统    : brain-ops, soul-audit, testing, self-improvement, agent-maintenance
```

## Known Deduplications

| Keep | Drop/Alternative | Reason |
|------|-----------------|--------|
| `tdd` | `test-driven-development` | Same approach, tdd is shorter name |
| `planning` | `planning-with-files` | Same file-based planning approach |
| `hindsight` | `hindsight-architect/local/cloud/self-hosted/docs` | Hindsight umbrella covers all |
| `design-taste-frontend` | `frontend-design`, `ui-ux-pro-max` | Frontend design taste skill |
| `native-mcp` | `mcp-builder` | MCP is built-in Hermes feature |
| browser tools | `web-access`, `playwright`, `webapp-testing`, `screenshot` | Built-in Hermes browser |
| `adversarial-code-review-orchestrator` | `gitnexus-pr-swarm-review` | Multi-model code review |
| `coding-workflow` | `yeet` | Full shipping pipeline |
| `diagnose` | `systematic-debugging` | Both debugging, diagnose is more refined |
| `writing-great-skills` | `writing-skills` | Same purpose, great-skills has richer content |

## Scenario Combos

### 日常开发
`grill-with-docs → decision-mapping → planning → tdd/diagnose → review → verification-before-completion`

### 新项目启动
`design-taste-frontend → sketch → figma-generate-design → create-prd → to-issues → coding-workflow`

### 写作
`writing-fragments → writing-beats → writing-shape → humanizer/humanizer-zh → grammar-check`

### 金融建模
`deal-workflow → cim-builder/ic-memo → dcf-model/lbo-model → pitch-deck`

### 产品设计
`brainstorming → assumptions-prioritization → user-stories → create-prd → sprint-plan`

### CI 故障
`gh-fix-ci + diagnose`

### AI 微调
`dspy (prototype) → axolotl/unsloth (train) → evaluating-llms-harness (eval)`

### 数据分析
`data-analysis + sql-queries + show-widget`

### 前端设计
`design-taste-frontend → popular-web-designs → sketch → figma-design-system → code`

### 社交/关系
`self-cognition → qingsheng/relationship-coaching → hinge-profile-optimizer`
