---
name: git-proxy-workflow
description: Git 操作通过 Xray 代理的完整工作流 — clone/push/pull、PAT 认证、空 repo 初始化、push protection 绕过。
---

# Git Proxy Workflow

> 在本服务器（中国网络）上通过 Xray 代理操作 GitHub 的完整方案。

---

## 环境

- Xray 代理：`http://127.0.0.1:10809`（HTTP CONNECT 代理）
- Git 全局代理设置：
  ```bash
  git config --global http.proxy http://127.0.0.1:10809
  git config --global https.proxy http://127.0.0.1:10809
  ```
- PAT 存储：`~/.git-credentials`（格式：`https://user:PAT@github.com`）
- Git 邮箱：`jt.cao@outlook.com`
- Git 用户名：`Zhuzhu Wei` / `JTCAO515`（看项目）

---

## 基本操作

### 克隆仓库

```bash
# 方式一：全局代理（推荐）
git config --global http.proxy http://127.0.0.1:10809
git config --global https.proxy http://127.0.0.1:10809
git clone https://github.com/JTCAO515/VP-Codex-Web.git

# 方式二：单次代理
git -c http.proxy=http://127.0.0.1:10809 clone https://github.com/JTCAO515/VP-Codex-Web.git
```

### 推送仓库

```bash
cd ~/projects/REPO
PAT=$(grep -o 'https://[^:]*:[^@]*@github.com' ~/.git-credentials | head -1 | sed 's|.*:\([^@]*\)@github.com|\1|')
git remote set-url origin "https://JTCAO515:${PAT}@github.com/JTCAO515/REPO.git"
git -c http.proxy=http://127.0.0.1:10809 push -u origin main
```

### 读取 PAT

```bash
# 从 ~/.git-credentials 提取
grep -o 'https://[^:]*:[^@]*@github.com' ~/.git-credentials | head -1 | sed 's|.*:\([^@]*\)@github.com|\1|'
```

---

## 空仓库初始化（关键技巧）

新建的空 GitHub 仓库无法直接通过 `git push` 推送（会触发 "Repository is empty" 409 或 proxy 超时）。

**解决步骤：**

1. 先用 GitHub Contents API 创建 README.md（初始化 main 分支）：
   ```bash
   PAT=<token>
   echo '{"message":"init","content":"'$(echo -n "# Repo Name" | base64 -w0)'","branch":"main"}' | \
   curl -s --noproxy '*' -X PUT "https://api.github.com/repos/JTCAO515/REPO/contents/README.md" \
     -H "Authorization: token $PAT" \
     -H "Content-Type: application/json"
   ```

2. 然后设置 remote 并 push（此时 main 分支已存在，push 正常工作）：
   ```bash
   git remote set-url origin "https://JTCAO515:${PAT}@github.com/JTCAO515/REPO.git"
   git -c http.proxy=http://127.0.0.1:10809 push --force -u origin main
   ```

---

## Push Protection 绕过

GitHub 的 secret scanning 会阻止包含 PAT 的提交。如果在文件中误写入 PAT：

**方案一：用 bypass URL（推荐）**
推送被拒绝时，GitHub 输出中会包含 bypass URL：
```
https://github.com/JTCAO515/REPO/security/secret-scanning/unblock-secret/XXXX
```
打开该链接（通过浏览器或 curl）即可允许。

**方案二：reset + force push（已写入 history 时）**
```bash
# 回到干净的 commit
git reset --soft <last_clean_commit_sha>
# 修改文件移除 PAT，重新提交
git add <file>
git commit -m "fix: remove PAT from file"
git -c http.proxy=http://127.0.0.1:10809 push --force origin main
```

**方案三：不 commit PAT 到文件**
- 用 `~/.git-credentials` 存储 PAT
- prompt 中用 `<TOKEN>` 占位符，说明从 git-credentials 读取
- 或者用 `$PAT` 环境变量

---

## 直接连接（绕过代理）

某些服务（status.claude.com）通过代理会超时，需要用直接连接：

```python
# Python 脚本中 bypass proxy
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
```

```bash
# curl 绕过代理
curl -s --noproxy '*' https://api.github.com/...
```

---

## 常见坑

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `Recv failure: Connection reset by peer` | Git 代理未设置 | `git config --global http.proxy` |
| `gnutls_handshake() failed` | 直接连接被墙 | 设置代理后再试 |
| `HTTP 408 curl 22` | 推送文件过多超时 | 先初始化仓库再用 `--force` push |
| `push declined due to repository rule violations` | PAT 误提交到文件 | 用 bypass URL 或 reset |
| `Remote end hung up unexpectedly` | 大文件推送超时 | 增大 `http.postBuffer` |
