#!/usr/bin/env python3
"""
VisePanda Daily News Briefing — Real-time news aggregator for China.

Fetches from 4 categories via direct Chinese API endpoints (no Tavily).
Outputs Markdown suitable for WeChat delivery.

Usage:
  python3 news_briefing.py morning   # 早报
  python3 news_briefing.py evening   # 晚报
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from html import unescape

BEIJING_TZ = timezone(timedelta(hours=8))

# News API endpoints that work from China
APIS = {
    # 财经 — 新浪财经滚动
    "finance_sina": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=8&page=1",
    # 国际 — 澎湃国际新闻
    "intl_thepaper": "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar",
    # 科技 — 36氪快讯
    "tech_36kr": "https://36kr.com/api/newsflash",
    # 国内热点 — 澎湃热榜
    "hot_thepaper": "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar",
}


def fetch(url, timeout=15):
    """Fetch a URL and return text content."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html, */*",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def parse_sina_finance(text):
    """Parse Sina finance roll API response."""
    if not text:
        return []
    try:
        d = json.loads(text)
        items = d.get("result", {}).get("data", [])
        results = []
        for item in items[:6]:
            title = item.get("title", "").strip()
            url = item.get("url", "") or item.get("link", "")
            if title and len(title) > 6:
                results.append({"title": title, "url": url})
        return results
    except (json.JSONDecodeError, KeyError):
        return []


