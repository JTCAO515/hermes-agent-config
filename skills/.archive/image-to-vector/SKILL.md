---
name: image-to-vector
description: AI 图像生成 + 位图转矢量 (SVG) 管线。支持通过 NUWA API (gpt-image-2) 生成图像，使用 potrace 将栅格图转换为矢量 SVG，多层合并、背景移除。适用于 LOGO 设计、品牌图标、印刷物料等需要矢量化输出的场景。
version: 1.0.0
---

# 图像生成与矢量化管线

> 从 AI 图像生成到矢量 SVG 的完整工作流，附带 LOGO 迭代最佳实践。

## 触发条件

- 「生成 LOGO/图标/图案」
- 「转成矢量图 / SVG」
- 「透明背景」
- 「线稿/线条风格」

## 管线概览

```
AI 图像生成 (NUWA gpt-image-2) 
  → PNG 下载 (base64 解码)
  → 位图预处理 (阈值/边缘检测)
  → potrace 矢量化 (SVG)
  → SVG 清理 (移除背景矩形 / 多层合并)
  → [可选] 透明背景 PNG / 最终 SVG
```

---

## 阶段 1：AI 图像生成

### API 配置 (NUWA 中转)

```bash
BASE_URL=https://api.nuwaflux.com/v1
API_KEY=$NUWA_API_KEY  # 环境变量中
```

### 支持的图像模型

```bash
gpt-image-2    # 主力图像生成模型，OpenAI 兼容接口
gpt-image-1    # 旧版
gemini-2.5-flash-image  # Gemini 图片模型
gemini-3-pro-image-preview
```

### 调用方式

```bash
curl -s $BASE_URL/images/generations \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "...",
    "n": 1,
    "size": "1024x1024"
  }'
```

**注意**：响应中 `b64_json` 字段包含 base64 编码的 PNG，**不是 URL**。需要用 Python 解码保存。

### Prompt 技巧（LOGO 场景）

| 目标 | Prompt 关键词 |
|------|-------------|
| 扁平极简 | flat minimalist vector design, pure solid flat colors no gradients, clean crisp geometric lines |
| 线条风格 | pure line art, only simple clean contour lines, no filled areas, thin outline strokes |
| 赛博/科技感 | cyberpunk tech style, bright cyan/neon accents, circuit board trace patterns, dark background |
| Swag/叛逆 | cocky half-smirk, one eyebrow raised, tilted slightly, sideways visor/goggles, cool attitude |
| 企业 LOGO | simple flat silhouette like modern app icon or brand logo, vector quality, sharp clean edges |

### 保存为 PNG

```python
import json, base64
resp = json.loads(response_text)
b64 = resp['data'][0]['b64_json']
with open('output.png', 'wb') as f:
    f.write(base64.b64decode(b64))
```

---

## 阶段 2：位图 → SVG 转换 (potrace)

### 安装

```bash
sudo apt-get install -y potrace
```

### 基本流程

```python
from PIL import Image
import numpy as np

img = Image.open('input.png').convert('L')  # 灰度
# 二值化 (调整阈值控制细节)
bw = (np.array(img) > 128) * 255
Image.fromarray(bw.astype(np.uint8), 'L').save('/tmp/input.pbm')

import subprocess
subprocess.run(['potrace', '-s', '-o', 'output.svg', '/tmp/input.pbm'])
```

### 关键参数

- `-s` : 输出 SVG 格式
- `--turdsize N` : 忽略小于 N 像素的杂点 (默认 2，LOGO 场景建议 10-20)
- `--alphamax N` : 曲线平滑度 (0-1，默认 1)
- `-b` : 指定背景颜色

### potrace SVG 的坐标系

potrace 输出默认坐标变换为 `translate(0,H) scale(0.1,-0.1)`，其中 H 为输入图片高度。**必须保留**这个 transform，否则路径坐标不匹配 viewBox。

路径中的 `c` 命令是三次贝塞尔曲线 (cubic bezier)，是标准 SVG 格式。

---

## 阶段 3：SVG 清理与多层合并

### potrace 输出的问题

1. **背景矩形**：potrace 会把图像边界之外的空白区域也追迹为一个全画布矩形路径。必须手动过滤。

2. **单层单色**：potrace 只输出单色 SVG。彩色图像需要按颜色分层后分别追迹再合并。

### 颜色分层法

```python
# 提取特定颜色通道
r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
cyan_mask = ((g > 150) & (b > 150) & (r < 100)) * 255
dark_mask = (np.mean(arr, axis=2) < 100) * 255
edge_mask = (edge_detected > threshold) * 255
```

对每层分别执行 potrace，然后合并到同一个 SVG 文件的不同 `<g>` 中。

### 过滤背景矩形

```python
def is_background_rect(d):
    return d.startswith('M0 ') or '5120 -5120' in d or 'l0 -5120' in d
```

