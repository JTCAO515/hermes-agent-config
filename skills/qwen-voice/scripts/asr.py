#!/usr/bin/env python3
"""Qwen3-ASR — DashScope 原生端点语音识别 + 情绪检测
Usage: python3 asr.py <audio_file>
Outputs: JSON with text, emotion, language, tokens
"""
import os, sys, json, base64
import urllib.request

audio_path = sys.argv[1]
context_hint = sys.argv[2] if len(sys.argv) > 2 else ""

# Encode audio
with open(audio_path, "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode()

# Determine MIME type
ext = audio_path.rsplit(".", 1)[-1].lower()
mime_map = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
            "m4a": "audio/mp4", "webm": "audio/webm", "flac": "audio/flac"}
mime = mime_map.get(ext, "audio/mpeg")

# Build request
payload = {
    "model": "qwen3-asr-flash",
    "input": {
        "messages": [
            {"role": "user", "content": [
                {"audio": f"data:{mime};base64,{audio_b64}"}
            ]}
        ]
    },
    "parameters": {"asr_options": {"enable_itn": False}}
}

# Add context hint (system message with vocabulary bias)
if context_hint:
    payload["input"]["messages"].insert(0, {
        "role": "system",
        "content": [{"text": context_hint}]
    })

req = urllib.request.Request(
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": "Bearer sk-00ee627a0e2243f2ac451c05d438eee5",
        "Content-Type": "application/json"
    }
)

resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read())

# Extract results
output = data.get("output", {})
choices = output.get("choices", [])
if not choices:
    print(json.dumps({"error": "no choices", "raw": data}, ensure_ascii=False))
    sys.exit(1)

msg = choices[0].get("message", {})
annotations = msg.get("annotations", [{}])[0]

# Content is array of {text: "..."}
content_parts = msg.get("content", [])
text = "".join(p.get("text", "") for p in content_parts)

# Usage is at output level, not choices level
usage = output.get("usage", {})
result = {
    "text": text,
    "emotion": annotations.get("emotion", "unknown"),
    "language": annotations.get("language", "unknown"),
    "seconds": usage.get("seconds", 0),
    "audio_tokens": usage.get("audio_tokens", usage.get("input_tokens_details", {}).get("audio_tokens", 0)),
}

print(json.dumps(result, ensure_ascii=False, indent=2))
