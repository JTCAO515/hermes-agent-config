---
name: github-auth
description: "GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
    related_skills: [github-pr-workflow, github-code-review, github-issues, github-repo-management]
---

# GitHub Authentication Setup

This skill sets up authentication so the agent can work with GitHub repositories, PRs, issues, and CI. It covers two paths:

- **`git` (always available)** — uses HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

## Detection Flow

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. If `gh auth status` shows authenticated → you're good, use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method below
3. If `gh` is not installed → use "git-only" method below (no sudo needed)

---

## Method 1: Git-Only Authentication (No gh, No sudo)

This works on any machine with `git` installed. No root access needed.

### Option A: HTTPS with Personal Access Token (Recommended)

This is the most portable method — works everywhere, no SSH config needed.

**Step 1: Create a personal access token**

Tell the user to go to: **https://github.com/settings/tokens**

- Click "Generate new token (classic)"
- Give it a name like "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (if working with organization repos)
- Set expiration (90 days is a good default)
- Copy the token — it won't be shown again

**Step 2: Configure git to store the token**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

After entering credentials once, they're saved and reused for all future operations.

**Alternative: cache helper (credentials expire from memory)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Alternative: set the token directly in the remote URL (per-repo)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Step 3: Configure git identity**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Step 4: Verify**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### China Server Workaround

When running on a server located in mainland China, **HTTPS (port 443) to GitHub is blocked at the firewall level**. This means:

- `git clone https://github.com/...` → **will fail** (TCP timeout, not TLS error)
- `GIT_SSL_NO_VERIFY=1` → **will NOT help** (blocked before TLS handshake)
- `git clone git@github.com:...` on port 22 → **works fine**

**Rule: from China-based servers, always use SSH for GitHub operations.** If SSH is not yet configured, generate a key and have the user add it to GitHub before any git operations.

---

## Option B: SSH Key Authentication

Good for users who prefer SSH or already have keys set up.

**Step 1: Check for existing SSH keys**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Step 2: Generate a key if needed**

```bash
# Default key (shared across all repos)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# OR: Dedicated key per project (recommended for multi-project servers)
ssh-keygen -t ed25519 -C "project-name-deploy" -f ~/.ssh/project_name -N ""
```

**When to use a dedicated key:** If the server hosts multiple projects with different GitHub repos, use a per-project key (`~/.ssh/my_project`) rather than the default `~/.ssh/id_ed25519`. This gives per-key access control — revoke one project's key without affecting others.

Display the public key:
```bash
cat ~/.ssh/id_ed25519.pub
# or for dedicated key:
cat ~/.ssh/project_name.pub
```

Tell the user to add the public key at: **https://github.com/settings/keys**
- Click "New SSH key"
- Paste the public key content
- Give it a title like "hermes-agent-<machine-name>"

**Step 3: Test the connection**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Step 4: Configure git to use SSH for GitHub**

Two approaches — pick one:

**Approach A: `~/.ssh/config` Host block (recommended for per-project keys)**

```bash
cat >> ~/.ssh/config << 'EOF'

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/my_project_key
    StrictHostKeyChecking accept-new
EOF
```

Then set the remote to SSH:
```bash
git remote set-url origin git@github.com:owner/repo.git
```

Verification:
```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Approach B: Global URL rewrite (simpler, but rewrites ALL repos)**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

Approach A is better when you have multiple projects with different SSH keys — each project's `~/.ssh/config` Host block can specify a different `IdentityFile`. Approach B is simpler for single-project setups.

**Step 5: Configure git identity**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Method 2: gh CLI Authentication

If `gh` is installed, it handles both API access and git credentials in one step.

### Interactive Browser Login (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### Verify

```bash
gh auth status
```

---

## Using the GitHub API Without gh

When `gh` is not available, you can still access the full GitHub API using `curl` with a personal access token. This is how the other GitHub skills implement their fallbacks.

### Setting the Token for API Calls

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Extracting the Token from Git Credentials

If git credentials are already configured (via credential.helper store), the token can be extracted:

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Helper: Detect Auth Method

Use this pattern at the start of any GitHub workflow:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

---

## User-Specific Auth Preferences

For user **猪猪微 / JTCAO515**:
- **Preferred method: PAT Classic via HTTPS** — the user explicitly requires all GitHub operations use a Personal Access Token (Classic). Do NOT default to SSH for this user.
- **PAT setup**: The token is exported as `GH_TOKEN` in `~/.bashrc` and available in the session environment. Fallback: embed directly in git remote URLs as `https://JTCAO515:PAT@github.com/OWNER/REPO.git`.
- **Avoid `gh` CLI**: `gh` has TLS handshake timeout issues on this server. If you must use `gh`, always verify with `gh auth status` first. Prefer direct `git` + `curl` with the PAT.

### PAT Auth Quick Setup

```bash
# Option A: Export as env var (preferred — already in ~/.bashrc)
# Already sourced on new login shells. In current session, use:
export GH_TOKEN="<the-token>"

# Option B: Embed in git remote URL (works immediately, no env needed)
git remote set-url origin https://JTCAO515:<PAT>@github.com/OWNER/REPO.git

# Option C: Create repo via API with PAT
curl -s -X POST -H "Authorization: token $GH_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"REPO_NAME","private":false}'
```

### gh CLI TLS Timeout Workaround

On some servers (common with China-based hosts), `gh` fails with `TLS handshake timeout`. Symptoms:
```
gh repo create → "net/http: TLS handshake timeout" (not DNS or connectivity — DNS resolves fine)
```

**Do NOT** spend time debugging `gh` connectivity. Immediately switch to:
1. **Create repo**: Use `curl` with `GH_TOKEN` and GitHub REST API
2. **Push code**: Use `git` with token-embedded remote URL:
   ```bash
   git remote set-url origin https://USERNAME:PAT@github.com/OWNER/REPO.git
   ```
3. **API calls**: Use `curl -H "Authorization: token $GH_TOKEN"` instead of `gh api`

The root cause is likely an incompatible TLS library between the OS and `gh`'s Go runtime — not fixable without upgrading the OS or rebuilding `gh` from source.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |
| `GnuTLS recv error (-110): The TLS connection was non-properly terminated` | TLS handshake failure, common from China servers to GitHub. Workaround: `GIT_SSL_NO_VERIFY=1 git push <url>` or use SSH instead. Note: SSL verification is skipped — only use with trusted repos. |
| `Failed to connect to github.com port 443 after ... ms: Couldn't connect to server` | **China firewall blocking GitHub HTTPS.** This is different from the TLS error above — the connection itself is blocked at the TCP level. HTTPS (port 443) will NEVER work, even with `GIT_SSL_NO_VERIFY`. **Solution: always use SSH (port 22) from China-based servers.** See "China Server Workaround" section below. |
| `Permission denied (publickey)` with SSH | (1) Verify key was added to GitHub: open https://github.com/settings/keys. (2) Check `ssh -i <key_path> -T git@github.com`. (3) If using multiple keys, ensure `~/.ssh/config` points to the correct `IdentityFile`. |
