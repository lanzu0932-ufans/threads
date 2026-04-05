#!/usr/bin/env python3
"""
改進版 Trip.com 促銷活動抓取腳本 v2
深度抓取首页，获取所有促销链接
"""

import json
import os
from datetime import datetime, timezone
import re
from playwright.sync_api import sync_playwright

# 配置
MEMORY_DIR = "/home/ying/桌面/happy/memory"
STATE_FILE = os.path.join(MEMORY_DIR, "trip-promo-state.json")
LIST_FILE = os.path.join(MEMORY_DIR, "trip-promo-list.md")

AFFILIATE_TRACKING = {
    "offer_id": 2226,
    "affiliate_base": "https://vbtrax.com/track/clicks/2226"
}

# 已知的促销活动列表（基于之前抓取的）
KNOWN_PROMOTIONS = [
    {
        "title": "LINE Bank 週三日韓泰旅遊低至85折",
        "url": "https://tw.trip.com/sale/w/18090/linebankpromotion.html",
        "coupon_code": "",
        "discount": "15%"
    },
    {
        "title": "國泰世華 日本賞限時優惠",
        "url": "https://tw.trip.com/sale/w/34099/cub.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "學生航班優惠",
        "url": "https://tw.trip.com/sale/w/3319/global-student-flight-campaign.html",
        "coupon_code": "HKD30",
        "discount": "",
        "is_infinity": True
    },
    {
        "title": "新開幕飯店高達 20% OFF",
        "url": "https://tw.trip.com/sale/w/21947/super-new-opening-hotels.html",
        "coupon_code": "",
        "discount": "20%"
    },
    {
        "title": "Trip.com x Visa 專屬優惠",
        "url": "https://tw.trip.com/sale/w/21051/visapromotion.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "門票/體驗快閃優惠",
        "url": "https://tw.trip.com/sale/w/15871/happyfriday.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "【Trip 遊釜山】每週一機票優惠！",
        "url": "https://tw.trip.com/sale/w/31376/superbusan-promotion.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "探索日本（4月限定）",
        "url": "https://tw.trip.com/sale/w/15500/april-2026-super-destination-bloom-in-japan.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "機票專區",
        "url": "https://tw.trip.com/sale/w/4823/flight-deals.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "【大陸深度旅遊】春季旅遊限時優惠",
        "url": "https://tw.trip.com/sale/w/19280/gochina.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "【韓國自由行攻略】來回機票$4500起！",
        "url": "https://tw.trip.com/sale/w/4337/southkorea-destination.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "【2026 走進東北亞】4月主題優惠",
        "url": "https://tw.trip.com/sale/w/4823/seasonal-promotion.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "週末親子出遊Trip",
        "url": "https://tw.trip.com/sale/w/27386/familytraveldeals.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "【快閃 Trip 沖繩】每週一機票+飯店優惠！",
        "url": "https://tw.trip.com/sale/w/17859/okinawapromotion.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "台灣旅遊5折起",
        "url": "https://tw.trip.com/sale/w/4823/hotel-deals.html",
        "coupon_code": "",
        "discount": "50%"
    },
    {
        "title": "【泰國深度旅遊】陽光假期立刻出發",
        "url": "https://tw.trip.com/sale/w/26497/go-thailand.html",
        "coupon_code": "",
        "discount": ""
    },
    {
        "title": "【香港澳門自由行】指定飯店5%回饋",
        "url": "https://tw.trip.com/sale/w/5025/cn-hk-mo-promotion.html",
        "coupon_code": "",
        "discount": "5%"
    },
    {
        "title": "【玩轉日本】機票、飯店、門票最新優惠",
        "url": "https://tw.trip.com/sale/w/4217/japan-travel.html",
        "coupon_code": "",
        "discount": ""
    }
]

