# PNG → SVG 矢量转换（Image-to-SVG）

> 将 AI 生成的 PNG logo/图标转换为可缩放的矢量 SVG。适用于品牌 logo、图标、简单插图的矢量化。

## 概述

使用 **potrace**（位图→矢量追踪引擎）+ **Python PIL/numpy**（颜色分层）实现多层矢量转换。

### 安装

```bash
sudo apt-get install -y potrace
# Python 依赖（通常在 Hermes Agent venv 中已可用）
pip3 install pillow numpy
```

## 工作流

### 第 1 步：颜色分层

AI 生成的图像通常包含多个颜色区域（主体填充、色调线条、背景）。需要按颜色分离成不同图层，分别追踪。

```python
from PIL import Image, ImageFilter
import numpy as np

img = Image.open('/tmp/input.png').convert('RGB')
arr = np.array(img)

# 提取暗色区域（主体轮廓）
dark = (np.mean(arr.astype(float), axis=2) < 100) * 255
Image.fromarray(dark.astype(np.uint8), 'L').save('/tmp/layer_dark.pbm')

# 提取青色/高亮区域
r, g, b = arr[:,:,0].astype(float), arr[:,:,1].astype(float), arr[:,:,2].astype(float)
cyan = ((g > 150) & (b > 150) & (r < 100)) * 255
Image.fromarray(cyan.astype(np.uint8), 'L').save('/tmp/layer_cyan.pbm')

# 边缘检测（线条艺术风格）
gray = img.convert('L')
edges = gray.filter(ImageFilter.FIND_EDGES)
edge_bw = (np.array(edges) > 60) * 255
Image.fromarray(edge_bw.astype(np.uint8), 'L').save('/tmp/layer_edges.pbm')
```

### 第 2 步：potrace 追踪

```bash
# -s 输出 SVG
# --turdsize <N> 清除噪点（N 越大过滤越多）
# -a <N> 转角容忍度
potrace -s --turdsize 20 -o /tmp/trace_dark.svg /tmp/layer_dark.pbm
potrace -s -o /tmp/trace_cyan.svg /tmp/layer_cyan.pbm
```

### 第 3 步：合并为彩色 SVG

potrace 输出的 SVG 使用 `translate(0, H) scale(0.1, -0.1)` 坐标变换。合并时需要保持此变换。

```python
# 构建最终 SVG
svg_parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">',
    '  <g transform="translate(0,1024) scale(0.1,-0.1)" fill="#000000" stroke="none">',
    dark_paths_here,
    '  </g>',
    '  <g transform="translate(0,1024) scale(0.1,-0.1)" fill="#00CED1" stroke="none">',
    cyan_paths_here,
    '  </g>',
    '</svg>'
]
```

### 第 4 步：过滤背景矩形

potrace 的 `-s` 模式有时会包含一个覆盖全画布的背景矩形路径（`M0 0 ... 5120 -5120`）。必须在合并前移除。

**检测条件：** 路径以 `M0 ` 开头且包含大坐标绝对值（如 `5120 -5120`）。

## 参数调优

| 参数 | 效果 |
|------|------|
| `--turdsize 20` | 清除小于 20px 的噪点。值越大越简洁 |
| `--alphamax 1` | 优化曲线平滑度。默认 1，值越大转角越圆 |
| `--opttolerance 0.2` | 优化容差。越小越保真 |
| `--longcurve` | 保持长曲线不分段（更流畅） |

## 颜色分层策略

| 提取方式 | 适用场景 | 代码 |
|---------|---------|------|
| 亮度阈值 | 暗色主体/轮廓 | `np.mean(arr, axis=2) < threshold` |
| 颜色通道 | 纯色 accent 元素 | `(R < r_th) & (G > g_th) & (B > b_th)` |
| 边缘检测 | 线稿风格 | `ImageFilter.FIND_EDGES` + 阈值 |
| 色相范围 | 特定颜色区域 | `rgb_to_hsv(arr)` + 色相区间筛选 |

## 已知问题

- potrace 追踪实心面积的轮廓会生成**大而精确**的路径，文件较大（10-20KB 对 1024×1024 图）。如需要更小文件，可先用 PIL 缩小图像再用 potrace
- 检测到的边缘可能产生**双重轮廓**（路径内外各一圈）。可通过形态学腐蚀/膨胀预处理减少
- potrace 不支持渐变——矢量输出是纯色填充。需要渐变效果则用 SVG `<defs><linearGradient>` 手动添加

## 替代方案

| 工具 | 安装 | 特点 |
|------|------|------|
| **potrace** | `apt install potrace` | 成熟可靠，命令行，轻量 |
| **vtracer** | `pip install vtracer` | Rust 实现，支持彩色自动分层，效果更好但安装更复杂 |
| **ImageMagick trace** | `convert input.png -trace output.svg` | 集成度高但质量一般 |
| **AutoTrace** | `apt install autotrace` | 类似 potrace 的备选 |
