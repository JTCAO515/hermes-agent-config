# API Probing Methodology — Reverse-Engineering Unknown Auth

## When to Use

When the API documentation is behind a login/behind a CAPTCHA, unavailable, or outdated.
You have credentials (username + secret) but don't know:

- The exact endpoint URL (domain may have changed)
- The auth format (header vs query param vs body)
- The param names (`user` vs `username` vs `email` vs `account`)
- The actual endpoint path structure

## Core Principle: Error Message as Signal

**Every error message contains information.** Two different error messages =
the API reached different code paths. Use this to narrow down WHICH part
of your request is wrong and WHICH part is correct.

## Step-by-Step Methodology

### Step 1: Establish basic connectivity

Start with the most basic request possible — no auth, no params, just the endpoint:

```bash
curl -s --max-time 10 "https://api.example.com/api/v5/football/season/list"
```

**What to observe:**
- `HTTP 200` + HTML → Live website, not an API endpoint (try different paths)
- `HTTP 503` → Service temporarily unavailable (try again later)
- `HTTP 404` → Wrong path (try `/v5/`, `/v2/`, `/api/`, no `/api/`)
- `HTTP 403/401` → Auth needed (good — server is alive!)
- `Connection refused` / `NXDOMAIN` → Wrong domain entirely
- `{"err": "some Chinese text"}` → Server is alive and rejecting something specific

### Step 2: Isolate the problem — auth vs IP whitelist vs endpoint

Make requests with different degrees of wrongness to see how errors change:

```bash
# No auth at all
curl -s "https://api.example.com/api/v5/football/season/list"

# Wrong auth
curl -s -u "wrong:wrong" "https://api.example.com/api/v5/football/season/list"

# Just one param
curl -s "https://api.example.com/api/v5/football/season/list?user=myuser"

# Both params but different names
curl -s "https://api.example.com/api/v5/football/season/list?user=myuser&key=mykey"
curl -s "https://api.example.com/api/v5/football/season/list?username=myuser&secret=mykey"
curl -s "https://api.example.com/api/v5/football/season/list?appkey=myuser&secret=mykey"
```

**Error message taxonomy (for Chinese APIs):**

| Error (Chinese) | Error (English) | Meaning |
|----------------|-----------------|---------|
| 用户名或者密钥错误 | Username or key error | Auth reached the validation layer — format is probably correct |
| 密钥错误 | Key error only | Username was accepted, only the key param/value is wrong |
| ip未授权访问 | IP not authorized | Auth credentials accepted, IP whitelist rejected |
| url未授权访问 | URL not authorized | Endpoint path is correct but not in your subscription |
| 参数错误 | Parameter error | Wrong param names or format |
| 请求被拒绝 | Request denied | Generic rejection (usually IP not in whitelist) |

**Key insight:** If you get different error messages with different param names → you've found the right param names! The API is telling you which part of your request it understood.

Example from real session:
```
user=naofpmibbn&key=xxx  → "密钥错误" (key wrong — username ACCEPTED)
username=naofpmibbn&secret=xxx → "用户名或者密钥错误" (both wrong — 'username' not recognized)
user=naofpmibbn&secret=xxx → "ip未授权访问" (auth OK, IP rejected — PERFECT!)
```

This tells us: `user` + `secret` are the correct param names, and the credentials are valid.

### Step 3: Probe endpoint structure

Once auth format is confirmed, probe available endpoints:

```bash
BASE="https://api.example.com/api/v5"
AUTH="?user=myuser&secret=mysecret"

for ep in "football" "football/live" "football/match" "football/season"; do
  echo -n "$ep → "
  curl -s --max-time 8 "$BASE/$ep$AUTH" | python3 -c "
import json,sys; d=json.load(sys.stdin)
if 'err' in d:
  print('ERR:', d['err'][:30])
else:
  print('OK — keys:', list(d.keys())[:5])
"
done
```

**What to look for:**
- Same error for different paths → path structure is wrong
- New errors ("参数错误" vs "未授权") → path was recognized
- JSON with data keys → found it!

### Step 4: Probe different path patterns

Try common API path structures:

```bash
# Different version prefixes
/v5/football/...
/api/v5/football/...
/football/...
/api/football/...

# Different path patterns
/football/season/list
/football/season/list/
/football/seasons
/api/football/getSeasonList
```

### Step 5: Probe auth endpoints

Some APIs have separate auth/login endpoints:

```bash
for path in "/auth/login" "/api/auth/login" "/api/v5/auth/token" "/api/v5/user/login"; do
  curl -s -X POST -H "Content-Type: application/json" \
    -d '{"username":"user","secret":"key"}' \
    "https://api.example.com$path"
done
```

### Step 6: Capture session cookies after web login

If the API has a web login page but the API needs a session:

```bash
# Login via POST
curl -s -c /tmp/cookies.txt -X POST \
  -d 'username=user&password=pass' \
  "https://example.com/api/login"

# Use session cookie for API calls
curl -s -b /tmp/cookies.txt \
  "https://example.com/api/data"
```

### Step 7: Verify from correct network context

If API uses IP whitelisting, test from BOTH:
- Your dev server (add its IP to whitelist)
- The production deployment (may have different IP)

```bash
# From dev server
curl -s "https://api.example.com/..."

# From Vercel production (proxy through deployed app)
curl -s "https://my-app.vercel.app/api/nami/health"
```

## Common Chinese API Pitfalls

1. **Domain migration is common** — old domains get abandoned (`api.namiplat.com` → NXDOMAIN). The live website (`www.nami.com`) often still works but may point to different API hostnames.
2. **IP whitelisting** — Authentication may PASS but IP is rejected with a misleading "密钥错误" message. Always check with `user=xxx&secret=xxx` format to distinguish auth vs IP.
3. **Query-param auth** — Many Chinese APIs use `user` + `secret` (or `appkey` + `secret`, `ak` + `sk`) as query parameters rather than HTTP headers. This is different from Western API conventions.
4. **CAPTCHA on login** — The web control panel will almost certainly have a CAPTCHA that automated login can't bypass. Don't spend time trying to automate it — ask the user to log in or provide credentials directly.
5. **Error messages in Chinese** — Even tiny changes in Chinese text ("密钥错误" vs "用户名或者密钥错误") carry signal. Read them carefully, don't translate and dismiss.
6. **HTTPS → HTTP redirect** — Some Chinese API domains support both. If HTTPS times out but HTTP returns a different response, the API may not support HTTPS even on a live domain.
