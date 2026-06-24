---
name: markitdown
description: "MarkItDown — 微软文件转Markdown工具。将PDF/Word/Excel/PPT/图片/音频等格式转换为Markdown"
version: 1.0.0
source: https://github.com/microsoft/markitdown
triggers:
  - markitdown
  - 转换文档
  - 转markdown
  - 文件转md
  - convert to markdown
---

# MarkItDown — 文件转Markdown

## 简介

MarkItDown 是微软开源的 Python 工具，将各种文件格式转换为 Markdown，专为 LLM 使用优化。

## 安装

```bash
pip install 'markitdown[all]'
```

## 使用方式

### 命令行

```bash
# 基本用法
markitdown 输入文件.pdf > 输出.md

# 指定输出文件
markitdown 输入文件.docx -o 输出.md

# 管道
cat 文件.pptx | markitdown
```

### Python API

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("文件.pdf")
print(result.text_content)
```

## 支持格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| PDF | .pdf | 文本PDF |
| Word | .docx | 完整保留结构 |
| PowerPoint | .pptx | 含幻灯片备注 |
| Excel | .xlsx, .xls | 含表格 |
| HTML | .htm, .html | - |
| 图片 | .jpg, .png, .gif | 需LLM Vision插件 |
| 音频 | .mp3, .wav | 需转录插件 |
| 文本 | .txt, .csv, .json, .xml, .md | - |
| Outlook | .msg | - |

## 可选依赖安装

```bash
# 最小安装（仅常用格式）
pip install 'markitdown[pdf,docx,pptx,xlsx]'

# 全功能
pip install 'markitdown[all]'
```
