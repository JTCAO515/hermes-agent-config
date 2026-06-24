---
name: deploy-external-skills
version: 1.0.0
description: |
  Deploy external repos/projects/CLI tools as Hermes Agent skills.
  Covers all deployment strategies: ClawHub install, manual SKILL.md copy,
  multi-skill repo extraction, pip/npm wrapper creation, full-app differentiation.
  Repeated use case across many sessions — not a one-off.
triggers:
  - "部署这个"
  - "安装这个skill"
  - "怎么装这个项目"
  - "deploy this repo"
  - "install this skill"
  - "how to deploy"
  - "部署<repo>"
tools:
  - exec
  - read
  - write
  - web_extract
mutating: true
---

# Deploy External Skills to Hermes Agent

A systematic workflow for turning external GitHub repos, npm/pip packages, and CLI tools into Hermes-compatible skills.

## Contract

This skill guarantees that after following the workflow:
1. Every deployable skill from the target repo is installed to `~/.hermes/skills/<name>/`
2. The user knows which items were installed and which need additional setup (API keys, Docker, etc.)
3. Non-skill projects are clearly distinguished from skill-compatible repos
4. The install result is verified via `hermes skills list`

## Phase 0: Classify the Source

Before doing anything, determine what type of resource you're dealing with.

| Signal | Type | Strategy |
|--------|------|----------|
| Has `SKILL.md` with frontmatter (`name:`, `description:`) | **Native Hermes skill** | Install directly |
| Listed on ClawHub (`clawhub://<owner>/<repo>`) | **ClawHub skill** | `hermes install <owner>/<repo>` |
| Has `skills/` dirs with `SKILL.md` | **Multi-skill repo** | Bulk extract per-skill |
| Is on PyPI / npm | **CLI/lib** | Create wrapper skill |
| Has only `CLAUDE.md` / `.claude-plugin` | **Claude-only skill** | Convert to Hermes SKILL.md |
| Requires Docker / Docker Compose | **Full app** | Not a skill; check Docker, then deploy via `docker compose up -d` |
| Has `install.sh hermes` | **Hermes-aware** | Run the installer directly |
| Is a Tauri / desktop app (Rust+Webview) | **Desktop app** | Skip unless user insists |

## Phase 1: Strategy Selection

```
Strategy A — Single SKILL.md (ClawHub or native skill repo)
  └── hermes skills install <owner>/<repo>
  └── Or: web_extract raw SKILL.md → write to ~/.hermes/skills/<name>/SKILL.md

Strategy B — Multi-skill repo (many SKILL.md files in subdirs)
  └── git clone --depth 1 <repo-url>
  └── find . -name 'SKILL.md' -type f | while read f; do
        name=$(grep '^name: ' "$f" | head -1 | sed 's/name: //' | tr -d '[:space:]')
        [ -z "$name" ] && name=$(basename "$(dirname "$f")")
        mkdir -p ~/.hermes/skills/"$name"
        cp "$f" ~/.hermes/skills/"$name"/SKILL.md
      done

Strategy C — pip-installable Python library
  └── pip install <pkg>
  └── Create SKILL.md with usage examples as a reference wrapper
  └── File is NOT invocation-triggering; it's a "how to use this lib" document

Strategy D — npm/binary CLI tool
  └── Create SKILL.md documenting the CLI commands
  └── The skill teaches how to invoke the tool, not a replacement for it

Strategy E — Claude-only skill (CLAUDE.md, no SKILL.md)
  └── Check if SKILL.md exists in subdirs first
  └── If not, create a Hermes-compatible SKILL.md from the Claude instructions
  └── Keep the same content structure but add frontmatter
```

## Phase 2: Execute

### Strategy A: Single Skill Install

```bash
# If on ClawHub:
hermes skills install <owner>/<repo>
# If --force needed for DANGEROUS-rated:
hermes skills install <owner>/<repo> --force
```

#### Strategy A1: Root-level SKILL.md + supporting files (scripts/, docs/, references/)

Some repos have a root-level SKILL.md that references external files in `scripts/`, `docs/`, `references/`, or other subdirectories. These supporting files must be preserved for the skill to function.

