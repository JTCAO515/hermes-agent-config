#!/usr/bin/env python3
"""
VP 多仓库变更监控脚本 (v5)
监控: WC26-Main + VP-Hermes-Web + VP-Claude-Web + VP-Codex-APK
模式: 静默看门狗 (有变更才输出)
功能: 变更内容详情 (文件级+diff摘要) + 迭代版本号
修复: v5 加入重试+代理回退，解决间歇性 SSL Reset
"""

import json
import os
import sys
import time
import urllib.request
import base64
import re
import ssl
import socket

# Attempt to bypass http_proxy for GitHub API, but fall back to proxy if needed
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("all_proxy", None)
os.environ.pop("ALL_PROXY", None)

STATES_DIR = os.path.expanduser("~/.hermes/cron/states")
os.makedirs(STATES_DIR, exist_ok=True)

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Hermes-Monitor/5.0",
}

# Read PAT from git-credentials for private repo access
GITHUB_PAT = None
try:
    with open(os.path.expanduser("~/.git-credentials")) as f:
        for line in f:
            m = re.search(r"https://[^:]+:([^@]+)@github\.com", line)
            if m:
                GITHUB_PAT = m.group(1)
                break
except Exception:
    pass


def _auth_headers():
    if GITHUB_PAT:
        return {**HEADERS, "Authorization": f"token {GITHUB_PAT}"}
    return HEADERS


# ── Retry / proxy fallback ──

_using_proxy = True  # Default to proxy since direct GitHub from China is flaky


def _urlopen_with_retry(req, timeout=15, max_attempts=2):
    """Open URL with retry on transient errors. Falls back to the other path if primary fails."""
    global _using_proxy

    last_error = None
    for attempt in range(max_attempts):
        try:
            if _using_proxy:
                proxy_handler = urllib.request.ProxyHandler({
                    "http": "http://127.0.0.1:10809",
                    "https": "http://127.0.0.1:10809",
                })
                opener = urllib.request.build_opener(proxy_handler)
                return opener.open(req, timeout=timeout)
            else:
                return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, socket.timeout, ssl.SSLError,
                ConnectionResetError, ConnectionError) as e:
            last_error = e
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500:
                raise
            if attempt < max_attempts - 1:
                time.sleep(1.0 * (attempt + 1))

    # All primary path retries exhausted → try the other path once
    _using_proxy = not _using_proxy
    try:
        if _using_proxy:
            proxy_handler = urllib.request.ProxyHandler({
                "http": "http://127.0.0.1:10809",
                "https": "http://127.0.0.1:10809",
            })
            opener = urllib.request.build_opener(proxy_handler)
            return opener.open(req, timeout=timeout)
        else:
            return urllib.request.urlopen(req, timeout=timeout)
    except Exception:
        pass

    raise last_error  # type: ignore[misc]


def api_get(url):
    try:
        req = urllib.request.Request(url, headers=_auth_headers())
        with _urlopen_with_retry(req, timeout=12, max_attempts=2) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def api_get_dict(url):
    result = api_get(url)
    if isinstance(result, dict):
        return result
    return {"error": "unexpected_type", "detail": str(type(result))}


