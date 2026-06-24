# GitHub Repo Watchdog — no_agent=True Cron Pattern

> Reusable pattern for monitoring GitHub repos for new commits and reporting via cron delivery.

## Overview

A **no_agent=True** (classic watchdog) cron job that:
1. Periodically polls the GitHub Commits API
2. Compares the latest SHA against a persisted state file
3. If new commits found: reports commit messages + file-level change detail + version info
4. If no changes: stays silent (watchdog pattern)

## Architecture

```
cron (every 2h)
  └── monitor-{repo}.py (no_agent=True)
        ├── Fetches: GitHub Commits API (per_page=10)
        ├── Reads:   State file (~/.hermes/cron/states/state-{owner}-{repo}.txt)
        ├── Fetches: Version source (CHANGELOG.md / build.gradle / package.json)
        ├── Fetches: Commit detail API for each new commit (files changed, +N/-N)
        ├── Writes:  Updated SHA to state file
        └── Output:  Only on change → delivered as cron message
```

## Script Template

```python
#!/usr/bin/env python3
"""
{label} — GitHub repo watchdog.
Monitors {owner}/{repo} for new commits on the {branch} branch.
Silent if no changes, reports on new commits.
"""

import json
import os
import re
import urllib.request

# CRITICAL: Bypass http_proxy for GitHub API
# (unlike curl --noproxy '*', Python urllib respects proxy env vars)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

STATES_DIR = os.path.expanduser("~/.hermes/cron/states")
os.makedirs(STATES_DIR, exist_ok=True)

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Hermes-Watchdog/1.0",
}


def api_get(url):
    """Safe API call — returns dict on error."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def raw_get(url):
    """Fetch raw text content."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode()
    except Exception:
        return None


def get_version_changelog(raw_url):
    """Extract version from CHANGELOG.md — match ## vX.Y.Z header."""
    content = raw_get(raw_url)
    if not content:
        return None
    match = re.search(r"^##\s+(v?\d+\.\d+\.\d+)", content, re.MULTILINE)
    return match.group(1) if match else None


def get_version_gradle(raw_url):
    """Extract version from build.gradle — match versionName."""
    content = raw_get(raw_url)
    if not content:
        return None
    match = re.search(r'versionName\s+"([^"]+)"', content)
    return match.group(1) if match else None


def summarize_diff(patch_text, max_lines=6):
    """
    Extract meaningful change lines from a unified diff patch.
    Shows actual code changes (adds/removes) for files, not just line counts.
    Skips boilerplate (imports, comments, whitespace).
    """
    if not patch_text:
        return []

    summary = []
    in_hunk = False
    added = []
    removed = []

    for line in patch_text.split("\n"):
        if line.startswith(("diff --git", "index ", "--- ", "+++ ")):
            continue
        if line.startswith("@@"):
            if added or removed:
                added = []
                removed = []
            in_hunk = True
            continue
        if in_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                clean = line[1:].strip()
                if clean and not clean.startswith(("import ", "// ", "/*", "* ", "# ", "}")):
                    added.append(clean[:80])
            elif line.startswith("-") and not line.startswith("---"):
                clean = line[1:].strip()
                if clean and not clean.startswith(("import ", "// ", "/*", "* ", "# ", "}")):
                    removed.append(clean[:80])

    result = []
    for a in added[:3]:
        result.append(f"    + {a}")
    if len(added) > 3:
        result.append(f"    … +{len(added)} more")
    return result[:max_lines]


def get_commit_detail(sha, repo):
    """
    Fetch full commit detail including file-level changes AND diff summaries.

    Makes TWO API calls:
    1. Structured JSON → file names, stats (+N/-N)
    2. Diff content → actual code changes (extracted via summarize_diff)

    Only call this for the 1-2 most recent commits to avoid timeout.
    """
    # Structured data
    url = f"{GITHUB_API}/repos/{repo}/commits/{sha}"
    data = api_get(url)
    if isinstance(data, dict) and "error" in data:
        return None

    # Diff content (separate request with diff Accept header)
    diff_headers = {**HEADERS, "Accept": "application/vnd.github.v3.diff"}
    req = urllib.request.Request(url, headers=diff_headers)
    diff_text = None
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            diff_text = resp.read().decode(errors="replace")
    except Exception:
        pass

    files = data.get("files", [])
    total_add = data.get("stats", {}).get("additions", 0)
    total_del = data.get("stats", {}).get("deletions", 0)

    file_lines = []
    for f in files[:10]:
        fn = f.get("filename", "?")
        status = f.get("status", "modified")[:1].upper()
        adds = f.get("additions", 0)
        dels = f.get("deletions", 0)
        emoji = {"A": "➕", "M": "📝", "D": "🗑️", "R": "🔀"}.get(status, "📄")
        file_lines.append(f"  {emoji} {fn} (+{adds}/-{dels})")

    if len(files) > 10:
        file_lines.append(f"  … and {len(files) - 10} more files")

    # Diff summary — actual code change content (not just counts)
    diff_summary = []
    if diff_text and len(diff_text) < 10000:
        for f in files[:3]:
            fn = f.get("filename", "?")
            patch = f.get("patch", "")
            if patch:
                s = summarize_diff(patch)
                if s:
                    diff_summary.append(f"    📄 {fn}:")
                    diff_summary.extend(s)

    return {
        "additions": total_add,
        "deletions": total_del,
        "changes": len(files),
        "file_lines": file_lines,
        "diff_summary": diff_summary,
        "message": data.get("commit", {}).get("message", ""),
    }


def check_repo(repo, branch, label, version_getter=None):
    """Check a single repo. Returns report string or empty string."""
    state_file = os.path.join(STATES_DIR, f"state-{repo.replace('/', '-')}.txt")
    url = f"{GITHUB_API}/repos/{repo}/commits?sha={branch}&per_page=10"
    data = api_get(url)

    if isinstance(data, dict) and "error" in data:
        return ""
    if not isinstance(data, list) or len(data) == 0:
        return ""

    latest_sha = data[0]["sha"]
    last_sha = ""
    if os.path.exists(state_file):
        with open(state_file) as f:
            last_sha = f.read().strip()

    # First run → store SHA, stay silent
    if not last_sha:
        with open(state_file, "w") as f:
            f.write(latest_sha)
        return ""

    # No changes
    if latest_sha == last_sha:
        return ""

    # --- New commits detected ---
    lines = [f"📦 {label}", f"  仓库：https://github.com/{repo}"]

    if version_getter:
        version = version_getter()
        if version:
            lines.append(f"  当前版本：{version}")

    lines.append("")
    found_new = False

    for c in data:
        sha = c["sha"][:8]
        msg = c["commit"]["message"].split("\n")[0]
        author = c["commit"]["author"]["name"]
        date = c["commit"]["author"]["date"][:10]

        lines.append(f"  [{date}] {sha} — {author}")
        lines.append(f"    {msg}")

        detail = get_commit_detail(c["sha"], repo)
        if detail and detail["file_lines"]:
            lines.append(f"    📊 +{detail['additions']}/-{detail['deletions']} ({detail['changes']} files)")
            lines.extend(detail["file_lines"])

        lines.append("")
        found_new = True
        if c["sha"] == last_sha:
            break

    if not found_new:
        return ""

    lines.append(f"  查看全部：https://github.com/{repo}/commits/{branch}")
    lines.append("")

    with open(state_file, "w") as f:
        f.write(latest_sha)

    return "\n".join(lines)


def main():
    reports = []
    # Example usage — customize per repo:
    # r = check_repo("owner/repo", "main", "My Project", get_version_changelog)
    # if r: reports.append(r)

    if reports:
        print("🔔 仓库有新提交！")
        print("")
        print("\n".join(reports))


if __name__ == "__main__":
    main()
```

