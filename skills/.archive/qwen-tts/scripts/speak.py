#!/usr/bin/env python3
"""Qwen CosyVoice TTS — custom command provider for Hermes.
Usage: speak.py <text_file> <output_audio_path> [voice]
Hermes writes the text to <text_file>, this script reads it,
synthesizes speech, and writes to <output_audio_path>.
"""
import os, sys

# Read text from file (Hermes passes the text file path as arg 1)
text_file = sys.argv[1]
output_path = sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "longxiaochun_v3"

with open(text_file, "r", encoding="utf-8") as f:
    text = f.read().strip()

if not text:
    sys.exit(1)

# Must be set BEFORE importing dashscope SDK (reads from env at import time)
if not os.environ.get("DASHSCOPE_API_KEY"):
    print("ERROR: DASHSCOPE_API_KEY not set. Source ~/.hermes/.env first.", file=sys.stderr)
    sys.exit(1)

from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

format_map = {
    ".mp3": AudioFormat.MP3_22050HZ_MONO_256KBPS,
    ".ogg": AudioFormat.OGG_OPUS_24KHZ_MONO_32KBPS,
    ".wav": AudioFormat.WAV_22050HZ_MONO_16BIT,
}
ext = os.path.splitext(output_path)[1].lower()
audio_format = format_map.get(ext, AudioFormat.MP3_22050HZ_MONO_256KBPS)

synthesizer = SpeechSynthesizer(
    model="cosyvoice-v3-flash",
    voice=voice,
    format=audio_format
)
result = synthesizer.call(text)

if isinstance(result, bytes):
    with open(output_path, "wb") as f:
        f.write(result)
elif hasattr(result, 'get_audio_data'):
    with open(output_path, "wb") as f:
        f.write(result.get_audio_data())
else:
    print(f"Error: unexpected result type: {type(result)}", file=sys.stderr)
    sys.exit(1)
