# juggler-dashboard CLAUDE.md

## このツールのゴール
朝プッシュ通知が来て「今日は鶴見UNO 23番台（期待時給1,200円）」
→ 行くか判断するだけの状態を作る。
AIが自動でデータ取得・分析・推薦・学習する。
しちろうさんは最終判断だけすればいい。

理想の1日の流れ：
1. 朝、プッシュ通知が来る
2. 「今日は鶴見UNO 23番台（期待時給1,200円）」を確認
3. 行くか判断するだけ
4. 結果が自動で学習される

## アーキテクチャ
| ファイル | 役割 |
|---|---|
| scrape_juggler.py | ana-slo.comをスクレイピング → raw_data.csvに追記 |
| scrape_minrepo.py | みんレポから周辺ホールをスキャン → store_list.json更新 |
| backfill_new_stores.py | 新規店舗の過去データを一括取得 |
| compute.py | raw_data.csvを集計・ベイズ計算 → data.jsonを生成 |
| feedback.py | sessions.jsonとraw_data.csvを照合 → 予測精度を更新（未実装） |
| index.html | エントリポイント |
| style.css | スタイル |
| app.js | ダッシュボードロジック |
| sessions.json | 実戦記録 |
| store_list.json | 対象店舗リスト |
| store_freshness.json | 店舗別データ取得日時 |

## 対象店舗
| 店舗名 | 換金率 | 備考 |
|---|---|---|
| 鶴見UNO | 4.9枚 | source=manual |
| マルハン都筑 | 5.0枚 | アナスロ上は「都筑」(U+7B51)。「築」(U+7BC9)と混同しないこと |
| 中山UNO | 等価 | source=manual |
| エスパス日拓新宿歌舞伎町 | 5.17枚 | source=manual |
| みんレポ優良店 | 各店舗に依存 | スコア65点以上・データ30件以上・ジャグラー系に☆か◎ |

## GitHub Actions実行スケジュール（JST）
- 5:00・6:00・8:00の3回
- scrape_juggler.py → compute.pyの順で実行
- 重複データ対策：同じ日付・店名・台番号は上書き

## 開発ルール
- 実装・修正・git commitまで確認なしで自律的に完結する
- 途中経過の報告は不要。完了時にまとめて報告する
- 3ファイル構成（index.html・style.css・app.js）を必ず維持する
- compute.pyを変更したら必ずpy_compileで構文確認する
- git commitは機能単位でこまめに行う

## 自動検証ルール（UIバグ修正時に必ず実施）
1. data.json構造検証
python3 -c "
import json
d = json.load(open('data.json'))
for store, sv in d['stores'].items():
    models = sv.get('models', {})
    for name, m in list(models.items())[:3]:
        assert 'byDay' in m, f'{store}/{name} にbyDayなし'
        assert len(m['byDay']) > 0, f'{store}/{name} のbyDayが空'
print('✅ data.json構造OK')
"
2. app.js構文チェック
node -e "const fs=require('fs');new Function(fs.readFileSync('app.js','utf8'));console.log('✅ app.js構文OK')" 2>&1
3. compute.py構文チェック
python3 -m py_compile compute.py && echo "✅ compute.py構文OK"

## 要件定義（確定済み・変更不可）
- 答え合わせ閾値：P(設定4以上)60%以上
- 撤退ライン：損切り-2万円 かつ P30%以下で警告
- データ重み付け：直近90日はweight=2.0、それ以前はweight=1.0
- 期待時給通知閾値：1,000円・Web Push形式
- 優良店判定：差枚プラス頻度×0.5＋特定日出玉率×0.5≥65点・データ30件以上・ジャグラー系に☆か◎

## sessions.json保存仕様
保存項目：日付・店舗・台番号・機種・G数・BIG・REG・差枚・小役・ベイズスコア・撤退理由
保存方法：GitHub API経由でスマホから直接push（PAT使用）
PATはLocalStorageに保存済み（設定タブから入力）

