---
name: vercel-vps-hybrid-deployment
description: Vercel 静态前端 + VPS 后端 API 混合部署架构。vercel.json rewrites 代理到外网 VPS 端口，PM2 持久化后端服务，安全组端口管理。适用于 hermes-dashboard、mission-control 等 Vercel 前端 + 自建后端项目。
category: devops
---

# Vercel-VPS 混合部署架构

## 概述

该模式用于「Vercel 托管静态前端 + VPS 运行后端 API」的混合部署。前端在 Vercel 上作为静态站点部署，后端 API 通过 `vercel.json` 的 `rewrites` 规则代理到 VPS 的外网可达端口。

**不适用于：** 纯 Python API 部署（用 `vercel-python-deployment` skill）、纯静态站点、WebSocket 依赖项目（Vercel 不支持 WS 代理）。

## 架构图

```
User Browser
    ↓
Vercel CDN (hermes.jtcao.space / mission.jtcao.space)
    ↓
vercel.json rewrites (HTTP proxy)
    ↓
VPS 公网 IP:8504 (hermes-api) / :8503 (mission-control)
    ↑
PM2 持久化进程 (node / python3)
```

## 诊断流程

### 0. 第一件事：确认云服务商（别猜）

**不要假设服务器是哪个云。** 先查 metadata，否则可能一直查错方向。

```bash
# 腾讯云
curl -s --noproxy '*' http://metadata.tencentyun.com/latest/meta-data/placement/region

# 阿里云
curl -s --noproxy '*' http://100.100.100.200/latest/meta-data/region-id

# AWS
curl -s --noproxy '*' http://169.254.169.254/latest/meta-data/placement/region

# 兜底：查公网 IP
curl -s --noproxy '*' https://api.ipify.org
```

### 1. 发现代理不通

当 Vercel 访问正常（前端 200）但接口数据加载失败时：

```bash
# 1a — 查 vercel.json 指向的 IP 和端口
cat vercel.json | python3 -m json.tool | grep destination

# 1b — 查本地服务是否在监听
ss -tlnp | grep -E "850[34]"

# 1c — 从外网测试端口是否可达
# ⚠️ 必须加 --noproxy '*'，否则 http_proxy 环境变量会导致 curl 走代理而不是直连本地
curl -s --noproxy '*' --connect-timeout 5 http://<VPS_PUBLIC_IP>:<PORT>/api/health

# 1d — TCP 级连通性测试（不依赖 HTTP）
timeout 3 nc -zv <VPS_PUBLIC_IP> <PORT> 2>&1

# 1e — 查服务器公网 IP
curl -s --noproxy '*' http://metadata.tencentyun.com/latest/meta-data/public-ipv4 2>/dev/null
# 或
curl -s --noproxy '*' https://api.ipify.org 2>/dev/null
```

### 2. 五种常见故障模式

| 现象 | 原因 | 修复 |
|------|------|------|
| Vercel 前端 200，API 超时 | vercel.json 指向 IP 错误（旧服务器/Vultr 等） | 修正 IP，git push |
| Vercel 前端 200，API 连接拒绝 | VPS 本地端口未监听 | `pm2 start` 或检查进程是否崩溃 |
| Vercel 前端 200，API 连接超时 | 云安全组/防火墙拦截了端口 | 开安全组入站规则（见 §3） |
| **本地 curl localhost 超时 / 走代理** | `http_proxy` 环境变量导致 curl 通过代理连接本地 | 加 `--noproxy '*'` |
| **PM2 启动成功但外网不通** | PM2 进程目录指向错误（旧代码路径），或进程实际上跑在默认端口而非目标端口 | 见 §PM2 陷阱 |

### 3. 云安全组端口管理

确认云服务商后，在对应云控制台放行端口：

**腾讯云：** 控制台 → 安全组 → 入站规则 → 新增 TCP 端口

