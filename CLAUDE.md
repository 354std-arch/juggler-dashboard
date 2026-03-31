# juggler-dashboard

パチンコ店のジャグラー台データを収集・分析する静的ダッシュボード。

## アーキテクチャ

| ファイル | 役割 |
|---|---|
| `scrape_juggler.py` | ana-slo.com をスクレイピング → `raw_data.csv` に追記 |
| `compute.py` | `raw_data.csv` を集計・ベイズ計算 → `data.json` を生成 |
| `index.html` | `data.json` を読む静的ダッシュボード（フレームワーク不使用） |
| GitHub Actions | 毎朝 JST 7:45 に scrape → compute を自動実行 |

## コマンド

```bash
python3 scrape_juggler.py   # 前日分をスクレイピング
python3 compute.py          # data.json を再生成
```

## 重要な注意事項

**店舗スラグ (IMPORTANT)**
- URL 形式: `https://ana-slo.com/YYYY-MM-DD-{slug}/`
- スラグは URL エンコード済み文字列。変更前に必ずデコードして確認する:
  `python3 -c "from urllib.parse import unquote; print(unquote('スラグ'))"`
- マルハン都筑は `筑`（U+7B51）を使用。`築`（U+7BC9）と混同しないこと

**文字コード**
- `raw_data.csv` は `utf-8-sig`（BOM付き）。読み書き両方 `encoding='utf-8-sig'` を使うこと

**重み付け**
- `compute.py` は直近90日のデータに `weight=2.0`、それ以前は `weight=1.0` を付与
- ベイズ計算・平均値は重み付き（`wavg`）で計算される

**ファイルサイズ**
- `raw_data.csv` は 20MB+ になる。全行を不必要にメモリに展開しないこと

## データ仕様

**raw_data.csv カラム:**
`日付, 店名, 機種名, 台番号, G数, 差枚, BB, RB, 合成確率, BB確率, RB確率`

**data.json トップキー:**
`updated_at, stores, specialByStore, byStore, predictionAccuracy`

**byStore[店名] キー:**
`special, dayStats, modelStats, nextStats, heatmap, weekMatrix, dayWdayMatrix, taiDetail, dateSummary, weekdayStats, todayAnalysis`
