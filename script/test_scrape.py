"""
在庫検知 確認スクリプト

Apple の整備済ページを取得し、
  1) 掲載中の全製品タイトルを表示
  2) 検知ロジックのテスト（iPhone 15 Pro 128GB／現在在庫あり）
  3) config.json に登録した監視対象（iPhone 16 各種）の現在の状態
を表示する。

「iPhone 15 Pro が検知できている」ことが確認できれば、
在庫検知ロジックが正しく機能していると判断できる。

使い方:
  cd script
  python test_scrape.py
"""
from config_loader import get_monitor_config
from scraper import fetch_html, parse_products, match_item

# 検知ロジック検証用（現在ページに在庫がある製品）
DETECTION_TEST_ITEM = {
    "label": "iPhone 15 Pro 128GB ブラックチタニウム（検知テスト用）",
    "keywords": ["iPhone 15 Pro", "128GB", "ブラックチタニウム"],
    "ng_keywords": ["Max"],
}


def main():
    print("=== 在庫検知 確認 ===")
    monitor = get_monitor_config()
    url = monitor["target_url"]
    print(f"対象URL: {url}\n")

    try:
        html = fetch_html(url)
    except Exception as e:  # noqa: BLE001
        print(f"[失敗] ページ取得に失敗: {e}")
        return

    titles = parse_products(html)
    print(f"■ 掲載中の製品（{len(titles)}件）:")
    if not titles:
        print("  （製品が取得できませんでした。ページ構造が変わった可能性があります）")
    for t in titles:
        print(f"  - {t}")

    # --- 検知ロジックのテスト ---
    print(f"\n■ 検知ロジックのテスト: {DETECTION_TEST_ITEM['label']}")
    matched = match_item(titles, DETECTION_TEST_ITEM)
    if matched:
        print("  [OK] 検知できました:")
        for m in matched:
            print(f"       {m}")
    else:
        print("  [NG] 検知できませんでした。ページ構造やキーワードを確認してください。")

    # --- 監視対象（iPhone 16 各種）の現在の状態 ---
    watch_items = monitor["watch_items"]
    print(f"\n■ 監視対象の状態（{len(watch_items)}件）:")
    any_in_stock = False
    for item in watch_items:
        matched = match_item(titles, item)
        if matched:
            any_in_stock = True
            print(f"  [在庫あり!] {item['label']}")
            for m in matched:
                print(f"             {m}")
        else:
            print(f"  [在庫なし ] {item['label']}")
    if not any_in_stock:
        print("\n  （iPhone 16 はまだ整備済ページに登場していません。想定どおりです）")


if __name__ == "__main__":
    main()
