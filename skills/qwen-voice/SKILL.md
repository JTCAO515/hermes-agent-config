---
name: qwen-voice
description: "Qwen/CosyVoice 阿里云 DashScope 语音服务 — 语音识别 (ASR) + 情绪检测 + 文字转语音 (TTS)。49+ 高质量音色，11 种语言识别，共享 DASHSCOPE_API_KEY。"
version: 1.0.0
category: voice
triggers:
  - "语音识别"
  - "转写"
  - "情绪检测"
  - "文字转语音"
  - "语音合成"
  - "读出来"
  - "说给我听"
  - "qwen asr"
  - "qwen tts"
  - "cosyvoice"
---

# Qwen Voice — 阿里云语音服务

> 本技能是**语音与音频处理统一入口**。涵盖：DashScope ASR + 情绪检测、CosyVoice TTS 合成、以及 Gemini 原生音频分析（已吸收 `gemini-audio`）。
> 
> **什么时候用哪个：**
> | 场景 | 工具 |
> |------|------|
> | 纯文字转写（便宜、快） | Qwen ASR |
> | 需要分析语气/情绪/背景音 | Gemini 原生音频 |
> | 文字转语音（TTS） | Qwen CosyVoice |
> | 会议录音、多说话人 | Gemini 原生音频 |
> | 方言识别 | Qwen ASR |

---

## Section A — Qwen DashScope ASR + 情绪检测

> DashScope 原生端点。两大功能：ASR 语音识别 + 情绪检测，TTS 语音合成。
> 共享 `DASHSCOPE_API_KEY`，通过 `os.environ` 设置（不支持 `api_key=` 构造参数）。

## 前置条件

```bash
pip install dashscope
# 不要用系统 pip，用 Hermes Agent venv:
# /home/ubuntu/.hermes/hermes-agent/venv/bin/pip3 install dashscope
```

API Key 在环境中设置：
```bash
export DASHSCOPE_API_KEY="sk-..."
```

## 一、ASR — 语音识别 + 情绪检测

通过 DashScope 原生 multimodal-generation 端点，返回文字转写 + 7 种情绪标签 + 语言检测。

### 使用方式

```bash
python3 scripts/asr.py <audio_file> [context_hint]
```

示例：
```bash
python3 scripts/asr.py /tmp/voice.mp3 "讨论VisePanda项目的Supabase方案"
```

### 返回的情绪标签

| 标签 | 含义 |
|------|------|
| `neutral` | 中性/平静 |
| `happy` | 开心 |
| `sad` | 悲伤 |
| `angry` | 生气 |
| `surprised` | 惊讶 |
| `fearful` | 害怕 |
| `disgusted` | 厌恶 |

### 输出 JSON

```json
{
  "text": "转写文字",
  "emotion": "happy",
  "language": "zh",
  "seconds": 5.2,
  "audio_tokens": 130
}
```

### 支持的音频格式

MP3, WAV, OGG, M4A, WEBM, FLAC (≤10MB)

### 与 faster-whisper 对比

| | faster-whisper | Qwen3-ASR |
|------|------|------|
| 情绪检测 | ❌ | ✅ 7种情绪 |
| 方言 | ❌ | ✅ 粤语/四川话/闽南话/吴语 |
| 背景噪声 | 一般 | ✅ 抗噪强 |
| 成本 | 免费(本地) | ¥0.0006/秒 |

### ASR Pitfalls

- **❌ OpenAI 兼容端点不行**：`/compatible-mode/v1/chat/completions` 报 `InternalError.Algo.InvalidParameter`。必须用 DashScope 原生端点。
- **❌ 响应格式差异**：原生端点 `content` 是 `[{text: "..."}]` 数组，不是字符串。
- **⚠️ 微信语音**：微信自带语音识别，agent 拿不到原始音频。需用户**发文件**（非语音按钮）才能跑情绪检测。
- **✅ 情绪准确度**：实测 happy/sad/angry/neutral 全中。

## 二、TTS — 文字转语音 (CosyVoice V3)

DashScope CosyVoice v3，49+ 音色，自然流畅的中文/英文/多语种合成。

### 使用方式

```python
import os
os.environ["DASHSCOPE_API_KEY"] = "sk-..."

from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

def speak(text, voice="longanyang", output="/tmp/tts_output.mp3"):
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
```

命令行：
```bash
python3 scripts/speak.py <text_file> <output_path>
```