## Version Source Strategies

| Project Type | File | Extractor |
|---|---|---|
| Node.js | `package.json` (root) | `json.loads(content)["version"]` |
| Python | `pyproject.toml` | `re.search(r'^version\s*=\s*"(.+)"', content, re.M)` |
| Python | `CHANGELOG.md` | `re.search(r'^##\s+(v?\d+\.\d+\.\d+)', content, re.M)` |
| Android | `app/build.gradle` | `re.search(r'versionName "(.+)"', content)` |
| Rust | `Cargo.toml` | `re.search(r'^version = "(.+)"', content, re.M)` |
| Generic | Git tag | `GET /repos/{o}/{r}/tags` → first tag's name |

### Private Repo Version Extraction

### Private Repo Version Extraction

For private repos, `raw.githubusercontent.com` returns 404. Two approaches:

**Option A — GitHub Contents API (works for any remote state):**
Use the GitHub Contents API with a PAT:
```python
def get_version_pyproject(repo, branch="master"):
    pat = _read_pat_from_git_credentials()
    if not pat:
        return None
    url = f"https://api.github.com/repos/{repo}/contents/pyproject.toml?ref={branch}"
    req = urllib.request.Request(url, headers=_auth_headers(pat))
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            content = base64.b64decode(data["content"]).decode()
            match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
            return match.group(1) if match else None
    except Exception:
        return None
```

