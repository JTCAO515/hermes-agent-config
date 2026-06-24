# 记忆导出工作流 — 迁移到其他 AI Agent

> 用途：将 Hermes Agent 的完整记忆（事实 + 推理链 + 行为宪章 + 工作流程 + Skills清单）导出为其他 AI Agent 可理解的格式。
> 触发场景：用户说"把记忆导出"、"同步到另一个 AI"、"迁移使用习惯"。

---

## 导出内容清单

| # | 内容 | 来源 | 价值 |
|---|------|------|------|
| 1 | 所有 L2 记忆条目（含推理链） | `memory` 工具 | 用户偏好/环境/项目/规则 |
| 2 | 用户 Profile 条目 | `memory(target='user')` | 用户背景/人际关系 |
| 3 | SOUL.md 核心摘要 | `~/.hermes/SOUL.md` | 行为宪章（价值排序/硬约束/失效判定） |
| 4 | AGENTS.md 核心摘要 | `~/.hermes/AGENTS.md` | 工作流/用户翻译层/编码规范 |
| 5 | Skills 清单 | `hermes skills list` | 能力参考，按需迁移 |
| 6 | 通信偏好/风格指南 | 综合以上 | 应对外部 AI Agent 的风格匹配 |

---

## 导出步骤

### Step 1: 收集记忆条目

```python
# 通过 memory tool 读取所有条目
# 工具返回的 entries 列表就是所有 L2 条目
# 注意：每个条目包含分类标签 [环境][规则][用户][项目][工具] + 推理链 【→推理: ...】

# 同时读取 user profile
memory(action='add', target='memory', content='[Status] 导出中...')
```

### Step 2: 收集系统文件

```bash
# 读取行为宪章和工作指南
cat ~/.hermes/SOUL.md
cat ~/.hermes/AGENTS.md
```

### Step 3: 获取 Skills 清单

```bash
hermes skills list
# 或直接从目录结构：ls ~/.hermes/skills/ | wc -l
```

### Step 4: 编写导出文档

输出格式：一份结构化 Markdown 文档，包含：

```
# Hermes Agent 记忆导出 — <用户名称>

> 导出时间: <timestamp>
> 用途: 迁移到其他 AI Agent 时同步使用习惯

## 第一部分：用户画像
- 基本身份（姓名/生日/城市/教育/经历/GitHub）
- 沟通风格
- 重要人际关系

## 第二部分：记忆系统完整转储
- L1 索引说明
- 分类表格：环境 / 规则 / 项目 / 工具 / 工作流

## 第三部分：行为宪章摘要
- 工作人格
- 价值排序
- 硬约束（C2/C3/C7/§7）
- 输出语言要求
- 第一性原理
- 禁止伪完成
- 失效判定

## 第四部分：工作流核心
- 用户翻译层原则
- 验证门禁

## 第五部分：Skills 清单
- 按类别列表

## 第六部分：导入建议
- 导入方式（System Prompt / SOUL.md 替换 / Memory 注入）
- 优先级排序
```

### Step 5: 打包交付

```bash
# 导出文档 + 原始 SOUL.md + AGENTS.md + Skills zip
cp ~/.hermes/SOUL.md /tmp/soul-export.md
cp ~/.hermes/AGENTS.md /tmp/agents-export.md
cd ~/.hermes/skills && tar -czf /tmp/skills-export.tar.gz \
  --exclude='node_modules' --exclude='__pycache__' --exclude='*.pyc' .
cd /tmp && tar -czf /tmp/hermes-full-export.tar.gz \
  memory-export.md soul-export.md agents-export.md skills-export.tar.gz
```

### Step 6: 文件移交

- Markdown 阅读版 → 直接发送（MEDIA: /tmp/memory-export.md）
- 完整存档包 → ZIP/TAR.GZ（MEDIA: /tmp/hermes-full-export.tar.gz）

---

## 导入建议（给接收方 AI Agent）

| 方式 | 做法 | 适用场景 |
|------|------|---------|
| System Prompt 注入 | 把导出文档整份塞进 System Prompt | 新 Agent 快速上手 |
| SOUL.md 替换 | 将 SOUL.md + AGENTS.md 放到对应目录 | 有 SOUL 支持的 Agent 平台 |
| Skills 部署 | 解压 skills 包到 skills 目录 | 需要完整能力 |
| 仅偏好同步 | 只读第1部分（用户画像）+ 第3部分（行为宪章） | 只想借用风格 |

---

## 注意

- 导出文档约 12-18KB（含 SOUL/AGENTS 完整内容）
- Skills 压缩包通常 10-15MB（取决于安装的技能数量，约200-300个）
- 不要导出 `.env` 或任何含 API Key 的文件
- SSH 私钥路径信息在导出时需要用替代描述
