---
name: nano-banana-pro
description: >
  Nano Banana Pro (Gemini 图片生成) 通过 NUWA API。
  触发词：nano banana / 生成图片 / AI 绘图 / 香蕉生成 / gemini 画图。
version: 2.1.0
---

# Nano Banana Pro — AI 图片生成

通过 NUWA API 或 LemonData API 调用 Gemini 图片生成（国内直连）。

## 前置条件

API Key 配置 `~/.hermes/.nanobanana`：
```
NUWA_API_KEY=sk-xxxxxxxx
GEMINI_API_KEY=AIzaSy...           # Google 官方 API Key（备选）
```

获取 Key：
- NUWA: https://nuwaapi.com → 注册 → API Key 管理
- LemonData: https://www.lemondata.cc → 注册 → API Key 管理

## 连通性验证（必须先做）

### NUWA

```bash
curl -s -w "\nHTTP %{http_code}" \
  "https://api.nuwaapi.com/v1/chat/completions" \
  -H "Authorization: $NUWA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

期望 HTTP 200。若返回 `401 Invalid Token` → 可能 Key 已过期，换 LemonData。

### LemonData

```bash
curl -s -w "\nHTTP %{http_code}" \
  "https://api.lemondata.cc/v1/chat/completions" \
  -H "Authorization: Bearer $LEMONDATA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

期望 HTTP 200。LemonData 用 `Bearer` 前缀认证。

---

## 图片生成流程

### 方式 A：LemonData `/v1/images/generations`（推荐，已验证可用）

LemonData 上的 nano-banana-pro 使用**异步任务模式**：

```bash
# 1. 提交任务
TASK_RESPONSE=$(curl -s -X POST "https://api.lemondata.cc/v1/images/generations" \
  -H "Authorization: Bearer $LEMONDATA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano-banana-pro",
    "prompt": "PROMPT_HERE",
    "n": 1,
    "operation": "text-to-image",
    "aspect_ratio": "9:16",
    "resolution": "2k"
  }')

# 2. 提取 task_id 和 poll_url
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
POLL_URL="/v1/tasks/$TASK_ID"

# 3. 轮询直到完成
sleep 10
RESULT=$(curl -s "https://api.lemondata.cc$POLL_URL" \
  -H "Authorization: Bearer $LEMONDATA_API_KEY")
# status: pending → completed / failed
# image_url 在 result.image_url 或 result.data[0].url
```

**参数：**
- `model`: `nano-banana-pro`（或 `nano-banana`, `nano-banana-2`）
- `operation`: `"text-to-image"`
- `aspect_ratio`: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
- `resolution`: `1k`, `2k`, `4k`

**支持的图片模型：**
| 模型 ID | 说明 |
|---------|------|
| `nano-banana-pro` | Gemini 2.5 Flash 图片生成（推荐） |
| `nano-banana` | 标准版 |
| `nano-banana-2` | 升级版 |
| `gpt-image-2` | OpenAI 模型，同步返回（非异步） |
| `flux-pro` | Flux Pro |
| `gpt-image-2` | OpenAI 模型，同步返回（非异步），推荐用于 logo/图标类设计 |

**GPT Image-2（同步，无需轮询）：**
### 通过 LemonData：
```bash
curl -s -X POST "https://api.lemondata.cc/v1/images/generations" \
  -H "Authorization: Bearer $LEMONDATA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "PROMPT_HERE",
    "n": 1,
    "size": "1024x1792"
  }'
# 返回 data[0].b64_json 或 data[0].url
```

### 通过 NUWA（nuwaflux.com，国内直连已验证可用）：
```bash
curl -s -X POST "https://api.nuwaflux.com/v1/images/generations" \
  -H "Authorization: Bearer $NUWA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "PROMPT_HERE",
    "n": 1,
    "size": "1024x1024"
  }'
# 返回 data[0].b64_json（base64 PNG），保存：
# python3 -c "import base64,json,sys; d=json.load(sys.stdin); open('/tmp/output.png','wb').write(base64.b64decode(d['data'][0]['b64_json']))"
```

**经验：** `gpt-image-2` 适合生成扁平矢量风格 logo、图标、品牌元素（非照片级写实）。1024×1024 方图效果最好。不同风格用不同 prompt 工程（极简线稿 / 赛博朋克 / 卡通等）。

**👉 生成的 logo PNG 如需转 SVG 矢量图：** 见 `references/image-to-svg.md`（potrace + Python 颜色分层工作流）。

**LemonData Key 管理（通过管理令牌）：**
```bash
# 获取管理令牌: 登录 https://lemondata.cc → 设置 → API Keys → 管理令牌 (mt- 前缀)

# 创建带模型权限的 Key
curl -s -X POST "https://api.lemondata.cc/v1/management/api-keys" \
  -H "Authorization: Bearer mt-xxxx" \
  -H "Content-Type: application/json" \
  -d '{"name":"image-gen","models":["nano-banana-pro","gpt-image-2","flux-pro"]}'
# 返回的 key 包含完整值（仅创建时可见）

# 列出 Key
curl -s "https://api.lemondata.cc/v1/management/api-keys" \
  -H "Authorization: Bearer mt-xxxx"
# 只返回 key_prefix，完整 key 仅在创建时返回
```

### 方式 B：Google 官方 GenAI SDK（需境外网络）

