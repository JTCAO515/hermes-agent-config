# 服务器拓扑（猪猪微）

## 机器清单

| 用途 | 提供商 | IP | 位置 | 运行服务 |
|------|--------|-----|------|---------|
| **主服务器** | 腾讯云 | `122.51.121.116` | 上海 | Hermes Agent, hermes-api:8504, mission-control:8503, Aesculap, Xray, FIFA sync, all projects |
| **中继服务器** | Vultr | `64.176.82.81` | 新加坡 | Nano data relay (nami_relay.py:8080), 已被 Vultr 云防火墙限制端口 |

## Vercel 代理指向

| 域名 | 项目 | 代理后端 | 状态 |
|------|------|---------|------|
| hermes.jtcao.space | hermes-dashboard | `122.51.121.116:8504/api/hermes/` | ✅ 8504 端口已开，上线中 |
| worldcup.jtcao.space | WC26 Edge Lab | Vercel Serverless (Python) | N/A - 纯 Vercel 部署 |

## 端口占用

| 端口 | 服务 | 启动方式 | 外网开放 |
|:----:|------|---------|:--------:|
| 8504 | Hermes Dashboard API | PM2 (python3) | ✅ 已开 |
| 8080 | 纳米数据中继 | Vultr 手动 | ❌ Vultr 防火墙拦截 |
| 22 | SSH | systemd sshd | ✅ |
| 10808 | Xray SOCKS5 | systemd | ❌ 本地代理 |

## 诊断速查

```bash
# 本地服务监听检查
ss -tlnp | grep -E "850[34]"

# 外网端口可达性（从其他机器测）
timeout 3 nc -zv 122.51.121.116 8504  # ✅
timeout 3 nc -zv 122.51.121.116 8503  # ❌ timeout=拦截

# 绕过代理测本地
curl -s --noproxy '*' http://localhost:8504/api/hermes/health
curl -s --noproxy '*' http://localhost:8503/api/tasks

# PM2 状态
pm2 list
pm2 logs <name> --lines 10 --nostream
```

## 历史失误

- **[已修正]** vercel.json 中 hermes-dashboard 和 mission-control 的 destination IP 写成了 Vultr `64.176.82.81`，但实际上后端服务跑在腾讯云 `122.51.121.116`。修正后 git push 即可。
- **[已修正]** mission-control 启动时未设 `PORT=8503`，默认跑在 3000 端口。需 `PORT=8503 pm2 start ...` 并先 kill 旧进程释放端口。
- **[已修正]** PM2 hermes-api 注册时 `cwd` 指向了错误的项目目录（`jarvis-mission-control-vercel/`），需 `pm2 delete` 后从正确目录重新启动。
- **[已移除]** JARVIS Mission Control — 用户评估后认为无用，完全卸载。清理步骤：`pm2 delete` → `pkill -f` → `rm -rf` 项目目录 → `rm -rf` skill → 删 memory 条目 → 删 GitHub 仓库 (可选)。不留下任何残留。