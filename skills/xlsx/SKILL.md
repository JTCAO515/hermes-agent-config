---
name: xlsx
description: >
  Excel/CSV 数据处理与生成。触发词：Excel/xlsx/表格/导出excel/csv/数据表。
version: 1.0.0
---

# Excel/CSV 数据处理

```bash
pip install openpyxl pandas
```

## 创建 Excel
```python
from openpyxl import Workbook
wb = Workbook(); ws = wb.active
ws['A1'] = '名称'; ws['B1'] = '价格'
ws.append(['酒店A', 1200])
wb.save('output.xlsx')
```

## 读取/处理 CSV
```python
import pandas as pd
df = pd.read_csv('data.csv')
df.groupby('城市')['价格'].mean()  # 透视
df.to_excel('output.xlsx', index=False)
```

## 常用
- 合并单元格: `ws.merge_cells('A1:D1')`
- 样式: `Font(bold=True)`, `PatternFill`, `Border`
- 图表: `openpyxl.chart.BarChart`
- 公式: `ws['C1'] = '=SUM(A1:B1)'`
- 多Sheet: `wb.create_sheet('Sheet2')`

## Headless / Managed-Agent Mode

When producing a .xlsx file on disk without a live Office app, use openpyxl with these conventions:

- Write to `./out/<name>.xlsx`. Create `./out/` if needed.
- Return the relative path in your final message.
- **Blue/black/green.** Blue = hardcoded input, black = formula, green = link to another sheet/file.
- **No hardcodes in calc cells.** Every calculation cell is a formula; inputs live on an Inputs tab.
- **Named ranges** for any value referenced from a deck or memo.
- **Balance checks.** Include a Checks tab that ties and surfaces TRUE/FALSE.
- **One model per file.** Do not append to an existing workbook unless explicitly asked.