def generate_affiliate_link(target_url, coupon_code=None):
    """生成带追踪的推广链接"""
    if not target_url:
        return None

    clean_url = target_url.split('?')[0]
    affiliate_url = f"{AFFILIATE_TRACKING['affiliate_base']}/c627c2bc980829d9fb82ec23d62e9841206b5b9633e0e5f10169a44365091bac8562?t={clean_url}"

    return affiliate_url

def fetch_homepage_deals():
    """
    从首页抓取所有促销链接
    使用多种策略获取完整列表
    """
    promotions = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("🌐 访问 Trip.com 台湾首页...")
            page.goto("https://tw.trip.com", timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)

            # 获取页面上所有链接
            all_links = page.query_selector_all("a[href]")
            print(f"  页面总链接数: {len(all_links)}")

            # 筛选促销相关链接
            promo_patterns = ['/sale/', '/w/', '/promotion', '/offer', '/coupon']
            seen_urls = set()

            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue

                    # 获取链接文字
                    try:
                        text = link.evaluate("el => el.innerText").strip()
                    except:
                        text = ""

                    # 清理文字
                    text = ' '.join(text.split())
                    if not text:
                        continue

                    # 检查是否为促销链接
                    if any(pattern in href for pattern in promo_patterns):
                        # 构建完整URL
                        if href.startswith("/"):
                            full_url = f"https://tw.trip.com{href}"
                        else:
                            full_url = href

                        # 去重
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        # 限制标题长度
                        if len(text) > 100:
                            text = text[:100] + "..."

                        promotions.append({
                            "title": text,
                            "url": full_url,
                            "source": "首页"
                        })
                except:
                    continue

            print(f"  ✓ 找到促销链接: {len(promotions)} 个")

        except Exception as e:
            print(f"❌ 首页抓取失败: {e}")

        finally:
            browser.close()

    return promotions

def crawl_promo_page_details(promotion):
    """
    访问单个促销页面获取详情
    """
    url = promotion["url"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=15000)

            # 提取标题
            title_selectors = ["h1", "h2", "[class*='title']"]
            title = promotion["title"]
            for sel in title_selectors:
                el = page.query_selector(sel)
                if el:
                    try:
                        t = el.evaluate("el => el.innerText").strip()
                        if t:
                            title = t
                            break
                    except:
                        pass

            # 提取优惠码
            content = page.content()
            coupon_patterns = [
                r'代碼[：:\s]*([A-Z0-9]+)',
                r'優惠碼[：:\s]*([A-Z0-9]+)',
                r'折扣碼[：:\s]*([A-Z0-9]+)',
                r'code[：:\s]*([A-Z0-9]+)',
                r'([A-Z]{3,10}\d{2,6})',
            ]
            coupon_code = ""
            for pattern in coupon_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    coupon_code = match.group(1).upper()
                    break

            # 提取折扣
            discount_match = re.search(r'(\d+)%?\s*[-OFF折扣折]', content)
            discount = discount_match.group(1) + "%" if discount_match else ""

            browser.close()

            return {
                "title": title,
                "coupon_code": coupon_code,
                "discount": discount
            }

        except Exception as e:
            print(f"  ⚠️ 详情抓取失败 ({url[:50]}...): {e}")
            browser.close()
            return {
                "title": promotion["title"],
                "coupon_code": "",
                "discount": ""
            }

def merge_with_known_promotions(scraped_promos):
    """
    合并抓取的活动和已知活动列表
    """
    # 从抓取的活动中提取URL
    scraped_urls = {p["url"] for p in scraped_promos}

    # 合并
    all_promotions = []

    # 添加抓取到的活动
    for promo in scraped_promos:
        all_promotions.append({
            "title": promo["title"],
            "url": promo["url"],
            "source": "抓取",
            "coupon_code": "",
            "discount": ""
        })

    # 添加已知的活动
    for promo in KNOWN_PROMOTIONS:
        if promo["url"] not in scraped_urls:
            all_promotions.append({
                "title": promo["title"],
                "url": promo["url"],
                "source": "已知",
                "coupon_code": promo.get("coupon_code", ""),
                "discount": promo.get("discount", ""),
                "is_infinity": promo.get("is_infinity", False)
            })
        else:
            # 更新已抓取活动的信息（从已知列表中获取优惠码等）
            for p in all_promotions:
                if p["url"] == promo["url"]:
                    if not p.get("coupon_code") and promo.get("coupon_code"):
                        p["coupon_code"] = promo["coupon_code"]
                    if not p.get("discount") and promo.get("discount"):
                        p["discount"] = promo["discount"]
                    if promo.get("is_infinity"):
                        p["is_infinity"] = True
                    break

    return all_promotions

