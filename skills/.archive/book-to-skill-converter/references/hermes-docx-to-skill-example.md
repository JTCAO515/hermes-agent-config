# 实战：DOCX → Hermes Skill 转换示例（2026-06-16）

## 来源
用户发送文件 `pilotdeck-article.docx`（11,240 字中文文章），内容是 Hermes 记忆系统升级方案，借鉴自 PilotDeck 开源项目。

## 执行步骤

### 1. 接收文件
文件通过元宝平台发送，自动缓存到 `~/.hermes/cache/documents/doc_f88254f371b6_pilotdeck-article.docx`。

### 2. 提取文本
用 python-docx 提取纯文本：
```python
from docx import Document
doc = Document('/path/to/file.docx')
text = []
for p in doc.paragraphs:
    text.append(p.text)
full = '\n'.join(text)
```

### 3. 阅读全文
将全文导出到 `/tmp/pilotdeck-article.txt`，分两轮读完全文（370 行）。
识别出：
- 作者核心痛点（4 个问题）
- 系统架构图（三层架构：记忆层/路由层/进化层）
- 10 个核心模块（各有 Python 代码模板）
- 4 个 cron 任务配置
- 数据文件结构
- 4 个可直接复用的设计模式

### 4. 创建 Skill
命名：`hermes-memory-pilotdeck`
位置：`~/.hermes/skills/hermes-memory-pilotdeck/SKILL.md`
大小：12,529 字节
结构：
- 标准 Hermes frontmatter（name, version, description, triggers）
- 解决的问题表格（痛点 vs 表现 vs 解法）
- 系统架构 ASCII 图
- 10 个模块详细说明（含 Python 代码模板）
- Cron 配置表
- 数据文件结构树
- 4 个设计模式一览表

### 5. 验证
```bash
ls ~/.hermes/skills/hermes-memory-pilotdeck/SKILL.md  # ✅ 存在
hermes skills list | grep hermes-memory-pilotdeck       # ✅ enabled
```

## 关键决策

### 为什么不用 extract.py 管线？
virgiliojr94 版的 extract.py 输出是给 Copilot CLI / Amp / Claude Code 的格式（含 glossary/patterns/cheatsheet 等目录）。Hermes Agent 的 skill 只需要一个 SKILL.md — 更扁平、更直接。对于单篇文章（非书），手工萃取比跑管线更快、结果更精。

### 命名规则
避免与 apple-ouyang 的 `book-to-skill` 冲突，重命名为 `book-to-skill-converter`。

### 内容取舍
文章有大量 Python 代码模板 — 保留核心逻辑，去掉重复的 import 语句和 docstring，保持 SKILL.md 在 4,000 token 以内（实际 12,529 bytes ≈ ~3,100 tokens，可接受）。
