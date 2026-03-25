import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import json
import time

# ===== 設定 =====
GAS_URL = 'https://script.google.com/macros/s/AKfycbxkecyCx6PxoikwVdDYQxWqU9O0v4AjVZPskdvrvMsKy68MXwRc1V4H0bZ3pmxXloClGQ/exec'

STORES = [
    ('鶴見UNO',                   '%e9%b6%b4%e8%a6%8buno-data'),
    ('マルハン都築',               '%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%91%e5%ba%97-data'),
    ('中山UNO',                   '%e4%b8%ad%e5%b1%b1uno-data'),
    ('エスパス日拓新宿歌舞伎町',    '%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data'),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://ana-slo.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# ===== 昨日の日付を自動取得 =====
def get_target_date():
    return (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# ===== スクレイピング =====
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

    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table', id='all_data_table')
    if not table:
        print(f'  ⚠️  {store_name} {target_date}: テーブルなし（データなしの日かも）')
        return []

    rows = []
    for tr in table.find_all('tr')[1:]:  # ヘッダー行をスキップ
        cols = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(cols) < 11:
            continue
        machine = cols[0]
        if 'ジャグラー' not in machine:
            continue
        # [日付, 店名, 機種名, 台番号, G数, 差枚, BB, RB, 合成確率, BB確率, RB確率]
        row = [target_date, store_name, cols[0], cols[1], cols[2], cols[3], cols[4], cols[5], cols[7], cols[8], cols[9]]
        rows.append(row)

    print(f'  ✅ {store_name} {target_date}: {len(rows)}行取得')
    return rows

# ===== GASに送信 =====
def post_to_sheet(rows):
    if not rows:
        return
    payload = {'sheetName': 'RAW', 'rows': rows, 'append': True}
    try:
        res = requests.post(GAS_URL, json=payload, timeout=30)
        result = res.json()
        print(f'  📝 GAS送信: {result}')
    except Exception as e:
        print(f'  ❌ GAS送信エラー: {e}')

# ===== メイン =====
if __name__ == '__main__':
    target_date = get_target_date()
    print(f'=== 取得日付: {target_date} ===')

    all_rows = []
    for store_name, slug in STORES:
        rows = scrape(target_date, store_name, slug)
        all_rows.extend(rows)
        time.sleep(1)  # サーバーに優しく

    print(f'\n合計 {len(all_rows)} 行取得')
    post_to_sheet(all_rows)
    print('完了！')
