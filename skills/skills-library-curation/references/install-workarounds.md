# Hermes Skill Install Workarounds

## Problem

`hermes skills install <URL>` hangs indefinitely behind certain network configurations (proxies, Chinese firewall). The SKILL.md is fetched but the command never completes.

## Solution: Direct Download

```bash
mkdir -p ~/.hermes/skills/<skill-name>
curl -s --noproxy '*' "<raw-SKILL.md-url>" > ~/.hermes/skills/<skill-name>/SKILL.md
```

No registration needed — Hermes discovers skills by scanning `~/.hermes/skills/` at startup.

## Finding Skills

### Step 1: Search npx ecosystem
```bash
npx skills find "<query>"
```

Parse output for lines like:
```
<owner>/<repo>@<skill> <count> installs
└ https://skills.sh/<owner>/<repo>/<skill>
```

### Step 2: Derive GitHub raw URL
Common patterns:
- `owner/repo` → `https://raw.githubusercontent.com/<owner>/<repo>/main/SKILL.md`
- `owner/repo` with `skills/` subdir → `https://raw.githubusercontent.com/<owner>/<repo>/main/skills/<skill>/SKILL.md`

### Step 3: Test the URL
```bash
curl -s -o /dev/null -w "%{http_code}" --noproxy '*' "<url>"
```

### Step 4: Install
Use direct download method above.

## Known Working Sources

| Source | Raw URL Pattern | Skills |
|--------|----------------|--------|
| mattpocock/skills | `raw.githubusercontent.com/mattpocock/skills/main/skills/<category>/<name>/SKILL.md` | engineering, productivity, misc |
| op7418/humanizer-zh | `raw.githubusercontent.com/op7418/humanizer-zh/main/SKILL.md` | humanizer-zh |
| davila7/claude-code-templates | `raw.githubusercontent.com/davila7/claude-code-templates/main/cli-tool/components/skills/<category>/<skill>/SKILL.md` | gh-fix-ci, dev skills |
| anthropics/skills | `raw.githubusercontent.com/anthropics/skills/main/skills/<skill>/SKILL.md` | internal-comms |

## Verified Unavailable Skills (no public repo found)

Skills from npx ecosystem that are definitively NOT available as public GitHub repos.
These either only exist as npm packages or were never open-sourced:

| Skill | Status |
|-------|--------|
| `ui-ux-pro-max` | ❌ Not found |
| `hyperframes` | ❌ Not found |
| `motion-graphics` | ❌ Not found |
| `gsap-core` / `gsap-react` / `gsap-scrolltrigger` | ❌ Not found |
| `yeet` | ❌ Not found |
| `gitnexus-pr-swarm-review` | ❌ Not found |

## When Git Clone Fails: GitHub API Push Alternative

When you cannot clone/push to a GitHub repo (no disk space, network blocked, proxy issues),
use the GitHub REST API to create or update files directly.

**Prerequisites:** GitHub PAT stored in `~/.git-credentials` or environment.

**Check for PAT:**
```bash
cat ~/.git-credentials
# Format: https://<user>:<pat>@github.com
```

**Push a new file via API:**
```bash
PAT="ghp_..."  # from .git-credentials

python3 -c "
import json, base64
with open('/path/to/file.md') as f:
    content = f.read()
encoded = base64.b64encode(content.encode()).decode()
print(json.dumps({
    'message': 'docs: add report',
    'content': encoded,
    'branch': 'main'
}))
" | curl -s --noproxy '*' -X PUT \
  -H "Authorization: token $PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/<owner>/<repo>/contents/<path>" \
  -d @-
```

**Update an existing file:** Same API, but include the `sha` of the existing file.
Get the sha first:
```bash
curl -s --noproxy '*' -H "Authorization: token $PAT" \
  "https://api.github.com/repos/<owner>/<repo>/contents/<path>" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('sha',''))"
```

**Pitfalls:**
- `base64` on macOS: use `base64 -i` or `openssl base64` instead of `base64 -w0`
- PAT scope: the token needs `repo` scope for private repos, `public_repo` for public
- The API creates a commit directly — no local repo needed
- `--noproxy '*'` is critical behind proxies