**Option B — Local file read (faster, more reliable for cloned repos):**
If the repo is cloned locally on the same server (e.g., `~/projects/WC26-Main`), read the file directly — no API call, no SSL risk:
```python
def get_version_from_local(path="~/projects/WC26-Main/pyproject.toml"):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            content = f.read()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        return match.group(1) if match else None
    except Exception:
        return None
```
Limitation: local file may be stale if another user pushed to GitHub without the local clone being pulled. Acceptable for most watchdog use cases — the version string is approximate.

## Output Format

When changes are detected, the cron job delivers a formatted report:

```
🔔 VP-Codex 系列仓库有新的提交！

📦 VP-Codex-Web
  仓库：https://github.com/JTCAO515/VP-Codex-Web
  当前版本：v6.1.1

  [2026-06-23] a1b2c3d4 — AuthorName
    Fixed guest Trips empty-state action
    📊 +127/-83 (12 files)
    📝 web/app.js (+89/-42)
    📝 web/index.html (+23/-31)
    ➕ web/new-component.js (+15/-0)

  查看全部：https://github.com/JTCAO515/VP-Codex-Web/commits/main
```

## Key Pitfalls

### ⚠️ Python urllib + HTTP_PROXY (Unfiltered Networks)
On unfiltered networks (non-China VPS, local dev), Python's `urllib` respects `http_proxy`/`https_proxy` env vars. If these are set, `urlopen` will try to route GitHub API calls through the proxy, causing `ConnectionResetError`.

**Fix:** Strip proxy env vars at the top of the script:
```python
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
```

### ⚠️ Proxy Strategy for Restricted Networks (China VPS)
From Chinese servers, **direct** connections to GitHub API have intermittent SSL reset (`ConnectionResetError: [Errno 104]`). Even public repos and the commit list endpoint fail ~50% of the time. The proxy IS needed, not bypassed.

**Strategy:** Default to Xray HTTP proxy (`127.0.0.1:10809`), with automatic fallback to direct. Use a global `_using_proxy` flag:

```python
_using_proxy = True  # default: use Xray

def _urlopen_with_retry(req, timeout=12, max_attempts=2):
    global _using_proxy
    last_error = None
    for attempt in range(max_attempts):
        try:
            if _using_proxy:
                ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10809", "https": "http://127.0.0.1:10809"})
                opener = urllib.request.build_opener(ph)
                return opener.open(req, timeout=timeout)
            else:
                return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionResetError) as e:
            last_error = e
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500:
                raise
            if attempt < max_attempts - 1:
                time.sleep(1.0 * (attempt + 1))
    # Flip path and try once more
    _using_proxy = not _using_proxy
    try:
        if _using_proxy:
            ph = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10809", "https": "http://127.0.0.1:10809"})
            opener = urllib.request.build_opener(ph)
            return opener.open(req, timeout=timeout)
        else:
            return urllib.request.urlopen(req, timeout=timeout)
    except Exception:
        pass
    raise last_error
```

**IMPORTANT:** Do NOT use `with ... as resp: return resp` inside `_urlopen_with_retry`. The `with` context manager closes the response, causing "I/O operation on closed file" in the caller. Either `return opener.open(...)` directly (caller wraps in `with`) or keep the `with` block only in the caller.

### ⚠️ Commit Detail API Unreliable from Restricted Networks
The commit detail endpoint (`GET /repos/{owner}/{repo}/commits/{sha}` with `Accept: application/vnd.github.v3.diff`) frequently SSL-resets from China. When it works, it's slow (3-7s). The structured JSON response (same URL, default Accept header) also fails intermittently.