```bash
git clone --depth 1 <repo-url> ~/projects/<repo-name>
SKILL_NAME=$(grep '^name: ' ~/projects/<repo-name>/SKILL.md | head -1 | sed 's/name: //' | tr -d '[:space:]')
mkdir -p ~/.hermes/skills/"$SKILL_NAME"
cp ~/projects/<repo-name>/SKILL.md ~/.hermes/skills/"$SKILL_NAME"/SKILL.md

# Copy all supporting directories referenced by the skill
for dir in scripts docs references templates; do
  [ -d ~/projects/<repo-name>/$dir ] && cp -r ~/projects/<repo-name>/$dir ~/.hermes/skills/"$SKILL_NAME"/
done
```

**Name conflict handling:** If `$SKILL_NAME` already exists in `~/.hermes/skills/`, rename to disambiguate:
- Append a suffix like `-converter`, `-tool`, `-cli`, or `-lite`
- Update `name:` in the copied SKILL.md to match the new folder name
- Log the rename to the user's memory

**Post-install dependency check:** For skill repos with scripts/, verify runtime dependencies:
```bash
# Check Python deps (if scripts/ contains .py files)
if ls ~/.hermes/skills/"$SKILL_NAME"/scripts/*.py 2>/dev/null; then
  grep -rE '^import |^from ' ~/.hermes/skills/"$SKILL_NAME"/scripts/*.py | \
    grep -vE 'os|sys|re|json|math|typing|pathlib|collections|dataclasses|itertools|functools' | \
    sort -u
fi

# Check system-level dependencies (pdftotext, pandoc, ffmpeg, etc.)
grep -ri 'apt install\|brew install\|choco install\|pip install' \
  ~/.hermes/skills/"$SKILL_NAME"/SKILL.md | head -10
```

Report any missing dependencies to the user with install commands.

**Example:** `virgiliojr94/book-to-skill` → installed as `book-to-skill-converter` (name conflict with apple-ouyang/book-to-skill), preserving scripts/ + docs/. Needs `sudo apt install poppler-utils` for PDF text extraction.

### Strategy B: Multi-Skill Bulk Extract

### Standard (git clone)

```bash
git clone --depth 1 <repo-url> ~/projects/<repo-name>
cd ~/projects/<repo-name>
find . -name 'SKILL.md' -type f | while read f; do
  name=$(grep '^name: ' "$f" | head -1 | sed 's/name: //' | tr -d '[:space:]')
  [ -z "$name" ] && name=$(basename "$(dirname "$f")")
  mkdir -p ~/.hermes/skills/"$name"
  cp "$f" ~/.hermes/skills/"$name"/SKILL.md
done
```

### For China Servers (blocked GitHub)

**Probe first: check which sites need proxy.** Not all external hosts are blocked.
```bash
for host in github.com raw.githubusercontent.com mcp.directory objects-us-east-1.dream.io docs.openclaw.ai; do
  code=$(curl -sL --max-time 10 -o /dev/null -w "%{http_code}" "https://$host" 2>/dev/null || echo "BLOCKED")
  echo "$host → $code"
done
```
Some hosts (mcp.directory, objects-us-east-1.dream.io, docs.openclaw.ai, skillsllm.com) work without proxy even when GitHub is blocked. Prefer no-proxy when it works — faster and more reliable.

**When proxy fails (SSL errors / exit 35 / timeouts):** Try the tarball approach next — routes through different CDN and may succeed. Fall back to web_extract on GitHub blob page.

**Python extraction when shell commands time out:** The terminal tool may consistently time out on pipe-heavy or archive commands (`tar`, `unzip`, multi-step `&&` chains). Use Python stdlib instead:
```python
import tarfile
t = tarfile.open('/tmp/repo.tar.gz')
t.extractall('/tmp/extract')
t.close()
import shutil, os
os.makedirs('/dest/dir', exist_ok=True)
shutil.copy2('/tmp/extract/file.md', '/dest/dir/file.md')
```
Use this whenever you see repeated `BLOCKED: Command timed out` on shell archive commands.

```bash
PROXY="http://127.0.0.1:10809"
BASE="https://raw.githubusercontent.com/<owner>/<repo>/main/skills"
SKILLS_DIR="/home/ubuntu/.hermes/skills"

for skill in name1 name2 name3; do
  curl -sL --max-time 20 -x "$PROXY" "$BASE/<category>/$skill/SKILL.md" > /tmp/$skill.md
  if [ -s /tmp/$skill.md ] && head -1 /tmp/$skill.md | grep -q "^---"; then
    mkdir -p "$SKILLS_DIR/$skill" && cp /tmp/$skill.md "$SKILLS_DIR/$skill/SKILL.md"
  fi
done
```

