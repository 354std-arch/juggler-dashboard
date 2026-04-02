import csv
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Tuple
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV = os.path.join(REPO_DIR, "raw_data.csv")
STORE_LIST_JSON = os.path.join(REPO_DIR, "store_list.json")

CSV_HEADER = ["日付", "店名", "機種名", "台番号", "G数", "差枚", "BB", "RB", "合成確率", "BB確率", "RB確率"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://ana-slo.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

KNOWN_SLUG_BY_NAME = {
    "鶴見UNO": "%e9%b6%b4%e8%a6%8buno-data",
    "マルハン都筑": "%e3%83%9e%e3%83%ab%e3%83%8f%e3%83%b3%e9%83%bd%e7%ad%9c%e5%ba%97-data",
    "中山UNO": "%e4%b8%ad%e5%b1%b1uno-data",
    "エスパス新宿": "%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data",
    "エスパス日拓新宿歌舞伎町": "%e3%82%a8%e3%82%b9%e3%83%91%e3%82%b9%e6%97%a5%e6%8b%93%e6%96%b0%e5%ae%bf%e6%ad%8c%e8%88%9e%e4%bc%8e%e7%94%ba%e5%ba%97-data",
}

NORMAL_TYPE_KEYWORDS = [
    "ジャグラー",
    "ハナビ",
    "クランキー",
    "ニューパルサー",
    "ドリームクランキー",
    "バーサス",
    "タコスロ",
]

REQUEST_TIMEOUT_SECONDS = 30
REQUEST_RETRY_MAX = 3
REQUEST_RETRY_WAIT_SECONDS = 5
PAGE_INTERVAL_SECONDS = 3
STORE_INTERVAL_SECONDS = 10
BACKFILL_DAYS = 365
JST = timezone(timedelta(hours=9))


def log_info(message: str) -> None:
    print(f"[INFO] {message}")


def log_warn(message: str) -> None:
    print(f"[WARN] {message}")


def log_error(message: str) -> None:
    print(f"[ERROR] {message}")


def jst_today() -> date:
    return datetime.now(JST).date()


def slug_from_store_name(store_name: str) -> str:
    if store_name in KNOWN_SLUG_BY_NAME:
        return KNOWN_SLUG_BY_NAME[store_name]
    return f"{quote(store_name, safe='').lower()}-data"


def is_normal_type(machine_name: str) -> bool:
    return any(keyword in machine_name for keyword in NORMAL_TYPE_KEYWORDS)


def dedup_key(row: Dict[str, str]) -> Tuple[str, str, str]:
    return (row.get("日付", ""), row.get("店名", ""), row.get("台番号", ""))


def load_store_list() -> Dict:
    if not os.path.exists(STORE_LIST_JSON):
        log_warn("store_list.json が見つからないため、バックフィル対象は0件です")
        return {"stores": []}
    try:
        with open(STORE_LIST_JSON, encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:  # pylint: disable=broad-except
        log_error(f"store_list.json 読み込み失敗: {exc}")
        return {"stores": []}
    if not isinstance(payload, dict):
        return {"stores": []}
    stores = payload.get("stores")
    if not isinstance(stores, list):
        payload["stores"] = []
    return payload


def save_store_list(store_list: Dict) -> None:
    with open(STORE_LIST_JSON, "w", encoding="utf-8") as f:
        json.dump(store_list, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_existing_store_names_from_raw() -> set:
    if not os.path.exists(RAW_CSV):
        return set()
    names = set()
    with open(RAW_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            store_name = str(row.get("店名", "")).strip()
            if store_name:
                names.add(store_name)
    return names


def find_backfill_targets(store_list: Dict, existing_store_names: set) -> List[Dict]:
    targets = []
    seen = set()

    for store in store_list.get("stores", []):
        if not isinstance(store, dict):
            continue

        store_name = str(store.get("name", "")).strip()
        source = str(store.get("source", "")).strip()
        is_backfilled = bool(store.get("backfilled", False))

        if not store_name or store_name in seen:
            continue
        seen.add(store_name)

        if source != "minrepo":
            continue
        if is_backfilled:
            continue
        if store_name in existing_store_names:
            continue

        targets.append(store)

    return targets


def request_with_retry(url: str) -> Tuple[str, bool]:
    last_error = ""

    for attempt in range(1, REQUEST_RETRY_MAX + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                return response.text, True
            last_error = f"HTTP {response.status_code}"
        except Exception as exc:  # pylint: disable=broad-except
            last_error = str(exc)

        if attempt < REQUEST_RETRY_MAX:
            log_warn(f"リトライ {attempt}/{REQUEST_RETRY_MAX - 1}: {url} ({last_error})")
            time.sleep(REQUEST_RETRY_WAIT_SECONDS)

    log_error(f"リクエスト失敗: {url} ({last_error})")
    return "", False


def scrape_day(target_date: str, store_name: str, slug: str) -> Tuple[List[Dict[str, str]], bool]:
    url = f"https://ana-slo.com/{target_date}-{slug}/"
    html, ok = request_with_retry(url)
    if not ok:
        return [], False

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="all_data_table")
    if not table:
        return [], True

    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) < 11:
            continue
        if not is_normal_type(cols[0]):
            continue
        rows.append(
            {
                "日付": target_date,
                "店名": store_name,
                "機種名": cols[0],
                "台番号": cols[1],
                "G数": cols[2],
                "差枚": cols[3],
                "BB": cols[4],
                "RB": cols[5],
                "合成確率": cols[7],
                "BB確率": cols[8],
                "RB確率": cols[9],
            }
        )

    return rows, True


def save_to_csv(rows: List[Dict[str, str]]) -> int:
    if not rows:
        return 0

    updates = {}
    for row in rows:
        updates[dedup_key(row)] = row

    if not os.path.exists(RAW_CSV):
        with open(RAW_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
            writer.writerows(updates.values())
        return len(updates)

    tmp_csv = RAW_CSV + ".tmp"
    replaced = 0

    with open(RAW_CSV, encoding="utf-8-sig", newline="") as src, open(
        tmp_csv, "w", encoding="utf-8-sig", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or CSV_HEADER
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            key = dedup_key(row)
            if key in updates:
                writer.writerow(updates.pop(key))
                replaced += 1
            else:
                writer.writerow(row)

        for row in updates.values():
            writer.writerow(row)

    os.replace(tmp_csv, RAW_CSV)
    appended = len(updates)
    return replaced + appended


def date_window(today: date) -> List[str]:
    start_date = today - timedelta(days=BACKFILL_DAYS)
    end_date = today - timedelta(days=1)

    dates = []
    cursor = start_date
    while cursor <= end_date:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


def main() -> int:
    today = jst_today()
    today_str = today.isoformat()
    targets_start = today - timedelta(days=BACKFILL_DAYS)
    targets_end = today - timedelta(days=1)

    log_info("===== 新規店舗バックフィル開始 =====")
    log_info(f"対象期間: {targets_start.isoformat()} 〜 {targets_end.isoformat()} ({BACKFILL_DAYS}日)")

    store_list = load_store_list()
    existing_store_names = load_existing_store_names_from_raw()
    targets = find_backfill_targets(store_list, existing_store_names)

    if not targets:
        log_info("バックフィル対象の店舗はありません")
        return 0

    target_dates = date_window(today)
    all_new_rows: List[Dict[str, str]] = []
    success_count = 0
    failure_count = 0

    for index, store in enumerate(targets, start=1):
        store_name = str(store.get("name", "")).strip()
        slug = slug_from_store_name(store_name)

        log_info(f"[{index}/{len(targets)}] 店舗開始: {store_name}")

        store_rows: List[Dict[str, str]] = []
        store_failed = False

        for day_index, target_date in enumerate(target_dates, start=1):
            rows, ok = scrape_day(target_date, store_name, slug)
            if not ok:
                store_failed = True
            store_rows.extend(rows)

            if day_index % 30 == 0 or day_index == len(target_dates):
                log_info(
                    f"  進捗 {store_name}: {day_index}/{len(target_dates)}日 ({len(store_rows)}行取得)"
                )

            if day_index < len(target_dates):
                time.sleep(PAGE_INTERVAL_SECONDS)

        if store_failed:
            failure_count += 1
            log_error(f"店舗失敗: {store_name} (リクエスト失敗日あり。backfilled は更新しません)")
        else:
            success_count += 1
            store["backfilled"] = True
            store["backfilled_date"] = today_str
            all_new_rows.extend(store_rows)
            log_info(f"店舗完了: {store_name} ({len(store_rows)}行)")

        if index < len(targets):
            time.sleep(STORE_INTERVAL_SECONDS)

    saved_rows = save_to_csv(all_new_rows)
    save_store_list(store_list)

    log_info("===== 新規店舗バックフィル終了 =====")
    log_info(
        f"サマリー: 対象店舗={len(targets)}, 成功={success_count}, 失敗={failure_count}, CSV更新行={saved_rows}"
    )

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
