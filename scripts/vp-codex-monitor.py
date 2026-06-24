#!/usr/bin/env python3
"""
VP-Codex-Web 仓库更新监控脚本
每轮检查 GitHub API 的最新提交，跟上次记录的 SHA 对比，
有更新则拉取 commit 详情并总结成非技术语言。
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

REPO = "JTCAO515/VP-Codex-Web"
STATE_FILE = os.path.expanduser("~/.hermes/data/vp-codex-state.json")
PROXY = "http://127.0.0.1:10809"

BEIJING_TZ = timezone(timedelta(hours=8))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_sha": None, "first_run": True}


def save_state(sha):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_sha": sha, "first_run": False}, f)


def curl(url):
    """请求 GitHub API"""
    result = subprocess.run(
        ["curl", "-s", url],
        capture_output=True, text=True,
        timeout=30,
        env={**os.environ, "https_proxy": PROXY}
    )
    return result.stdout


def fetch_commits(since_sha=None):
    """获取最新提交列表"""
    url = f"https://api.github.com/repos/{REPO}/commits?per_page=10"
    if since_sha:
        url += f"&sha=main"
    
    data = curl(url)
    try:
        commits = json.loads(data)
        if not isinstance(commits, list):
            return []
        return commits
    except (json.JSONDecodeError, TypeError):
        return []


def fetch_commit_detail(sha):
    """获取单个提交的详细信息，含文件变更列表"""
    url = f"https://api.github.com/repos/{REPO}/commits/{sha}"
    data = curl(url)
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def summarize_for_user(commits):
    """把技术commit翻译成小白能听懂的语言"""
    lines = []
    lines.append(f"🔄 VP-Codex-Web 更新报告")
    lines.append(f"📅 {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M')} (北京时间)")
    lines.append("")
    
    for i, c in enumerate(commits):
        msg = c["commit"]["message"].split("\n")[0]
        author = c["commit"]["author"]["name"]
        date_str = c["commit"]["author"]["date"]
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(BEIJING_TZ)
        sha = c["sha"][:7]
        
        lines.append(f"--- 更新 #{i+1} ---")
        lines.append(f"⏰ {date.strftime('%m-%d %H:%M')}")
        lines.append(f"👤 作者: {author}")
        lines.append(f"📝 {msg}")
        
        # 获取详情分析文件改动
        detail = fetch_commit_detail(sha)
        if detail and "files" in detail:
            files = detail["files"]
            added = [f["filename"] for f in files if f.get("status") == "added"]
            modified = [f["filename"] for f in files if f.get("status") == "modified"]
            deleted = [f["filename"] for f in files if f.get("status") == "removed"]
            
            changes_parts = []
            if added:
                changes_parts.append(f"➕ 新增 {len(added)} 个文件")
            if modified:
                changes_parts.append(f"✏️ 修改 {len(modified)} 个文件")
            if deleted:
                changes_parts.append(f"🗑️ 删除 {len(deleted)} 个文件")
            
            lines.append(f"📂 {' | '.join(changes_parts)}")
            
            # 统计总改动行数
            total_additions = sum(f.get("additions", 0) for f in files)
            total_deletions = sum(f.get("deletions", 0) for f in files)
            if total_additions or total_deletions:
                lines.append(f"📊 +{total_additions} / -{total_deletions} 行代码")
            
            # 重要的文件变更（去掉测试文件）
            key_files = [f for f in files 
                        if not f["filename"].startswith("tests/") 
                        and f.get("status") in ("added", "modified")]
            if key_files:
                key_list = [f["filename"] for f in key_files[:5]]
                label = "主要变更" if not added else "新增/修改"
                lines.append(f"📄 {label}:")
                for fname in key_list:
                    f = next(x for x in key_files if x["filename"] == fname)
                    if f.get("additions", 0) + f.get("deletions", 0) > 0:
                        lines.append(f"   • {fname} (+{f['additions']}/-{f['deletions']})")
                    else:
                        lines.append(f"   • {fname}")
                if len(key_files) > 5:
                    lines.append(f"   ... 还有 {len(key_files)-5} 个文件")
        
        lines.append("")
    
    # 做一个"一句话总结"
    first_msg = commits[0]["commit"]["message"].split("\n")[0]
    lines.append("---")
    lines.append(f"💬 一句话: {first_msg}")
    lines.append("")
    lines.append("🔗 https://github.com/JTCAO515/VP-Codex-Web")
    
    return "\n".join(lines)


def main():
    state = load_state()
    last_sha = state.get("last_sha")
    
    # 获取最新提交
    commits = fetch_commits()
    if not commits:
        print("[SILENT]")
        return
    
    latest_sha = commits[0]["sha"]
    
    # 第一次运行：记录SHA但不报告（初始化）
    if last_sha is None:
        save_state(latest_sha)
        print("[SILENT]")
        return
    
    # 没有新提交
    if latest_sha == last_sha:
        print("[SILENT]")
        return
    
    # 有新的提交——找出从上次到现在的所有新提交
    new_commits = []
    for c in commits:
        new_commits.append(c)
        if c["sha"] == last_sha:
            break
    
    save_state(latest_sha)
    
    # 生成小白友好的报告
    report = summarize_for_user(new_commits)
    print(report)


if __name__ == "__main__":
    main()
