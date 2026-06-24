---
name: gemini-audio
description: Gemini 原生音频识别与分析 — 直接理解语音内容、语气、情绪、背景音，无需先转文字。比 Whisper 管道多了语义理解和上下文感知。
version: 1.0.0
triggers:
  - "分析这段音频"
  - "听听这个说了什么"
  - "音频识别"
  - "语音分析"
  - "gemini audio"
  - "原生音频"
  - "直接听"
category: voice
---

# Gemini 原生音频识别

> 不是管道（STT → 文本 → LLM），而是 Gemini 直接"听"原始音频，理解语气、情绪、背景音和隐含信息。

## 触发词

- "分析这段音频"
- "听听这个说了什么"
- "语音分析"
- 任何需要从音频中提取信息（不仅是文字，还有语气/情绪）的场景

## 使用方式

### 方法一：Python 脚本（推荐）

```bash
python3 scripts/analyze_audio.py <audio_file> [prompt]
```

默认 prompt: "请完整转录这段音频，并分析说话人的语气、情绪、语速和背景环境。如果是中文，用简体中文输出。"

### 方法二：从工具调用

在 execute_code 中调用：

```python
from hermes_tools import terminal
import base64, json

audio_path = "/path/to/audio.mp3"
with open(audio_path, "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "gemini-2.5-flash",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请完整转录这段音频，并分析语气和情绪。"},
                {"type": "audio", "data": audio_b64}
            ]
        }
    ],
    "max_tokens": 2000
}

tmp = "/tmp/gemini_audio_payload.json"
with open(tmp, "w") as f:
    json.dump(payload, f)

result = terminal(
    "curl -s https://api.nuwaflux.com/v1/chat/completions "
    "-H 'Content-Type: application/json' "
    "-H 'Authorization: Bearer sk-kKduIUGbmvQEZRvjM8Qy2jtVFlk914gOXPe9F2kZnJNI8QXy' "
    f"-d @{tmp}", timeout=120
)

print(json.loads(result["output"])["choices"][0]["message"]["content"])
```

## 支持格式

| 格式 | MIME |
|------|------|
| MP3 | audio/mpeg |
| WAV | audio/wav |
| OGG | audio/ogg |
| M4A | audio/mp4 |
| WEBM | audio/webm |

## 与 Whisper STT 的区别

| | Whisper STT | Gemini 原生音频 |
|------|------|------|
| 输出 | 纯文字 | 文字 + 语气 + 情绪 + 背景音描述 |
| 上下文 | 无 | 理解对话场景 |
| 多语言混合 | 一般 | 强 |
| 口音 | 一般 | 强 |
| 延迟 | <1s (local) | 3-8s (API) |
| 成本 | 免费 | NUWA token |

## 最佳实践

- **语音消息**：用 Whisper STT 管道（快、免费）
- **需要分析语气的录音**：用 Gemini 原生音频
- **会议录音/多说话人**：用 Gemini + 提示词要求区分说话人
- **背景音识别**：Gemini 能识别场景（咖啡厅、车里、户外）
- **图片分析**：通过 NUWA API + `gemini-2.5-flash` + `type: "image_url"` + `data:image/png;base64,...` 格式，已实测可用。用于截图分析、UI问题诊断等场景。

## 已确认可用的 API 模式

| 输入类型 | content type | 状态 |
|------|------|------|
| 图片 (截图/照片) | `type: "image_url"` + `image_url: {url: "data:image/png;base64,..."}` | ✅ 已确认 |
| 音频 (MP3/WAV) | `type: "audio"` + `data: "<base64>"` | ⚠️ 待测 |
