import requests
from bs4 import BeautifulSoup

urls = {
    'マルハン都築': 'https://ana-slo.com/2026-04-10-%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%91%e5%ba%97-data/',
    'マルハンメガシティ横浜町田': 'https://ana-slo.com/%E3%83%9B%E3%83%BC%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF/%E7%A5%9E%E5%A5%88%E5%B7%9D%E7%9C%8C/%E3%83%9E%E3%83%AB%E3%83%8F%E3%83%B3%E3%83%A1%E3%82%AC%E3%82%B7%E3%83%86%E3%82%A3%E6%A8%AA%E6%B5%9C%E7%94%BA%E7%94%B0-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/',
    'ギンザホール707': 'https://ana-slo.com/%E3%83%9B%E3%83%BC%E3%83%AB%E3%83%87%E3%83%BC%E3%82%BF/%E7%A5%9E%E5%A5%88%E5%B7%9D%E7%9C%8C/%E3%82%AE%E3%83%B3%E3%82%B6%E3%83%9B%E3%83%BC%E3%83%AB707-%E3%83%87%E3%83%BC%E3%82%BF%E4%B8%80%E8%A6%A7/',
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, url in urls.items():
    print(f'\n=== {name} ===')
    r = requests.get(url, headers=headers, timeout=10)
    print(f'Status: {r.status_code}')
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')
    print(f'テーブル数: {len(tables)}')
    for i, t in enumerate(tables[:2]):
        print(f'テーブル{i+1} 先頭行: {t.find("tr")}')
