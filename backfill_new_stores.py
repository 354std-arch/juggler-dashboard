import argparse
import csv
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
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

DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_REQUEST_RETRY_MAX = 3
DEFAULT_REQUEST_RETRY_WAIT_SECONDS = 5.0
DEFAULT_PAGE_INTERVAL_SECONDS = 3.0
DEFAULT_STORE_INTERVAL_SECONDS = 10.0
DEFAULT_BACKFILL_DAYS = 365
JST = timezone(timedelta(hours=9))


def log_info(message: str) -> None:
    print(f"[INFO] {message}")


def log_warn(message: str) -> None:
    print(f"[WARN] {message}")


def log_error(message: str) -> None:
    print(f"[ERROR] {message}")


def jst_today() -> date:
    return datetime.now(JST).date()


def parse_iso_date(value: Optional[str], label: str) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{label} は YYYY-MM-DD 形式で指定してください: {value}") from None


def resolve_date_window(
    today: date,
    start_date_arg: Optional[str],
    end_date_arg: Optional[str],
    backfill_days: int,
) -> Tuple[date, date]:
    if backfill_days < 1:
        raise ValueError("--backfill-days は1以上で指定してください")

    default_start = today - timedelta(days=backfill_days)
    default_end = today - timedelta(days=1)

    start_date = parse_iso_date(start_date_arg, "--start-date") or default_start
    end_date = parse_iso_date(end_date_arg, "--end-date") or default_end

    if end_date >= today:
        log_warn(f"--end-date={end_date.isoformat()} は未来日を含むため {default_end.isoformat()} に補正します")
        end_date = default_end

    if start_date > end_date:
        raise ValueError(
            f"対象期間が不正です: start={start_date.isoformat()} end={end_date.isoformat()}"
        )

    return start_date, end_date


def slug_from_store_name(store_name: str) -> str:
    if store_name in KNOWN_SLUG_BY_NAME:
        return KNOWN_SLUG_BY_NAME[store_name]
    return f"{quote(store_name, safe='').lower()}-data"


def parse_csv_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_store_slug(store: Dict) -> str:
    slug = str(store.get("slug", "")).strip()
    if slug:
        return slug
    store_name = str(store.get("name", "")).strip()
    return slug_from_store_name(store_name)


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


def find_backfill_targets(
    store_list: Dict,
    existing_store_names: set,
    include_existing_stores: bool,
    selected_store_names: Optional[set] = None,
) -> List[Dict]:
    targets = []
    seen = set()
    selected = selected_store_names or set()
    explicit_selection = bool(selected)

    for store in store_list.get("stores", []):
        if not isinstance(store, dict):
            continue

        store_name = str(store.get("name", "")).strip()
        source = str(store.get("source", "")).strip()
        is_backfilled = bool(store.get("backfilled", False))

        if not store_name or store_name in seen:
            continue
        seen.add(store_name)

        if explicit_selection and store_name not in selected:
            continue
        if source != "minrepo":
            continue
        if (not explicit_selection) and is_backfilled:
            continue
        if (not explicit_selection) and (not include_existing_stores) and store_name in existing_store_names:
            continue

        targets.append(store)

    return targets


def request_with_retry(
    url: str,
    timeout_seconds: int,
    retry_max: int,
    retry_wait_seconds: float,
) -> Tuple[str, bool, str]:
    if retry_max < 1:
        retry_max = 1

    last_error = ""

    for attempt in range(1, retry_max + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout_seconds)
            if response.status_code == 200:
                return response.text, True, ""
            last_error = f"HTTP {response.status_code}"
        except Exception as exc:  # pylint: disable=broad-except
            last_error = str(exc)

        if attempt < retry_max and retry_wait_seconds > 0:
            log_warn(f"リトライ {attempt}/{retry_max - 1}: {url} ({last_error})")
            time.sleep(retry_wait_seconds)

    log_error(f"リクエスト失敗: {url} ({last_error})")
    return "", False, last_error


def scrape_day(
    target_date: str,
    store_name: str,
    slug: str,
    request_timeout_seconds: int,
    request_retry_max: int,
    request_retry_wait_seconds: float,
) -> Tuple[List[Dict[str, str]], bool]:
    url = f"https://ana-slo.com/{target_date}-{slug}/"
    html, ok, _ = request_with_retry(
        url,
        timeout_seconds=request_timeout_seconds,
        retry_max=request_retry_max,
        retry_wait_seconds=request_retry_wait_seconds,
    )
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


