#!/usr/bin/env python3
"""
extract-yt-cookies.py — 从运行中的 Chromium (CDP) 提取 YouTube cookie，
保存为 yt-dlp 可用的 Netscape 格式 cookies.txt。

前置条件：
  1. Chromium 已以 --remote-debugging-port=9222 --remote-allow-origins=* 启动
  2. 用户已通过 noVNC 登录 YouTube

用法：python3 extract-yt-cookies.py [--port PORT] [--output PATH]
"""

import json, urllib.request, websocket, time, sys, os

def main():
    port = 9222
    output = "/tmp/yt-cookies.txt"

    # 解析参数
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
        if a == "--output" and i + 1 < len(args):
            output = args[i + 1]

    # 连接 CDP
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5)
        tabs = json.loads(resp.read())
        ws_url = tabs[0]['webSocketDebuggerUrl']
    except Exception as e:
        print(f"❌ CDP 连接失败: {e}")
        print(f"   确保 Chromium 已以 --remote-debugging-port={port} 启动")
        sys.exit(1)

    # 提取所有 cookie
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        ws.recv()
        ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
        resp = json.loads(ws.recv())
        ws.close()
    except Exception as e:
        print(f"❌ Cookie 提取失败: {e}")
        sys.exit(1)

    cookies = resp.get('result', {}).get('cookies', [])

    if not cookies:
        print("⚠️  没有提取到任何 cookie")
        sys.exit(1)

    # 保存为 Netscape 格式
    # ⚠️ 格式陷阱：domain 必须保留前导点，否则 Python http.cookiejar assert 失败
    FUTURE = int(time.time()) + 365 * 86400

    with open(output, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        for c in cookies:
            domain = c.get('domain', '')
            include_sub = "TRUE" if domain.startswith('.') else "FALSE"
            path = c.get('path', '/')
            secure = "TRUE" if c.get('secure', False) else "FALSE"
            expires = int(c.get('expires', 0))
            if expires <= 0:  # session cookie → 设未来时间
                expires = FUTURE
            name = c.get('name', '')
            value = c.get('value', '')
            f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

    # 统计
    yt_count = len([c for c in cookies if 'youtube' in c.get('domain', '')])
    login_count = len([c for c in cookies if 'SID' in c.get('name', '') or 'LOGIN_INFO' in c.get('name', '')])

    print(f"✅ 已保存 {len(cookies)} 个 cookie 到 {output}")
    print(f"   YouTube cookie: {yt_count} 个")
    print(f"   登录 cookie: {login_count} 个")

    if login_count == 0:
        print("⚠️  未检测到登录 cookie — 用户可能未登录 YouTube")
        print(f"   文件大小: {os.path.getsize(output)} bytes")
        sys.exit(0)
    else:
        print(f"   ✅ 用户已登录，cookie 可用")
        print(f"   文件大小: {os.path.getsize(output)} bytes")

if __name__ == "__main__":
    main()
