# 参考案例: WC26 Edge Lab 续写项目恢复流程

> 对应 handoff skill 中「续写项目」三步骤的实际执行记录。

## 场景

用户说"现在续写wc26这个项目"，HANDOFF.md 已存在于仓库根目录。

## 执行记录

### 恢复 Step 1 — 读 HANDOFF.md
- 读取 `~/projects/world-cup-edge-lab/HANDOFF.md`
- 理解产品定位: 2026 世界杯实时中文预测平台
- 版本: v5.0.2，仓库 SSH 推送，域名 worldcup.jtcao.space

### 恢复 Step 2 — 验证真实状态（文档 vs 现实）

| HANDOFF 声称 | 实际验证 | 差异 |
|--------------|---------|------|
| Vercel 已部署 | `curl worldcup.jtcao.space` → 不可达 | ❌ 部署丢失 |
| | `curl 26-worldcup-edge.vercel.app` → `DEPLOYMENT_NOT_FOUND` | ❌ 项目不存在 |
| DeepSeek API Key 待配置 | `echo $DEEPSEEK_API_KEY` → 空 | ❌ 同上 |
| Cron 2 个 | `cronjob list` → wc26-daily-update + WC26赛果自动更新 均活跃 | ✅ |
| 104 场比赛 | `wc2026_matches.json` matches 数组 = 104 | ✅ |
| 8 场已赛 | has_result=true 共 8 条，有真实比分 | ✅ 但预测字段为空 |
| 预测数据 | predictions 根键存在，但概率字段全空 `{}` | ❌ 需重跑管线 |
| 小组积分榜 | groups 13 组 | ✅ |

### 恢复 Step 3 — 理解后提问

基于扫描结果向用户提出 4 个候选方向：
1. 🔥 重跑预测管线 — 填充概率数据
2. 🌐 Vercel 重新部署 + 环境变量
3. 📊 已赛赛果→淘汰赛 bracket 更新
4. 📝 文档对齐

## 关键发现

1. **文档不等于现实** — HANDOFF 说"8场已赛"是对的，但说"预测引擎可用"是错的（概率为空）
2. **Vercel 部署可能因项目改名/删除而丢失** — 即使 git push 成功，如果 Vercel 项目被删了也不会自动部署
3. **Cron 任务独立于部署** — 即使 Vercel 挂了，Cron 仍然每天在跑（只是 push 到的网站看不到）
4. **恢复时至少验证 3 个维度**：Git 状态、API 可用性、关键数据完整性
