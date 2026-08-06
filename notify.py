# -*- coding: utf-8 -*-
"""
新着の信号機関連入札(国家公安委員会)をメールで通知するバッチスクリプト。

前回実行以降の「新着」を判定する代わりに、公告日(CFT_Issue_Date)が
直近2日以内のものを毎回まとめて通知する(状態を保存する仕組みが不要でシンプル)。
1日1回の実行を想定し、多少の重複通知は許容する設計。

実行方法:
    python notify.py

必要な環境変数:
    SMTP_HOST      例: smtp.gmail.com
    SMTP_PORT      例: 587
    SMTP_USER      送信元メールアドレス
    SMTP_PASSWORD  メールアプリパスワード等
    MAIL_TO        通知先メールアドレス(複数の場合はカンマ区切り)
    MAIL_FROM      省略時は SMTP_USER を使う
"""

from __future__ import annotations

import datetime as dt
import os
import smtplib
import sys
from email.mime.text import MIMEText

import kkj_client

LOOKBACK_DAYS = 2  # 公告日がこの日数以内のものを通知対象にする


def build_email_body(results: list[dict]) -> str:
    lines = [
        f"信号機入札ナビ: 新着の信号機関連入札(国家公安委員会) {len(results)}件",
        "",
    ]
    for r in results:
        lines.append(f"■ {r.get('projectName') or '(件名不明)'}")
        if r.get("organizationName"):
            lines.append(f"  発注機関: {r['organizationName']}")
        loc = " ".join(filter(None, [r.get("prefectureName"), r.get("cityName")]))
        if loc:
            lines.append(f"  地域: {loc}")
        if r.get("cftIssueDate"):
            lines.append(f"  公告日: {r['cftIssueDate'][:10]}")
        if r.get("tenderSubmissionDeadline"):
            lines.append(f"  入札締切: {r['tenderSubmissionDeadline'][:10]}")
        if r.get("externalDocumentURI"):
            lines.append(f"  詳細: {r['externalDocumentURI']}")
        lines.append("")
    lines.append("-- ")
    lines.append("このメールは信号機入札ナビの自動通知バッチから送信されています。")
    return "\n".join(lines)


def send_mail(subject: str, body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    mail_from = os.environ.get("MAIL_FROM", smtp_user)
    mail_to = [addr.strip() for addr in os.environ["MAIL_TO"].split(",") if addr.strip()]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = ", ".join(mail_to)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(mail_from, mail_to, msg.as_string())


def main() -> int:
    today = dt.date.today()
    start = today - dt.timedelta(days=LOOKBACK_DAYS)
    cft_issue_date = f"{start.isoformat()}/"

    data = kkj_client.search(cft_issue_date=cft_issue_date, count="1000")

    if data["error"]:
        print(f"検索エラー: {data['error']}", file=sys.stderr)
        return 1

    results = data["results"]
    if not results:
        print("新着なし。メールは送信しません。")
        return 0

    subject = f"【信号機入札ナビ】新着 {len(results)}件（{today.isoformat()}）"
    body = build_email_body(results)

    try:
        send_mail(subject, body)
    except KeyError as e:
        print(f"環境変数 {e} が設定されていません。SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/MAIL_TO を設定してください。", file=sys.stderr)
        return 1
    except smtplib.SMTPException as e:
        print(f"メール送信に失敗しました: {e}", file=sys.stderr)
        return 1

    print(f"{len(results)}件をメール送信しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
