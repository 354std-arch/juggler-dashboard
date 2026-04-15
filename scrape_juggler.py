import argparse
import csv
import json
import os
import time
from datetime import date, timedelta, datetime, timezone
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV  = os.path.join(REPO_DIR, "raw_data.csv")
STORE_MODEL_SUMMARY_CSV = os.path.join(REPO_DIR, "store_model_summary.csv")
STORE_FRESHNESS_JSON = os.path.join(REPO_DIR, "store_freshness.json")
STORE_LIST_JSON = os.path.join(REPO_DIR, "store_list.json")
JST = timezone(timedelta(hours=9))

HARDCODED_STORES = [
    ('鶴見UNO',               '%e9%b6%b4%e8%a6%8buno-data'),
    ('マルハン都筑',           '%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%9c%e5%ba%97-data'),
    ('中山UNO',               '%e4%b8%ad%e5%b1%b1uno-data'),
    ('エスパス日拓新宿歌舞伎町', '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data'),
]

KNOWN_SLUG_BY_NAME = {
    '鶴見UNO': '%e9%b6%b4%e8%a6%8buno-data',
    'マルハン都筑': '%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%9c%e5%ba%97-data',
    'マルハン都築': '%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%91%e5%ba%97-data',
    '中山UNO': '%e4%b8%ad%e5%b1%b1uno-data',
    'エスパス新宿': '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data',
    'エスパス日拓新宿歌舞伎町': '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data',
    'SKIP関内店': 'skip%e3%82%b9%e3%83%ad%e3%83%83%e3%83%88%e3%82%af%e3%83%a9%e3%83%96%e9%96%a2%e5%86%85%e5%ba%97-data',
    'マルハンメガシティ横浜町田': '%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e3%83%a1%e3%82%ac%e3%82%b7%e3%83%86%e3%82%a3%e6%a8%aa%e6%b5%9c%e7%94%ba%e7%94%b0-data',
    'ギンザホール707': '%e3%82%ae%e3%83%b3%e3%82%b6%e3%83%9b%e3%83%bc%e3%83%ab707-data',
}

MODEL_NAME_MAP = {
    'ネオアイムジャグラーEX': 'ネオアイムジャグラー',
    'ジャグラーガールズ': 'ジャグラーガールズSS',
    'スマスロ ハナビ': 'スマスロハナビ',
}

NORMAL_TYPE_KEYWORDS = [
    'ジャグラー','ハナビ','クランキー','ニューパルサー',
    'ドリームクランキー','バーサス','タコスロ',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    'Referer': 'https://ana-slo.com/',
}

CSV_HEADER = ['日付','店名','機種名','台番号','G数','差枚','BB','RB','合成確率','BB確率','RB確率']
STORE_MODEL_SUMMARY_HEADER = ['date', 'store', 'model', 'total_diff', 'avg_diff', 'avg_g', 'win_rate']


def slug_from_store_name(store_name):
    if store_name in KNOWN_SLUG_BY_NAME:
        return KNOWN_SLUG_BY_NAME[store_name]
    # ana-slo 側スラッグが未知の店舗向けのフォールバック
    return f'{quote(store_name, safe="").lower()}-data'


def load_target_stores():
    if not os.path.exists(STORE_LIST_JSON):
        print('⚠️  store_list.json がないため、固定4店舗で実行します')
        return HARDCODED_STORES
    try:
        with open(STORE_LIST_JSON, encoding='utf-8') as f:
            payload = json.load(f)
    except Exception as e:
        print(f'⚠️  store_list.json 読み込み失敗({e})のため、固定4店舗で実行します')
        return HARDCODED_STORES

    stores = payload.get('stores', []) if isinstance(payload, dict) else []
    if not isinstance(stores, list):
        print('⚠️  store_list.json の形式不正のため、固定4店舗で実行します')
        return HARDCODED_STORES

    targets = []
    seen = set()
    for store in stores:
        if not isinstance(store, dict):
            continue
        name = str(store.get('name', '')).strip()
        if not name or name in seen:
            continue
        targets.append((name, slug_from_store_name(name)))
        seen.add(name)

    if not targets:
        print('⚠️  store_list.json に有効な店舗がないため、固定4店舗で実行します')
        return HARDCODED_STORES
    return targets