### 合并 SVG 示例

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <g transform="translate(0,1024) scale(0.1,-0.1)" fill="#000000" stroke="none">
    <!-- dark layer paths -->
  </g>
  <g transform="translate(0,1024) scale(0.1,-0.1)" fill="#00CED1" stroke="none">
    <!-- accent layer paths (filtered, no background rect) -->
  </g>
</svg>
```

---

## 阶段 4：透明背景 PNG

### 背景颜色估计

从图像四个角采样确定背景色。

```python
bg_sample = arr[0:5, 0:5].mean(axis=(0,1))  # Top-left corner
```

### 泛洪填充法 (推荐)

从边缘种子点向外填充连通的背景区域。对深色/纯色背景效果最好。

```python
from collections import deque
import numpy as np

h, w = arr.shape[:2]
visited = np.zeros((h, w), dtype=bool)
q = deque()

def is_bg(y, x, bg_color, threshold=30):
    return np.max(np.abs(arr[y,x].astype(float) - bg_color)) < threshold

# 从四边种子
for y in range(h):
    for x in [0, w-1]:
        if not visited[y,x] and is_bg(y,x, bg_color):
            visited[y,x] = True; q.append((y,x))
for x in range(1, w-1):
    for y in [0, h-1]:
        if not visited[y,x] and is_bg(y,x, bg_color):
            visited[y,x] = True; q.append((y,x))

while q:
    y, x = q.popleft()
    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
        ny, nx = y+dy, x+dx
        if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
            if is_bg(ny, nx, bg_color, threshold=25):
                visited[ny, nx] = True
                q.append((ny, nx))

alpha = np.where(visited, 0, 255).astype(np.uint8)
rgba = np.dstack([arr, alpha])
Image.fromarray(rgba, 'RGBA').save('output_transparent.png')
```

### 简单阈值法 (快速但不精确)

```python
bg_mean = np.array([15, 15, 20])  # 估计的背景色
dist = np.max(np.abs(arr.astype(float) - bg_mean), axis=2)
alpha = np.where(dist < 35, 0, 255).astype(np.uint8)
```

---

## LOGO 迭代工作流 (经验总结)

### 典型迭代路径

1. **第 1 轮**：全彩写实 → 确认构图和方向
2. **第 2 轮**：扁平矢量风（solid color, no gradient）
3. **第 3 轮**：纯线条极简（black lines on white, no fill）
4. **矢量转换**：potrace → SVG 合并 → 透明背景

### Prompt 迭代技巧

- 每一轮只改变 **1-2 个变量**，不要同时改构图+风格+颜色
- 用户说「更XXX」时，把 XXX 参数化加到 prompt 开头
- 用 `flat minimalist vector design` + `no gradients no shading` 控制扁平程度
- 用 `pure line art` / `only outline strokes` / `no filled areas` 走向线稿

### 图片格式选择

| 场景 | 推荐格式 | 原因 |
|------|---------|------|
| 微信预览 | PNG | 微信不支持 SVG 预览 |
| 网站 LOGO | SVG | 可缩放、轻量（~12KB vs PNG ~800KB）|
| 印刷物料 | SVG → PDF | 矢量无损 |
| App 图标 | PNG (1024x1024) | 需各平台适配 |

---

## 注意事项

### ⚠️ NUWA API 限制

- 图像模型 `gpt-image-2` 返回 base64 而非 URL
- 调用时注意 `n` 参数只支持 1（目前）
- `size` 参数支持 1024x1024
- API key 需要通过 `NUWA_API_KEY` 环境变量获取，base URL 为 `https://api.nuwaflux.com/v1`

### ⚠️ potrace 局限性

- 只输出单色（黑白）SVG
- 彩色图像需手动分层 → 分别追迹 → 合并
- 过小的细节会被 `--turdsize` 过滤掉
- 不支持渐变/透明度（这些需要手动在 SVG 中添加）

### ⚠️ 矢量转换的质量

- potrace 转换的 SVG 路径可能包含大量贝塞尔曲线节点，不适合手工编辑
- 如果需要可编辑的 SVG（如 Adobe Illustrator），建议用 Adobe Illustrator 的「图像描摹」功能获得更好的效果
- potrace 适合「快速生成可用矢量」而非「高质量可编辑矢量」

## 参考文件

- `references/svg-layer-merge.py` — 完整管线 Python 脚本（生成 → 分层 → potrace → SVG 合并 → 透明背景），可复制修改后直接运行

  快速使用：
  ```bash
  # 从 prompt 生成:
  python references/svg-layer-merge.py --prompt "A minimalist panda logo..." --output mylogo

  # 从已有 PNG:
  python references/svg-layer-merge.py --input input.png --output mylogo
  ```

- Pi4/WeChat 环境的 NUWA API 配置细节（见 memory 与 env var `NUWA_API_KEY`）
