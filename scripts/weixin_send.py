#!/usr/bin/env python3
"""Helper: send a text message to Weixin via iLink API synchronous HTTP.
Bypasses the Hermes async gateway aiohttp bug."""
import json, struct, secrets, sys, requests

TOKEN = "YOUR_ILINK_BOT_TOKEN"  # Format: "account@im.bot:secret"
BASE = "https://ilinkai.weixin.qq.com"
ACCOUNT = "YOUR_BOT_ACCOUNT@im.bot"
TO_USER = "YOUR_RECIPIENT@im.wechat"

def _uin():
    return secrets.token_urlsafe(8)

def send(text: str) -> bool:
    msg = {
        "from_user_id": ACCOUNT, "to_user_id": TO_USER,
        "client_id": ACCOUNT, "message_type": 1, "message_state": 4,
        "item_list": [{"type": 1, "text_item": {"text": text}}]
    }
    payload = {"base_info": {"channel_version": "2.2.0"}, "msg": msg}
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "Content-Length": str(len(body.encode("utf-8"))),
        "X-WECHAT-UIN": _uin(), "iLink-App-Id": "bot",
        "iLink-App-ClientVersion": str((2 << 16) | (2 << 8) | 0),
        "Authorization": f"Bearer {TOKEN}",
    }
    resp = requests.post(f"{BASE.rstrip('/')}/ilink/bot/sendmessage", data=body, headers=headers, timeout=15)
    return resp.status_code == 200

if __name__ == "__main__":
    text = sys.stdin.read()
    if text.strip():
        ok = send(text.strip())
        sys.exit(0 if ok else 1)
