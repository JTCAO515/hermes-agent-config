# AI Chat Bot Integration — Sports Betting Knowledge Base

Extends the football-odds and betting-math engines with an AI chat interface.
Users can ask natural language questions about match predictions, betting value,
and strategy without clicking through complex UIs.

## Architecture

```
用户输入 → POST /api/wc/chat → chat_engine.chat()
                                  │
                                  ├─ build_system_prompt()
                                  │    ├─ _build_tournament_context()
                                  │    ├─ _build_team_ratings_context()
                                  │    ├─ _build_standings_context()
                                  │    ├─ _build_recent_results_context()
                                  │    ├─ _build_polymarket_context()
                                  │    └─ _build_top_bets_context()
                                  │
                                  ├─ build_match_context(match_id)
                                  │    └─ analyze_match_markets()
                                  │
                                  └─ DeepSeek V4 Pro API
                                       └─ 回复 → 前端聊天界面
```

## Key Components

### 1. chat_engine.py

Two entry points:
- `chat(messages, match_id=None, model=None)` — Main chat function
- `build_system_prompt()` — Builds full knowledge base context

### 2. API Endpoint

```python
# POST /api/wc/chat
# Body: {"messages": [...], "match_id": "optional"}
# Response: {"reply": "...", "model": "deepseek-chat", "usage": {...}}
```

Key considerations:
- **Timeout**: 65s client-side (Vercel serverless max ~60s)
- **CORS**: Standard `Access-Control-Allow-Origin: *`
- **Error handling**: Returns `{"error": "..."}` on failure
- **API Key**: Environment variable `DEEPSEEK_API_KEY`

### 3. Knowledge Base Builders

| Builder | Content | Approx Lines |
|---------|---------|-------------|
| `_build_tournament_context()` | Total matches, played/upcoming | ~5 |
| `_build_team_ratings_context()` | Elite-only with xG ratings | ~15 |
| `_build_standings_context()` | Top 3 per group with points | ~15 |
| `_build_recent_results_context()` | Last 10 played matches | ~12 |
| `_build_polymarket_context()` | Top 10 winner market odds | ~12 |
| `_build_top_bets_context()` | EV>5% across ALL matches | ~15 |
| `build_match_context(id)` | Single match, 33 market types | ~20 |

Total system prompt: ~1,500-2,000 tokens

### 4. DeepSeek API

```python
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"  # V4 Pro
temperature = 0.5  # Low for factual betting advice
max_tokens = 2048
```

### 5. Frontend Chat UI

Message types: `ai` (left), `user` (right), `error` (red), `loading` (italic)
Built with vanilla JS + CSS, following Linear dark theme conventions.

## System Prompt Structure

1. **Role** — "expert AI betting advisor for 2026 FIFA World Cup"
2. **Capabilities** — odds analysis, EV detection, Kelly sizing
3. **Rules** — show EV%/Grade/Kelly%, mention risk, don't fabricate
4. **Dynamic data** — tournament, teams, standings, results, markets, top bets
5. **Reference** — market types, grading system, Kelly guidelines

### Key Embedded Rules
```
- When recommending bets: show EV%, Grade, and Kelly%
- Always mention risk: positive EV doesn't guarantee profit
- Chinese input OK, team names in English
- Quarter-Kelly recommended, never >10% of bankroll on single outcome
```

## Vercel Deployment

| Variable | Value | Required |
|----------|-------|----------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key | ✅ |
| `DEEPSEEK_MODEL` | `deepseek-chat` (default) | ❌ |

Set via Vercel Dashboard: Project → Settings → Environment Variables

## Troubleshooting

- **"DeepSeek API 密钥未配置"**: DEEPSEEK_API_KEY env var missing in Vercel
- **Timeout ≥60s**: Vercel serverless limit; use 65s AbortSignal on fetch
- **Poor response quality**: Lower temperature (try 0.3-0.5), verify system prompt isn't truncated
- **Missing data**: Add a builder function for the missing context type
