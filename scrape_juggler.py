import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime, timezone
import csv
import os
import time
import json
from urllib.parse import quote

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV  = os.path.join(REPO_DIR, "raw_data.csv")
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
    '中山UNO': '%e4%b8%ad%e5%b1%b1uno-data',
    'エスパス新宿': '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data',
    'エスパス日拓新宿歌舞伎町': '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data',
}

NORMAL_TYPE_KEYWORDS = [
    'ジャグラー','ハナビ','クランキー','ニューパルサー',
    'ドリームクランキー','バーサス','タコスロ',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://ana-slo.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

CSV_HEADER = ['日付','店名','機種名','台番号','G数','差枚','BB','RB','合成確率','BB確率','RB確率']


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

def is_normal_type(machine_name):
    return any(kw in machine_name for kw in NORMAL_TYPE_KEYWORDS)

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
        'scraped_at': datetime.now(JST).replace(tzinfo=None).isoformat(timespec='seconds'),
        'data_date': data_date,
    }
    with open(STORE_FRESHNESS_JSON, 'w', encoding='utf-8') as f:
        json.dump(freshness, f, ensure_ascii=False, indent=2)

def scrape(target_date, store_name, slug):
    url = f'https://ana-slo.com/{target_date}-{slug}/'
    res = None
    last_err = ''
    for attempt in range(1, 4):
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                break
            last_err = f'HTTP {res.status_code}'
        except Exception as e:
            last_err = str(e)
        if attempt < 3:
            time.sleep(2 * attempt)
    if res is None or res.status_code != 200:
        print(f'  ❌ {store_name} {target_date}: {last_err or "request failed"}')
        return [], False
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table', id='all_data_table')
    if not table:
        print(f'  ⚠️  {store_name} {target_date}: テーブルなし')
        return [], False
    rows = []
    for tr in table.find_all('tr')[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(cols) < 11:
            continue
        if not is_normal_type(cols[0]):
            continue
        rows.append({
            '日付': target_date,'店名': store_name,
            '機種名': cols[0],'台番号': cols[1],
            'G数': cols[2],'差枚': cols[3],
            'BB': cols[4],'RB': cols[5],
            '合成確率': cols[7],'BB確率': cols[8],'RB確率': cols[9],
        })
    print(f'  ✅ {store_name} {target_date}: {len(rows)}行取得')
    return rows, True

def _dedup_key(row):
    return (row.get('日付', ''), row.get('店名', ''), row.get('台番号', ''))

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

if __name__ == '__main__':
    target_date = get_target_date()
    stores = load_target_stores()
    print(f'=== 取得日付: {target_date} ===')
    all_rows = []
    scraped_store_count = 0
    for store_name, slug in stores:
        rows, ok = scrape(target_date, store_name, slug)
        all_rows.extend(rows)
        if ok:
            latest_data_date = get_latest_data_date(rows) or target_date
            update_store_freshness(store_name, latest_data_date)
            scraped_store_count += 1
        time.sleep(1)
    print(f'\n合計 {len(all_rows)} 行取得')
    saved = save_to_csv(all_rows)
    print(f'✅ 完了（更新/追加: {saved}行, freshness更新: {scraped_store_count}店舗）')
