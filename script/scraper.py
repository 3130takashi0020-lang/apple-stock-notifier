"""
Apple 整備済ページ 取得＆在庫パースモジュール（使いまわし可能）

Apple の整備済ページは「在庫がある製品だけ」がリンク付きで掲載される。
したがって、掲載中の製品タイトル一覧を取り出し、
狙っている製品のキーワードにマッチするものがあれば「在庫あり」と判定する。

製品タイトルの形式（例）:
  iPhone 15 Pro 128GB - ブラックチタニウム（SIMフリー）[整備済製品]
"""
import time
import unicodedata

import requests
from bs4 import BeautifulSoup


def _normalize(text: str) -> str:
    """文字列を NFKC 正規化する。

    Apple のページと config.json で、見た目が同じでも Unicode の内部表現
    （NFC/NFD、全角/半角など）が異なることがある。比較する両側を同じ形に
    揃えることで、正規化形のズレによる検知漏れを防ぐ。
    """
    return unicodedata.normalize("NFKC", text)

# 行儀よくアクセスするための固定ヘッダー
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}
REQUEST_TIMEOUT = 20  # 秒


def fetch_html(url: str, retries: int = 3) -> str:
    """対象ページの HTML を取得する。

    失敗時は指数バックオフ（2秒→4秒→8秒）でリトライする。
    """
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS,
                                timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"ページ取得に失敗しました: {last_err}")


def parse_products(html: str) -> list[str]:
    """掲載中の製品タイトル一覧を返す。

    整備済製品のリンクは /shop/product/ を含むため、それを手掛かりに抽出し、
    重複を排除して返す（順序は保持）。
    """
    soup = BeautifulSoup(html, "html.parser")
    titles = []
    for a in soup.find_all("a", href=True):
        if "/shop/product/" in a["href"]:
            text = a.get_text(strip=True)
            if text:
                titles.append(text)
    seen = set()
    unique = []
    for t in titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def match_item(titles: list[str], item: dict) -> list[str]:
    """1つの監視対象 item に一致する製品タイトルを返す。

    keywords をすべて含み、ng_keywords をどれも含まないタイトルにマッチ。
    """
    keywords = [_normalize(kw) for kw in item.get("keywords", [])]
    ng = [_normalize(n) for n in item.get("ng_keywords", [])]
    matched = []
    for title in titles:
        ntitle = _normalize(title)
        if all(kw in ntitle for kw in keywords) and not any(n in ntitle for n in ng):
            matched.append(title)  # 表示は元のタイトルを返す
    return matched


def check_stock(html: str, watch_items: list[dict]) -> dict:
    """在庫チェックを実行する。

    戻り値: { item_label: [マッチした製品タイトル, ...], ... }
    在庫なしの item はマッチ結果が空リストになる。
    """
    titles = parse_products(html)
    return {item["label"]: match_item(titles, item) for item in watch_items}
