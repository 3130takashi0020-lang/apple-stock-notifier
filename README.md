# Apple整備済 iPhone 在庫通知ツール

## フォルダ構成

```
apple_stock_notifier/
├── config/
│   ├── config.json          <- 実際の設定（機密。Git管理外）
│   └── config.example.json  <- テンプレート
└── script/
    ├── config_loader.py     <- config.json 読み込みモジュール
    ├── mailer.py            <- Gmail送信モジュール（再利用可）
    ├── scraper.py           <- ページ取得＆在庫パースモジュール（再利用可）
    ├── test_mail.py         <- ① Gmail疎通確認
    └── test_scrape.py       <- ② 在庫検知確認
```

※ 本番監視（notifier）と GitHub Actions は、検知確認が済んでから追加します。

## 監視対象（config.json の monitor.watch）

色と容量のリストから全組み合わせを自動生成する。初期設定は
iPhone 16無印・4色（ブラック/ホワイト/ティール/ウルトラマリン）×
2容量（128GB/256GB）＝ 8通り。

```json
"monitor": {
  "target_url": "https://www.apple.com/jp/shop/refurbished/iphone",
  "check_interval_minutes": 5,
  "watch": [
    {
      "model": "iPhone 16",
      "exclude": ["Pro", "Plus", "Max"],
      "colors": ["ブラック", "ホワイト", "ティール", "ウルトラマリン"],
      "capacities": ["128GB", "256GB"]
    }
  ]
}
```

色や容量を足したいときは、colors / capacities に語を追加するだけ。
（色名は Apple の表記と一字一句一致させること）

## ② 在庫検知の確認

```bash
cd script
python test_scrape.py
```

確認ポイント:
- 「検知ロジックのテスト: iPhone 15 Pro 128GB … [OK]」と出る
  → 検知ロジックが正しく機能している証明
- iPhone 16 各種は現状すべて「在庫なし」
  → まだ整備済に登場していないため（想定どおり）

将来 iPhone 16 が整備済に登場したら、その行が「[在庫あり!]」に変わる。

## 注意
- iPhone 16 の整備済での正確な表記は登場後に最終確認するのが確実
  （発売中モデルと同じ色名になる見込み）
- config/config.json は機密情報を含むため Git にコミットしない（.gitignore 済み）