## データ仕様
raw_data.csvカラム：日付・店名・機種名・台番号・G数・差枚・BB・RB・合成確率・BB確率・RB確率
エンコード：utf-8-sig（BOM付き）。読み書き両方encoding='utf-8-sig'を使うこと
ファイルサイズ：20MB+のため全行を不必要にメモリに展開しないこと

data.jsonトップキー：updated_at・stores・specialByStore・byStore・predictionAccuracy
byStore[店名]キー：special・dayStats・modelStats・nextStats・heatmap・weekMatrix・dayWdayMatrix・taiDetail・dateSummary・weekdayStats・todayAnalysis・store_freshness

## フィードバックループ設計（未実装・feedback.py新規作成）
設計方針：設定番号の照合ではなく「予測が当たったかを実績で検証する」

flows:
sessions.jsonの1セッション
  └ 予測：P(設定4以上) = 72%
  └ 実戦：G数3000・BB8・RB6
         ↓ 翌朝Actions実行後
raw_data.csvの同日・同店・同台番号
  └ 最終データで合成確率を算出
  └ 機種別閾値と比較して高設定相当か判定
         ↓
ベータ二項モデル更新（EMAで直近に重み付け）
  └ 的中（P高×好実績）→ α +1
  └ 外れ（P高×悪実績）→ β +1

## 機種別フィードバック判定閾値
# ジャグラー系（設定4以上相当）
- アイムジャグラー系：合成1/135以下
- マイジャグラー系：合成1/140以下
- ファンキージャグラー系：合成1/138以下
- ゴーゴージャグラー系：合成1/136以下

# ハナビ系（設定2以上相当・4段階設定のため）
- 新ハナビ：合成1/148以下
- スマスロハナビ：合成1/161以下

※ジャグラーは設定4以上、ハナビは設定2以上を「好実績」と判定する

## 作業レポートの形式
各タスク完了時に以下を必ず報告すること：
- 現在のゴール（朝の推薦通知1台で行くか判断できる状態）への達成度：XX%
- 残タスク数：XX個
- 次のスライスで完了する予定のタスク

## 現在の未解決タスク（上から順に対応する）

### UIバグ修正
- [ ] 日にちフィルター（0の付く日〜ゾロ目）が「該当データなし」になる
- [ ] 機種別 日にちごとの平均差枚が全機種「データなし」になる
- [ ] 第2段階「どの機種・どの狙い方か」が表示されない（JST日付ずれ疑い）
- [ ] 当日/翌日切り替えバグ

### feedback.pyの設計見直し
- [ ] 条件ごと（店舗×機種×特定日/通常日）にα・βを個別管理する
  - 現状：全セッションを1つのα・βで管理→全体的中率しか出ない
  - 改善：条件ごとに個別管理してcompute.pyの事前分布に反映する
  - フォールバック：データ20件以上→店舗×機種×台番号×特定日/通常日、5〜20件→店舗×機種×特定日/通常日、5件未満→店舗×特定日/通常日
  - compute.pyの動的事前分布と役割を分けて加算する形で反映する
  - G数による信頼度重み付けを追加する：3000G以上→1.0、1500〜3000G→0.5、1500G未満→判定しない

### compute.pyの追加改善
- [ ] G数による信頼度重み付けをベイズスコア計算に追加する
  - 3000G以上→重み1.0
  - 1500〜3000G→重み0.5
  - 1500G未満→スコア計算対象外（表示はするが推薦対象外）

## 未実装機能（バグ修正完了後に着手・優先度順）
- [ ] アナスロ自動照合フィードバックループ（feedback.py新規作成）
- [ ] Web Pushプッシュ通知（期待時給1,000円以上で通知）
- [ ] 期待時給計算式の改善
- [ ] 新ハナビ・スマスロハナビのデータ取得追加

## 技術的注意事項
- 店舗スラグはURLエンコード済み文字列。変更前に必ずデコードして確認する
- マルハン都筑は筑（U+7B51）を使用。築（U+7BC9）と混同しないこと
- JST日付処理：new Date()はUTCになるため、必ずJSTに変換してから日付比較する
- raw_data.csvは20MB+のため全行メモリ展開禁止
