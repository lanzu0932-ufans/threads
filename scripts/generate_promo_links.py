#!/usr/bin/env python3
"""
手動生成含代碼的推廣連結
使用 Affiliates.one 追蹤連結格式
"""
import json
import urllib.parse
from datetime import datetime, timezone

# 配置
CONFIG_FILE = "config/affiliates.json"
STATE_FILE = "memory/trip-promo-state.json"
LIST_FILE = "memory/trip-promo-list.md"
MEMORY_DIR = "memory"

# 你的代碼
YOUR_PROMO_CODE = "YINGKUO001"

# Affiliates.one 追蹤連結配置
TRACKING_BASE = "https://vbtrax.com/track/clicks"
OFFER_ID = "3569"  # Trip.com Offer ID
TRACKING_CODE = "c627c2bc980829d9fb82ec23d62e9841206b5b9633e0e5f10169a44365091bac8562"

def load_config():
    """加載配置"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置檔案不存在: {CONFIG_FILE}")
        return None
    except Exception as e:
        print(f"❌ 讀取配置失敗: {e}")
        return None

def load_promotions():
    """加載促銷活動"""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("promotions", [])
    except FileNotFoundError:
        print(f"❌ 狀態檔案不存在: {STATE_FILE}")
        return []
    except Exception as e:
        print(f"❌ 讀取狀態失敗: {e}")
        return []

def generate_affiliate_link(target_url, promo_code=None):
    """
    手動生成 Affiliates.one 追蹤連結

    格式: https://vbtrax.com/track/clicks/{offer_id}/{tracking_code}?t={encoded_target_url}&coupon={promo_code}
    """
    encoded_url = urllib.parse.quote_plus(target_url)

    link = f"{TRACKING_BASE}/{OFFER_ID}/{TRACKING_CODE}?t={encoded_url}"

    if promo_code:
        link += f"&coupon={promo_code}"

    return link

def save_with_promo_links(promotions):
    """
    使用生成的含代碼連結保存促銷活動
    """
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()

    # 保存 Markdown
    lines = [
        "# Trip.com 促銷活動列表",
        f"**最後更新時間**: {now_str} (Asia/Taipei)",
        f"**總計**: {len(promotions)} 個",
        f"**推廣來源**: Affiliates.one 追蹤連結 (手動生成，含代碼)",
        ""
    ]

    for idx, promo in enumerate(promotions, 1):
        title = promo.get("title", "")
        url = promo.get("url", "")
        source = promo.get("source", "未知")
        offer_id = promo.get("id", "未知")

        # 生成含代碼的推廣連結
        promo_link = generate_affiliate_link(url, YOUR_PROMO_CODE)
        # 不含代碼的連結（用於對比）
        regular_link = generate_affiliate_link(url, None)

        lines.append(f"### {idx}. {title}")
        lines.append(f"- **來源**: {source}")
        lines.append(f"- **Offer ID**: {offer_id}")
        lines.append(f"- **原始連結**: {url}")
        lines.append(f"- **推廣連結 (含代碼 {YOUR_PROMO_CODE})**: {promo_link}")
        lines.append(f"- **推廣連結 (不含代碼)**: {regular_link}")
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(LIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 保存 JSON state
    state = {
        "last_check": now_str,
        "promo_code": YOUR_PROMO_CODE,
        "promotions": []
    }

    for promo in promotions:
        url = promo.get("url", "")
        offer_id = promo.get("id", "未知")

        # 生成連結
        promo_link = generate_affiliate_link(url, YOUR_PROMO_CODE)
        regular_link = generate_affiliate_link(url, None)

        state["promotions"].append({
            "id": offer_id,
            "title": promo.get("title", ""),
            "url": url,
            "source": promo.get("source", "未知"),
            "affiliate_link_with_code": promo_link,
            "affiliate_link": regular_link,
            "promo_code": YOUR_PROMO_CODE
        })

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"✅ 已儲存：{len(promotions)} 個促銷活動")
    return len(promotions)

def main():
    print("=" * 50)
    print("🚀 含代碼推廣連結生成工具 (手動模式)")
    print("=" * 50)
    print(f"📱 你的專屬代碼: {YOUR_PROMO_CODE}")
    print(f"🔗 追蹤連結基礎: {TRACKING_BASE}/{OFFER_ID}/[追蹤碼]")

    # 第一步：加載促銷活動
    print("\n📍 第一步：加載促銷活動...")
    promotions = load_promotions()
    if not promotions:
        print("❌ 找不到促銷活動")
        return

    print(f"✅ 找到 {len(promotions)} 個促銷活動")

    # 第二步：生成推廣連結
    print("\n📍 第二步：生成含代碼推廣連結...")
    print(f"   使用代碼: {YOUR_PROMO_CODE}")

    # 第三步：保存結果
    print("\n📍 第三步：保存結果...")
    save_with_promo_links(promotions)

    print("\n" + "=" * 50)
    print("📊 結果")
    print("=" * 50)
    print(f"\n總計: {len(promotions)} 個促銷活動")
    print(f"生成連結: {len(promotions)} 個")

    print("\n✅ 已儲存到:")
    print(f"  - {LIST_FILE}")
    print(f"  - {STATE_FILE}")

    print("\n📌 連結格式說明:")
    print(f"   - 基礎連結: {TRACKING_BASE}/{OFFER_ID}/[追蹤碼]?t=[編碼目標URL]")
    print(f"   - 含代碼: 增加參數 &coupon={YOUR_PROMO_CODE}")

if __name__ == "__main__":
    main()
