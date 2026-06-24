## Consolidation Summary — Umbrella-Building Pass

### Clusters Processed (20)

| # | Cluster | Old Skills | Umbrella | Merge Type | Notes |
|---|---------|-----------|----------|-----------|-------|
| 1 | XCrawl | 5 | xcrawl | Patch existing | Same API key, auth, base URL; 4 operation-specific files absorbed as labeled sections |
| 2 | Understand | 7 | understand | Patch + refs | understand-chat/dashboard/diff/domain/explain/knowledge/onboard → references/ |
| 3 | Figma sub-utilities | 4 | figma-use | Patch + refs | figjam-mode, slides-mode, create-new-file, swiftui → references/ |
| 4 | KYC | 2 | kyc | New umbrella | kyc-doc-parse + kyc-rules = two-phase pipeline |
| 5 | XLSX | 1 | xlsx | Patch | xlsx-author absorbed as headless-mode section |
| 6 | Brain | 1 | brain-ops | Patch | brain-pdf absorbed as PDF-rendering section |
| 7 | Brainstorming | 5 | brainstorming | New umbrella | experiments-existing/new + ideas-existing/new + OKRs |
| 8 | Decision-Making | 4 | making-decisions | Patch + refs | WRAP framework umbrella; tripwires, reality-testing, disconfirming-evidence, pre-mortem, red-team → refs |
| 9 | Earnings | 3 | earnings-coverage | New umbrella | analysis + preview + preview-single |
| 10 | Deal Workflow | 5 | deal-workflow | New umbrella | screening + sourcing + tracker + dd-checklist + dd-meeting-prep |
| 11 | Market Analysis | 3 | market-analysis | New umbrella | segments + sizing + marketing-ideas |
| 12 | Strategic Analysis | 4 | strategic-analysis | New umbrella | SWOT + PESTLE + Five Forces + Growth Loops |
| 13 | GTM | 2 | go-to-market | New umbrella | gtm-motions + gtm-strategy |
| 14 | Competitive | 2 | competitive-analysis | Patch | battlecard + competitor-analysis absorbed |
| 15 | Customer Insight | 4 | customer-insight | New umbrella | journey-map + value-prop + value-prop-statements + ICP |
| 16 | Business Model | 2 | business-model | Patch | lean-canvas + startup-canvas absorbed |
| 17 | Assumptions & Prioritization | 4 | assumptions-prioritization | New umbrella | identify-assumptions-existing/new + prioritize-assumptions/features |
| 18 | User Stories & Research | 5 | user-stories | Patch + refs | personas + segmentation + stories + interview + job-stories |
| 19 | Book-to-Skill | 1 | book-to-skill | Patch | book-to-skill-converter absorbed as references/converter.md |
| 20 | Product Strategy | 2 | product-strategy | Patch + refs | product-name + product-vision absorbed as refs |
| 21 | LJG | 16 | ljg | New umbrella + refs | All 16 ljg-* cognitive tools → references/*.md |

### Key Decisions

- **FIGMA**: Kept `figma-generate-design`, `figma-generate-diagram`, `figma-generate-library`, `figma-code-connect` separate. These are complex workflow orchestrators that compose on top of `figma-use`, not sub-sections of it. Each has its own multi-phase process with user checkpoints that would make a combined skill unwieldy.
- **Vercel deployment** (vercel-python-deployment, vercel-vps-hybrid-deployment): Kept separate. One is pure-Vercel serverless Python deployment; the other is a hybrid static+VPS architecture. Different deployment problems.
- **Data analysis/show-widget**: Kept separate. data-analysis is CSV/Excel stats; show-widget is visualization widgets.
- **Product management**: Kept as-is. The existing product-management skill is already comprehensive (PRD, strategy, OKRs, roadmap).

### Structural Pattern Used

22 of 26 umbrella operations used the same pattern:
1. **Patch the existing (or create new) umbrella** SKILL.md with labeled A/B/C/D sections
2. **Copy sibling detail** into umbrella's `references/` directory
3. **Archive the sibling** to `~/.hermes/skills/.archive/`

The LJG cluster (16 skills) used a slightly different approach: a table-of-contents umbrella SKILL.md with all detailed content in `references/*.md`.
