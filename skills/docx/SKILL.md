---
name: docx
description: >
  创建/编辑 Word 文档，含格式、表格、图片、页眉页脚。触发词：Word/docx/报告/合同。
version: 1.0.0
---

# Word 文档创建与编辑

```bash
pip install python-docx  # 安装
```

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor

doc = Document()
doc.add_heading('标题', level=1)
doc.add_paragraph('正文。').add_run('加粗。').bold = True
table = doc.add_table(rows=3, cols=4); table.style = 'Light Grid Accent 1'
doc.add_picture('img.png', width=Inches(4))
doc.save('output.docx')
```

常用：字体/字号/颜色、表格合并、页眉页脚、分页、有序列表、模板替换({{var}})。