**Python-based extraction (when shell commands time out):** The terminal tool may consistently time out on commands with pipes, redirections, or archive extraction (`tar`, `unzip`). In these cases, use Python stdlib modules — they never fail for these operations:
```python
# Instead of 'tar xzf file.tar.gz -C dir'
import tarfile
t = tarfile.open('/tmp/repo.tar.gz')
t.extractall('/tmp/extract')
t.close()

# Instead of 'unzip file.zip -d dir'
import zipfile
z = zipfile.ZipFile('/tmp/file.zip')
z.extractall('/tmp/extract')
z.close()

# Instead of 'cp src dst'
import shutil, os
os.makedirs('dest_dir', exist_ok=True)
shutil.copy('src_file', 'dest_dir/file')
```
Use these when you see repeated `BLOCKED: Command timed out` on archive/pipe commands.

```bash
PROXY="http://127.0.0.1:10809"
BASE="https://raw.githubusercontent.com/<owner>/<repo>/main/skills"
SKILLS_DIR="/home/ubuntu/.hermes/skills"

for skill in name1 name2 name3; do
  curl -sL --max-time 20 -x "$PROXY" "$BASE/<category>/$skill/SKILL.md" > /tmp/$skill.md
  if [ -s /tmp/$skill.md ] && head -1 /tmp/$skill.md | grep -q "^---"; then
    mkdir -p "$SKILLS_DIR/$skill" && cp /tmp/$skill.md "$SKILLS_DIR/$skill/SKILL.md"
  fi
done
```

### Fallback: raw CDN 404

Some files exist on GitHub (visible via web UI) but return 404 from `raw.githubusercontent.com` — a known CDN cache issue that can last days. In this case:

**Method 1: web_extract + skill_manage (recommended)**
```
1. web_extract on the GitHub blob page for the SKILL.md
   URL pattern: https://github.com/<owner>/<repo>/blob/<branch>/path/to/SKILL.md
2. Extract the YAML frontmatter + body from the returned content
3. skill_manage(action="create", name="<skill-name>", content="<extracted>")
```
The blob page renders markdown content reliably, while raw CDN may cache stale 404s.

**Method 2: Repo tarball**
```bash
curl -sL -x $PROXY "https://github.com/<owner>/<repo>/archive/main.tar.gz" -o /tmp/repo.tar.gz
cd /tmp && tar xzf repo.tar.gz
find skills-main -name 'SKILL.md' | while read f; do
  name=$(grep '^name: ' "$f" | head -1 | sed 's/name: //' | tr -d '[:space:]')
  [ -z "$name" ] && name=$(basename "$(dirname "$f")")
  mkdir -p ~/.hermes/skills/"$name" && cp "$f" ~/.hermes/skills/"$name"/SKILL.md
done
```

**Method 3: GitHub API with PAT**
```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/contents/<path>/SKILL.md" | \
  python3 -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"
```

**Never assume a 404 from raw CDN means the file doesn't exist — always check the GitHub web UI first.**

### Strategy C: pip Wrapper

```bash
pip install <pkg>
# Then create SKILL.md with:
# - Installation verification
# - Core API usage examples
# - Configuration requirements
```

### Strategy D: CLI Wrapper

Create SKILL.md documenting:
- Binary/package name and source
- All subcommands with examples
- Configuration / environment variables
- Limitations

## Phase 3: Report to User

Always present a matrix showing:
- **What was installed** (skill names listed)
- **What needs their action** (API keys, Docker, config)
- **What was skipped and why**

Format:
```
| Project | Result | Need from you |
|---------|--------|---------------|
| foo     | ✅ 3 skills | — |
| bar     | ✅ installed | iFind API key |
| baz     | ⏭️ not a skill | Docker or skip |
```

## Phase 4: Verify

```bash
hermes skills list 2>&1 | grep <skill-name>
# Or check total count
hermes skills list 2>&1 | grep -c enabled
```

## Phase 5: Docker Deploy (for Full-Application Projects)

When the source is a full application (not a skill):

1. **Check Docker** — If not installed, see `references/docker-prerequisites.md`
2. **Clone or download** the project's `docker-compose.yml`
3. **Configure** — Set environment variables (API keys, encryption keys, ports)
4. **Deploy**:
   ```bash
   docker compose up -d
   docker compose logs -f    # Monitor startup
   ```
5. **Confirm** — Check the application is reachable on its configured port

