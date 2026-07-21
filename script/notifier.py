"""
本番の監視オーケストレーション

処理の流れ:
  1) ページ取得＆在庫チェック
  2) 前回の状態（state ファイル）を読み込む
  3) 「前回は在庫なし → 今回在庫あり」に変わった製品だけ通知メールを送る
  4) 今回の状態を state ファイルに保存

これにより、入荷し続けている間に毎回メールが飛ぶことを防ぎ、
「入荷した瞬間」だけ通知される。

使い方:
  cd script
  python notifier.py                      # 本番設定 config/config.json を使用
  python notifier.py --config ../config/config.test.json   # テスト設定を使用

state ファイルの場所:
  config の monitor.state_file で指定可能。未指定ならプロジェクト直下の state.json。
  設定ごとに別ファイルにできるので、テストと本番の状態が混ざらない。
"""
import argparse
import json
import os
from datetime import datetime

from config_loader import (
    _PROJECT_ROOT,
    load_config,
    get_gmail_config,
    get_monitor_config,
)
from scraper import fetch_html, check_stock
from mailer import send_mail


def resolve_state_path(config: dict) -> str:
    """state ファイルの絶対パスを決める。

    monitor.state_file が指定されていればそれを使う（相対パスは
    プロジェクト直下を基準に解決）。未指定なら state.json。
    """
    monitor = config.get("monitor", {})
    name = monitor.get("state_file", "state.json")
    if os.path.isabs(name):
        return name
    return os.path.join(_PROJECT_ROOT, name)


def load_state(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Apple整備済 在庫監視")
    parser.add_argument(
        "--config", default=None,
        help="使用する config.json のパス（未指定なら config/config.json）",
    )
    args = parser.parse_args()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 在庫チェック開始")

    # 設定読み込み
    config = load_config(args.config)
    gmail_cfg = get_gmail_config(config)
    monitor = get_monitor_config(config)
    watch_items = monitor["watch_items"]
    url = monitor["target_url"]
    state_path = resolve_state_path(config)

    # ページ取得
    try:
        html = fetch_html(url)
    except Exception as e:  # noqa: BLE001
        print(f"[エラー] ページ取得失敗: {e}")
        return

    result = check_stock(html, watch_items)
    prev_state = load_state(state_path)
    new_state = {}
    newly_in_stock = []

    for label, matched in result.items():
        in_stock_now = bool(matched)
        was_in_stock = prev_state.get(label, False)
        new_state[label] = in_stock_now

        print(f"  - {label}: {'在庫あり' if in_stock_now else '在庫なし'}")

        # 「なし → あり」に変化したものだけ通知対象
        if in_stock_now and not was_in_stock:
            newly_in_stock.append((label, matched))

    # 通知
    if newly_in_stock:
        lines = ["以下の製品が入荷しました！\n"]
        for label, matched in newly_in_stock:
            lines.append(f"■ {label}")
            for m in matched:
                lines.append(f"   {m}")
            lines.append("")
        lines.append(f"確認ページ: {url}")
        lines.append(f"検知時刻: {now}")
        body = "\n".join(lines)
        subject = "【入荷通知】Apple整備済 iPhone"

        try:
            send_mail(subject, body, gmail_config=gmail_cfg)
            print(f"  → 入荷通知メールを送信しました（{len(newly_in_stock)}件）。")
        except Exception as e:  # noqa: BLE001
            print(f"  → [エラー] メール送信失敗: {e}")
            # 送信失敗時は状態を保存せず、次回リトライさせる
            return
    else:
        print("  → 新規入荷なし。通知は送りません。")

    save_state(state_path, new_state)
    print(f"状態を保存しました: {state_path}")


if __name__ == "__main__":
    main()
