# juggler-dashboard CLAUDE.md

## このツールのゴール
アナスロの過去データを見て、店・機種・島・台番の扱いがどう変化しているかを確認できるビューアにする。
「この台に座る」と断定するのではなく、データ鮮度・件数・期間差・ホール図の位置根拠を見て、ユーザーが判断できる材料を整理する。

理想の1日の流れ：
1. Macローカルの `run_daily.sh` が前日分データを取得する
2. 集計JSONが生成され、GitHubへpushされる
3. スマホ/PCでダッシュボードを開き、概況・変遷・ホール図・機種/台履歴を見る
4. ユーザーが店・機種・台番の扱い変化を読んで判断する

## 現在のアーキテクチャ
| ファイル | 役割 |
|---|---|
| scrape_juggler.py | ana-slo.comをスクレイピング → raw_data.csv / store_model_summary.csv / store_freshness.json を更新 |
| compute.py | raw_data.csvを集計・ベイズ計算 → data.jsonを生成 |
| morning_compute.py | 朝イチ用MVP集計 → morning_data.jsonを生成 |
| candidate_compute.py | morning_data.jsonをもとに candidate_data.json を生成し、raw_data.csvから seat_data.json を生成 |
| index.html | エントリポイント |
| style.css | スタイル |
| app.js | ダッシュボードロジック |
| store_list.json | 対象店舗リスト |
| store_freshness.json | 店舗別データ取得日時 |

## 現在の運用方針
- データ取得・生成・pushはMacローカルの `run_daily.sh` に一本化する。
- GitHub Actionsではデータ生成・pushをしない。Actionsは構文/JSON検証のみ。
- 実戦セッション保存・フィードバック学習・GAS読込は現在の通常運用では使わないため削除済み。
- `candidate_compute.py` は `morning_data.json` を再利用し、朝イチ集計を再実行しない。

## 実行スケジュール（JST）
- 毎朝7:31に launchd（Mac ローカル）で自動実行
- `run_daily.sh` の実行順：
  1. `scrape_juggler.py`
  2. `compute.py`
  3. `morning_compute.py`
  4. `candidate_compute.py`
  5. 生成データをcommit/push
- 重複データ対策：同じ日付・店名・台番号・機種名は上書き

## 対象店舗
| 店舗名 | 換金率 | 備考 |
|---|---|---|
| 鶴見UNO | 4.9枚 | source=manual |
| マルハン都築 | 5.0枚 | 現在のcanonical表記 |
| 中山UNO | 等価 | source=manual |
| エスパス日拓新宿歌舞伎町 | 5.17枚 | source=manual |
| みんレポ優良店 | 各店舗に依存 | store_list.json参照 |

## 開発ルール
- 3ファイル構成（index.html・style.css・app.js）を維持する。
- compute.pyを変更したら必ずpy_compileで構文確認する。
- git commitは機能単位で行う。
- raw_data.csvは大きいため、不必要な全行読み直し・再集計を増やさない。

## データ仕様
raw_data.csvカラム：日付・店名・機種名・台番号・G数・差枚・BB・RB・合成確率・BB確率・RB確率
エンコード：utf-8-sig（BOM付き）。読み書き両方encoding='utf-8-sig'を使うこと。

data.jsonトップキー：updated_at・stores・specialByStore・byStore・predictionAccuracy
byStore[店名]キー：special・dayStats・modelStats・nextStats・heatmap・weekMatrix・dayWdayMatrix・taiDetail・dateSummary・weekdayStats・todayAnalysis

## 変遷ビューア方針
- 分析の主役は過去データの変化（店×期間×機種×台番号/位置）。
- `compute.py` は `data.json.byStore[store].trendView` に店舗推移・機種推移・台履歴を出力する。
- `morning_data.json` / `candidate_data.json` は互換維持するが、メインUIでは朝候補の断定表示には使わない。
- ホール図は現行スタイルを維持し、当日差枚・直近推移・過去根拠・スマスロ扱いを見るビューとして扱う。
- 外部情報（旧イベ・取材・入替など）はv1では自動取得せず、将来重ねるための枠だけ用意する。

## 仮ラベル定義
- 強上候補：G数5000以上・RB設定4相当以上・合算設定4相当以上
- 上候補：G数3500以上・RB設定4相当以上または合算設定4相当以上
- 除外寄り：G数2500未満・BBだけ強い台・差枚だけ良い台

## 技術的注意事項
- 店舗スラグはURLエンコード済み文字列。変更前に必ずデコードして確認する。
- JST日付処理：new Date()はUTCになるため、必ずJSTに変換してから日付比較する。
- `store_freshness.json` の `data_date` は取得元データ日、`morning_data.json` / `candidate_data.json` の `data_date` は生成対象日として扱われている。
