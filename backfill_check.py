import csv
import json
import os
from datetime import timedelta

from scrape_juggler import (
    RAW_CSV,
    STORE_LIST_JSON,
    build_target_dates,
    get_target_date,
    parse_date_str,
    save_model_summary_to_csv,
    save_to_csv,
    scrape,
    slug_from_store_name,
)


def load_target_stores_from_store_list():
    if not os.path.exists(STORE_LIST_JSON):
        raise SystemExit(f'❌ store_list.json が見つかりません: {STORE_LIST_JSON}')

    with open(STORE_LIST_JSON, encoding='utf-8-sig') as f:
        payload = json.load(f)

    stores = payload.get('stores', []) if isinstance(payload, dict) else []
    if not isinstance(stores, list):
        raise SystemExit('❌ store_list.json の stores が配列ではありません')

    targets = []
    seen = set()
    for item in stores:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name', '')).strip()
        if not name or name in seen:
            continue
        targets.append((name, slug_from_store_name(name)))
        seen.add(name)

    if not targets:
        raise SystemExit('❌ store_list.json に有効な店舗がありません')

    return targets


def build_recent_7days():
    end_date = parse_date_str(get_target_date())
    start_date = end_date - timedelta(days=6)
    return build_target_dates(start_date, end_date)


def collect_existing_pairs(target_store_names, target_dates):
    existing = set()
    if not os.path.exists(RAW_CSV):
        return existing

    target_date_set = set(target_dates)
    with open(RAW_CSV, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            store_name = str(row.get('店名', '')).strip()
            target_date = str(row.get('日付', '')).strip()
            if store_name in target_store_names and target_date in target_date_set:
                existing.add((store_name, target_date))

    return existing


def main():
    stores = load_target_stores_from_store_list()
    target_dates = build_recent_7days()
    target_store_names = {store_name for store_name, _ in stores}

    existing_pairs = collect_existing_pairs(target_store_names, target_dates)

    missing_targets = []
    for store_name, slug in stores:
        for target_date in target_dates:
            if (store_name, target_date) not in existing_pairs:
                missing_targets.append((store_name, slug, target_date))

    print(
        f'=== backfill check: 対象店舗 {len(stores)}件 / 期間 {target_dates[0]} 〜 {target_dates[-1]} / 欠損 {len(missing_targets)}件 ==='
    )

    if not missing_targets:
        print('✅ 欠損なし')
        return

    fetched_rows = []
    fetched_model_summary_rows = []
    for store_name, slug, target_date in missing_targets:
        rows, model_summary_rows, ok = scrape(target_date, store_name, slug)
        fetched_rows.extend(rows)
        fetched_model_summary_rows.extend(model_summary_rows)
        status = '✅' if ok else '⚠️'
        print(f'{status} 店舗名: {store_name} / 欠損日付: {target_date} / 取得行数: {len(rows)}')

    saved = save_to_csv(fetched_rows)
    model_saved = save_model_summary_to_csv(fetched_model_summary_rows)
    print(
        f'✅ backfill 完了: 欠損 {len(missing_targets)}件 / 取得 {len(fetched_rows)}行 / '
        f'更新・追加 {saved}行 / 機種別 {model_saved}行'
    )


if __name__ == '__main__':
    main()
