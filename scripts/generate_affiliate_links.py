#!/usr/bin/env python3
"""
使用 Affiliates.one API 生成推廣連結
生成含有指定代碼的 Deeplinks
"""
import json
import sys
import os

# 配置
CONFIG_FILE = "config/affiliates.json"
MEMORY_DIR = "memory"
STATE_FILE = f"{MEMORY_DIR}/trip-promo-state.json"
LIST_FILE = f"{MEMORY_DIR}/trip-promo-list.md"

# 你的代碼（可以修改這裡）
YOUR_PROMO_CODE = "YINGKUO001"  # 你的專屬代碼

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

def test_api_connection():
    """測試 API 連接和權限"""
    config = load_config()
    if not config:
        return False

    api_key = config.get("api_key")
    if not api_key:
        print("❌ 找不到 API Key")
        return False

    print("\n" + "=" * 50)
    print("🧪 測試 Affiliates.one API 連接")
    print("=" * 50)

    # 測試 1: API Endpoint 連通性
    print(f"\n📍  測試端點: {config.get('api_endpoint', 'N/A')}")

    import requests
    try:
        response = requests.get(config.get("api_endpoint", ""), timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API 端點正常")
        else:
            print(f"⚠️ API 狀態: {response.status_code}")
    except Exception as e:
        print(f"❌ 連接測試失敗: {e}")

    # 測試 2: Deeplinks API
    print(f"\n📍 測試 Deeplinks API...")
    deeplinks_url = f"{config.get('api_endpoint', '')}/deeplinks"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    # 測試不同的請求格式
    test_offer_id = "2226"  # Trip.com 的 offer ID

    # 格式 1: 標準格式
    payload1 = {
        "offer_id": test_offer_id,
        "promo_code": YOUR_PROMO_CODE
    }

    print(f"📡 請求 Payload 1: {json.dumps(payload1, ensure_ascii=False)}")
    try:
        response = requests.post(deeplinks_url, json=payload1, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 格式 1 成功")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, ensure_ascii=False)[:200]}")
            except:
                print("   Response: 無法解析")
        else:
            print(f"⚠️ 格式 1 失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 格式 1 請求失敗: {e}")

    # 格式 2: 嘗試更簡單的格式
    payload2 = {
        "offer_id": test_offer_id,
        "promo_code": YOUR_PROMO_CODE
    }

    print(f"📡 請求 Payload 2: {json.dumps(payload2, ensure_ascii=False)}")
    try:
        response = requests.post(deeplinks_url, json=payload2, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 格式 2 成功")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, ensure_ascii=False)[:200]}")
            except:
                print("   Response: 無法解析")
        else:
            print(f"⚠️ 格式 2 失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 格式 2 請求失敗: {e}")

    # 檢查是否需要 token
    print(f"\n📍 檢查是否需要認證...")
    try:
        headers_with_auth = headers.copy()
        headers_with_auth["Authorization"] = f"Bearer {api_key}"  # 嘗試用 Bearer token
        response = requests.get(config.get("api_endpoint", ""), headers=headers_with_auth, timeout=10)
        print(f"Status with token: {response.status_code}")
    except Exception as e:
        print(f"❌ Token 測試失敗: {e}")

    print("\n" + "=" * 50)
    print("📋 測試完成")
    print("=" * 50)

    return config.get("api_key") is not None

def get_deeplinks(api_key, offer_id, promo_code=None):
    """
    使用 Affiliates.one API 生成 Deeplinks
    """
    url = f"{config.get('api_endpoint', '')}/deeplinks"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    payload = {
        "offer_id": offer_id,
        "promo_code": promo_code or ""
    }

    print(f"📡 請求生成 Deeplinks...")
    print(f"  Offer ID: {offer_id}")
    print(f"  代碼: {promo_code or '無'}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            deeplinks = result.get("data", {}).get("deeplinks", {})
            print(f"✅ 成功生成 {len(deeplinks)} 個 Deeplinks")

            # 列出所有 Deeplinks
            print("\n📋 可用 Deeplinks:")
            for link_type, link in deeplinks.items():
                print(f"  - {link_type}: {link}")
            return deeplinks
        else:
            error_msg = result.get("message", "Unknown error")
            print(f"❌ API 返回錯誤: {error_msg}")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 錯誤: {e}")
        return None
    except Exception as e:
        print(f"❌ 請求失敗: {e}")
        return None

def save_with_affiliate_links(promotions, deeplinks_map):
    """
    使用生成的 Deeplinks 保存促銷活動
    """
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()

    # 保存 Markdown
    lines = [
        "# Trip.com 促銷活動列表",
        f"**最後更新時間**: {now_str} (Asia/Taipei)",
        f"**總計**: {len(promotions)} 個",
        f"**推廣來源**: Affiliates.one Deeplinks API (含代碼)",
        ""
    ]

    for idx, promo in enumerate(promotions, 1):
        title = promo.get("title", "")
        url = promo.get("url", "")
        source = promo.get("source", "未知")

        # 嘗試從 URL 提取 Offer ID
        offer_id = "未知"
        if "/sale/w/" in url:
            try:
                offer_id = url.split("/sale/w/")[1].split("/")[0]
            except:
                pass

        # 獲取對應的 Deeplink
        deeplink = deeplinks_map.get(offer_id, {})

        lines.append(f"### {idx}. {title}")
        lines.append(f"- **來源**: {source}")
        lines.append(f"- **原始連結**: {url}")

        # 根據 Deeplink 類型選擇最適合的連結
        if deeplink and isinstance(deeplink, dict):
            # 嘗試選擇代碼推廣連結
            code_promo_link = deeplink.get("promo_code_link", "")
            if code_promo_link:
                link = code_promo_link
                lines.append(f"- **代碼推廣連結** ({YOUR_PROMO_CODE}): {link}")
                lines.append("")
            # 其他連結
            for link_type, link_url in deeplink.items():
                lines.append(f"- **{link_type}: {link_url}")
        else:
            if deeplink:
                lines.append(f"- **代碼推廣連結**: {deeplink}")
            else:
                lines.append("- **預設連結**: 使用預構建的追蹤連結")

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
        # 提取 Offer ID
        offer_id = "未知"
        url = promo.get("url", "")
        if "/sale/w/" in url:
            try:
                offer_id = url.split("/sale/w/")[1].split("/")[0]
            except:
                pass

        # 獲取 Deeplink
        deeplink = deeplinks_map.get(offer_id, {})

        state["promotions"].append({
            "id": offer_id,
            "title": promo.get("title", ""),
            "url": url,
            "source": source,
            "affiliate_link": deeplink.get("direct", "") if deeplink and isinstance(deeplink, dict) else "",
            "promo_code": YOUR_PROMO_CODE,
            "deeplinks": deeplink if isinstance(deeplink, dict) else {}
        })

    with open( STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"✅ 已儲存：{len(promotions)} 個促銷活動")
    return len(promotions)

def main():
    print("=" * 50)
    print("🚀 Affiliates.one Deeplinks 生成工具 v2")
    print("=" * 50)
    print(f"📱 你的專屬代碼: {YOUR_PROMO_CODE}")

    # 第一步：測試 API 連接
    print("\n📍 第一步：測試 API 連接...")
    api_key = test_api_connection()
    if not api_key:
        print("\n❌ API 連接測試失敗，無法繼續")
        return

    # 第二步：加載促銷活動
    print("\n📋 第二步：加載促銷活動...")
    promotions = load_promotions()
    if not promotions:
        print("❌ 找不到促銷活動")
        return

    print(f"✅ 找到 {len(promotions)} 個促銷活動")

    # 第三步：為每個 Offer ID 生成 Deeplinks
    print("\n📡 第三步：生成 Deeplinks...")
    print(f"   使用代碼: {YOUR_PROMO_CODE}")

    offer_ids = set()
    deeplinks_map = {}

    for promo in promotions:
        url = promo.get("url", "")
        if "/sale/w/" in url:
            try:
                offer_id = url.split("/sale/w/")[1].split("/")[0]
                if offer_id and offer_id not in offer_ids:
                    print(f"\n📡 為成為 Offer {offer_id} 生成 Deeplinks...")
                    deeplinks = get_deeplinks(api_key, offer_id, YOUR_PROMO_CODE)
                    if deeplinks:
                        deeplinks_map[offer_id] = deeplinks
                        offer_ids.add(offer_id)
                    else:
                        print(f"   ⚠️ Offer {offer_id} 失敗")
            except Exception as e:
                print(f"   ⚠️ 處理 Offer ID 時出錯: {e}")

    # 等待所有請求完成
    import time
    time.sleep(2)

    # 保存帶 Deeplinks 的促銷活動
    print("\n📋 第四步：保存結果...")
    save_with_affiliate_links(promotions, deeplinks_map)

    print("\n" + "=" * 50)
    print("📊 結果")
    print("=" * 50)
    print(f"\n總計: {len(promotions)} 個促銷活動")
    print(f"成功生成 Deeplinks: {len(offer_ids)} 個")
    print(f"失敗: {len(promotions) - len(offer_ids)}")

    print("\n✅ 已儲存到:")
    print(f"  - {LIST_FILE}")
    print(f"  - {STATE_FILE}")

if __name__ == "__main__":
    main()
