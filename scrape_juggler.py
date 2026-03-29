import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import csv
import os
import time

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV  = os.path.join(REPO_DIR, "raw_data.csv")

STORES = [
    ('鶴見UNO',               '%e9%b6%b4%e8%a6%8buno-data'),
    ('マルハン都築',           '%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%91%e5%ba%97-data'),
    ('中山UNO',               '%e4%b8%ad%e5%b1%b1uno-data'),
    ('エスパス日拓新宿歌舞伎町', '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data'),
]

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

def get_target_date():
    return (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

def is_normal_type(machine_name):
    return any(kw in machine_name for kw in NORMAL_TYPE_KEYWORDS)

def load_existing_keys():
    keys = set()
    if not os.path.exists(RAW_CSV):
        return keys
    with open(RAW_CSV, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            keys.add((row['日付'], row['店名'], row['台番号'], row['機種名']))
    return keys

def scrape(target_date, store_name, slug):
    url = f'https://ana-slo.com/{target_date}-{slug}/'
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f'  ❌ {store_name} {target_date}: HTTP {res.status_code}')
            return []
    except Exception as e:
        print(f'  ❌ {store_name} {target_date}: {e}')
        return []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table', id='all_data_table')
    if not table:
        print(f'  ⚠️  {store_name} {target_date}: テーブルなし')
        return []
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
    return rows

def save_to_csv(rows, existing_keys):
    if not rows:
        return 0
    new_rows = []
    for row in rows:
        key = (row['日付'], row['店名'], row['台番号'], row['機種名'])
        if key not in existing_keys:
            new_rows.append(row)
            existing_keys.add(key)
    if not new_rows:
        print('  ℹ️  追記なし（全て重複）')
        return 0
    file_exists = os.path.exists(RAW_CSV)
    with open(RAW_CSV, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)
    print(f'  📝 {len(new_rows)}行をCSVに追記')
    return len(new_rows)

if __name__ == '__main__':
    target_date = get_target_date()
    print(f'=== 取得日付: {target_date} ===')
    existing_keys = load_existing_keys()
    print(f'既存レコード数: {len(existing_keys)}件')
    all_rows = []
    for store_name, slug in STORES:
        rows = scrape(target_date, store_name, slug)
        all_rows.extend(rows)
        time.sleep(1)
    print(f'\n合計 {len(all_rows)} 行取得')
    saved = save_to_csv(all_rows, existing_keys)
    print(f'✅ 完了（新規追記: {saved}行）')
