# GitHub仓库变更监控模式 (v2)

> 需要监控某个GitHub仓库的提交变化并静默汇报时使用。
> 模式：Python脚本 + no_agent=True cron → 有变更才输出，无变更静默。

## 架构

```
┌─ 看门狗脚本 ─────────────────────────┐
│  ~/.hermes/scripts/<name>-monitor.py   │
│  no_agent=True (脚本=任务, 无LLM消粍)   │
│                                        │
│  1. 读 state 文件（上次SHA）             │
│  2. GitHub API /commits 拿最新提交       │
│  3. 对比SHA                            │
│     - 无变更 → 输出空 (静默)             │
│     - 有变更 → 提取版本+文件改动+输出     │
│  4. 更新 state 文件                      │
└────────────────────────────────────────┘
         ↓ stdout (有变更时才非空)
┌─ cron (no_agent=True) ───────────────┐
│  stdout=none → 静默不打扰              │
│  stdout=有内容 → 直接送微信             │
└───────────────────────────────────────┘
```

## 关键实现细节

### 代理陷阱（重要！）

**错误做法：** 用 `https_proxy=http://127.0.0.1:10809` 走代理访问 GitHub API

**正确做法：在 Python 脚本中完全剥离 proxy env vars：**

```python
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
```

**原因：** GitHub API 通过代理连接时会触发 `ConnectionResetError`。这与 `curl --noproxy '*'` 的语义等价。如果脚本不剥离代理，urllib 会因代理中断 SSL 握手而失败。

### 状态追踪

**格式：** 纯文本文件，只存最新 SHA

```
~/.hermes/cron/states/state-{owner}-{repo}.txt
```

```
a905ecf409ffe8e6f7011692406e859d270d1a02
```

简单文本 > JSON 文件，无解析开销。

### GitHub API 调用

```python
import urllib.request, json

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Hermes-Monitor/2.0",
}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

# 获取提交列表
commits = api_get(f"{GITHUB_API}/repos/{repo}/commits?sha={branch}&per_page=10")

# 获取单提交详情（含文件改动）
detail = api_get(f"{GITHUB_API}/repos/{repo}/commits/{sha}")
# detail["stats"] → {"additions": N, "deletions": N, "total": N}
# detail["files"] → [{"filename": "path/to/file", "status": "added|modified|removed", "additions": N, "deletions": N}]
```

### 版本号提取

| 项目类型 | 提取源 | 正则 |
|---------|--------|------|
| Python/通用 | CHANGELOG.md | `r"^##\s+(v?\d+\.\d+\.\d+)"` |
| Android | app/build.gradle | `r'versionName\s+"([^"]+)"'` |
| Node.js | package.json | `json["version"]` |
| Python | pyproject.toml | `r'version = "([^"]+)"'` |

版本提取函数应作为 `version_getter` 回调传入，支持 `None` 返回（repo 无版本文件时跳过）。

### 文件级改动输出格式

```
📊 +1149/-0 (1149 files)
  ➕ app/src/main/java/.../MainActivity.java (+1023/-0)
  ➕ app/build.gradle (+14/-0)
  📝 api/routes.py (+23/-5)
  🗑️ old_module.py (+0/-89)
```

状态 emoji: `➕ added` / `📝 modified` / `🗑️ deleted` / `🔀 renamed`

## 模板脚本

参考 `~/.hermes/scripts/monitor-vp-codex.py` — 已实现的双仓库监控，支持：
- 多仓库并行检查（共用 report 变量拼接）
- 异步版本号提取（每个 repo 独立的 version_getter）
- 提交详情缓存（API 调用 + 错误降级）
- 10 个文件上限（避免报告过长）

## cron 设置

```bash
hermes cron create \
  --name "repo-name 监控" \
  --schedule "every 2h" \
  --script "monitor-script.py" \
  --no-agent \
  --deliver weixin
```

**关键参数：**
- `--no-agent` — 脚本=任务，无 LLM 推理开销
- `--deliver weixin` — 有变更时微信通知
- 首次运行自动初始化 state，不产生报告

## 错误处理

- API 失败 → 静默跳过（下次再试），不污染 state 文件
- 单 commit 详情获取失败 → 跳过文件级详情，仍显示 commit 基本消息
- 重复提交 → SHA 比较天然去重
- 脚本崩溃 → cron 记录 error 状态，下次正常执行
