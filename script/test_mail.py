"""
Gmail 疎通確認スクリプト

config/config.json に設定した Gmail アカウントから、
自分宛て（notify_to）にテストメールを送る。
これが届けば、通知の土台（送信）が正しく動くと確認できる。

使い方:
  cd script
  python test_mail.py
"""
from datetime import datetime

from config_loader import get_gmail_config
from mailer import send_mail


def main():
    print("=== Gmail 疎通確認 ===")

    try:
        cfg = get_gmail_config()
    except Exception as e:  # noqa: BLE001
        print(f"[エラー] 設定の読み込みに失敗: {e}")
        return

    print(f"送信元: {cfg['address']}")
    print(f"送信先: {cfg['notify_to']}")
    print(f"SMTP : {cfg['smtp_host']}:{cfg['smtp_port']}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "【疎通テスト】Apple整備済 在庫通知ツール"
    body = (
        "このメールはテスト送信です。\n"
        f"送信時刻: {now}\n\n"
        "このメールが届いていれば、Gmail送信の設定は正常です。"
    )

    try:
        send_mail(subject, body, gmail_config=cfg)
        print("\n[成功] テストメールを送信しました。受信箱を確認してください。")
    except Exception as e:  # noqa: BLE001
        print(f"\n[失敗] 送信に失敗しました: {e}")
        print("確認ポイント:")
        print("  ・app_password が正しいか（16桁）")
        print("  ・2段階認証が有効か")
        print("  ・address（Gmailアドレス）が正しいか")


if __name__ == "__main__":
    main()