def date_window(start_date: date, end_date: date) -> List[str]:
    dates = []
    cursor = start_date
    while cursor <= end_date:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="新規 minrepo 店舗の過去データを ana-slo からバックフィルします")
    parser.add_argument("--start-date", type=str, default=None, help="開始日 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None, help="終了日 (YYYY-MM-DD)。未指定時は前日")
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=DEFAULT_BACKFILL_DAYS,
        help="開始日/終了日未指定時の遡り日数",
    )
    parser.add_argument(
        "--include-existing-stores",
        action="store_true",
        help="raw_data.csv に既存行がある店舗も対象に含める",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        help="HTTP リクエストタイムアウト秒",
    )
    parser.add_argument(
        "--request-retry-max",
        type=int,
        default=DEFAULT_REQUEST_RETRY_MAX,
        help="HTTP リクエストの最大試行回数",
    )
    parser.add_argument(
        "--request-retry-wait-seconds",
        type=float,
        default=DEFAULT_REQUEST_RETRY_WAIT_SECONDS,
        help="HTTP リトライ待機秒",
    )
    parser.add_argument(
        "--page-interval-seconds",
        type=float,
        default=DEFAULT_PAGE_INTERVAL_SECONDS,
        help="1日ごとの取得間隔秒",
    )
    parser.add_argument(
        "--store-interval-seconds",
        type=float,
        default=DEFAULT_STORE_INTERVAL_SECONDS,
        help="店舗ごとの取得間隔秒",
    )
    parser.add_argument(
        "--stores",
        type=str,
        default=None,
        help="対象店舗名をカンマ区切りで指定（指定時は backfilled 状態を無視）",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        today = jst_today()
        targets_start, targets_end = resolve_date_window(
            today=today,
            start_date_arg=args.start_date,
            end_date_arg=args.end_date,
            backfill_days=args.backfill_days,
        )
    except ValueError as exc:
        log_error(str(exc))
        return 1

    today_str = today.isoformat()

    log_info("===== 新規店舗バックフィル開始 =====")
    log_info(
        f"対象期間: {targets_start.isoformat()} 〜 {targets_end.isoformat()} "
        f"({(targets_end - targets_start).days + 1}日)"
    )

    store_list = load_store_list()
    existing_store_names = load_existing_store_names_from_raw()
    selected_store_names = set(parse_csv_list(args.stores))
    if selected_store_names:
        log_info(f"明示指定店舗: {', '.join(sorted(selected_store_names))}")

    targets = find_backfill_targets(
        store_list=store_list,
        existing_store_names=existing_store_names,
        include_existing_stores=args.include_existing_stores,
        selected_store_names=selected_store_names,
    )

    if not targets:
        log_info("バックフィル対象の店舗はありません")
        return 0

    _, reachable, err = request_with_retry(
        "https://ana-slo.com/",
        timeout_seconds=args.request_timeout_seconds,
        retry_max=1,
        retry_wait_seconds=0,
    )
    if not reachable:
        log_error(f"ana-slo.com に接続できないため中断します: {err}")
        return 1

    target_dates = date_window(targets_start, targets_end)
    all_new_rows: List[Dict[str, str]] = []
    success_count = 0
    failure_count = 0

    for index, store in enumerate(targets, start=1):
        store_name = str(store.get("name", "")).strip()
        slug = resolve_store_slug(store)

        log_info(f"[{index}/{len(targets)}] 店舗開始: {store_name} (slug={slug})")

        store_rows: List[Dict[str, str]] = []
        store_failed = False

        for day_index, target_date in enumerate(target_dates, start=1):
            rows, ok = scrape_day(
                target_date=target_date,
                store_name=store_name,
                slug=slug,
                request_timeout_seconds=args.request_timeout_seconds,
                request_retry_max=args.request_retry_max,
                request_retry_wait_seconds=args.request_retry_wait_seconds,
            )
            if not ok:
                store_failed = True
            store_rows.extend(rows)

            if day_index % 30 == 0 or day_index == len(target_dates):
                log_info(
                    f"  進捗 {store_name}: {day_index}/{len(target_dates)}日 ({len(store_rows)}行取得)"
                )

            if day_index < len(target_dates) and args.page_interval_seconds > 0:
                time.sleep(args.page_interval_seconds)

        if store_failed:
            failure_count += 1
            log_error(f"店舗失敗: {store_name} (リクエスト失敗日あり。backfilled は更新しません)")
        else:
            success_count += 1
            store["backfilled"] = True
            store["backfilled_date"] = today_str
            all_new_rows.extend(store_rows)
            log_info(f"店舗完了: {store_name} ({len(store_rows)}行)")

        if index < len(targets) and args.store_interval_seconds > 0:
            time.sleep(args.store_interval_seconds)

    saved_rows = save_to_csv(all_new_rows)
    save_store_list(store_list)

    log_info("===== 新規店舗バックフィル終了 =====")
    log_info(
        f"サマリー: 対象店舗={len(targets)}, 成功={success_count}, "
        f"失敗={failure_count}, CSV更新行={saved_rows}"
    )

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
