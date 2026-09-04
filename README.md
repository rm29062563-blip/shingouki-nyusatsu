# 信号機入札ナビ

中小企業庁が公開している「官公需情報ポータルサイト検索API」
(http://www.kkj.go.jp/api/) を使って、信号機関連（発注機関: 国家公安委員会）
の入札公告を検索できるWebアプリです。

- API利用に登録・APIキーは不要です（誰でも無料で利用できます）
- 締切が近い順に自動で並び替え
- 都道府県・分類（工事／物品／役務）・公示種別・入札資格（A〜D）で絞り込み
- 締切までの残り日数に応じて、カードの左端が信号機のように
  🟢緑（余裕あり）→🟡黄（10日以内）→🔴赤（3日以内）で変化
- 仕様書などの添付ファイルへの直接リンクを表示
- 新着案件を毎朝メールで通知するバッチ（`notify.py`）付き

## ファイル構成

| ファイル | 役割 |
|---|---|
| `app.py` | Webアプリ本体（Flask） |
| `kkj_client.py` | API呼び出し・検索ロジック（Webアプリと通知バッチで共用） |
| `notify.py` | 新着案件をメール通知するバッチ（Renderのcronジョブから実行） |
| `requirements.txt` | 依存パッケージ |
| `render.yaml` | Renderへのデプロイ設定（Webアプリ＋cronジョブ） |

## ローカルでの使い方

```bash
pip install -r requirements.txt
python app.py
```

ブラウザで http://localhost:5001 を開いてください。

## 新着メール通知の設定

`notify.py` は以下の環境変数を使ってメールを送信します（Gmailの場合は
「アプリパスワード」の発行が必要です。Googleアカウントの
セキュリティ設定 → 2段階認証を有効化 → アプリパスワードで取得できます）。

| 環境変数 | 例 |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 送信元メールアドレス |
| `SMTP_PASSWORD` | アプリパスワード |
| `MAIL_FROM` | 省略時は `SMTP_USER` を使用 |
| `MAIL_TO` | 通知先メールアドレス（複数はカンマ区切り） |

Renderにデプロイする場合、`render.yaml` に定義済みの
`shingouki-nyusatsu-notify` というcronジョブが、毎日日本時間 8:00 に
自動実行されるよう設定されています（UTC 23:00 = JST 8:00）。
Renderダッシュボードの該当サービスの「Environment」タブで、上記の
環境変数を設定してください。

ローカルで手動テストする場合：

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your-address@gmail.com
export SMTP_PASSWORD=xxxxxxxxxxxxxxxx
export MAIL_TO=your-address@gmail.com
python notify.py
```

## 仕組み

- `app.py` がFlaskサーバーとして動作し、ブラウザからの検索リクエストを
  受け取ると、サーバー側から `http://www.kkj.go.jp/api/` にリクエストを
  送ります（サーバー側で呼び出すことで、ブラウザのCORS制限を回避してい
  ます）。
- 返ってくるXMLをJSONに変換し、締切が近い順に並び替えてフロント画面に
  表示します。
- `notify.py` は公告日が直近2日以内の案件をAPIから直接検索して
  メール送信します（状態を保存する仕組みがないシンプルな設計のため、
  多少の重複通知が発生することがあります）。

## 注意事項

- 官公需情報ポータルサイトは**すべての**入札情報を網羅しているわけでは
  ありません。個別案件の最新状況・詳細は各発注機関に直接ご確認くださ
  い。
- APIの利用規約により、本アプリでは画面下部にAPI利用元へのリンクを明記
  しています。
- 検索APIの詳細仕様: https://www.kkj.go.jp/doc/ja/api_guide.pdf

## Renderへのデプロイ

`render.yaml` を使ってWebアプリとcronジョブをまとめてデプロイできます。
Renderダッシュボードで「New +」→「Blueprint」からこのリポジトリを選ぶと、
`render.yaml` の内容が自動で読み込まれます。

