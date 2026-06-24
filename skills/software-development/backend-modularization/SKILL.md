---
name: backend-modularization
description: Extract domain logic from a monolithic WSGI/API handler into a module-per-domain architecture with a thin router entry point. Covers the common.py + domain modules + entry point pattern.
category: software-development
related: [systematic-debugging, test-driven-development]
---

# Backend Modularization

## When to Use

A single handler file (e.g. `api/index.py`, `app.py`, `server.py`) has grown beyond ~400 lines and mixes:
- Route dispatching
- Multiple domain handlers (chat, cities, tools, auth)
- Static file serving
- Large inline data structures
- Configuration and env-var access

This skill extracts each concern into its own module.

## Architecture Pattern

```
api/
├── common.py          # Shared helpers: _json, _serve_static, _read_post, DATA_DIR, MIME types
├── cities.py          # City listing + detail + estimate data + map data
├── chat.py            # SSE streaming + FAQ matching + system prompt builder
├── tools.py           # Tool listing + detail
├── config.py          # Map coordinates + client-safe config
├── auth.py            # Auth, admin, trip routes (pre-existing, left untouched)
├── index.py           # Thin router (84 lines) — imports all modules, routes by path+method
└── __init__.py
```

## Step-by-Step

### Step 1: Extract shared utilities → `common.py`

Move these to a single `common.py`:
- Path constants (`DATA_DIR`, `WEB_DIR`, `STATIC_DIR`)
- MIME type dictionary
- `_json()`, `_json_error()`, `_read_post()`, `_load_json()`
- `_serve_static()` — served file resolution + cache headers
- `_sse_event()` — SSE event formatting

All other modules import from `common.py`.

### Step 2: Extract domain modules

One file per API domain, each importing only from `common.py`:
- `chat.py` — SSE handlers, FAQ matcher, system prompt builder, image marker handler
- `cities.py` — city data, estimate data, map data (avoid polluting with large inline dicts)
- `tools.py` — tool listing + detail
- `config.py` — map endpoint + client config

### Step 3: Thin router in `index.py`

The entry point should only:
1. Import `common.py`
2. Define `app(environ, start_response)` with path-matching branches
3. Use **lazy imports** (`from api.chat import handle_chat` inside the matching branch, not at module top)

**Why lazy imports:** Avoids circular import issues and keeps cold-start fast — module is only loaded when its route is hit.

```python
# index.py — thin router
from api.common import _json, _json_error, _serve_static

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/chat" and method == "POST":
        from api.chat import handle_chat
        return handle_chat(environ, start_response)

    if path.startswith("/api/cities") and method == "GET":
        from api.cities import handle_cities
        return handle_cities(start_response, path)

    # ... more routes ...

    # Fallback: static files or 404
    result = _serve_static(start_response, path)
    if result is not None:
        return result
    return _json_error(start_response, f"Not found: {path}", "404 Not Found")
```

### Step 4: Verify no regression

Run a smoke test against all API endpoints:

```python
tests = [
    ('GET', '/api/health', 200),
    ('GET', '/api/cities', 200),
    ('GET', '/api/tools', 200),
    ('GET', '/api/config', 200),
    ('GET', '/api/map', 200),
    ('GET', '/', 200),           # static file
    ('GET', '/app.js', 200),     # static file
    ('GET', '/api/nonexist', 404),
]
```

## Pitfalls

- **Circular imports**: Domain modules import from `common.py`. `index.py` lazy-imports domain modules inside route branches. Never import `index.py` from a domain module.
- **Inline data bloat**: Large dicts (MAP_DATA, ESTIMATE_DATA) belong in the relevant domain module, not in `common.py`. Keep `common.py` lean — only utility functions and path constants.
- **Auth modules with route handling**: If auth.py handles routes (via `handle_auth_route()`), call it as a catch-all after explicit API routes. Its response pattern (`returns None if unmatched`) makes it ideal as a final dispatcher before static file fallback.
- **Check before building**: Before adding new API endpoints, scan existing modules (especially auth.py) — the handler may already exist. Saves duplicate work.
- **Preserve `__init__.py`**: Even if empty, ensures Python treats `api/` as a package.

## Verification

After refactoring, run:
```
python3 -c "from api.index import app; ..."  # smoke test all endpoints
git diff --stat  # should show -- (deletions) > ++ (additions) for the monolithic file
```

The monolith file should lose ~90% of its line count (e.g. 826 → 84 lines).