def save_to_files(promotions):
    """保存促销列表到 Markdown 和 JSON"""
    # 保存 Markdown
    lines = [
        "# Trip.com 促銷活動列表",
        f"**更新時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')} (台北時間)",
        f"**來源**: 首頁抓取 + 已知活動列表",
        "",
        f"**總計**: {len(promotions)} 個促銷活動",
        "",
        "---",
        ""
    ]

    for idx, promo in enumerate(promotions, 1):
        lines.append(f"## {idx}. {promo['title']}")
        lines.append(f"**來源**: {promo['source']}")
        if promo.get("coupon_code"):
            lines.append(f"**優惠碼**: `{promo['coupon_code']}`")
        if promo.get("discount"):
            lines.append(f"**折扣**: {promo['discount']}")
        lines.append(f"**連結**: {generate_affiliate_link(promo['url'])}")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(LIST_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # 保存 JSON state
    state = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "promotions": []
    }

    for promo in promotions:
        # 提取 ID
        id_match = re.search(r'/(\d+)[/\.]', promo["url"])
        promo_id = int(id_match.group(1)) if id_match else None

        state["promotions"].append({
            "id": promo_id,
            "title": promo["title"],
            "coupon_code": promo.get("coupon_code", ""),
            "source": promo.get("source", ""),
            "url": promo["url"],
            "is_infinity_time": promo.get("is_infinity", False)
        })

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return state

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Happy Agent - Trip.com 促销抓取 v2")
    print("=" * 50)

    # 1. 抓取首页
    print("\n📌 第一步: 从首页抓取促销链接...")
    scraped = fetch_homepage_deals()

    # 2. 合并已知活动
    print("\n📌 第二步: 合并已知活动列表...")
    all_promos = merge_with_known_promotions(scraped)
    print(f"✅ 合并后: 共 {len(all_promos)} 个促销活动")

    # 3. 抓取详情（使用已知数据，不访问每个页面）
    print("\n📌 第三步: 更新活动详情...")
    for promo in all_promos:
        # 从已知列表中查找详情
        for known in KNOWN_PROMOTIONS:
            if promo["url"] == known["url"]:
                if known.get("coupon_code"):
                    promo["coupon_code"] = known["coupon_code"]
                if known.get("discount"):
                    promo["discount"] = known["discount"]
                if known.get("is_infinity"):
                    promo["is_infinity"] = known["is_infinity"]
                break
        print(f"  ✓ {promo['title'][:30]} - {promo.get('coupon_code', '') or '无优惠码'}")

    # 4. 保存文件
    print("\n📌 第四步: 保存文件...")
    state = save_to_files(all_promos)
    print(f"✅ 已保存到:")
    print(f"  - {LIST_FILE}")
    print(f"  - {STATE_FILE}")

    # 5. 汇总
    print("\n" + "=" * 50)
    print("📊 抓取汇总")
    print("=" * 50)
    print(f"总计促销活动: {len(state['promotions'])} 个")
    print(f"有优惠码的: {sum(1 for p in state['promotions'] if p['coupon_code'])} 个")
    print(f"来源分布: {len([p for p in all_promos if p.get('source') == '抓取'])} 个抓取 + {len([p for p in all_promos if p.get('source') == '已知'])} 个已知")
    print("\n✅ 抓取完成！")

    return len(all_promos)

if __name__ == "__main__":
    main()
