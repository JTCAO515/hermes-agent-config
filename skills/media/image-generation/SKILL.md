---
name: image-generation
version: 2.0.0
description: |
  AI image generation and vectorization pipeline. Defaults:
  🎨 **生图** → Seedream 5.0 (Volcengine/Doubao, 0.22元/张)
  👁️ **图片识别** → Doubao-Seed-2.0-Lite VLM (Volcengine, 0.2元/百万输入)
  Also supports Gemini/NUWA/LemonData APIs + potrace SVG conversion.
triggers:
  - "生成图片"
  - "AI 绘图"
  - "画图"
  - "转矢量图"
  - "SVG"
  - "LOGO"
  - "图标"
  - "nano banana"
  - "gemini 画图"
  - "透明背景"
  - "seedream"
  - "豆包画图"
  - "火山引擎"
  - "VLM"
  - "图片识别"
  - "看图"
  - "视觉理解"
  - "批量生成"
  - "batch"
  - "城市图片"
  - "批量配图"
mutating: false
---

# Image Generation — AI Generation + Vectorization

> Umbrella skill. **默认配置：**
> - 🎨 **生图** → Seedream 5.0 (Method D) — 0.22元/张
> - 👁️ **图片识别** → Doubao-Seed-2.0-Lite VLM (Method E) — 0.2元/百万输入tokens
> - 📐 **SVG转化** → potrace (Section B)
>
> Absorbed: `nano-banana-pro` (generation) and `image-to-vector` (SVG conversion) — archived 2026-06-02.

Two-phase pipeline: (A) generate images via NUWA/LemonData APIs, (B) convert raster to SVG via potrace.

---

## Section A: Image Generation (Nano Banana Pro)

### Prerequisites

API Key config in `~/.hermes/.nanobanana`:
```bash
NUWA_API_KEY=sk-xxxxxxxx
GEMINI_API_KEY=AIzaSy...           # Google official API Key (fallback)
LEMONDATA_API_KEY=ld-xxxxxxxx      # LemonData API Key
```

Get keys:
- NUWA: https://nuwaapi.com → Register → API Key Management
- LemonData: https://www.lemondata.cc → Register → API Key Management

### Method A: LemonData API (recommended, China-accessible)

Uses async task mode:

```bash
# 1. Submit task
TASK_RESPONSE=$(curl -s -X POST "https://api.lemondata.cc/v1/images/generations" \
  -H "Authorization: Bearer $LEMONDATA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano-banana-pro",
    "prompt": "PROMPT",
    "n": 1,
    "operation": "text-to-image",
    "aspect_ratio": "9:16",
    "resolution": "2k"
  }')

# 2. Extract task_id
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")

# 3. Poll until complete
sleep 10
RESULT=$(curl -s "https://api.lemondata.cc/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $LEMONDATA_API_KEY")
```

**Parameters:**
- `model`: `nano-banana-pro`, `nano-banana`, `nano-banana-2`, `gpt-image-2`, `flux-pro`
- `aspect_ratio`: 1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9, 21:9
- `resolution`: 1k, 2k, 4k

### Method B: NUWA API (gpt-image-2, synchronous)

```bash
curl -s -X POST "https://api.nuwaflux.com/v1/images/generations" \
  -H "Authorization: Bearer $NUWA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "PROMPT",
    "n": 1,
    "size": "1024x1024"
  }'
# Returns data[0].b64_json (base64 PNG)
```

**Note:** `gpt-image-2` is good for flat vector logos, icons, brand elements (not photorealistic). 1024x1024 works best.

### Method C: Google Official GenAI SDK (requires VPN/proxy)

```python
from google import genai
from google.genai import types
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)
```

### Method D: 🔥 Volcengine Seedream 5.0 (⭐ 默认生图 | China-accessible)

**豆包 Seedream 5.0** — 火山引擎文生图模型，国内直连，质量优秀。OpenAI 兼容接口。

**Parameters:**
| Parameter | Value | Notes |
|-----------|-------|-------|
| endpoint | `https://ark.cn-beijing.volces.com/api/v3/images/generations` | OpenAI-compatible |
| model | `doubao-seedream-5-0-260128` | Latest Seedream 5.0 |
| min size | 3,686,400 pixels | e.g. 1920×1920, 2048×2048 |
| auth | `VOLCENGINE_API_KEY` in `.env` | Bearer token |