def raw_get(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with _urlopen_with_retry(req, timeout=8, max_attempts=2) as resp:
            return resp.read().decode()
    except Exception:
        return None


def _raw_api_get(url, timeout=8):
    """Like raw_get but with auth headers (for private repo raw content)."""
    try:
        req = urllib.request.Request(url, headers=_auth_headers())
        with _urlopen_with_retry(req, timeout=timeout) as resp:
            return resp.read().decode()
    except Exception:
        return None


# ── Version getters ──


def get_latest_version_wc26():
    """Extract version from WC26-Main pyproject.toml (local file for reliability)."""
    local_path = os.path.expanduser("~/projects/WC26-Main/pyproject.toml")
    if os.path.exists(local_path):
        try:
            with open(local_path) as f:
                content = f.read()
            match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
            return match.group(1) if match else None
        except Exception:
            return None
    return None


def get_latest_version_hermes():
    """Extract latest version from VP-Hermes-Web CHANGELOG.md."""
    url = "https://api.github.com/repos/JTCAO515/VP-Hermes-Web/contents/CHANGELOG.md?ref=main"
    data = api_get_dict(url)
    if "error" in data:
        return None
    try:
        content = base64.b64decode(data["content"]).decode()
        match = re.search(r"^##\s+(v?\d+\.\d+\.\d+\w*)", content, re.MULTILINE)
        return match.group(1) if match else None
    except Exception:
        return None


def get_latest_version_apk():
    """Extract version from VP-Codex-APK build.gradle."""
    url = "https://api.github.com/repos/JTCAO515/VP-Codex-APK/contents/app/build.gradle?ref=main"
    data = api_get_dict(url)
    if "error" in data:
        return None
    try:
        content = base64.b64decode(data["content"]).decode()
        match = re.search(r'versionName\s+"([^"]+)"', content)
        version = match.group(1) if match else None
        match2 = re.search(r"versionCode\s+(\d+)", content)
        code = match2.group(1) if match2 else None
        if version and code:
            return f"{version} (build {code})"
        return version
    except Exception:
        return None


# ── Commit detail with diff summary ──


def summarize_diff(patch_text, max_lines=8):
    """
    Summarize a unified diff patch into key changes.
    Returns a list of meaningful change lines (max `max_lines`).
    """
    if not patch_text:
        return []

    added_lines = []
    removed_lines = []

    for line in patch_text.split("\n"):
        if line.startswith("diff --git") or line.startswith("index ") \
           or line.startswith("--- ") or line.startswith("+++ "):
            continue
        if line.startswith("@@"):
            added_lines = []
            removed_lines = []
            continue

        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:].strip())
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(line[1:].strip())

    summary = []
    additions = []
    for l in added_lines[:3]:
        if l and not l.startswith(("import ", "// ", "/*", "* ", "# ")):
            additions.append(f"+{l[:60]}")
    if len(added_lines) > 3:
        additions.append(f"  …+{len(added_lines)} lines")

    if additions:
        summary.append("    ✏️ Changes:")
        for a in additions:
            summary.append(f"    {a}")

    return summary[:max_lines]


def get_commit_detail(sha, repo):
    """Fetch full commit detail including file changes and diff summaries."""
    detail_headers = _auth_headers()
    detail_headers["Accept"] = "application/vnd.github.v3.diff"
    req = urllib.request.Request(
        f"{GITHUB_API}/repos/{repo}/commits/{sha}",
        headers=detail_headers,
    )
    diff_text = None
    try:
        with _urlopen_with_retry(req, timeout=10, max_attempts=2) as resp:
            diff_text = resp.read().decode(errors="replace")
    except Exception:
        pass

    # Also get structured data for file stats
    url = f"{GITHUB_API}/repos/{repo}/commits/{sha}"
    data = api_get_dict(url)
    if "error" in data:
        return None

    files = data.get("files", [])
    total_additions = data.get("stats", {}).get("additions", 0)
    total_deletions = data.get("stats", {}).get("deletions", 0)
    total_changes = data.get("stats", {}).get("total", 0)

    file_lines = []
    for f in files[:10]:
        fn = f.get("filename", "?")
        status = f.get("status", "M")[:1].upper()
        adds = f.get("additions", 0)
        dels = f.get("deletions", 0)
        emoji = {"M": "📝", "A": "➕", "D": "🗑️", "R": "🔀"}.get(status, "📄")
        file_lines.append(f"  {emoji} {fn} (+{adds}/-{dels})")

    if len(files) > 10:
        file_lines.append(f"  … and {len(files) - 10} more files")

    diff_summary_lines = []
    if diff_text and len(diff_text) < 10000:
        for f in files[:5]:
            fn = f.get("filename", "?")
            patch = f.get("patch", "")
            if patch:
                s = summarize_diff(patch)
                if s:
                    diff_summary_lines.append(f"    📄 {fn}:")
                    diff_summary_lines.extend(s)

    return {
        "additions": total_additions,
        "deletions": total_deletions,
        "changes": total_changes,
        "files": total_changes,
        "file_lines": file_lines,
        "diff_summary": diff_summary_lines,
        "message": data.get("commit", {}).get("message", ""),
    }


