# Vercel Serverless 部署约束

## 不可用的 Python 特性

| 特性 | 原因 | 替代方案 |
|------|------|---------|
| `ProcessPoolExecutor` | Vercel (AWS Lambda) 禁止 `os.fork()` | 强制单进程 (`num_workers=1`) |
| `threading` 多线程 I/O | 可用但有限 | 单线程 + async/await |
| `tempfile` 大文件 | `/tmp` 仅 512MB | 避免大文件临时写入 |
| `numpy` 等 C 扩展 | 部分可用（需预编译） | 内置 `random` 替代 |

## `ProcessPoolExecutor` 崩溃诊断

**症状：** Vercel 返回 500，本地 27/27 测试全过。

**根因链路：**
```
make_decision() → monte_carlo_equity() → os.cpu_count()=2
  → ProcessPoolExecutor(max_workers=2) → fork() → OSError: [Errno 38] Function not implemented
  → 500 Internal Server Error
```

**修复（2026-06-02）：**
- `equity_calculator.py` 中 `n_workers = os.cpu_count() or 1` → `n_workers = num_workers or 1`
- 默认强制单进程，仅显式传 `num_workers > 1` 才启用多进程
- 单进程 10000 sims 在 Vercel 上约 20-30s

## 部署检查清单

- [ ] 本地 `python -m pytest tests/ -v` 全通过
- [ ] 无 `os.fork()`, `ProcessPoolExecutor`（未显式启用时）
- [ ] `requirements.txt` 不含 Vercel 不支持的包
- [ ] `vercel.json` runtime 版本匹配（python3.11）
- [ ] 推送后等 1-2 分钟让 Vercel 自动构建
- [ ] 强制刷新页面 (Ctrl+Shift+R) 清空缓存

## 强制 Redeploy

```bash
git commit --allow-empty -m "force redeploy"
git push origin main
```

Vercel 仪表盘 → Deployments 确认最新 commit 已部署成功。
