# Vercel npm 11 Bug — 完整修复记录

## 错误症状

Vercel 构建日志：
```
npm error Exit handler never called!
npm error This is an error with npm itself. Please report this error at:
npm error   <https://github.com/npm/cli/issues>
npm error A complete log of this run can be found in: /vercel/.npm/_logs/2026-06-17T06_16_38_442Z-debug-0.log
Error: Command "npm install" exited with 1
```

## 根因

- Vercel 默认构建环境使用 **Node 24.x** + **npm 11**
- npm 11 在无交互/CI 环境下存在一个 bug，退出时无法正确处理句柄（"Exit handler never called!"）
- 此 bug 触发率高，非偶发

## ✅ 已验证修复方案：切换到 pnpm

**pnpm 是唯一经此 session 验证有效的方案。** Vercel 原生支持 pnpm（自动检测 `pnpm-lock.yaml`）。

### 步骤

#### 1. 本地切换到 pnpm

```bash
cd admin/
rm -rf node_modules package-lock.json
npm install -g pnpm
pnpm install
pnpm build    # 验证构建通过
```

#### 2. 更新 `vercel.json`

```json
{
  "framework": "vite",
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "installCommand": "pnpm install"
}
```

#### 3. 保留 lock 文件

- 删除 `package-lock.json`
- **提交 `pnpm-lock.yaml`** — Vercel 通过这个文件自动检测到 pnpm
- 可选：添加 `.npmrc` 防止意外混用 npm 和 pnpm
  ```
  # This project uses pnpm - don't use npm
  package-lock.json=false
  ```

#### 4. 推送并 Redeploy

```bash
git add -A
git commit -m "Switch to pnpm — fix npm11 Exit handler bug on Vercel"
git push
# Vercel 自动检测 pnpm-lock.yaml，使用 pnpm 构建
```

### pnpm 优势

| | npm 11 | pnpm |
|---|---|---|
| Vercel 支持 | ✅ 默认 | ✅ 原生（自动检测） |
| 安装速度 | ~32s | ~7s |
| 构建速度 | ~309ms | ~349ms |
| npm 11 bug | ❌ 触发 | ✅ 无 |

## ❌ 方案一尝试：`package.json engines` + `preinstall` 脚本（失败）

```json
{
  "engines": { "node": "22.x", "npm": ">=10.0.0 <11.0.0" },
  "scripts": { "preinstall": "npx npm@10 install -g npm@10 2>/dev/null || true" }
}
```

```ini
# .npmrc
legacy-peer-deps=true
```

**结果：** Vercel 仍报错。可能原因：preinstall 脚本本身就被 npm 11 调用，npm 11 在 preinstall 阶段已崩溃。

## ❌ 方案二尝试：`vercel.json installCommand` 用 npx 绕过（失败）

```json
{
  "installCommand": "npx --yes npm@10 install --legacy-peer-deps --no-optional"
}
```

**结果：** 同样报 `exited with 1`。可能原因：
- `npx` 本身也是 npm 11 的一部分，同样有 bug
- Vercel CI 环境的网络/版本限制导致 npx 缓存或下载失败

## 附加优化

### 清理多余依赖

移除 `autoprefixer`（Tailwind CSS v4 不再需要）：
```
npm uninstall autoprefixer
```

### Tailwind CSS v4 配置确认

Tailwind v4 改用 `@import "tailwindcss"` 替代 `@tailwind` 指令，不再需要 `tailwind.config.js` 和 `postcss.config.js`。所需依赖：
- `tailwindcss`（运行库）
- `@tailwindcss/vite`（Vite 插件）

### 本地验证

```bash
pnpm install    # 预期：0 vulnerabilities, 正常退出
pnpm build      # 预期：✓ built in XXms
```

## 关键词

Vercel, npm install failed, Exit handler never called, npm 11, pnpm, Vite deployment, CI environment, npx failed too