```bash
export GEMINI_API_KEY=AIzaSy...

python3 << 'PYEOF'
from google import genai
from google.genai import types
import os, re, base64

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
)

prompt = """PROMPT_PLACEHOLDER"""

response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
            image_size="2K",
        ),
    ),
)

out_path = "/tmp/nanobanana_output.png"
for part in response.parts:
    if part.text:
        match = re.search(r'data:image/(png|jpeg|jpg|gif|webp);base64,([A-Za-z0-9+/=]+)', part.text)
        if match:
            ext, b64 = match.group(1), match.group(2)
            out_path = f"/tmp/nanobanana_output.{ext}"
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"MEDIA:{out_path}")
        else:
            print(part.text)
    elif hasattr(part, 'inline_data') and part.inline_data:
        with open(out_path, "wb") as f:
            f.write(part.inline_data.data)
        print(f"MEDIA:{out_path}")
PYEOF
```

**注意：** Google 官方 API 在中国服务器上可能被墙（api.generativelanguage.googleapis.com 不可达），需要用代理或走 LemonData 中转。

---

## 批量生成

```bash
export $(grep -v '^#' ~/.hermes/.nanobanana | xargs)

python3 << 'PYEOF'
from google import genai
from google.genai import types
import os, re, base64, json

client = genai.Client(
    api_key=os.environ["NUWA_API_KEY"],
    http_options={"base_url": "https://api.nuwaapi.com"},
)

prompts = json.loads(os.environ.get("PROMPTS", '["a sunset over mountains"]'))
results = []

for i, prompt in enumerate(prompts):
    response = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )
    for part in response.parts:
        if part.text:
            match = re.search(r'data:image/(png|jpeg|jpg|gif|webp);base64,([A-Za-z0-9+/=]+)', part.text)
            if match:
                out_path = f"/tmp/nanobanana_{i}.{match.group(1)}"
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(match.group(2)))
                results.append(out_path)
                print(f"MEDIA:{out_path}")
                break
        elif hasattr(part, 'inline_data') and part.inline_data:
            out_path = f"/tmp/nanobanana_{i}.png"
            with open(out_path, "wb") as f:
                f.write(part.inline_data.data)
            results.append(out_path)
            print(f"MEDIA:{out_path}")
            break

print(f"生成 {len(results)} 张图片")
PYEOF
```

---

## 图片编辑（图生图）

```bash
export $(grep -v '^#' ~/.hermes/.nanobanana | xargs)

python3 << 'PYEOF'
from google import genai
from google.genai import types
import os, re, base64

client = genai.Client(
    api_key=os.environ["NUWA_API_KEY"],
    http_options={"base_url": "https://api.nuwaapi.com"},
)

img_path = os.environ["IMG_PATH"]
edit_prompt = os.environ.get("EDIT_PROMPT", "make it look like a watercolor painting")

with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[
        {"inline_data": {"mime_type": "image/png", "data": img_b64}},
        edit_prompt,
    ],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)

out_path = "/tmp/nanobanana_edited.png"
for part in response.parts:
    if part.text:
        match = re.search(r'data:image/(png|jpeg|jpg|gif|webp);base64,([A-Za-z0-9+/=]+)', part.text)
        if match:
            ext, b64 = match.group(1), match.group(2)
            out_path = f"/tmp/nanobanana_edited.{ext}"
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"MEDIA:{out_path}")
        else:
            print(part.text)
    elif hasattr(part, 'inline_data') and part.inline_data:
        with open(out_path, "wb") as f:
            f.write(part.inline_data.data)
        print(f"MEDIA:{out_path}")
PYEOF
```

---

## 可用模型

| 模型 | 说明 |
|------|------|
| `gemini-2.5-flash-image-preview` | Nano Banana Pro（推荐，速度快） |
| `gemini-3-pro-image-preview` | 更高质量，速度较慢 |

## 参数

| 参数 | 可选值 |
|------|--------|
| aspect_ratio | 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 |
| resolution | 1K, 2K, 4K |

---

## 故障排查

### 401 Invalid Token

此错误在腾讯云部署中实际出现（2026-05-21）。NUWA 认证格式为 `Authorization: sk-xxx`（不含 `Bearer` 前缀）。

可能原因：
1. **Key 未激活** — 注册后需在控制台手动生成，可能需完成充值/实名认证
2. **SDK 认证不匹配** — Google GenAI SDK 的 `api_key` 传参方式可能与 NUWA 的 Authorization header 不同。如 SDK 失败，回退到 curl HTTP 直接调用
3. **Key 来源不对** — 确认是从 NUWA 工作台 → API Key 管理 → 生成的 `sk-` 开头密钥

排查顺序：
1. NUWA 控制台确认 Key 状态为「已激活」
2. curl 测试 `/v1/chat/completions` 确认 Key 有效（见上方连通性验证）
3. 若 curl 通但 SDK 不通：改用 `http_options={"headers": {"Authorization": api_key}}` 替代 `api_key=` 参数

---

## 常见问题

- **国内直连**：NUWA 国内可直连，无需代理（端点 `api.nuwaapi.com` 腾讯云可达）
- **费用**：按 NUWA 定价，需在控制台充值
- **SDK 安装**：`pip install google-genai`，本项目需用 Hermes Agent venv

## 环境说明

本项目 Python 为 uv-managed CPython 3.11（通过 Hermes Agent venv）。安装依赖：
```bash
/home/ubuntu/.hermes/hermes-agent/venv/bin/pip3 install google-genai
```
不要用系统 `pip3`（会装到 Python 3.12 user-local，与运行时 3.11 不匹配）。
