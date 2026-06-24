---
name: qwen-tts
description: Qwen3/CosyVoice 文字转语音 — 阿里云 DashScope TTS。49+高质量音色，支持中文/英文/多语种，自然流畅。通过 DashScope SDK (cosyvoice-v3-flash)。
version: 1.0.0
triggers:
  - "文字转语音"
  - "读出来"
  - "说给我听"
  - "语音回复"
  - "tts"
  - "qwen tts"
  - "cosyvoice"
  - "念一遍"
category: voice
---

# Qwen3-TTS — 阿里云语音合成

> DashScope CosyVoice v3，49+ 音色，自然流畅的中文/英文/多语种合成。

## 可用音色（cosyvoice-v3-flash 实测）

> ⚠️ **2026-05-23**: 以下音色经实测。`longwanqing`/`longanning`/`longsitong`/`longyuxuan`/`longxiaoming` 均返回 error 418，不可用。

| 音色 | 性别 | 风格 | 状态 |
|------|------|------|------|
| `longanyang` | 女 | 自然活泼 | ✅ 已确认 |
| `longhuhu_v3` | 女 | 童声 6-10岁 | 待测 |
| `longjielidou_v3` | 男 | 阳光顽皮 10岁 | 待测 |
| `longxiaochun_v3` | 女 | 知性积极（**默认**） | ✅ 已确认 |
| `longjiayi_v3` | 女 | 知性粤语 | 待测 |
| `longlaotie_v3` | 男 | 东北话 | 待测 |
| `longshange_v3` | 男 | 陕西话 | 待测 |

其他 `long*` 不带 `_v3` 后缀的音色（如 longwanqing, longanning, longyuxuan, longxiaoming）在 cosyvoice-v3-flash 模型下**不可用**。

## 使用方式

```python
import os
os.environ["DASHSCOPE_API_KEY"] = "sk-00ee627a0e2243f2ac451c05d438eee5"

from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

def speak(text, voice="longanyang", output="/tmp/tts_output.mp3"):
    """将文字转为语音"""
    synthesizer = SpeechSynthesizer(
        model="cosyvoice-v3-flash",
        voice=voice,
        format=AudioFormat.MP3_22050HZ_MONO_256KBPS
    )
    result = synthesizer.call(text)
    if isinstance(result, bytes):
        with open(output, "wb") as f:
            f.write(result)
        return output
    return None

# 使用
path = speak("今天天气真好，适合出去走走。")
print(f"MEDIA:{path}")
```

## 音色选择建议

- **日常聊天（默认）** → `longxiaochun_v3`（女，知性积极）
- **活泼调侃** → `longanyang`（女，自然活泼）
- **童趣内容** → `longhuhu_v3`（女童声）/ `longjielidou_v3`（男童声）
- **方言特色** → `longlaotie_v3`（东北话）/ `longshange_v3`（陕西话）

## 依赖

```bash
pip install dashscope
```

## 限制

- 单次 ≤ 5000 字符
- 成本：cosyvoice-v3-flash 约 ¥0.7/万字
- 通过 DashScope SDK 调用，不需要额外配置 API endpoint

## Pitfalls

- **❌ `api_key` 不是构造参数**：`SpeechSynthesizer(api_key=...)` 报 `unexpected keyword argument 'api_key'`。必须用 `os.environ["DASHSCOPE_API_KEY"]` 在 import 前设置。
- **❌ 不带 `_v3` 的音色不可用**：`longwanqing`/`longanning`/`longyuxuan`/`longxiaoming` 等全部返回 error 418。CosyVoice V3 仅支持带 `_v3` 后缀或 `longanyang`。
- **❌ OGG 格式名**：正确是 `OGG_OPUS_24KHZ_MONO_32KBPS`，不是 `OGG_OPUS_16000HZ_MONO_24KBPS`。
- **✅ 返回 `bytes` 直接就是音频**：新版 SDK 返回 `bytes`，不是对象。直接用 `f.write(result)` 即可。

## 自动回复语音

> ⚠️ **用户偏好**：默认不要自动语音回复！用户已明确要求 `auto_tts: false`，只在用户主动说"读出来""说给我听""语音回复"等触发词时才用 TTS。

当前配置：

```yaml
# ~/.hermes/config.yaml
voice:
  auto_tts: false   # ← 用户要求关闭

tts:
  provider: qwen     # Qwen CosyVoice V3
  qwen:
    type: command
    command: /home/ubuntu/.hermes/hermes-agent/venv/bin/python3 /home/ubuntu/.hermes/skills/qwen-tts/scripts/speak.py {text_file} {output_path}
```