```bash
# 检查 metadata 确认是腾讯云
curl -s --noproxy '*' http://metadata.tencentyun.com/latest/meta-data/placement/region

# 测试 TCP 端口是否真的开放（不依赖 HTTP 应答）
timeout 3 nc -zv <IP> <PORT>
# → "Connection succeeded" = 端口已开
# → timeout = 端口被安全组拦截
```
> **注意：** 即使 `ss -tlnp` 显示端口在监听，安全组仍可能从外网拦截。`nc -zv` 从本机测试是误解——必须从外网或另一台机器测。但本机可以用 `curl --noproxy '*'` 测试本地服务正常启动后再检查外网。

### 4. PM2 陷阱合集

#### 陷阱 A：Node.js PORT 环境变量

Node 服务通常用 `PORT = process.env.PORT || 3000`。PM2 启动时如果不设 PORT 就默认跑在 3000：

```bash
# ❌ 错误：跑在 3000 不是 8503
pm2 start server/index.js --name mission-control

# ✅ 正确：显式设 PORT
PORT=8503 pm2 start server/index.js --name mission-control
```

**Python 服务** 通常硬编码端口或从命令行参数读取，不受此影响。

#### 陷阱 B：EADDRINUSE（端口已被占用）

PM2 restart 遇到 EADDRINUSE 时，说明有旧进程还占着端口（可能是之前手动启动的，不是 PM2 管理的）：

```bash
# 1. 找到占端口的进程
fuser 8503/tcp 2>/dev/null
# 或
ss -tlnp | grep 8503

# 2. 杀掉旧进程
kill -9 <PID>

# 3. 确认端口已释放
ss -tlnp | grep 8503 || echo "✓ Free"

# 4. 重启 PM2
pm2 restart <name>
```

#### 陷阱 C：PM2 脚本路径错误

如果 PM2 进程是从旧目录启动的（如 `jarvis-mission-control-vercel/` 而非 `jarvis-mission-control/`），删除旧进程并从正确目录重新启动：

```bash
pm2 delete <name>
cd /correct/path && pm2 start <entry> --name <name>
```

## 标准部署流程

### 新建项目

1. **Vercel 创建项目** — 通过 GitHub 自动部署，或 Vercel Dashboard 手动创建
2. **vercel.json 配置：**

```json
{
  "version": 2,
  "builds": [
    { "src": "**/*", "use": "@vercel/static" }
  ],
  "rewrites": [
    { "source": "/api/(.*)", "destination": "http://<VPS_PUBLIC_IP>:<PORT>/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

3. **PM2 持久化后端：**
```bash
cd ~/projects/<project> && pm2 start server.py --name <name> --interpreter python3
pm2 save
```

4. **git push 触发 Vercel 部署**

### 修复 IP 变化/配置错误

```bash
# 1. 查 vercel.json 当前 IP
cat vercel.json | grep destination

# 2. 查当前服务器公网 IP
curl -s --noproxy '*' http://metadata.tencentyun.com/latest/meta-data/public-ipv4

# 3. 修正 IP
patch vercel.json  # 替换 destination 中的 IP

# 4. 提交并推送
git add vercel.json
git commit -m "fix: redirect Vercel proxy to correct backend IP"
git push origin main

# 5. 等待部署并验证
sleep 20
curl -sL -o /dev/null -w "%{http_code}" https://<VERCEL_DOMAIN>/api/health
```

## 模式二：Vercel Rewrites 模式（Admin 后台首选）

当前端是 **React + Vite** SPA 管理后台时，**优先使用 vercel.json rewrites 代理**，
而非环境变量模式。Rewrites 实现同域代理（无 CORS、同一域名、Vercel 自动 SSL）。

**经实测验证：** admin 前台 + API 代理走同一个域名表现最佳。见 vp-hermes 项目。

### 推荐架构（rewrites）

```json
{
  "framework": "vite",
  "installCommand": "pnpm install",
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "http://<VPS_IP>:<PORT>/api/$1" }
  ]
}
```

```javascript
// src/api/client.ts — 无需 VITE_API_URL，baseURL 用 '/'
const api = axios.create({
  baseURL: '/',  // 同域相对路径，rewrites 自动代理 /api/* 到 VPS
  headers: { 'Content-Type': 'application/json' },
});
```

### 模式对比

| | Rewrites 模式 ✅（推荐） | Env-Var 模式 |
|---|---|---|
| API 路径 | `/api/xxx`（同域代理） | `https://VPS_IP:PORT/api/xxx`（直连） |
| 需要 | Vercel Edge Proxy | 后端 CORS 配置 + 安全组端口 |
| CORS | ❌ 无问题 | ⚠️ 需后端放行 Vercel 域名 |
| SSL | Vercel 自动处理 | ⚠️ 需后端或 Nginx 处理 |
| 环境变量 | 不需要 | 需要 `VITE_API_URL` |
| 适用场景 | 首选方案 | 后端无法通过 Vercel 代理时兜底 |