**Pitfalls:**
- China network: always configure registry mirrors before pulling images
- Port conflicts: check `sudo lsof -i :<port>` before deploying
- Data persistence: verify volumes are properly mapped before `docker compose down`

## Phase 6: PM2 Deploy (for Node.js Full-Application Projects)

When the source is a Node.js application (not Docker-based, not a skill):

1. **Check Node.js** — `node --version` (needs >= 18)
2. **Clone** the repo to `~/projects/<name>/`
3. **Install deps** — `cd server && npm install` (or whichever subdir has package.json)
4. **Start with PM2**:
   ```bash
   cd ~/projects/<name>
   pm2 start server/index.js --name <service-name> --env PORT=<port>
   pm2 save
   ```
5. **Verify** — `pm2 list` shows `online` status. Test with `curl --noproxy '*' http://localhost:<port>/`
6. **Auto-restart on boot**:
   ```bash
   pm2 startup systemd -u ubuntu --hp /home/ubuntu
   sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u ubuntu --hp /home/ubuntu
   ```
   (PM2 dump already saved in step 4 → resurrect on reboot)

**Pitfalls:**
- The server may have a default port in code — override with `PORT=<port>` env var or `--env` flag
- PM2 fork mode is fine for single-instance apps; cluster mode (`-i max`) only when the app supports it
- Node 22+ is installed on this server via nvm or system package
- **PM2 working directory mismatch**: PM2 resolves script paths relative to the `cwd` where `pm2 start` was called. If you move the script to a different project directory and restart, PM2 will still look for it at the OLD path. Symptom: `can't open file '/old/dir/script.py'` in PM2 logs. Fix: `pm2 delete <name>` → `cd /actual/directory` → `pm2 start script.py --name <name>`. Always verify with `pm2 describe <name>` after restart.

## Anti-Patterns

- ❌ Trying `hermes skills install` on a repo that isn't registered on ClawHub (will 404)
- ❌ Installing full Docker projects as skills (they're apps, not skills)
- ❌ Assuming multi-skill repos have a single SKILL.md at root (they usually don't)
- ❌ Creating a skill that's just "run this tool" with no documentation — the skill should teach usage, not just be a pointer
- ❌ Forgetting to check Claude Code skills directory for actual SKILL.md files (they might use different structure)
- ❌ Using raw `curl` or `wget` to test localhost services when `http_proxy` env var is set — always use `--noproxy '*'` or `unset http_proxy` first
- ❌ Copying only `SKILL.md` from repos that have supporting directories (`scripts/`, `docs/`, `references/`, `templates/`) — these files contain runtime code, critical API docs, usage patterns, and gotchas. Always check for and copy supporting files.
- ❌ Ignoring name conflicts when two repos have the same `name:` frontmatter — deploy silently overwrites the existing skill. Check `~/.hermes/skills/` for collisions before copying.
- ❌ Skipping dependency verification after deploying tool-like skills — a skill with Python scripts is useless if its required libraries aren't installed. Run a quick import/exec check.
- ❌ Assuming `raw.githubusercontent.com` is always in sync with GitHub — CDN edge nodes frequently return 404 for valid files. Check the GitHub web UI before declaring a file missing, and always have a fallback plan (web_extract, tarball, API).
- ❌ Using serial `hermes skills install` for 20+ skill batches — each call is slow. Use batch curl or git clone for large repos.
- ❌ Using shell `tar`, `unzip`, or multi-step `&&` chains for archive extraction — these consistently time out with `BLOCKED: Command timed out` errors in this environment. Always use Python stdlib (`tarfile`, `zipfile`, `shutil`) for archive operations.
- ❌ Relying on `web_extract` to return the full raw content of a large SKILL.md file — web_extract LLM-summarizes pages over ~5000 chars, silently condensing rules and commands. For full raw content, use `raw.githubusercontent.com` via proxy curl, the GitHub blob page (which renders full markdown), or the GitHub API. Always verify that a summarized answer hasn't dropped critical instructions.

## References

See `references/multi-skill-extract.md` for detailed techniques on common multi-skill repos.
See `references/wrapper-creation.md` for templates on creating pip/npm/CLI wrapper skills.
See `references/figma-skill-deploy.md` for the specific pattern used for Figma official MCP skills (multi-skill repo with `references/` subdirectories).
See `references/mattpocock-skills.md` for the mattpocock/skills deployment reference (130k+ star repo, 22 skills, known raw CDN 404 issues).