**Better approach:** Skip `get_commit_detail()` entirely. The commit list endpoint (`?per_page=5`) already returns enough info:
- SHA, commit message, author, date
- `stats` object with add/delete counts (sometimes available)
- List of changed files with +N/-N (sometimes available)

Example — use commit list data inline instead of a separate API call:
```python
for c in data:
    sha = c["sha"][:8]
    msg = c["commit"]["message"].split("\n")[0]
    author = c["commit"]["author"]["name"]
    date = c["commit"]["author"]["date"][:10]
    lines.append(f"  [{date}] {sha} — {author}")
    lines.append(f"    {msg}")

    # Use inline data (no separate API call)
    stats = c.get("stats") or {}
    if stats:
        adds = stats.get("additions", 0)
        dels = stats.get("deletions", 0)
        lines.append(f"    📊 +{adds}/-{dels} ({stats.get('total', 0)} files)")
    files = c.get("files") or []
    for f in files[:3]:
        lines.append(f"    📄 {f['filename']} (+{f['additions']}/-{f['deletions']})")
```

This avoids the unreliable commit detail API entirely and makes the watchdog 2-3x faster.

### ⚠️ GitHub API Rate Limiting
Unauthenticated requests are limited to 60/hr. For scripts that run every 2h monitoring 2 repos (4 API calls per run), this is fine. For more frequent or more repos, add authentication:
```python
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Hermes-Watchdog/1.0",
    "Authorization": f"token {PAT_TOKEN}",
}
```

### ⚠️ State File Consistency
The state file stores the **latest commit SHA**. When the script detects new commits:
1. It outputs the report (commits between `last_sha` and `latest_sha`)
2. It updates the state file to `latest_sha`

If the script crashes between step 1 and 2, the next run will re-report the same commits. This is acceptable (idempotent-ish — report duplicates once, then recovers).

### ⚠️ Commit Detail API Rate
`get_commit_detail()` makes one extra API call per new commit. The commit detail endpoint is more expensive but necessary for file-level stats. For repos with 5+ new commits, that's 5 extra calls per run — still well within limits for hourly runs.

### ⚠️ Private Repos — raw.githubusercontent.com Returns 404
`raw_get()` fetches from `raw.githubusercontent.com`, which returns 404 for private repos. To extract version info from private repos, use the GitHub Contents API with a PAT:

```python
def _read_pat():
    """Read PAT from ~/.git-credentials — pattern: https://user:PAT@github.com"""
    try:
        with open(os.path.expanduser("~/.git-credentials")) as f:
            for line in f:
                m = re.search(r"https://[^:]+:([^@]+)@github\.com", line)
                if m:
                    return m.group(1)
    except Exception:
        return None
    return None

def _auth_headers(pat=None):
    """Return headers with optional PAT auth."""
    h = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Hermes-Watchdog/1.0",
    }
    if pat:
        h["Authorization"] = f"token {pat}"
    return h
```

Pass these headers to **all** API calls (commits, commit detail, contents) when monitoring private repos:
```python
def api_get(url, pat=None):
    req = urllib.request.Request(url, headers=_auth_headers(pat))
    ...
```

The PAT is read once at script startup and reused — no need to read the file on every API call.

### ⚠️ api_get Can Return List or Dict — Type Guard Required
`api_get()` returns a list on success (from the commits endpoint) but `{"error": ...}` on failure. The `isinstance(data, dict)` check is correct but Pyright will warn. Use a helper:

```python
def api_get_dict(url, pat=None):
    """Ensure result is a dict (for commit detail, contents endpoints)."""
    result = api_get(url, pat)
    if isinstance(result, dict):
        return result
    return {"error": "unexpected_type", "detail": str(type(result))}
```

## Cron Job Registration

```bash
# Using cronjob tool:
cronjob action=create \
  schedule="every 2h" \
  script="monitor-my-repo.py" \
  no_agent=true \
  name="My Repo Monitoring" \
  deliver="weixin"
```

The `deliver` parameter routes output to the appropriate channel. Use `deliver="weixin"` for WeChat, `deliver="origin"` for the current chat, or omit for default.