### Vite Admin 项目结构

#### 独立项目（admin 即 root）

```
admin/
├── src/
│   ├── api/         # Axios + JWT 客户端（baseURL: '/'）
│   ├── components/  # Layout, Table, Filters, Header
│   └── pages/       # Login, Dashboard, List, Detail
├── vercel.json      # framework: vite + rewrites
├── vite.config.ts   # dev proxy → localhost backend
└── README.md
```

#### 主项目内的子目录（如 VP-Hermes-APK 的 admin/）

当  React SPA 是**主项目的一个子目录**（例如 `VP-Hermes-APK/admin/`），部署到 Vercel 时需要：

1. **Vercel Dashboard → Import → Root Directory: `admin/`** — Vercel 将 `admin/` 作为构建根目录
2. `admin/vercel.json` 的 `outputDirectory` 是相对于 `admin/dist/`
3. `admin/` 下必须有独立的 `package.json` 和 `pnpm-lock.yaml`（Vercel 不会读取父目录的配置）
4. Git push 时，整个仓库会被 Vercel clone，但只有 `admin/` 目录参与构建

**陷阱：** 如果漏配 Root Directory，Vercel 会尝试从仓库根目录构建，找不到 `vercel.json` 和 `package.json` 而失败。

#### 顶部导航栏 — 登录/登出状态组件

Admin SPA 通常需要一个固定的顶部导航栏（Header），包含登录按钮和版本号：

```tsx
// src/components/Header.tsx — AI 生成范本
export default function Header() {
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('vp_token');
    if (!token) { setUser(null); return; }
    checkAdmin()
      .then((u) => setUser({ email: u.email }))
      .catch(() => setUser(null));
  }, [location.pathname]);

  return (
    <header style={{ position:'fixed', top:0, left:0, right:0, height:48,
      background:'#1A1A1A', borderBottom:'1px solid #3A3A3A',
      display:'flex', alignItems:'center', justifyContent:'space-between',
      padding:'0 1.5rem', zIndex:100 }}>
      <div style={{ display:'flex', alignItems:'center', gap:10 }}>
        <span onClick={() => navigate('/')} style={{ color:'#C9A96E',
          fontWeight:600, cursor:'pointer' }}>🐼 VisePanda</span>
        <span style={{ color:'#6C6A64', fontSize:'0.75rem', fontFamily:'monospace',
          padding:'2px 6px', border:'1px solid #3A3A3A', borderRadius:4 }}>v0.2.7</span>
      </div>
      <div>
        {user ? (
          <><span style={{ color:'#9C9A94', fontSize:'0.85rem' }}>{user.email}</span>
            <button onClick={() => { logout(); navigate('/login'); }}
              style={{ background:'none', border:'1px solid #3A3A3A',
              color:'#D4CEC4', padding:'4px 12px', borderRadius:6 }}>Log Out</button></>
        ) : (
          <button onClick={() => navigate('/login')}
            style={{ background:'#C9A96E', border:'none', color:'#0A0A0A',
            padding:'6px 16px', borderRadius:6, fontWeight:600 }}>登录系统</button>
        )}
      </div>
    </header>
  );
}
```

然后在 `App.tsx` 中全局使用：

```tsx
export default function App() {
  return (
    <div style={{ paddingTop: 48 }}>  {/* 给固定 header 留空间 */}
      <Header />
      <Routes>{/* ... */}</Routes>
    </div>
  );
}
```

### Vercel 部署步骤

1. Dashboard → Import GitHub repo → Root Directory: `admin/`
2. Framework: Vite
3. 不需要 `VITE_API_URL`（rewrites 处理代理）
4. git push 触发部署

