# VisePanda 运维速查

## 项目信息

| 项目 | 仓库 | 架构 | LLM | 状态 |
|------|------|------|-----|------|
| **v2（当前）** | `JTCAO515/vise-panda-2` | 单文件后端渲染 | GLM 5.1 | 本地测试通过，待部署 |
| v1（旧版） | `JTCAO515/VisePanda-New` | 前后端分离 | DeepSeek | 已弃用（__API_BASE__ 架构缺陷） |

- **Supabase**: `jdlinmdhmulozrjeseyc.supabase.co`
- **生产域名**: `go2china.space`

## v2 本地启动

```bash
cd /home/ubuntu/projects/vise-panda-2

# 环境变量
source .env

# 启动（单文件，不需要前后端分离）
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 测试
curl http://localhost:8000/api/health         # → {"ok":true,"version":"0.1.0"}
curl http://localhost:8000/                   # → HTML 首页
curl -X POST http://localhost:8000/api/chat   # → SSE 流式对话
```

## v2 Vercel 部署清单

### 环境变量（Vercel Settings → Environment Variables）

| KEY | VALUE | 说明 |
|-----|-------|------|
| SUPABASE_URL | https://jdlinmdhmulozrjeseyc.supabase.co | |
| SUPABASE_ANON_KEY | sb_publishable_GDZz-hDv6m-GTzRwsAt7Lw_BaU7CQYM | |
| LLM_ENABLED | 1 | |
| LLM_BASE_URL | https://open.bigmodel.cn/api/paas/v4 | GLM 5.1 |
| LLM_MODEL | glm-5.1 | |
| LLM_API_KEY | f8deeed9d23b43c8a891f72dd99d8d10.tErLZfXyLsq5wFzc | |
| AUTH_TEST_BYPASS | 0 | 生产必须为 0 |

---

## Supabase Auth 配置

Supabase Dashboard → Authentication → URL Configuration：

- **Site URL**: `https://go2china.space`
- **Redirect URLs**: 加 `https://go2china.space/auth/callback`

> ⚠️ 这一步不做的话，即使 API 全通、JS 正常，OAuth 回调也会失败。

### Google OAuth Provider 配置

Supabase Dashboard → Authentication → Providers → Google：
- 启用 Google
- Client ID / Secret 从 Google Cloud Console 获取
- 确保 Google Cloud 的 Authorized redirect URIs 包含：
  `https://jdlinmdhmulozrjeseyc.supabase.co/auth/v1/callback`

## "Supabase 未配置" Bug 的 4 层根因

这是 VisePanda 最顽固的线上 bug，有四层可能原因，必须逐层排查：

| 层 | 症状 | 检查方法 | 修复 |
|----|------|---------|------|
| 1 | `/api/health` 500，`ModuleNotFoundError` | `curl https://go2china.space/api/health` | `api/index.py` 加 `sys.path.insert(0, ...)` |
| 2 | `/api/public-config` 返回空 `{}` | `curl https://go2china.space/api/public-config` | Vercel 加环境变量 SUPABASE_URL + SUPABASE_ANON_KEY |
| 3 | curl 正常但 JS 报"未配置" | Network 面板看 `/api/public-config` 是否 200 | `__API_BASE__` 条件化，不要硬编码 localhost |
| 4 | curl/JS 都正常但仍弹窗 | 模块加载竞态：fetch 还在飞，JS 已读到空配置 | 用 `__SUPABASE_CONFIG__` + `__CONFIG_READY__` Promise 预取模式 |

### api/index.py 关键修复

```python
import sys, os
# Vercel 不自动加 backend/ 到 Python path，必须手动注入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
```

不要依赖 `PYTHONPATH` 环境变量——Vercel Python Runtime 可能不认。

### __API_BASE__ 条件化

所有前端 HTML 文件的 `__API_BASE__` 必须条件化，否则线上全挂：

```html
<script>
if (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  window.__API_BASE__ = "http://localhost:8000";
</script>
```

涉及文件：`index.html` `chat.html` `dashboard.html` `auth/callback.html`

## 线上验证

部署后逐项检查：

1. `curl https://go2china.space/api/health` → `{"ok":true,"version":"3.0.0",...}`
2. `curl https://go2china.space/api/public-config` → `{"supabase_url":"...","supabase_anon_key":"..."}`
3. 浏览器访问首页，F12 Network 看 `/api/public-config` 是否 200
4. Sign in with Google 不应弹 "Supabase 未配置"

## GitHub Push（中国服务器）

### 首选：SSH（已配 key）

服务器已有专用 key `~/.ssh/vise_github`，`~/.ssh/config` 已配好：

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/vise_github
    StrictHostKeyChecking accept-new
```

直接 `git push` 即可，不走 HTTPS，不被墙。

### 备选：HTTPS + Token（网络不稳时）

```bash
GIT_SSL_NO_VERIFY=1 git push https://TOKEN@github.com/JTCAO515/vise-panda-2.git main
```

### 后台重试循环

```bash
for i in 1 2 3 4 5; do
  git push && break
  sleep 30
done
```

### 生成新 SSH Key（如需要）

```bash
ssh-keygen -t ed25519 -f ~/.ssh/vise_github -C "vise-panda-deploy"
cat ~/.ssh/vise_github.pub  # 复制到 GitHub → Settings → SSH Keys
```

## v3.0–v4.0 版本路线

| 版本 | 内容 |
|------|------|
| v3.0 | 限流/安全头/CORS/错误页/CI |
| v3.2 | 拖拽行程规划器 + 地图 + PDF |
| v3.3 | SSE 流式对话 + Markdown + 快捷回复 |
| v3.6 | 用户中心 + 证件夹 |
| v3.8 | SEO + PWA (manifest/SW/hreflang) |
| v4.0 | 语音输入 + PWA 安装 + 相机 |
