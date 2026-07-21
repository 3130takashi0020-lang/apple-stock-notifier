"""
Gmail 送信モジュール（使いまわし可能）

smtplib を使い、Gmail の SMTP(SSL) 経由でメールを送る。
設定は config/config.json から読み込む。

他プロジェクトでも `from mailer import send_mail` で流用できる。

前提:
  - Google アカウントで2段階認証が有効
  - アプリパスワード（16桁）を発行済み
  - config/config.json に address / app_password を設定
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formatdate

from config_loader import get_gmail_config


def send_mail(subject: str, body: str,
              to_addr: str = None,
              gmail_config: dict = None) -> None:
    """メールを1通送信する。

    gmail_config を渡さない場合は config.json から自動で読み込む。
    送信失敗時は例外を送出する（呼び出し側で捕捉する想定）。
    """
    cfg = gmail_config or get_gmail_config()

    from_addr = cfg["address"]
    to_addr = to_addr or cfg["notify_to"]
    app_password = cfg["app_password"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"],
                          context=context, timeout=30) as server:
        server.login(from_addr, app_password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
