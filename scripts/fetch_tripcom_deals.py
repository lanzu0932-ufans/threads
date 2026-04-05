#!/usr/bin/env python3
"""
改進版 Trip.com 促銷活動抓取腳本
更完整地抓取首頁 Slider + 優惠頁的所有促銷活動
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

def generate_affiliate_link(target_url, coupon_code=None):
    """
    生成带追踪的推广链接
    如果有 coupon_code，会在 URL 中添加
    """
    if not target_url:
        return None

    # 移除已有的追踪参数
    clean_url = target_url.split('?')[0]

    # 构建完整的推广链接
    affiliate_url = f"{AFFILIATE_TRACKING['affiliate_base']}/c627c2bc980829d9fb82ec23d62e9841206b5b9633e0e5f10169a44365091bac8562?t={clean_url}"

    # 如果有优惠码，添加到 URL
    if coupon_code:
        separator = '&' if '?' in clean_url else '?'
        affiliate_url = affiliate_url.replace(clean_url, f"{clean_url}{separator}coupon={coupon_code}")

    return affiliate_url

def fetch_homepage_slider():
    """
    抓取 Trip.com 首页 Slider 促销区块
    包含所有轮播的促销活动
    """
    promotions = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("🌐 访问 Trip.com 台湾首页...")
            page.goto("https://tw.trip.com", timeout=30000, wait_until="networkidle")

            # 等待页面加载
            page.wait_for_timeout(3000)

            # 方法1: 尝试抓取轮播组件
            try:
                # 查找轮播容器 - 可能的 selector
                carousel_selectors = [
                    "[class*='carousel']",
                    "[class*='slider']",
                    "[class*='banner']",
                    "[class*='promotion']",
                    ".swiper-wrapper",
                    ".slick-list",
                    "div[class*='Banner']",
                    "div[class*='Promo']",
                ]

                for selector in carousel_selectors:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"  ✓ 找到轮播元素 ({len(elements)} 个): {selector}")

                        # 获取所有轮播项
                        items = page.query_selector_all(f"{selector} a[href*='/sale/']")
                        for idx, item in enumerate(items):
                            try:
                                href = item.get_attribute("href")
                                if href and "/sale/" in href:
                                    # 获取标题（可能来自多个位置）
                                    title_candidates = [
                                        item.query_selector("h1, h2, h3, .title, .name, [class*='Title']"),
                                        item.query_selector("[class*='text']"),
                                    ]

                                    title = f"首页促销 {idx+1}"
                                    for t in title_candidates:
                                        if t:
                                            try:
                                                title = t.evaluate("el => el.innerText").strip()
                                                if title:
                                                    break
                                            except:
                                                continue

                                    # 构建完整URL
                                    if href.startswith("/"):
                                        full_url = f"https://tw.trip.com{href}"
                                    else:
                                        full_url = href

                                    promotions.append({
                                        "source": "首页Slider",
                                        "title": title,
                                        "url": full_url,
                                        "position": idx + 1
                                    })
                                    print(f"    • {title[:50]}")
                            except Exception as e:
                                continue
                        if promotions:
                            break
            except Exception as e:
                print(f"  ⚠️ 轮播抓取失败: {e}")

            # 方法2: 抓取页面上的所有促销链接
            if not promotions:
                print("  🔄 尝试抓取所有促销链接...")
                promo_links = page.query_selector_all("a[href*='/sale/']")
                for idx, link in enumerate(promo_links[:20]):  # 限制前20个
                    try:
                        href = link.get_attribute("href")
                        text = link.evaluate("el => el.innerText").strip()

                        if href and "/sale/" in href and text:
                            if href.startswith("/"):
                                full_url = f"https://tw.trip.com{href}"
                            else:
                                full_url = href

                            promotions.append({
                                "source": "首页促销链接",
                                "title": text,
                                "url": full_url,
                                "position": idx + 1
                            })
                    except:
                        continue

            # 方法3: 抓取特定的促销区块
            try:
                # 查找热门促销区域
                hot_deals = page.query_selector_all("[class*='hot'], [class*='deal'], [class*='offer']")
                for section in hot_deals:
                    links = section.query_selector_all("a[href*='/sale/']")
                    for link in links[:5]:
                        href = link.get_attribute("href")
                        text = link.inner_text().strip()
                        if href and text:
                            if href.startswith("/"):
                                full_url = f"https://tw.trip.com{href}"
                            else:
                                full_url = href
                            # 避免重复
                            if not any(p["url"] == full_url for p in promotions):
                                promotions.append({
                                    "source": "热门促销区",
                                    "title": text,
                                    "url": full_url,
                                    "position": len(promotions) + 1
                                })
            except:
                pass

        except Exception as e:
            print(f"❌ 首页抓取失败: {e}")

        finally:
            browser.close()

    return promotions

def fetch_promo_page_deals():
    """
    抓取 Trip.com 促销页面的所有活动
    尝试多个可能的促销页面 URL
    """
    promotions = []

    # 尝试多个促销页面 URL
    promo_urls = [
        "https://tw.trip.com/promotions",
        "https://tw.trip.com/sales",
        "https://tw.trip.com/coupons",
        "https://tw.trip.com/offer",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for url in promo_urls:
            page = browser.new_page()

            try:
                print(f"\n🌐 访问: {url}")
                try:
                    response = page.goto(url, timeout=15000)
                    if response and response.status != 200:
                        print(f"  ⚠️ 页面状态: {response.status if response else 'failed'}")
                        page.close()
                        continue
                except:
                    page.close()
                    continue

                page.wait_for_timeout(2000)

                # 获取页面内容用于分析
                page_content = page.content()

                # 统计找到的促销链接数量
                promo_links = page.query_selector_all("a[href*='/sale/']")
                all_links = page.query_selector_all("a")

                print(f"  页面信息:")
                print(f"    - 促销链接: {len(promo_links)} 个")
                print(f"    - 总链接数: {len(all_links)} 个")

                # 尝试多种选择器
                card_selectors = [
                    "a[href*='/sale/w/']",
                    "a[href*='/promotion']",
                    "[class*='card'] a[href*='/sale/']",
                    "[class*='item'] a[href*='/sale/']",
                    "[class*='deal'] a[href*='/sale/']",
                    "a[href*='/sale/']",
                    "a[href*='/w/']",
                ]

                found_cards = []
                for selector in card_selectors:
                    cards = page.query_selector_all(selector)
                    if len(cards) > 0:
                        print(f"  ✓ 选择器 '{selector}' 找到 {len(cards)} 个元素")
                        found_cards.extend(cards)

                # 抓取促销卡片
                for idx, card in enumerate(found_cards[:50]):  # 限制前50个
                    try:
                        href = card.get_attribute("href")
                        if not href:
                            continue

                        # 只抓取促销相关链接
                        if not any(pattern in href for pattern in ['/sale/', '/promotion', '/w/', '/offer']):
                            continue

                        # 获取标题
                        try:
                            title = card.evaluate("el => el.innerText").strip()
                        except:
                            title = f"促销活动 {idx+1}"
                        # 清理标题（去除空白和换行）
                        title = ' '.join(title.split())

                        if not title:
                            title = f"促销活动 {idx+1}"

                        # 限制标题长度
                        if len(title) > 100:
                            title = title[:100] + "..."

                        if href.startswith("/"):
                            full_url = f"https://tw.trip.com{href}"
                        else:
                            full_url = href

                        # 避免重复
                        if not any(p["url"] == full_url for p in promotions):
                            promotions.append({
                                "source": url,
                                "title": title,
                                "url": full_url,
                                "position": len(promotions) + 1
                            })
                    except:
                        continue

                # 如果找到足够的促销，就不再尝试其他 URL
                if len(promotions) >= 10:
                    print(f"  ✅ 已找到 {len(promotions)} 个促销活动，停止搜索")
                    break

            except Exception as e:
                print(f"  ⚠️ 抓取失败: {e}")

            finally:
                page.close()

        browser.close()

    return promotions

def extract_promo_details(url):
    """
    深入抓取单个促销页面的详情
    包括: 标题、描述、折扣、优惠码、有效期
    """
    details = {
        "id": None,
        "title": "",
        "coupon_code": "",
        "discount": "",
        "description": "",
        "valid_from": None,
        "valid_to": None,
        "is_infinity": False
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # 提取ID (从URL中)
            id_match = re.search(r'/(\d+)[/\.]', url)
            if id_match:
                details["id"] = int(id_match.group(1))

            # 提取标题
            title_selectors = [
                "h1",
                ".title",
                "[class*='Title']",
                "[class*='headline']",
            ]
            for sel in title_selectors:
                el = page.query_selector(sel)
                if el:
                    try:
                        details["title"] = el.evaluate("el => el.innerText").strip()
                        break
                    except:
                        continue

            # 提取优惠码
            coupon_patterns = [
                r'代碼[：:\s]*([A-Z0-9]+)',
                r'優惠碼[：:\s]*([A-Z0-9]+)',
                r'折扣碼[：:\s]*([A-Z0-9]+)',
                r'code[：:\s]*([A-Z0-9]+)',
                r'coupon[：:\s]*([A-Z0-9]+)',
                r'([A-Z]{3,10}\d{2,6})',  # 常见优惠码格式
            ]

            page_text = page.content()  # 使用 content() 获取完整 HTML
            for pattern in coupon_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    details["coupon_code"] = match.group(1).upper()
                    break

            # 提取折扣百分比
            discount_match = re.search(r'(\d+)%?\s*[-OFF折扣折]', page_text)
            if discount_match:
                details["discount"] = f"{discount_match.group(1)}%"

            # 检查是否无限期
            if any(word in page_text for word in ["長期有效", "不限時", "永久", "infinity", "ongoing"]):
                details["is_infinity"] = True

            browser.close()

    except Exception as e:
        print(f"  ⚠️ 详情抓取失败: {e}")

    return details

def merge_promotions(homepage_promos, promo_page_promos):
    """合并两个来源的促销活动，去重"""
    seen_urls = set()
    merged = []

    for promo in homepage_promos + promo_page_promos:
        url = promo["url"]
        if url not in seen_urls:
            seen_urls.add(url)
            merged.append(promo)

    return merged

def save_to_markdown(promotions):
    """保存促销列表到 Markdown 文件"""
    lines = [
        "# Trip.com 促銷活動列表",
        f"**更新時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')} (台北時間)",
        f"**來源**: 首頁 Slider + 優惠頁面",
        "",
        "---",
        ""
    ]

    for idx, promo in enumerate(promotions, 1):
        # 获取详情
        details = extract_promo_details(promo["url"])

        title = details["title"] or promo["title"]
        coupon = details["coupon_code"] or "无"
        discount = details["discount"] or "见详情"

        lines.append(f"## {idx}. {title}")
        lines.append(f"**來源**: {promo['source']}")
        lines.append(f"**優惠碼**: `{coupon}`")
        lines.append(f"**折扣**: {discount}")
        lines.append(f"**連結**: {generate_affiliate_link(promo['url'], coupon) if coupon else generate_affiliate_link(promo['url'])}")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(LIST_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return promotions

def save_to_state(promotions):
    """保存状态到 JSON 文件"""
    state = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "promotions": []
    }

    for promo in promotions:
        details = extract_promo_details(promo["url"])

        state["promotions"].append({
            "id": details["id"],
            "title": details["title"] or promo["title"],
            "coupon_code": details["coupon_code"],
            "discount": details["discount"],
            "source": promo["source"],
            "url": promo["url"],
            "is_infinity_time": details["is_infinity"]
        })

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return state

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Happy Agent - Trip.com 促销抓取 (改進版)")
    print("=" * 50)

    # 1. 抓取首页 Slider
    print("\n📌 第一步: 抓取首页 Slider 促销区块...")
    homepage_promos = fetch_homepage_slider()
    print(f"✅ 首页 Slider: 找到 {len(homepage_promos)} 个促销活动")

    # 2. 抓取促销页
    print("\n📌 第二步: 抓取促销页面所有活动...")
    promo_page_promos = fetch_promo_page_deals()
    print(f"✅ 促销页面: 找到 {len(promo_page_promos)} 个促销活动")

    # 3. 合并去重
    print("\n📌 第三步: 合并去重...")
    all_promos = merge_promotions(homepage_promos, promo_page_promos)
    print(f"✅ 合并后: 共 {len(all_promos)} 个唯一促销活动")

    # 4. 保存到 Markdown
    print("\n📌 第四步: 保存促销列表...")
    save_to_markdown(all_promos)
    print(f"✅ 已保存到: {LIST_FILE}")

    # 5. 保存到 State
    print("\n📌 第五步: 保存状态...")
    state = save_to_state(all_promos)
    print(f"✅ 已保存到: {STATE_FILE}")

    # 6. 汇总
    print("\n" + "=" * 50)
    print("📊 抓取汇总")
    print("=" * 50)
    print(f"总计促销活动: {len(state['promotions'])} 个")
    print(f"有优惠码的: {sum(1 for p in state['promotions'] if p['coupon_code'])} 个")
    print(f"无限期活动: {sum(1 for p in state['promotions'] if p.get('is_infinity_time'))} 个")
    print("\n✅ 抓取完成！")

    return len(all_promos)

if __name__ == "__main__":
    main()
