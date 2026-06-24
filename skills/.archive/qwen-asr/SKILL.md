---
name: qwen-asr
description: Qwen3-ASR-Flash 语音识别 + 情绪检测 — 阿里云 DashScope 原生端点。识别 11 种语言 + 方言，自动语言检测，返回文字 + 情绪标签 + 语言码。
version: 1.1.0
triggers:
  - "qwen asr"
  - "qwen3 语音"
  - "阿里语音识别"
  - "dashscope asr"
  - "用qwen转写"
  - "qwen转文字"
  - "识别语气"
  - "听语气"
category: voice
---

# Qwen3-ASR-Flash — 语音识别 + 情绪检测

> DashScope 原生 multimodal-generation 端点。返回：文字转写 + 情绪标签 + 语言检测。

## API 端点

```
POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
Authorization: Bearer $DASHSCOPE_API_KEY
```

## 返回的情绪标签

| 标签 | 含义 |
|------|------|
| `neutral` | 中性/平静 |
| `happy` | 开心 |
| `sad` | 悲伤 |
| `angry` | 生气 |
| `surprised` | 惊讶 |
| `fearful` | 害怕 |
| `disgusted` | 厌恶 |

## 使用方式

### 转写 + 情绪检测

```bash
python3 scripts/asr.py <audio_file> [context_hint]
```

输出 JSON：
```json
{
  "text": "转写文字",
  "emotion": "happy",
  "language": "zh",
  "seconds": 5.2,
  "audio_tokens": 130
}
```

### 带语境偏置（人名/地名/术语）

```bash
python3 scripts/asr.py /tmp/voice.mp3 "讨论VisePanda项目的Supabase方案"
```

## 与 faster-whisper 的区别

| | faster-whisper | Qwen3-ASR |
|------|------|------|
| 文字转写 | ✅ | ✅ |
| 情绪检测 | ❌ | ✅ 7种情绪 |
| 方言 | ❌ | ✅ 粤语/四川话/闽南话/吴语 |
| 背景噪声 | 一般 | ✅ 抗噪强 |
| 成本 | 免费(本地) | ¥0.0006/秒 |
| 端点 | 本地 CPU | DashScope API |

## 支持的音频格式

MP3, WAV, OGG, M4A, WEBM, FLAC (≤10MB)

## Pitfalls

- **❌ OpenAI 兼容端点不行**：`/compatible-mode/v1/chat/completions` 报 `InternalError.Algo.InvalidParameter`。必须用 DashScope 原生端点。
- **❌ 响应格式差异**：原生端点 `content` 是 `[{text: "..."}]` 数组，不是字符串；`annotations` 在 `message` 级别。
- **⚠️ 微信语音**：微信自带语音识别，agent 拿不到原始音频。需用户**发文件**（非语音按钮）才能跑情绪检测。
- **✅ 情绪准确度**：实测 happy/sad/angry/neutral 全中。
