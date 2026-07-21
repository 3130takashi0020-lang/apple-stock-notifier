"""
設定ローダー モジュール

config/config.json を読み込んで dict として返す。
script/ から見て 1つ上の config/config.json を参照する。

  apple_stock_notifier/
  ├── script/   <- このファイルはここ
  └── config/config.json
"""
import json
import os

# このファイル（script/config_loader.py）の場所を基準に config.json のパスを決める。
# 実行時のカレントディレクトリに依存しないようにするため。
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "config.json")


def load_config(path: str = None) -> dict:
    """config.json を読み込んで返す。

    ファイルが無い / JSON が壊れている場合は分かりやすい例外を送出する。
    """
    path = path or CONFIG_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {path}\n"
            f"config/config.example.json をコピーして config.json を作成してください。"
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"config.json の形式が不正です: {e}") from e


def get_gmail_config(config: dict = None) -> dict:
    """Gmail 関連設定を取り出し、最低限の検証を行う。

    戻り値: {address, app_password, notify_to, smtp_host, smtp_port}
    """
    config = config or load_config()
    gmail = config.get("gmail", {})
    smtp = config.get("smtp", {})

    address = gmail.get("address", "").strip()
    app_password = gmail.get("app_password", "").replace(" ", "").strip()
    notify_to = gmail.get("notify_to", "").strip() or address

    if not address or not app_password:
        raise ValueError(
            "config.json の gmail.address / gmail.app_password が未設定です。"
        )

    return {
        "address": address,
        "app_password": app_password,
        "notify_to": notify_to,
        "smtp_host": smtp.get("host", "smtp.gmail.com"),
        "smtp_port": int(smtp.get("port", 465)),
    }


def get_monitor_config(config: dict = None) -> dict:
    """監視関連設定を取り出す。

    watch グループ（model/colors/capacities/exclude）を、
    色×容量のすべての組み合わせに展開して watch_items にする。

    戻り値:
      {
        "target_url": str,
        "check_interval_minutes": int,
        "watch_items": [
          {"label": str, "keywords": [...], "ng_keywords": [...]}, ...
        ]
      }
    """
    config = config or load_config()
    monitor = config.get("monitor", {})

    target_url = monitor.get(
        "target_url", "https://www.apple.com/jp/shop/refurbished/iphone"
    )
    interval = int(monitor.get("check_interval_minutes", 5))

    watch_items = []
    for group in monitor.get("watch", []):
        model = group.get("model", "").strip()
        exclude = group.get("exclude", [])
        colors = group.get("colors", [])
        capacities = group.get("capacities", [])
        if not model or not colors or not capacities:
            continue
        # 色 × 容量 の全組み合わせを展開
        for capacity in capacities:
            for color in colors:
                label = f"{model} {capacity} {color}"
                watch_items.append({
                    "label": label,
                    "keywords": [model, capacity, color],
                    "ng_keywords": list(exclude),
                })

    return {
        "target_url": target_url,
        "check_interval_minutes": interval,
        "watch_items": watch_items,
    }
