# NUWA API 图片生成（gpt-image-2 + Gemini）

## API 配置

NUWA API 通过环境变量 `NUWAFLUX_BASE_URL` 和 `NUWAFLUX_API_KEY` 配置。

| 环境变量 | 值 |
|---------|-----|
| `NUWAFLUX_BASE_URL` | `https://api.nuwaflux.com/v1` |
| `NUWAFLUX_API_KEY` | `sk-xxx` （来源：`~/.hermes/.env`） |

## 支持的模型

| 模型 | 说明 | 适用场景 |
|------|------|---------|
| `gpt-image-2` | OpenAI 兼容图像生成 | 通用场景，赛博朋克/简约等任意风格 |
| `nano-banana-pro` | Gemini 2.5 Flash 图片生成 | 通常更便宜、速度快 |

## 调用方式

```bash
curl -s -X POST "${NUWAFLUX_BASE_URL}/images/generations" \
  -H "Authorization: Bearer ${NUWAFLUX_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "描述你的图片意图",
    "n": 1,
    "size": "1024x1024"
  }' > /tmp/response.json
```

## 保存图片

响应中包含 `data[0].b64_json`（base64 编码的 PNG）。

```python
import json, base64
with open('/tmp/response.json') as f:
    data = json.load(f)
b64 = data['data'][0]['b64_json']
img = base64.b64decode(b64)
with open('/tmp/image.png', 'wb') as f:
    f.write(img)
print(f"Saved: {len(img)} bytes | size: {data['size']}")
```

## 坑

- b64_json 可能非常大（~1MB 的 base64→~750KB PNG），命令行管道可能报 `Argument list too long`。**修复：** 先存 JSON 到文件，再用 Python 解析
- 模型名称必须是 `gpt-image-2`（不是 `gpt-image-2.0` 或 `gpt-image2`）
