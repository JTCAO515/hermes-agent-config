# Vite Admin Env-Var 模式（备选方案，rewrites 优先）

> **⚠️ 注意：** 此模式（env-var）是**备选方案**。**首选方案是 Vercel rewrites 代理**（见主 SKILL.md「模式二」）。
> 仅在后端无法通过 Vercel 代理时（如需要独立域名、Vercel 免费版限制等）才用此模式。

## 何时用

前端是用 **React + Vite** 构建的管理后台，且：
- 后端 API 运行在 VPS 固定 IP:PORT
- 前端是 SPA（单页应用），API 调用在客户端浏览器发起
- 不需要 vercel.json rewrites 代理（因为 API 域名和前端域名不同）

**对比 vercel.json rewrites 模式：**
| | rewrites 模式 | env-var 模式 |
|---|---|---|
| API 请求路径 | `/api/xxx`（同域） | `https://VPS_IP:PORT/api/xxx`（跨域） |
| 域名 | 单一域名 | 前端 Vercel 域名 + 后端 VPS IP |
| CORS | 不需要 | 需要后端设置 CORS |
| 适用场景 | 纯同域代理 | 管理后台/独立前端 |
| 安全性 | 较高（不暴露后端端口） | 较低（需要开安全组端口） |

## 架构

```
User Browser
    ↓  (axios fetch → VITE_API_URL)
Vercel CDN (admin 前端静态文件)
    ↓  (跨域请求)
VPS 公网 IP:8001 (FastAPI + PostgreSQL Docker)
```

## Vite 项目结构（以 vp-trae admin 为例）

```
admin/
├── src/
│   ├── api/
│   │   ├── client.ts        # Axios 实例 + JWT 拦截器
│   │   └── admin.ts         # Admin API 函数（login, checkAdmin, getStats, getUsers, getUser, updateUser）
│   ├── components/
│   │   ├── Layout.tsx       # 侧边栏 + 主内容区
│   │   ├── StatCard.tsx     # Dashboard 统计卡片
│   │   ├── UserTable.tsx    # 用户数据表格
│   │   └── UserFilters.tsx  # 搜索/筛选控件
│   └── pages/
│       ├── LoginPage.tsx    # 管理员登录
│       ├── DashboardPage.tsx# 用户统计
│       ├── UserListPage.tsx # 用户列表 + 分页
│       └── UserDetailPage.tsx# 用户详情 + 编辑
├── vercel.json              # { "framework": "vite" }
├── vite.config.ts           # 开发代理 proxy
└── index.html
```

## API 客户端模板

```typescript
// src/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/',
  headers: { 'Content-Type': 'application/json' },
});

// JWT 拦截器（可选）
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vp_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('vp_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;
```

## Vite 开发代理配置

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',  // 本地后端端口
        changeOrigin: true,
      },
    },
  },
});
```

## 部署到 Vercel

1. **Vercel Dashboard 创建项目**
   - Import GitHub repo
   - Root Directory 选 `admin/`（如果是 monorepo）
   - Framework Preset 选 Vite
   - 环境变量：`VITE_API_URL=https://<VPS_PUBLIC_IP>:<PORT>`

2. **vercel.json**
```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install"
}
```

3. **后端 CORS 配置**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或限制为 Vercel 域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Tailwind CSS v4 配置

Tailwind v4 （当前最新 4.x）使用 `@import "tailwindcss"` 而非 `@tailwind` 指令：
- ❌ 不用 `tailwind.config.js` 或 `postcss.config.js`
- ✅ CSS 入口：`@import "tailwindcss"`
- ✅ Vite 插件：`tailwindcss()` from `@tailwindcss/vite`

```bash
npm install tailwindcss @tailwindcss/vite @tailwindcss/postcss
```

## 已知陷阱

- **Tailwind v4 vs v3 配置差异**：v4 不再需要 `tailwind.config.js`，直接用 CSS `@import` 和 `@theme`；只需 `tailwindcss` + `@tailwindcss/vite`，不用 `@tailwindcss/postcss`
- **npm install 被误判为长进程**：此 VPS 上 `npm install` 可能触发 Hermes 的长进程警告。用 `background=true` 模式绕开。
- **Vercel npm11 "Exit handler never called!" 构建失败**：Vercel 默认使用 Node 24+（npm 11），npm@11 有一个 bug 会导致 `npm install` 在无交互环境下异常退出。修复方法见主 SKILL.md「Vercel 构建修复：npm11 Bug 指南」。
- **Vite 8 + TypeScript 6 兼容**：Vite 8 需要 TypeScript 6.x，Vercel 默认环境可能版本不匹配。在 `package.json` 的 `engines` 中锁定 Node 22.x 即可。
