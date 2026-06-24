# LLM API Proxy from Vercel Python (stdlib-only)

> How to call DeepSeek/OpenAI-compatible APIs from a Vercel Python WSGI handler with **zero pip dependencies** using `urllib.request`.

## Architecture

```
Browser → POST /api/chat { messages: [...] } → Vercel Python → urllib.request → DeepSeek API
                                                         ↑
                                                    read local WC data
                                                    build system prompt
```

No `requests` library needed. No `openai` SDK. Pure stdlib.

## Implementation

### `chat_engine.py`

```python
import json
import os
import urllib.request
import urllib.error

API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def build_system_prompt() -> str:
    """Build context by reading local data files."""
    parts = [
        "You are a football analyst...",
        _build_teams_context(),     # from local JSON
        _build_standings_context(), # from local JSON
        _build_matches_context(),   # from local JSON
        _build_odds_context(),      # from local JSON
    ]
    return "\n".join(parts)


def chat(messages: list[dict], model: str | None = None) -> dict | None:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return {"error": "API key not configured."}

    payload = {
        "model": model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            *messages,
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False,
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "reply": data["choices"][0]["message"]["content"],
                "model": data.get("model", model),
                "usage": data.get("usage"),
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"error": f"API error {e.code}: {err_body[:500]}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)[:500]}"}
```

### WSGI Route in `api/index.py`

```python
if path == "/api/wc/chat" and method == "POST":
    try:
        from your_package.chat_engine import chat as chat_engine
        params = json.loads(environ["wsgi.input"].read(
            int(environ.get("CONTENT_LENGTH", 0) or "0")
        ))
        messages = params.get("messages", [])
        model = params.get("model")
        if not messages:
            return _json(start_response, {"error": "messages required"}, status="400")
        result = chat_engine(messages, model=model)
        return _json(start_response, result)
    except Exception as ex:
        return _json_error(start_response, str(ex))
```

## Environment Variables (Vercel)

Must be set in **Vercel Dashboard → Project Settings → Environment Variables**:

| Variable | Value | Notes |
|----------|-------|-------|
| `DEEPSEEK_API_KEY` | `sk-...` | Required |
| `DEEPSEEK_MODEL` | `deepseek-chat` | Optional, defaults to `deepseek-chat` |

## Context Injection Pattern

The system prompt is rebuilt **on every request** by reading local JSON files. This ensures it always reflects the latest data. The prompt typically includes:

1. Team ratings (attack/defense per team) — 20-30 lines
2. Group standings — 30-50 lines  
3. Recent match results — 10-20 lines
4. Upcoming matches — 15-25 lines
5. Betting odds summary — 10-20 lines

Total: ~100-120 lines, ~3500-4000 chars — far under the 128K context window.

## Error Handling

| Case | Frontend Shows |
|------|---------------|
| No API key configured | Red error bubble: "DeepSeek API key not configured. Set DEEPSEEK_API_KEY..." |
| API returns 4xx/5xx | Red error bubble with error code + truncated body |
| Network timeout (60s) | Red error bubble: "Request failed: ..." |

## Alternatives

- **Streaming**: For SSE streaming, use `urllib.request.urlopen()` with `stream=True` in the payload, then yield SSE events from the WSGI handler using `start_response('200 OK', [('Content-Type', 'text/event-stream')])` + manual flush
- **Other providers**: The same pattern works for any OpenAI-compatible API — just change the `API_URL` and `Authorization` header scheme
