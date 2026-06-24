# Anthropic Financial Services Repo

**Repo**: `anthropics/financial-services`  
**Purpose**: Claude Cowork plugins + Claude Managed Agent templates for financial services (IB, equity research, PE, wealth management)  
**Fork target**: JTCAO515/financial-services (pending token)

## Structure

```
plugins/
  agent-plugins/             # 10 named agents — self-contained plugins each
    pitch-agent/
    meeting-prep-agent/
    market-researcher/
    earnings-reviewer/
    model-builder/
    valuation-reviewer/
    gl-reconciler/
    month-end-closer/
    statement-auditor/
    kyc-screener/
  vertical-plugins/          # FSI verticals — skill sources + commands + MCPs
    financial-analysis/      # Core: comps, DCF, LBO, 3-statement, Excel audit, ALL 11 connectors
    investment-banking/      # CIMs, teasers, process letters, merger models
    equity-research/         # Earnings notes, initiations, model updates
    private-equity/          # Sourcing, screening, diligence, IC memos
    wealth-management/       # Client reviews, financial plans, rebalancing
    fund-admin/              # GL recon, break tracing, NAV tie-out
    operations/              # KYC document parsing
  partner-built/             # LSEG, S&P Global plugins
managed-agent-cookbooks/     # CMA deploy cookbooks — one dir per agent (agent.yaml + subagents)
claude-for-msft-365-install/ # MS 365 admin tooling
scripts/                     # deploy-managed-agent.sh, check.py, validate.py, orchestrate.py, sync-agent-skills.py
```

## Key Files

- `CLAUDE.md` — canonical dev workflow (edit in vertical-plugins/, sync via sync-agent-skills.py)
- `.claude-plugin/plugin.json` — plugin metadata per agent/vertical
- `commands/*.md` — slash commands
- `scripts/check.py` — lints plugins before commit (hooks: pre-commit + CI)
- `marketplace.json` — top-level registry
- `managed-agent-cookbooks/<slug>/agent.yaml` — CMA deployment config

## Deployment Paths

1. **Claude Cowork plugin**: add marketplace URL → `https://github.com/anthropics/financial-services` in Cowork marketplace
2. **Claude Managed Agent**: use `managed-agent-cookbooks/<slug>/agent.yaml` → deploy via CMA API

## Forking Notes

- HTTPS clone works from this server (`git clone https://github.com/anthropics/financial-services.git`)
- SSH clone via config key (`vise_github`) works
- Need `GITHUB_TOKEN` or `gh auth` to fork via API (`POST /repos/anthropics/financial-services/forks`)
- Default `ssh -T git@github.com` may timeout if ~/.ssh/config specifies a non-default key