```bash
# Synchronous — returns URL directly
RESPONSE=$(curl -s --max-time 90 -X POST "$VOLCENGINE_BASE_URL/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VOLCENGINE_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "PROMPT",
    "n": 1,
    "size": "1920x1920"
  }')

# Extract image URL
IMAGE_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])")

# Download
curl -s -o output.jpg "$IMAGE_URL"
```

**Python (PIL passthrough):**
```python
import requests, json
resp = requests.post(
    "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    headers={"Authorization": "Bearer VOLCENGINE_API_KEY", "Content-Type": "application/json"},
    json={"model": "doubao-seedream-5-0-260128", "prompt": prompt, "n": 1, "size": "1920x1920"}
)
url = resp.json()["data"][0]["url"]
# Download
img_data = requests.get(url).content
with open("output.jpg", "wb") as f:
    f.write(img_data)
```

**Pitfalls:**
- Minimum image size: 3,686,400 pixels (1920×1920 or equivalent)
- URL expires in 24 hours — download immediately
- 14400 output tokens per image (billing)
- No base64 return — always URL

---

### Method E: 🔥 Volcengine Doubao VLM (⭐ 默认图片识别)

**豆包视觉语言模型** — 图片理解、内容分析。通过 chat completions endpoint 调用，与 Seedream 同一条 Key。

**Parameters:**
| Parameter | Lite (推荐) | Pro |
|-----------|------------|-----|
| model | `doubao-seed-2-0-lite-260215` | `doubao-seed-2-0-pro-260215` |
| 输入价格 | **0.2 元/百万 tokens** | 3.2 元/百万 tokens |
| 输出价格 | **2 元/百万 tokens** | 16 元/百万 tokens |

**Usage:**
```bash
# Encode image to base64
B64=$(base64 image.jpg | tr -d '\n')

# Call VLM
curl -s --max-time 90 -X POST "$VOLCENGINE_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VOLCENGINE_API_KEY" \
  -d "{
    \"model\": \"doubao-seed-2-0-lite-260215\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": [
          {\"type\": \"text\", \"text\": \"详细描述这张图片\"},
          {\"type\": \"image_url\", \"image_url\": {\"url\": \"data:image/jpeg;base64,$B64\"}}
        ]
      }
    ],
    \"max_tokens\": 500
  }"
```

**Python:**
```python
import requests, base64, json

with open("image.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

resp = requests.post(
    "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    headers={"Authorization": f"Bearer {VOLCENGINE_API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "doubao-seed-2-0-lite-260215",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        "max_tokens": 500
    }
)
print(resp.json()["choices"][0]["message"]["content"])
```

**Pitfalls:**
- Image size: keep under 512×512 for speed (tested: 256px works well, ~7KB base64)
- Large images (~156KB base64 for 1920x1920) can cause timeout — resize first
- Both Lite and Pro support image input via chat completions endpoint
- The model also outputs `reasoning_content` (思考链) — not always needed

### LOGO Prompt Tips

| Goal | Keywords |
|------|----------|
| Flat minimalist | flat minimalist vector design, pure solid flat colors no gradients |
| Line art | pure line art, only simple clean contour lines, no filled areas |
| Cyberpunk | cyberpunk tech style, bright cyan/neon accents, circuit board traces |
| Enterprise logo | simple flat silhouette like modern app icon, vector quality |

### Troubleshooting

- **401 Invalid Token**: Key may need activation on console. NUWA uses `Authorization: sk-xxx` (no Bearer prefix).
- **China direct access**: NUWA `api.nuwaapi.com` works from Tencent Cloud directly.
- **Google SDK blocked in China**: Use LemonData as fallback.

---

## Section F: Batch Image Generation (批量生图)

Use when you need to generate a large set of images (e.g., missing city photos, product shots, avatars). Pattern: associative array of prompts + loop + rate limiting.

### Seedream Batch Pattern (bash)

