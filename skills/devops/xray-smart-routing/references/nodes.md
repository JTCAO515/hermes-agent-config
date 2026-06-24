# 节点测试记录 (2026-05-24)

## 节点A: dmz.damaoziii.top (当前在用)

| 参数 | 值 |
|---|---|
| 类型 | VLESS + REALITY |
| 地址 | dmz.damaoziii.top:53423 |
| UUID | dcfa683c-ac5c-4589-a35d-f6b27fee998c |
| 流控 | xtls-rprx-vision |
| serverName | yahoo.com |
| publicKey | HxQc-SN7_E9M9ktOLuL-aybfEaMaCceUMbHEDhUxWAc |
| shortId | a2 |

**测试结果**：
- Google: ✅ 200 | 2.3s 
- GitHub: ✅ 200 | 5.3s
- YouTube: ✅ 200 | 3.7s
- httpbin: ❌ 503 (站点自身问题)

## 节点B: z1d03sg.maxxlcc.pro:33062 (新加坡 🇸🇬)

来自 Shadowrocket JSON 导出。

| 参数 | 值 |
|---|---|
| 类型 | VLESS |
| 地址 | z1d03sg.maxxlcc.pro:33062 |
| UUID | 60A69EA8-F93F-3278-D15E-8B954E13282C |
| IP | 18.138.243.125 |
| tls | true |
| xtls | 2 (Vision) |
| publicKey | LkGl8x3CJE29wALCp5XapDYkPsFX9XZzWBNH-gSJ4Go |
| peer | swdist.apple.com |
| shortId | 3c936ea4 |

**尝试的配置变体**：

| 尝试 | security | flow | 结果 |
|---|---|---|---|
| REALITY | reality | xtls-rprx-vision | SSL_ERROR_SYSCALL (0.6s) |
| TLS | tls | (none) | wrong version number (0.2s) |
| REALITY | reality | (none) | 000 (0.2s) |

**结论**：节点可能已失效或对该 VPS IP 有限制。当前节点 A 稳定可用。
