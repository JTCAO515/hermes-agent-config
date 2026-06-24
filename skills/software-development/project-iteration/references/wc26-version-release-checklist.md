# WC26 版本发布重命名清单

## 命名规范

**格式**：`26年世界杯预测v{版本号} - JTCao出品`

示例：
- v3.0 → `26年世界杯预测v3.0 - JTCao出品`
- v3.1 → `26年世界杯预测v3.1 - JTCao出品`

> 来源：用户 2026-06-14 明确指定此命名格式，【版本号】= git 版本号

---

## 必须更新的 10 个位置

每发布一个 WC26 大版本，必须一一扫描以下位置并更新：

### 1. HTML `<title>` 标签

**文件**：`web/index.html`

```html
<title>26年世界杯预测v3.0 - JTCao出品</title>
```

### 2. 导航栏标题（.nav-title）

```html
<span class="nav-title">26年世界杯预测v3.0</span>
```

### 3. 导航栏版本徽章（.nav-badge）

```html
<span class="nav-badge" style="color:var(--accent)">v3.0</span>
```

如果旧版本徽章不存在，添加一个新条目：
```html
<span class="nav-badge">双变量泊松</span>
<span class="nav-badge" style="color:var(--accent)">v3.0</span>
```

### 4. 加载文字（.loading-text）

```html
<p class="loading-text">26年世界杯预测v3.0 · JTCao出品</p>
```

### 5. 页脚版权文字

```html
<p>数据源: Polymarket 预测市场 · 模型: 双变量泊松 + 赔率去水 + 时间门控 · JTCao出品</p>
```

### 6. manifest.json（PWA 配置）

| 字段 | 值 |
|------|-----|
| `name` | `26年世界杯预测v3.0` |
| `short_name` | `WC26 v3.0` |
| `description` | `2026世界杯预测平台 — 双变量泊松模型 + Polymarket赔率 — JTCao出品` |

### 7. README.md

- 标题改为新版本号：`# 26 World Cup Edge Lab · v3.0`
- 更新「最新版本 v3.0」表格中的完成状态
- 检查所有版本号引用是否正确

### 8. PLAN.md

- 新增 Iteration 条目（如 Iteration 7 v3.0）
- 包含：本迭代完成的模块、数据亮点、前端/后端/数据维度说明
- 更新「当前项目状态」表格中的版本号和统计

### 9. PRD_PRODUCT_ANALYSIS.md

- 更新「交货清单」表格中本迭代完成项的状态（标注 `✅ v3.0 完成`）
- 检查新增 API 端点、前端功能、数据源是否在清单中有对应项，无则新增行

### 10. git commit

全部改动完成后：
```bash
git add -A
git commit -m "rename: 网页名称改为'26年世界杯预测v3.0 - JTCao出品'"
git push origin master
```

---

## 执行顺序

```
1. HTML title  + nav-title + 版本徽章          ← 肉眼最明显的改动，最先改
2. loading-text + footer                        ← 次要显示区域
3. manifest.json                                ← PWA 一致性
4. README.md                                    ← 版本文档
5. PLAN.md                                      ← 迭代路线图
6. PRD_PRODUCT_ANALYSIS.md                      ← 交付清单
7. git add + commit + push                      ← 一次性推送
8. 等待 Vercel 部署（~20s）
9. curl 验证首页 200
```

---

## 验证

```bash
# 验证 HTML 中的版本号
grep -n "v3.0\|JTCao" web/index.html

# 验证 manifest
grep -n "v3.0\|JTCao" web/manifest.json

# 验证文档
grep -c "v3.0" README.md PLAN.md PRD_PRODUCT_ANALYSIS.md

# 部署验证
curl -s -o /dev/null -w "%{http_code}" "https://worldcup.jtcao.space/"
# 应为 200
```