```bash
declare -A ITEMS
ITEMS[key1]="Prompt description for item 1"
ITEMS[key2]="Prompt description for item 2"

for key in "${!ITEMS[@]}"; do
    prompt="${ITEMS[$key]}"
    outfile="/path/to/output/${key}.jpg"

    response=$(curl -s --max-time 120 -X POST "$VOLCENGINE_BASE_URL/images/generations" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $VOLCENGINE_API_KEY" \
        -d "{
            \"model\": \"doubao-seedream-5-0-260128\",
            \"prompt\": \"${prompt}\",
            \"n\": 1,
            \"size\": \"1920x1920\"
        }")

    url=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])" 2>/dev/null || echo "ERROR")

    if [ "$url" = "ERROR" ]; then
        echo "FAILED: $(echo $response | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','unknown'))" 2>/dev/null)"
        continue
    fi

    curl -s -o "$outfile" --max-time 60 "$url"
    echo "Saved: $(basename $outfile)"
    sleep 5  # rate limit
done
```

### Key Pitfalls

- **Rate limiting**: Seedream API allows ~1 request per 3-5 seconds. Always add `sleep 5` between calls.
- **URL expiry**: Image URLs expire in 24 hours — download immediately in the same script.
- **Min size**: 1920×1920 minimum (or equivalent pixel count). 1024×1024 will fail with size error.
- **Failed generations**: Some prompts may hit content filters. Always check for `error` in the response and `continue` on failure rather than aborting the batch.
- **Token limits**: 14400 output tokens per image — batch of 10 images = 144K output tokens. Budget ~0.22元/张.

### Prompt Design for Travel/Location Images

For realistic travel destination photos, use this pattern:

```
"CityName Region, landmark/feature description, atmospheric condition, quality indicator"
```

Examples:
- `"Guiyang China, city skyline with karst mountains, modern cityscape surrounded by green hills, sunny day"`
- `"Jiuzhaigou National Park China, turquoise blue lakes, colorful autumn forest, waterfalls, snow-capped mountains"`

Tips:
- Always include the country name + region for geographic accuracy
- Specify atmosphere (sunny/misty/sunset) for visual variety
- Keep under 100 chars — longer prompts reduce image quality
- No people in frame (avoids content filter issues)

### Reference Script

`scripts/batch-generate.sh` — reusable batch generation script template with error handling and rate limiting.

---

## Section B: Raster to SVG (Vectorization)

### Prerequisites

```bash
sudo apt-get install -y potrace
pip install Pillow numpy
```

### Basic Pipeline

```python
from PIL import Image
import numpy as np

img = Image.open('input.png').convert('L')
bw = (np.array(img) > 128) * 255
Image.fromarray(bw.astype(np.uint8), 'L').save('/tmp/input.pbm')

import subprocess
subprocess.run(['potrace', '-s', '-o', 'output.svg', '/tmp/input.pbm'])
```

### Key potrace Parameters

| Parameter | Purpose | Default | Logo Recommendation |
|-----------|---------|---------|-------------------|
| `--turdsize N` | Ignore noise < N px | 2 | 10-20 |
| `--alphamax N` | Curve smoothness (0-1) | 1 | 1 |

### Coordinate System

potrace output default transform: `translate(0,H) scale(0.1,-0.1)` where H = image height. **Must preserve** this transform.

### Color Layer Separation

potrace only outputs single-color SVG. For multi-color images:

```python
r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
cyan_mask = ((g > 150) & (b > 150) & (r < 100)) * 255
dark_mask = (np.mean(arr, axis=2) < 100) * 255
```

Run potrace per layer, then merge into same SVG with different `<g>` tags:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <g transform="..." fill="#000000" stroke="none"><!-- paths --></g>
  <g transform="..." fill="#00CED1" stroke="none"><!-- accent paths --></g>
</svg>
```

### Background Rectangle Filtering

potrace traces the image boundary as a full-canvas path. Filter it:

```python
def is_background_rect(d):
    return d.startswith('M0 ') or '5120 -5120' in d or 'l0 -5120' in d
```

### Transparent Background PNG

Use flood fill from image corners:

```python
# Sample background color from corners
# Flood fill connected background region
# Set alpha = 0 for background, 255 for foreground
```

### Reference Script

`references/svg-layer-merge.py` — full pipeline script (generation → layer separation → potrace → SVG merge → transparent background).

### Format Selection

| Scenario | Format | Reason |
|----------|--------|--------|
| WeChat preview | PNG | WeChat doesn't support SVG preview |
| Website logo | SVG | Scalable, lightweight (~12KB vs PNG ~800KB) |
| Print material | SVG → PDF | Vector lossless |
| App icon | PNG (1024x1024) | Platform adaptation needed |