### 可用音色（实测）

| 音色 | 性别 | 风格 | 状态 |
|------|------|------|------|
| `longanyang` | 女 | 自然活泼 | ✅ |
| `longxiaochun_v3` | 女 | 知性积极（**默认**） | ✅ |
| `longhuhu_v3` | 女 | 童声 6-10岁 | 待测 |
| `longjielidou_v3` | 男 | 阳光顽皮 10岁 | 待测 |

> ⚠️ 不带 `_v3` 后缀的音色（如 longwanqing, longyuxuan, longxiaoming）在 cosyvoice-v3-flash 下**不可用**（error 418）。

### 音色选择建议

- **日常聊天（默认）** → `longxiaochun_v3`（女，知性积极）
- **活泼调侃** → `longanyang`（女，自然活泼）
- **童趣内容** → `longhuhu_v3`（女童声）/ `longjielidou_v3`（男童声）
- **方言特色** → `longlaotie_v3`（东北话）/ `longshange_v3`（陕西话）

### 成本

cosyvoice-v3-flash 约 ¥0.7/万字。单次 ≤ 5000 字符。

### TTS Pitfalls

- **❌ `api_key` 不是构造参数**：`SpeechSynthesizer(api_key=...)` 报错。必须用 `os.environ` 在 import 前设置。
- **❌ 不带 `_v3` 的音色不可用**：全部返回 error 418。
- **❌ OGG 格式名**：正确是 `OGG_OPUS_24KHZ_MONO_32KBPS`，不是其他变体。
- **✅ 返回 `bytes` 直接就是音频**：新版 SDK 返回 `bytes`，不是对象。

## Hermes Agent TTS 配置

```yaml
# ~/.hermes/config.yaml
voice:
  auto_tts: false   # 默认不要自动语音回复

tts:
  provider: qwen
  qwen:
    type: command
    command: /home/ubuntu/.hermes/hermes-agent/venv/bin/python3 /home/ubuntu/.hermes/skills/qwen-voice/scripts/speak.py {text_file} {output_path}
```

## Hermes Agent ASR 配置

ASR 通过 execute_code 或 terminal 调用：
```bash
/hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/qwen-voice/scripts/asr.py <audio_file>
```

## Anti-Patterns

- ❌ 用 OpenAI 兼容端点调 ASR — 必须用 DashScope 原生端点
- ❌ TTS 构造参数用 `api_key=` — 必须用环境变量
- ❌ 自动语音回复 — 用户偏好明确要求关闭
- ❌ 在语音消息上运行 ASR 以为能情绪检测 — 微信语音拿不到原始音频

---

## Section C — Gemini 原生音频分析

> 吸收自 `gemini-audio`（已归档）。使用 Gemini 2.5 Flash 直接\"听\"原始音频，理解语气、情绪、背景音。

Gemini 不经过 STT 管道 — 直接分析原始音频并输出语义理解。比纯 ASR 多了语境感知和情绪分析。

### 适用场景
- 需要分析说话人的**语气、情绪、语速**
- **会议录音/多说话人**场景（可用prompt要求区分）
- **背景音识别**（能识别咖啡厅、车里、户外等场景）
- 对转写准确度要求不极端，但对**语义理解**要求高

### 不适合的场景
- 纯文字转写（Qwen ASR 更快、更便宜）
- 需要 TTS 输出

### 调用方式

**Python 脚本：**
```bash
python3 scripts/gemini_audio.py <audio_file> [prompt]
```

**或用 curl 直调 NUWA API（见 `references/gemini-audio.md`）**

### 支持格式
MP3, WAV, OGG, M4A, WEBM

### 与 Qwen ASR 对比

| | Qwen ASR | Gemini 原生音频 |
|------|---------|----------------|
| 输出 | 纯文字 + 情绪标签 | 文字 + 语气 + 情绪 + 背景音描述 |
| 上下文 | 无 | 理解对话场景 |
| 方言 | ✅ 粤语/川话/闽南/吴语 | 一般 |
| 延迟 | <3s (API) | 3-8s (API) |
| 成本 | ¥0.0006/秒 | NUWA token |

### Pitfalls
- ❌ 微信语音消息拿不到原始音频 — agent 无法用于微信语音分析
- ✅ 情绪准确度实测良好：happy/sad/angry/neutral 全中

详细 API 调用方式 → `references/gemini-audio.md`
