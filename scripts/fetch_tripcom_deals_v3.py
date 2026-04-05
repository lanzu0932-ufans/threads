#!/usr/bin/env python3
"""
Trip.com 促銷活動抓取腳本 v3
修正：
- 正確的促銷頁 URL (/sale/deals/)
- 首頁 Slider 完整滾動抓取
- 正確的 affiliate tracking URL (clicks/3569)
- 移除 hardcoded 清單，全部動態抓取
"""

import json
import os
from datetime import datetime, timezone
from urllib.parse import quote
from playwright.sync_api import sync_playwright

MEMORY_DIR = "/home/ying/桌面/happy/memory"
STATE_FILE = os.path.join(MEMORY_DIR, "trip-promo-state.json")
LIST_FILE = os.path.join(MEMORY_DIR, "trip-promo-list.md")

AFFILIATE_BASE = "https://vbtrax.com/track/clicks/3569/c627c2bc980829d9fb82ec23d62e9841206b5b9633e0e5f10169a44365091bac8562"

def make_affiliate_link(url):
    clean = url.split('?')[0]
    return f"{AFFILIATE_BASE}?t={quote(clean, safe='')}"

def fetch_deals_page(page):
    """抓取 /sale/deals/ 完整促銷列表"""
    promos = {}
    print("📄 抓取促銷頁 /sale/deals/ ...")
    page.goto("https://tw.trip.com/sale/deals/?locale=zh-TW&curr=TWD", timeout=30000, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # 持續滾動直到底部，確保懶加載完全觸發
    prev_height = 0
    for _ in range(10):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        height = page.evaluate("document.body.scrollHeight")
        if height == prev_height:
            break
        prev_height = height

    links = page.query_selector_all("a[href*='/sale/w/']")
    print(f"  找到 {len(links)} 個促銷連結")

    for link in links:
        try:
            href = link.get_attribute("href") or ""
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://tw.trip.com{href}"
            # 去掉 query string 作為 key 去重
            key = href.split("?")[0]
            if key in promos:
                continue

            # 抓標題：優先找圖片 alt、再找文字
            title = ""
            img = link.query_selector("img")
            if img:
                title = (img.get_attribute("alt") or "").strip()
            if not title:
                title = " ".join((link.inner_text() or "").split())
            if not title:
                title = key.split("/")[-1].replace(".html", "").replace("-", " ")

            promos[key] = {"title": title, "url": key, "source": "促銷頁"}
        except:
            continue

    print(f"  ✅ 促銷頁共 {len(promos)} 個（去重後）")
    return promos

def fetch_homepage_slider(page):
    """完整滾動首頁，並點擊 slider 翻頁抓取所有 slide"""
    promos = {}
    print("🏠 抓取首頁 Slider ...")
    page.goto("https://tw.trip.com/?locale=zh-TW&curr=TWD", timeout=30000, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # 點擊 slider 按鈕翻頁（最多翻 15 次）
    for i in range(15):
        links = page.query_selector_all("a[href*='/sale/w/']")
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                if href.startswith("/"):
                    href = f"https://tw.trip.com{href}"
                key = href.split("?")[0]
                if key in promos:
                    continue
                title = ""
                img = link.query_selector("img")
                if img:
                    title = (img.get_attribute("alt") or "").strip()
                if not title:
                    title = " ".join((link.inner_text() or "").split())
                if not title:
                    title = key.split("/")[-1].replace(".html", "").replace("-", " ")
                promos[key] = {"title": title, "url": key, "source": "首頁Slider"}
            except:
                continue

        # 嘗試點擊 next 按鈕
        clicked = False
        for selector in [
            "[class*='next']", "[class*='arrow-right']", "[class*='right']",
            "button[aria-label*='next']", "button[aria-label*='Next']",
            ".swiper-button-next", "[class*='slick-next']"
        ]:
            btn = page.query_selector(selector)
            if btn:
                try:
                    btn.click()
                    page.wait_for_timeout(800)
                    clicked = True
                    break
                except:
                    continue
        if not clicked:
            break

    # 也整頁滾動一次補漏
    page.evaluate("window.scrollTo(0, 0)")
    for _ in range(8):
        page.evaluate("window.scrollBy(0, 600)")
        page.wait_for_timeout(500)
        links = page.query_selector_all("a[href*='/sale/w/']")
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                if href.startswith("/"):
                    href = f"https://tw.trip.com{href}"
                key = href.split("?")[0]
                if key in promos:
                    continue
                title = ""
                img = link.query_selector("img")
                if img:
                    title = (img.get_attribute("alt") or "").strip()
                if not title:
                    title = " ".join((link.inner_text() or "").split())
                if not title:
                    title = key.split("/")[-1].replace(".html", "").replace("-", " ")
                promos[key] = {"title": title, "url": key, "source": "首頁"}
            except:
                continue

    print(f"  ✅ 首頁共 {len(promos)} 個（去重後）")
    return promos

def save_results(all_promos):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Markdown
    lines = [
        "# Trip.com 促銷活動列表",
        f"**最後更新時間**: {now_str} (Asia/Taipei)",
        f"**總計**: {len(all_promos)} 個",
        ""
    ]
    for i, p in enumerate(all_promos, 1):
        lines += [
            f"### {i}. {p['title']}",
            f"- **來源**: {p['source']}",
            f"- **原始連結**: {p['url']}",
            f"- **台灣版追蹤連結**: {make_affiliate_link(p['url'])}",
            ""
        ]
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # JSON state
    state = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "promotions": [{"title": p["title"], "url": p["url"], "source": p["source"]} for p in all_promos]
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"✅ 已儲存：{len(all_promos)} 個促銷活動")

def load_previous_state():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f).get("promotions", [])

def main():
    print("=" * 50)
    print("🚀 Happy Agent - Trip.com 促銷抓取 v3")
    print("=" * 50)

    prev_urls = {p["url"] for p in load_previous_state()}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
        )

        deals = fetch_deals_page(page)
        slider = fetch_homepage_slider(page)
        browser.close()

    # 合併，促銷頁優先，slider 補充
    merged = {**slider, **deals}  # deals 覆蓋 slider（促銷頁更準確）
    all_promos = list(merged.values())
    all_promos.sort(key=lambda x: x["title"])

    # 比對新增/移除
    current_urls = {p["url"] for p in all_promos}
    new_ones = [p for p in all_promos if p["url"] not in prev_urls]
    removed = [u for u in prev_urls if u not in current_urls]

    print(f"\n📊 結果：{len(all_promos)} 個促銷（新增 {len(new_ones)}，移除 {len(removed)}）")
    if new_ones:
        print("🆕 新增：")
        for p in new_ones:
            print(f"  + {p['title']}")
    if removed:
        print("❌ 移除：")
        for u in removed:
            print(f"  - {u}")

    save_results(all_promos)
    return len(all_promos)

if __name__ == "__main__":
    main()
