---
name: vp-codex
version: 1.0.0
description: |
  VP-Codex project family topology — VP-Codex-Web (AI-first China travel SPA) vs VP-Codex-APK (native Android port).
  My role: product QA, bug reporting, requirement refinement, prompt writing for Codex.
  NOT a coder for this project — Codex implements, I review and document.
triggers:
  - "VP-Codex"
  - "codex.go2china.space"
  - "VisePanda"
  - "AI-First"
  - "optimization report"
  - "bug report"
tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
mutating: true
---

# VP-Codex Project Family

## Role Boundary

For VP-Codex projects, **I do not write code.** My responsibilities:
- Review deployed site + codebase for bugs and UI/UX issues
- Write structured optimization/bug reports (push to GitHub via API)
- Refine user requirements into specs for Codex
- Review Codex's implementation and report what's fixed vs what remains
- Set up repo monitoring (silent watchdog crons)

Codex handles: all code changes, deployment, implementation.

## Project Topology

| Attribute | VP-Codex-Web | VP-Codex-APK |
|-----------|---------------|---------------|
| **Purpose** | AI-first China travel SPA (English-native) | Native Android port of VP-Codex-Web |
| **GitHub** | `JTCAO515/VP-Codex-Web` | `JTCAO515/VP-Codex-APK` |
| **Domain** | `codex.go2china.space` | — |
| **Stack** | Python WSGI (`api/index.py`) + vanilla JS (`web/`) | Android native (Kotlin) |
| **Version** | v6.x.x (AI-first since v6.1.0) | v1.x.x |
| **CSS file** | `web/app.css` (NOT style.css) | — |
| **Cache buster** | `v=YYYYMMDD-vXXX-<name>` (in `index.html` `<link>` and `<script>`) | — |

## My Workflow (QA/Bug Reporting Cycle)

### Phase 1 — Initial Review
1. Fetch live site: `curl -s --noproxy '*' "https://codex.go2china.space"`
2. Check `/api/health` for version number
3. Download current `web/app.js`, `web/app.css`, and HTML
4. Check GitHub for recent commits: GitHub API → `GET /repos/JTCAO515/VP-Codex-Web/commits`
5. Review for: JS errors, broken UI, responsiveness, edge cases

### Phase 2 — Report Writing
Report format:
```
# VP-Codex-Web 优化报告 vX.Y

## Bug 清单（按严重程度排序）
### 🔴 P0 — 功能缺陷
### 🟡 P1 — 逻辑缺陷
### 🔵 P2 — 代码质量

## UI/UX 问题
## 文档问题
## 优化优先级
```
- Always include: file path, line number, code snippet, fix suggestion
- Use severity levels: 🔴 P0 (blocking) / 🟡 P1 (core) / 🔵 P2 (nice to have)
- For bugs found in vN+1 (Codex's fix round): mark ✅ fixed or ❌ still present

### Phase 3 — Push to GitHub
When `git clone` is unavailable:
```bash
# Use GitHub API PUT contents endpoint
PAT="<from .git-credentials>"
python3 -c "
import json, base64
with open('/tmp/REPORT.md') as f:
    content = f.read()
print(json.dumps({
    'message': 'docs: add report name',
    'content': base64.b64encode(content.encode()).decode(),
    'branch': 'main'
}))
" | curl -s --noproxy '*' -X PUT \
  -H "Authorization: token $PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/JTCAO515/VP-Codex-Web/contents/docs/REPORT.md" \
  -d @-
```

### Phase 4 — Update Monitoring State
After pushing, update the watchdog state file so the cron doesn't re-notify:
```bash
echo "<new-sha>" > ~/.hermes/cron/states/state-JTCAO515-VP-Codex-Web.txt
```

## Monitoring

Silent watchdog cron (every 2h):
- **Script**: `~/.hermes/scripts/monitor-vp-codex-web.sh` (monitors BOTH VP-Codex-Web and VP-Codex-APK)
- **State files**: `~/.hermes/cron/states/state-JTCAO515-VP-Codex-*.txt`
- **Behavior**: silent when no changes; pushes WeChat notification when new commits detected
- **Cron job**: created via `cronjob tool` with `no_agent=True` (watchdog pattern)

## Reports Archive

| Report | Focus |
|--------|-------|
| `OPTIMIZATION_REPORT.md` | v1 Bug + UI/UX diagnosis |
| `docs/AI_FIRST_REDESIGN.md` | AI-first product spec |
| `docs/NEW_PLAN.md` | Implementation plan |
| `docs/OPTIMIZATION_REPORT_v2.md` | v2 Mobile/desktop responsive review |
| `docs/REVIEW_v611.md` | v6.1.1 version QA check |

## Known Issues (tracking)

### Unfixed (as of v6.1.1)
- `setView("dashboard")` still referenced — not blocking, Overview button works
- DESIGN.md describes dark Chinese ink-wash theme; actual CSS is light blue/orange — mismatch
- 1440px+ wide screen: Chat capped at 1120px — could be wider on ultrawide

### Fixed in v6.1.1
- SSE JSON parse without try/catch → ✅ `try{JSON.parse}catch{}`
- API no timeout → ✅ `AbortController` 15s
- City images no fallback → ✅ `|| great-wall.jpg` + `onerror`
- Chat input editable during streaming → ✅ `isStreaming` + `input.disabled`
- `100vh` → ✅ `100dvh`
- Error toast 3.2s → ✅ 5.6s
- No dark mode → ✅ `prefers-color-scheme: dark`
- Chat narrow on wide screens → ✅ 1440px+ breakpoint (1120px)
- Keyboard detection → ✅ `is-chat-composing` hides bottom nav

## Related Skills
- `vp-hermes` — Sister project family (VP-Hermes-Web/APK, different domain and workflow)