### 关键陷阱

1. **localStorage key 一致性** — `client.ts`、`admin.ts`、`App.tsx` 中使用的 token key 名必须完全一致。不一致会导致「登录成功但刷新后未授权」的幽灵 bug。例如 `vp_admin_token` vs `vp_token` 混用。
2. **dev proxy 与 prod 路径匹配** — `vite.config.ts` 的 dev proxy 路径模式需与 `vercel.json` 的 rewrite source 一致，否则开发环境正常但生产异常。
3. **CORS 双重问题** — Rewrites 模式无 CORS 问题。如果用了 Env-Var 模式，后端 CORS 必须放行 Vercel 域名。
4. **版本号漂移** — 如果前端从 `/api/health` 动态拉取版本号（`fetch('/api/health').then(d => d.version)`），而后端 health 端点返回的是过时的硬编码版本（如 `0.1.0`），前端显示的版本号会一直落后。**修复方式：** 在 Header 组件中硬编码版本号（如 `<span>v0.2.7</span>`），而非依赖 API 动态返回。或用 git tag 自动注入构建版本。
5. **Vercel Root Directory 配置** — 当 admin SPA 是仓库子目录时（如 `admin/`），必须在 Vercel Dashboard 的 Project Settings → General → Root Directory 中设置正确的子目录路径，否则 Vercel 从根目录找不到 `vercel.json` 和 `package.json`。

## Vercel 构建修复：npm11 Bug 指南

### 问题
Vercel 默认构建环境使用 Node 24+（内置 npm 11）。npm@11 在无交互模式（Vercel 的 CI 环境）下存在一个已知 bug，`npm install` 会以 `Exit handler never called!` 异常退出，导致部署失败。

### 症状
```
npm error Exit handler never called!
npm error This is an error with npm itself. Please report this error at:
npm error   <https://github.com/npm/cli/issues>
Error: Command "npm install" exited with 1
```

### ✅ 唯一经实测验证的修复方案：切换到 pnpm

**⚠️ 注意：** `engines` 锁定、`preinstall` 降级、`npx npm@10` 绕过等方案均实测失败。**pnpm 是唯一确认有效的方案。** Vercel 原生支持 pnpm（自动检测 `pnpm-lock.yaml`）。

#### 步骤

1. **本地切换：**
```bash
cd admin/
rm -rf node_modules package-lock.json
npm install -g pnpm
pnpm install && pnpm build   # 验证通过
```

2. **更新 vercel.json：**
```json
{
  "framework": "vite",
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "installCommand": "pnpm install"
}
```

3. **提交 lock 文件：** 删除 `package-lock.json` → 提交 `pnpm-lock.yaml`。Vercel 通过此文件自动检测 pnpm。

4. **推送触发重新部署。** 安装速度从 32s → 7s，构建速度 349ms。

#### 已失败方案的记录

| 方案 | 方法 | 结果 |
|------|------|------|
| engines 锁定 | `package.json` 设 `"node": "22.x"` | ❌ 仍报错 |
| preinstall 降级 | 用 npx 装 npm@10 | ❌ preinstall 自己就被 npm11 调用 |
| npx 绕过 | `vercel.json` 中 `installCommand: "npx --yes npm@10 install"` | ❌ 同样 `exited with 1` |

详见 `references/vercel-npm11-bug.md`（完整修复记录含三次尝试对比）。

## 参考文件

- `references/vite-admin-envvar-pattern.md` — Vite Admin 部署参考（env-var 模式作为 rewrites 的备选方案）
- `references/docker-vps-python-china.md` — Docker + 中文 VPS Python 部署技巧
- `references/vercel-npm11-bug.md` — Vercel npm 11 构建失败完整修复记录
- `references/server-topology.md` — 当前服务器拓扑、端口状态、历史失误
- `references/dashboard-status-cache.md` — Cron-Driven 状态缓存模式
- `references/conversation-export-pipeline.md` — 全量对话历史导出管线

## 相关技能

- `vercel-python-deployment` — 纯 Python API 部署到 Vercel Serverless
- `xray-smart-routing` — VPS 出站代理路由（不影响 Vercel 代理入站）