def parse_thepaper(text):
    """Parse ThePaper hot news / international."""
    if not text:
        return []
    try:
        d = json.loads(text)
        items = d.get("data", {}).get("hotNews", [])
        results = []
        for item in items[:6]:
            title = item.get("name", "") or item.get("title", "")
            url = item.get("url", "") or item.get("link", "")
            if title and len(title) > 6:
                results.append({"title": title.strip(), "url": url})
        return results
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def parse_36kr(text):
    """Parse 36Kr newsflash API."""
    if not text:
        return []
    try:
        d = json.loads(text)
        items = d.get("data", {}).get("items", [])
        results = []
        for item in items[:6]:
            title = item.get("title", "") or item.get("widget_title", "") or ""
            url = item.get("url", "") or item.get("link", "") or ""
            title = title.strip()
            if title and len(title) > 6:
                results.append({"title": title, "url": url})
        return results
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def fetch_international_news():
    """Fetch international news via Xinhua (works from China) with Reuters fallback."""
    results = []
    
    # Primary: Xinhua International (works great from China)
    for url, name in [
        ("https://www.xinhuanet.com/world/", "Xinhua World"),
    ]:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                }
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            
            # Xinhua format: h3 tags or title attributes
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
            if titles:
                titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if len(t) > 10]
            if not titles:
                titles = re.findall(r'<a[^>]*title="([^"]{10,})"', html)
            
            seen = set()
            for t in titles:
                clean = unescape(t).strip()
                if clean and len(clean) > 8 and clean not in seen:
                    seen.add(clean)
                    results.append({"title": clean, "url": "https://www.xinhuanet.com/world/"})
                    if len(results) >= 4:
                        break
            if results:
                break
        except Exception:
            continue
    
    # Fallback: Reuters (might be slower from China)
    if not results:
        try:
            req = urllib.request.Request(
                "https://www.reuters.com/world/china/",
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            titles = re.findall(r'<h[2-3][^>]*>(.*?)</h[2-3]>', html, re.DOTALL)
            seen = set()
            for t in titles:
                clean = re.sub(r'<[^>]+>', '', t).strip()
                clean = unescape(clean)
                if clean and len(clean) > 10 and clean not in seen:
                    seen.add(clean)
                    results.append({"title": clean, "url": "https://www.reuters.com/world/china/"})
                    if len(results) >= 4:
                        break
        except Exception:
            pass
    
    return results


def format_briefing(mode, finance, intl, tech, hot, intl_fallback):
    """Format the final Markdown briefing."""
    now = datetime.now(BEIJING_TZ)
    date_str = now.strftime("%Y年%m月%d日")
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    
    emoji = "📰" if mode == "morning" else "🌙"
    title_emoji = "早报" if mode == "morning" else "晚报"
    
    lines = [f"{emoji} 每日{title_emoji} | {date_str} {weekday_cn}", ""]
    
    # ── 财经 ──
    lines.append("💰 **财经速览**")
    if finance:
        for item in finance[:4]:
            url_part = f" · [链接]({item['url']})" if item.get("url") else ""
            lines.append(f"• {item['title'][:65]}{url_part}")
    else:
        lines.append("• 暂未获取到财经数据")
    lines.append("")
    
    # ── 国际 ──
    lines.append("🌍 **国际局势**")
    intl_items = intl if intl else intl_fallback
    if intl_items:
        for item in intl_items[:4]:
            url_part = f" · [链接]({item['url']})" if item.get("url") else ""
            lines.append(f"• {item['title'][:65]}{url_part}")
    else:
        lines.append("• 暂未获取到国际新闻")
    lines.append("")
    
    # ── 科技 ──
    lines.append("🔬 **科技前沿**")
    if tech:
        for item in tech[:4]:
            url_part = f" · [链接]({item['url']})" if item.get("url") else ""
            lines.append(f"• {item['title'][:65]}{url_part}")
    else:
        lines.append("• 暂未获取到科技新闻")
    lines.append("")
    
    # ── 国内热点 ──
    lines.append("🔥 **国内热点**")
    if hot:
        for item in hot[:4]:
            url_part = f" · [链接]({item['url']})" if item.get("url") else ""
            lines.append(f"• {item['title'][:65]}{url_part}")
    else:
        lines.append("• 暂未获取到国内热点")
    lines.append("")
    
    # Footer
    lines.append("---")
    if mode == "morning":
        lines.append(f"⏰ *{date_str} 早间速览 · 今晚22:00见*")
    else:
        lines.append(f"⏰ *{date_str} 晚间盘点 · 明早7:00见*")
    
    return "\n".join(lines)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    
    # Fetch all sources in parallel (sequential due to no async lib)
    print(f"[News] Fetching {mode} briefing...", file=sys.stderr)
    
    # 1. Finance
    finance_text = fetch(APIS["finance_sina"])
    finance = parse_sina_finance(finance_text)
    if finance:
        print(f"[News] Finance: {len(finance)} items", file=sys.stderr)
    else:
        print(f"[News] Finance: failed", file=sys.stderr)
    
    # 2. Tech
    tech_text = fetch(APIS["tech_36kr"])
    tech = parse_36kr(tech_text)
    if tech:
        print(f"[News] Tech: {len(tech)} items", file=sys.stderr)
    else:
        print(f"[News] Tech: failed", file=sys.stderr)
    
    # 3. International + Hot from ThePaper
    thepaper_text = fetch(APIS["intl_thepaper"])
    
    # ThePaper has both hot news and categories
    hot = parse_thepaper(thepaper_text)
    if hot:
        print(f"[News] Hot/Domestic: {len(hot)} items", file=sys.stderr)
    else:
        print(f"[News] Hot: failed", file=sys.stderr)
    
    # For international, try Reuters + use some ThePaper items as fallback
    intl = fetch_international_news()
    if intl:
        print(f"[News] International: {len(intl)} items", file=sys.stderr)
    else:
        print(f"[News] International: failed, using fallback", file=sys.stderr)
    
    # International fallback: take items from hot that sound international
    intl_fallback = []
    intl_keywords = ["美国", "特朗普", "拜登", "欧洲", "俄罗斯", "普京", "乌克兰", "日本", "韩国", 
                     "朝鲜", "北约", "联合国", "G7", "G20", "OPEC", "美联储", "美元", "油价",
                     "全球", "国际", "欧盟", "英国", "法国", "德国", "伊朗", "以色列", "印度",
                     "中美", "关税", "贸易战", "外交", "大使"]
    if hot:
        for item in hot:
            for kw in intl_keywords:
                if kw in item["title"]:
                    intl_fallback.append(item)
                    break
        intl_fallback = intl_fallback[:4]
    
    # Build briefing
    output = format_briefing(mode, finance, intl, tech, hot, intl_fallback)
    
    print(output)


if __name__ == "__main__":
    main()