# ── Repo checking ──


def check_repo(repo, branch, label, version_getter=None):
    """Check a single repo for new commits. Returns report string or empty string."""
    state_file = os.path.join(STATES_DIR, f"state-{repo.replace('/', '-')}.txt")

    # Fetch recent commits (use per_page=5 to reduce API calls and timeouts)
    url = f"{GITHUB_API}/repos/{repo}/commits?sha={branch}&per_page=5"
    data = api_get(url)
    if "error" in data or not isinstance(data, list) or len(data) == 0:
        return ""

    latest_sha = data[0]["sha"]

    # Read previous state
    last_sha = ""
    if os.path.exists(state_file):
        with open(state_file) as f:
            last_sha = f.read().strip()

    # First run
    if not last_sha:
        with open(state_file, "w") as f:
            f.write(latest_sha)
        return ""

    # No changes
    if latest_sha == last_sha:
        return ""

    # ── New commits detected ──
    lines = []
    lines.append(f"📦 {label}")
    lines.append(f"  仓库：https://github.com/{repo}")

    if version_getter:
        version = version_getter()
        if version:
            lines.append(f"  版本：{version}")

    lines.append("")

    new_commits_found = False
    commit_index = 0
    for c in data:
        sha = c["sha"][:8]
        msg = c["commit"]["message"].split("\n")[0]
        author = c["commit"]["author"]["name"]
        date = c["commit"]["author"]["date"][:10]

        lines.append(f"  [{date}] {sha} — {author}")
        lines.append(f"    {msg}")

        # Get file stats from commit listing (no separate API call needed - avoid SSL reset issues)
        if commit_index < 2:
            # commit listing already includes limited file info in some cases
            stats = c.get("stats") or {}
            files = c.get("files") or []
            if stats:
                adds = stats.get("additions", 0)
                dels = stats.get("deletions", 0)
                changed = stats.get("total", 0)
                lines.append(f"    📊 +{adds}/-{dels} ({changed} files)")
            # File list: some commit list results include files, others don't
            if files:
                for f in files[:3]:
                    fn = f.get("filename", "?")
                    adds = f.get("additions", 0)
                    dels = f.get("deletions", 0)
                    lines.append(f"    📄 {fn} (+{adds}/-{dels})")
                if len(files) > 3:
                    lines.append(f"    … and {len(files) - 3} more files")
        else:
            lines.append("    📊 (see GitHub for details)")

        lines.append("")
        new_commits_found = True
        commit_index += 1

        if c["sha"] == last_sha:
            break

    if not new_commits_found:
        return ""

    lines.append(f"  🔗 https://github.com/{repo}/commits/{branch}")
    lines.append("")

    # Update state
    with open(state_file, "w") as f:
        f.write(latest_sha)

    return "\n".join(lines)


# ── Main ──


def main():
    deadline = time.monotonic() + 50
    reports = []

    repo_configs = [
        ("JTCAO515/WC26-Main", "master", "WC26-Main", get_latest_version_wc26),
        ("JTCAO515/VP-Hermes-Web", "main", "VP-Hermes-Web", get_latest_version_hermes),
        ("JTCAO515/VP-Claude-Web", "main", "VP-Claude-Web", get_latest_version_hermes),
        ("JTCAO515/VP-Codex-APK", "main", "VP-Codex-APK", get_latest_version_apk),
    ]

    for repo, branch, label, vg in repo_configs:
        if time.monotonic() >= deadline:
            break
        r = check_repo(repo, branch, label, vg)
        if r:
            reports.append(r)

    if reports:
        print("📡 仓库有新提交！")
        print("")
        print("\n".join(reports))


if __name__ == "__main__":
    main()