def get_target_date():
    # Actions は UTC で動くため、JST 基準で前日を取る
    return (datetime.now(JST).date() - timedelta(days=1)).strftime('%Y-%m-%d')

def normalize_machine_name(machine_name):
    name = str(machine_name or '').replace('　', ' ').strip()
    mapped = MODEL_NAME_MAP.get(name, name)
    if mapped.replace(' ', '') == 'スマスロハナビ':
        return 'スマスロハナビ'
    return mapped

def is_normal_type(machine_name):
    normalized = normalize_machine_name(machine_name)
    return any(kw in normalized for kw in NORMAL_TYPE_KEYWORDS)

def load_store_freshness():
    if not os.path.exists(STORE_FRESHNESS_JSON):
        return {}
    try:
        with open(STORE_FRESHNESS_JSON, encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def get_latest_data_date(rows):
    dates = sorted({row.get('日付', '') for row in rows if row.get('日付')})
    return dates[-1] if dates else None

def update_store_freshness(store_name, data_date):
    freshness = load_store_freshness()
    freshness[store_name] = {
        'scraped_at': datetime.now(JST).isoformat(timespec='seconds'),
        'data_date': data_date,
    }
    with open(STORE_FRESHNESS_JSON, 'w', encoding='utf-8') as f:
        json.dump(freshness, f, ensure_ascii=False, indent=2)

def scrape(target_date, store_name, slug, target_models=None):
    url = f'https://ana-slo.com/{target_date}-{slug}/'
    res = None
    last_err = ''
    for attempt in range(1, 4):
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                break
            print(f'  ❌ {store_name} {target_date}: HTTP {res.status_code}')
            print(f'    request headers: {dict(res.request.headers)}')
            print(f'    response headers: {dict(res.headers)}')
            print(f'    response body (first 500 chars): {res.text[:500]}')
            last_err = f'HTTP {res.status_code}'
        except Exception as e:
            last_err = str(e)
        if attempt < 3:
            time.sleep(2 * attempt)
    if res is None or res.status_code != 200:
        if res is None:
            print(f'  ❌ {store_name} {target_date}: {last_err or "request failed"}')
        return [], [], False
    soup = BeautifulSoup(res.text, 'html.parser')
    model_summary_rows = extract_model_summary_rows(soup, target_date, store_name, target_models=target_models)

    table = soup.find('table', id='all_data_table')
    if not table:
        print(f'  ⚠️  {store_name} {target_date}: テーブルなし')
        return [], model_summary_rows, False
    rows = []
    for tr in table.find_all('tr')[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all('td')]
        # フォーマット別対応:
        # 8列: 機種名,台番号,G数,BB,RB,合成確率,BB確率,RB確率（差枚なし）
        # 9列: 機種名,台番号,G数,差枚,BB,RB,合成確率,BB確率,RB確率
        # 11列+: 機種名,台番号,G数,差枚,BB,RB,?,合成確率,BB確率,RB確率,...
        if len(cols) == 8:
            model_name = normalize_machine_name(cols[0])
            if not is_normal_type(model_name):
                continue
            if target_models and model_name not in target_models:
                continue
            rows.append({
                '日付': target_date,'店名': store_name,
                '機種名': model_name,'台番号': cols[1],
                'G数': cols[2],'差枚': '',
                'BB': cols[3],'RB': cols[4],
                '合成確率': cols[5],'BB確率': cols[6],'RB確率': cols[7],
            })
            continue
        if len(cols) == 9:
            model_name = normalize_machine_name(cols[0])
            if not is_normal_type(model_name):
                continue
            if target_models and model_name not in target_models:
                continue
            rows.append({
                '日付': target_date,'店名': store_name,
                '機種名': model_name,'台番号': cols[1],
                'G数': cols[2],'差枚': cols[3],
                'BB': cols[4],'RB': cols[5],
                '合成確率': cols[6],'BB確率': cols[7],'RB確率': cols[8],
            })
            continue
        if len(cols) < 11:
            continue
        model_name = normalize_machine_name(cols[0])
        if not is_normal_type(model_name):
            continue
        if target_models and model_name not in target_models:
            continue
        rows.append({
            '日付': target_date,'店名': store_name,
            '機種名': model_name,'台番号': cols[1],
            'G数': cols[2],'差枚': cols[3],
            'BB': cols[4],'RB': cols[5],
            '合成確率': cols[7],'BB確率': cols[8],'RB確率': cols[9],
        })
    print(f'  ✅ {store_name} {target_date}: 台別{len(rows)}行 / 機種別{len(model_summary_rows)}行取得')
    return rows, model_summary_rows, True

def _dedup_key(row):
    return (row.get('日付', ''), row.get('店名', ''), row.get('台番号', ''))


def _model_summary_key(row):
    return (row.get('date', ''), row.get('store', ''), row.get('model', ''))


def normalize_header(text):
    return ''.join(str(text or '').replace('\u3000', ' ').split()).lower()


def resolve_header_index(headers, candidates):
    for idx, header in enumerate(headers):
        if any(all(token in header for token in required_tokens) for required_tokens in candidates):
            return idx
    return None


def _is_summary_table(table):
    """ヘッダーに 機種別差枚/平均差枚/平均G数/勝率 のいずれかを含むテーブルか判定する"""
    trs = table.find_all('tr')
    if not trs:
        return False
    header_cells = trs[0].find_all(['th', 'td'])
    if not header_cells:
        return False
    headers = [normalize_header(cell.get_text(' ', strip=True)) for cell in header_cells]
    keywords = ['機種別差枚', '平均差枚', '平均g数', '勝率', '平均ゲーム数']
    joined = ' '.join(headers)
    return any(kw in joined for kw in keywords)


def _get_preceding_model_name(table):
    """テーブル直前の要素から機種名を取得する"""
    import re as _re
    from bs4 import NavigableString as _NS
    _rank_prefix = _re.compile(r'^\d+位[：:]\s*')

    def _clean(text):
        return _rank_prefix.sub('', text).strip()

    for sibling in table.previous_siblings:
        if isinstance(sibling, _NS):
            text = sibling.strip()
            if text:
                return _clean(text)
        elif hasattr(sibling, 'get_text'):
            text = sibling.get_text(strip=True)
            if text:
                return _clean(text)
    # 直前兄弟に無ければ親の直前兄弟を辿る
    parent = table.parent
    if parent:
        for sibling in parent.previous_siblings:
            if hasattr(sibling, 'get_text'):
                text = sibling.get_text(strip=True)
                if text:
                    return _clean(text)
    return ''


def extract_model_summary_rows(soup, target_date, store_name, target_models=None):
    """
    ページ上の全テーブルを走査し、ヘッダーが機種別集計テーブルと判定されるもの全てからデータを取得する。
    鶴見UNOのように機種ごとに1テーブル＋直前に機種名が書かれているページ構造に対応する。
    """
    main_table_id = 'all_data_table'
    out = []

    for table in soup.find_all('table'):
        # メインの台別データテーブルはスキップ
        if table.get('id') == main_table_id:
            continue
        if not _is_summary_table(table):
            continue

        trs = table.find_all('tr')
        if len(trs) < 1:
            continue

        header_cells = trs[0].find_all(['th', 'td'])
        headers = [normalize_header(cell.get_text(' ', strip=True)) for cell in header_cells]

        total_diff_idx = resolve_header_index(headers, [('機種別差枚',), ('差枚合計',), ('合計差枚',)])
        avg_diff_idx = resolve_header_index(headers, [('平均差枚',), ('平均差',)])
        avg_g_idx = resolve_header_index(headers, [('平均g数',), ('平均ゲーム',), ('平均g',)])
        win_rate_idx = resolve_header_index(headers, [('勝率',)])

        # 機種名が列にある場合（複数機種をまとめたテーブル）
        # 注意: ('機種',) だと '機種別差枚' にもマッチするため除外する
        model_col_idx = resolve_header_index(headers, [('機種名',), ('model',)])

        if model_col_idx is not None:
            # テーブル内に機種名列がある → 複数機種まとめ型
            for tr in trs[1:]:
                tds = tr.find_all('td')
                if not tds:
                    continue
                cols = [td.get_text(strip=True) for td in tds]
                if model_col_idx >= len(cols):
                    continue
                model_name = normalize_machine_name(cols[model_col_idx])
                if not model_name or '合計' in model_name:
                    continue
                if target_models and model_name not in target_models:
                    continue

                def pick(idx, cols=cols):
                    if idx is None or idx >= len(cols):
                        return ''
                    return cols[idx]

                out.append({
                    'date': target_date,
                    'store': store_name,
                    'model': model_name,
                    'total_diff': pick(total_diff_idx),
                    'avg_diff': pick(avg_diff_idx),
                    'avg_g': pick(avg_g_idx),
                    'win_rate': pick(win_rate_idx),
                })
        else:
            # 機種名列がない → テーブル1つ＝機種1つ型（鶴見UNO方式）
            # テーブルの直前要素から機種名を取得
            raw_model = _get_preceding_model_name(table)
            model_name = normalize_machine_name(raw_model)
            if not model_name:
                continue
            # 特殊セクション名はスキップ
            if any(kw in model_name for kw in ('末尾別', '合計', '総合', 'データ一覧')):
                continue
            if target_models and model_name not in target_models:
                continue

            # データ行（ヘッダー行除く）の集計値を取得
            # 通常は1行のみ（合計行）
            for tr in trs[1:]:
                tds = tr.find_all('td')
                if not tds:
                    continue
                cols = [td.get_text(strip=True) for td in tds]

                def pick(idx, cols=cols):
                    if idx is None or idx >= len(cols):
                        return ''
                    return cols[idx]

                total_diff = pick(total_diff_idx)
                avg_diff = pick(avg_diff_idx)
                avg_g = pick(avg_g_idx)
                win_rate = pick(win_rate_idx)

                # 空行・フッター行はスキップ
                if not any([total_diff, avg_diff, avg_g, win_rate]):
                    continue
                # 末尾別データ等の特殊行はスキップ（実データが欠落している）
                if not total_diff and not avg_diff:
                    continue

                out.append({
                    'date': target_date,
                    'store': store_name,
                    'model': model_name,
                    'total_diff': total_diff,
                    'avg_diff': avg_diff,
                    'avg_g': avg_g,
                    'win_rate': win_rate,
                })
                break  # 最初の有効データ行のみ取得

    return out

def save_to_csv(rows):
    if not rows:
        return 0

    # 同一キー（日付,店名,台番号）の最新行で上書きする
    updates = {}
    for row in rows:
        updates[_dedup_key(row)] = row

    if not os.path.exists(RAW_CSV):
        with open(RAW_CSV, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
            writer.writerows(updates.values())
        print(f'  📝 新規作成: {len(updates)}行')
        return len(updates)

    tmp_csv = RAW_CSV + '.tmp'
    replaced = 0
    with open(RAW_CSV, encoding='utf-8-sig', newline='') as src, \
         open(tmp_csv, 'w', encoding='utf-8-sig', newline='') as dst:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or CSV_HEADER
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            key = _dedup_key(row)
            if key in updates:
                writer.writerow(updates.pop(key))
                replaced += 1
            else:
                writer.writerow(row)

        appended = len(updates)
        for row in updates.values():
            writer.writerow(row)

    os.replace(tmp_csv, RAW_CSV)
    print(f'  📝 {replaced}行を上書き / {appended}行を追加')
    return replaced + appended


def save_model_summary_to_csv(rows):
    if not rows:
        return 0

    updates = {}
    for row in rows:
        updates[_model_summary_key(row)] = row

    if not os.path.exists(STORE_MODEL_SUMMARY_CSV):
        with open(STORE_MODEL_SUMMARY_CSV, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=STORE_MODEL_SUMMARY_HEADER)
            writer.writeheader()
            writer.writerows(updates.values())
        print(f'  📝 機種別集計 新規作成: {len(updates)}行')
        return len(updates)

    tmp_csv = STORE_MODEL_SUMMARY_CSV + '.tmp'
    replaced = 0
    with open(STORE_MODEL_SUMMARY_CSV, encoding='utf-8-sig', newline='') as src, \
         open(tmp_csv, 'w', encoding='utf-8-sig', newline='') as dst:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or STORE_MODEL_SUMMARY_HEADER
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            key = _model_summary_key(row)
            if key in updates:
                writer.writerow(updates.pop(key))
                replaced += 1
            else:
                writer.writerow(row)

        appended = len(updates)
        for row in updates.values():
            writer.writerow({key: row.get(key, '') for key in fieldnames})

    os.replace(tmp_csv, STORE_MODEL_SUMMARY_CSV)
    print(f'  📝 機種別集計 {replaced}行を上書き / {appended}行を追加')
    return replaced + appended

def parse_args():
    parser = argparse.ArgumentParser(description='ana-slo のデータを取得して raw_data.csv を更新します。')
    parser.add_argument('--start-date', help='取得開始日 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='取得終了日 (YYYY-MM-DD)')
    parser.add_argument('--stores', help='対象店舗名をカンマ区切りで指定')
    parser.add_argument('--models', help='対象機種名をカンマ区切りで指定')
    parser.add_argument('--store-interval-sec', type=float, default=1.0, help='店舗間の待機秒数')
    parser.add_argument('--date-interval-sec', type=float, default=0.0, help='日付間の待機秒数')
    return parser.parse_args()

def parse_date_str(value):
    return datetime.strptime(value, '%Y-%m-%d').date()

def build_target_dates(start_date, end_date):
    dates = []
    cursor = start_date
    while cursor <= end_date:
        dates.append(cursor.strftime('%Y-%m-%d'))
        cursor += timedelta(days=1)
    return dates

def parse_csv_list(value):
    if not value:
        return []
    return [v.strip() for v in value.split(',') if v.strip()]

def resolve_target_stores(selected_names):
    if not selected_names:
        return load_target_stores()
    loaded = load_target_stores()
    slug_by_name = {name: slug for name, slug in loaded}
    for name, slug in HARDCODED_STORES:
        slug_by_name.setdefault(name, slug)
    resolved = []
    seen = set()
    for name in selected_names:
        if name in seen:
            continue
        resolved.append((name, slug_by_name.get(name, slug_from_store_name(name))))
        seen.add(name)
    return resolved

if __name__ == '__main__':
    args = parse_args()
    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            raise SystemExit('❌ --start-date と --end-date は同時に指定してください')
        start = parse_date_str(args.start_date)
        end = parse_date_str(args.end_date)
        if start > end:
            raise SystemExit('❌ 開始日が終了日より後です')
    else:
        start = end = parse_date_str(get_target_date())

    target_dates = build_target_dates(start, end)
    stores = resolve_target_stores(parse_csv_list(args.stores))
    target_models = {normalize_machine_name(m) for m in parse_csv_list(args.models)}
    model_desc = ', '.join(sorted(target_models)) if target_models else '通常対象すべて'

    print(f'=== 取得期間: {target_dates[0]} 〜 {target_dates[-1]} ({len(target_dates)}日) ===')
    print(f'=== 対象店舗: {len(stores)}件 / 対象機種: {model_desc} ===')
    all_rows = []
    all_model_summary_rows = []
    latest_by_store = {}
    scraped_store_count = set()

    for day_idx, target_date in enumerate(target_dates, start=1):
        print(f'\n--- {target_date} ({day_idx}/{len(target_dates)}) ---')
        for store_idx, (store_name, slug) in enumerate(stores, start=1):
            rows, model_summary_rows, ok = scrape(target_date, store_name, slug, target_models=target_models)
            all_rows.extend(rows)
            all_model_summary_rows.extend(model_summary_rows)
            if ok:
                latest_data_date = get_latest_data_date(rows) or target_date
                prev_latest = latest_by_store.get(store_name)
                if not prev_latest or latest_data_date > prev_latest:
                    latest_by_store[store_name] = latest_data_date
                scraped_store_count.add(store_name)
            if store_idx < len(stores) and args.store_interval_sec > 0:
                time.sleep(args.store_interval_sec)
        if day_idx < len(target_dates) and args.date_interval_sec > 0:
            time.sleep(args.date_interval_sec)

    for store_name, latest_data_date in latest_by_store.items():
        update_store_freshness(store_name, latest_data_date)

    print(f'\n合計 {len(all_rows)} 行取得')
    saved = save_to_csv(all_rows)
    model_saved = save_model_summary_to_csv(all_model_summary_rows)
    print(f'✅ 完了（台別更新/追加: {saved}行, 機種別更新/追加: {model_saved}行, freshness更新: {len(scraped_store_count)}店舗）')
