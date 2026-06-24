# VisePanda v3.0 迭代实操记录

> 真实案例：某 AI 旅行规划项目的六方向并行迭代
> 方向：美观 → UI排版 → 知识库 → LLM Prompt → 主动提问 → 地图

## 迭代路线图

```
v2.x (当前)               v3.0 知识库+Prompt       v3.1 UI重构+地图         v3.2 美观收尾
  中国风UI (初版)     ──→   结构化旅行知识库     ──→    Landing/聊天重排版   ──→   动画过渡润色
  建筑剪影背景               LLM System Prompt     地图路线交互增强         颜色/字体微调
  红金配色                  主动提问机制           分享页改进                PWA优化
```

## 每次迭代启动前准备

```bash
# 1. 创建规划文件
mkdir -p docs
cat > docs/ITERATION_PLAN.md << 'EOF'
# v3.x 迭代规划

## In Scope
- [模块列表]

## Out of Scope
- [不做的]

## 已知跳过项（需人工）
| # | 项 | 原因 |
|---|-----|------|
EOF

# 2. 加载已有知识
# - 检查 docs/ITERATIONS.md 了解历史
# - 检查 docs/ROADMAP.md 了解路线图

# 3. 代码统计 baseline
find . -name '*.py' -o -name '*.js' | grep -v git | xargs wc -l
```

## Iter 1 示例：知识库 + Prompt（2026-05-25）

### 规划阶段
1. 确定知识范围：18 城市 + 100 景点 + 13 城美食 + 12 类贴士
2. 确定 Prompt 结构：主动提问 6 维度 + 知识注入 + 格式化输出
3. 并行创建 4 个知识文件 → 1 个 prompt 文件 → 集成到主应用

### 执行阶段
```
文件创建顺序：
data/knowledge/__init__.py
data/knowledge/cities.py        → 18 城市基本信息
data/knowledge/attractions.py   → 100+ 景点数据
data/knowledge/food.py          → 13 城市美食
data/knowledge/tips.py          → 12 类贴士
api/prompt.py                   → System Prompt + 主动提问逻辑
集成到 api/index.py              → 替换硬编码 SYSTEM_PROMPT
```

### 验证
```bash
python3 -c "from data.knowledge.cities import CITIES; print(f'{len(CITIES)} cities')"
python3 -c "from api.prompt import SYSTEM_PROMPT; print(f'{len(SYSTEM_PROMPT)} chars')"
python3 -c "import py_compile; py_compile.compile('api/index.py')"
```

### 提交
```bash
git add -A && git commit -m "v3.0: Knowledge base + Prompt engine" && git push
```

## Iter 2 示例：UI 重排 + 地图增强（2026-05-25）

### 规划
1. Landing 页：分类导航栏（全部/美食/历史/自然/都市）+ 8 卡布局 + 中文适配
2. Chat 页：中文欢迎语 + 中文 placeholder
3. Map：红色/金色色系 + POI 弹窗 + 路线箭头 + 天切换

### 关键操作
```python
# 重要：修改含 f-string + CSS/SVG 的 Python 文件时
# 用 Python heredoc 全文替换，不用 patch 工具
with open('api/index.py', 'r') as f:
    content = f.read()
# 在大块替换…
with open('api/index.py', 'w') as f:
    f.write(content)
```

### 验证
- `py_compile` 语法通过
- curl / browser 检查页面内容
- git push → Vercel 自动部署

## 已知跳过项模板

| # | 项 | 跳过原因 | 用户需配合 |
|---|-----|---------|-----------|
| S1 | Supabase DATABASE_URL | 需密码 | 提供 Supabase 数据库密码 |
| S2 | 阿里云短信 | 需 AccessKey | 提供阿里云短信 Key |
| S3 | Google OAuth 验证 | 需人工确认 | 在浏览器走一遍 OAuth 流程 |

## 统计方法

| 维度 | 包含 |
|------|------|
| 指令数 | 用户发送的消息数 |
| 部署数 | write_file + git commit + push 次数 |
| 文件变更 | `git diff --stat` 统计 |
| 代码行数 | `wc -l` 统计 |

---

## v3.0.1 Iter 3 补充案例：平行选项执行 + 知识注入Prompt

> 用户对「Option A: Prompt强化 / Option B: 前端美化」回应「两个都做」

### 平行执行模式

助手给出两个方向后，用户选择「两个都做」。与普通的「继续」不同——两个方向在**同一轮**内并行完成：
1. **A - Prompt强化**: 重写 `_build_system_prompt()`，注入36城知识库（food/hotels/tips数据分节），结构化行程输出引导，JS添加 `detectCity()` 自动检测用户输入
2. **B - 前端美化**: 城市卡片真实图片（8城），Hero漂浮装饰元素（🎋🏮☁️🎐🌸），Chat建议芯片，升级骨架屏，城市标签徽章

### 知识注入Prompt架构

```
用户输入 "3 days in Beijing"
    ↓
JS detectCity("3 days in Beijing") → "beijing"
    ↓ POST /api/chat {city: "beijing"}
API _build_system_prompt({"city": "beijing"})
    ↓
1. System Prompt身份 + 输出格式（Core Rules / Itinerary Format / Quick Recommendation Format）
2. 城市知识注入（Name CN / Province / Best Season / Days / Vibe / Keywords）
3. 美食知识注入（Must-eat Foods: 名称+描述+价格+⭐标记）
4. 酒店知识注入（Budget / Mid / Luxury 三档 + 区域建议）
5. 本地贴士注入（Local Tips）
6. 8城快速参考指南
    ↓
DeepSeek V4 Flash → 带具体知识点的结构化回答
```

### 图片自动检测模式

```
API自动检测 static/img/city-{name}.jpg 是否存在：
    os.path.exists("static/img/city-beijing.jpg") → True → 注入 image URL
    os.path.exists("static/img/city-shenzhen.jpg") → False → image = ""
```

前端 `createCityCard()` 用 `<img>` 标签加载背景图（支持懒加载 + 优雅降级），而非 CSS background-image：
```javascript
<img class="city-bg-img" src="${info.image}" loading="lazy" onerror="this.parentElement.classList.remove('has-img');this.remove()">
```

### 关键点
- 平行执行不等于大杂烩——每个方向独立成块，但全部验证通过后统一 git push
- 知识注入Prompt是结构化注入，不是简单拼接——每个数据域分节、加标题、格式化
- 图片用 `<img>` 而非 CSS background（懒加载 + onerror 降级）
