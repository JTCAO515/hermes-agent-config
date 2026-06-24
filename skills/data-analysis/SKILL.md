---
name: data-analysis
description: >
  数据分析：CSV/Excel 统计、透视、可视化、报告。触发词：数据分析/pandas/统计/透视/chart。
version: 1.0.0
---

# 数据分析

```bash
pip install pandas matplotlib seaborn openpyxl
```

## 流程
1. **加载**: `pd.read_csv/excel`
2. **清洗**: `dropna()`, `fillna()`, `astype()`
3. **分析**: `describe()`, `groupby()`, `pivot_table()`, `corr()`
4. **可视化**: `sns.barplot/heatmap`, `plt.plot`
5. **导出**: `to_excel/to_csv`

## 常用代码
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_excel('data.xlsx')
df.describe()
df.groupby('category')['value'].agg(['mean','sum','count'])
df.pivot_table(values='sales', index='month', columns='region', aggfunc='sum')
sns.barplot(data=df, x='category', y='value')
plt.savefig('chart.png')
df.to_excel('report.xlsx')
```
