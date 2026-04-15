import csv
import json
import os
import subprocess
import sys
import argparse
from datetime import datetime, timedelta, timezone

import morning_compute as morning

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
COMPUTE_PY = os.path.join(REPO_DIR, "compute.py")
STORE_MODEL_SUMMARY_CSV = os.path.join(REPO_DIR, "store_model_summary.csv")
STORE_LIST_JSON = os.path.join(REPO_DIR, "store_list.json")
RAW_DATA_CSV = os.path.join(REPO_DIR, "raw_data.csv")
OUT_JSON = os.path.join(REPO_DIR, "candidate_data.json")
SEAT_DATA_JSON = os.path.join(REPO_DIR, "seat_data.json")
JST = timezone(timedelta(hours=9))


def parse_number(value):
    text = str(value or "").replace(",", "").replace("+", "").replace("枚", "").replace("%", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def parse_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    patterns = ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S")
    for fmt in patterns:
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(JST).replace(tzinfo=None)
    except Exception:
        return None


def load_store_model_condition_stats():
    model_stats = {}
    store_stats = {}
    if not os.path.exists(STORE_MODEL_SUMMARY_CSV):
        return model_stats, store_stats

    with open(STORE_MODEL_SUMMARY_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("date"))
            store = str(row.get("store", "")).strip()
            model = morning.normalize_model(str(row.get("model", "")).strip())
            avg_diff = parse_number(row.get("avg_diff"))
            win_rate = parse_number(row.get("win_rate"))
            if dt is None or not store or not model:
                continue
            if avg_diff is None and win_rate is None:
                continue

            weekday = dt.weekday()
            is_special = morning.is_special_day(dt.day)
            model_key = (store, model, weekday, is_special)
            store_key = (store, weekday, is_special)

            model_bucket = model_stats.setdefault(
                model_key,
                {"avg_diff_sum": 0.0, "avg_diff_count": 0, "win_rate_sum": 0.0, "win_rate_count": 0, "sample": 0},
            )
            model_bucket["sample"] += 1
            if avg_diff is not None:
                model_bucket["avg_diff_sum"] += avg_diff
                model_bucket["avg_diff_count"] += 1
            if win_rate is not None:
                model_bucket["win_rate_sum"] += win_rate
                model_bucket["win_rate_count"] += 1

            store_bucket = store_stats.setdefault(store_key, {"win_rate_sum": 0.0, "win_rate_count": 0, "sample": 0})
            store_bucket["sample"] += 1
            if win_rate is not None:
                store_bucket["win_rate_sum"] += win_rate
                store_bucket["win_rate_count"] += 1

    model_summary = {}
    for key, bucket in model_stats.items():
        model_summary[key] = {
            "avg_diff": (
                bucket["avg_diff_sum"] / bucket["avg_diff_count"] if bucket["avg_diff_count"] > 0 else None
            ),
            "win_rate": (
                bucket["win_rate_sum"] / bucket["win_rate_count"] if bucket["win_rate_count"] > 0 else None
            ),
            "sample": bucket["sample"],
        }

    store_summary = {}
    for key, bucket in store_stats.items():
        store_summary[key] = {
            "win_rate": (
                bucket["win_rate_sum"] / bucket["win_rate_count"] if bucket["win_rate_count"] > 0 else None
            ),
            "sample": bucket["sample"],
        }

    return model_summary, store_summary


def enrich_model_ranking_with_summary(payload):
    data_date = parse_date(payload.get("data_date")) or datetime.now(JST).replace(tzinfo=None)
    weekday = data_date.weekday()
    is_special = morning.is_special_day(data_date.day)
    model_summary, store_summary = load_store_model_condition_stats()

    stores_payload = payload.get("stores", {})
    if not isinstance(stores_payload, dict):
        return payload

    for store, store_data in stores_payload.items():
        if not isinstance(store_data, dict):
            continue
        store_cond = store_summary.get((store, weekday, is_special), {})
        store_win_rate = store_cond.get("win_rate")

        ranking = store_data.get("model_ranking")
        if not isinstance(ranking, list):
            continue

        for row in ranking:
            if not isinstance(row, dict):
                continue
            model = morning.normalize_model(row.get("model"))
            cond = model_summary.get((store, model, weekday, is_special), {})

            avg_diff = cond.get("avg_diff")
            win_rate = cond.get("win_rate")
            row["same_condition_avg_diff"] = round(avg_diff, 1) if avg_diff is not None else None
            row["same_condition_win_rate"] = round(win_rate, 1) if win_rate is not None else None
            row["same_condition_sample"] = int(cond.get("sample", 0))
            row["store_same_condition_win_rate"] = (
                round(store_win_rate, 1) if store_win_rate is not None else None
            )
            row["store_same_condition_sample"] = int(store_cond.get("sample", 0))

            is_juggler = "ジャグラー" in model
            if is_juggler and win_rate is not None and store_win_rate is not None:
                diff = win_rate - store_win_rate
                row["juggler_vs_store_win_rate_diff"] = round(diff, 1)
                row["juggler_stronger_than_store"] = diff > 0
            else:
                row["juggler_vs_store_win_rate_diff"] = None
                row["juggler_stronger_than_store"] = None

    return payload


def build_candidate_payload():
    data, normalized_models, unsupported_models = morning.read_labeled_rows()
    if morning.pd is None:
        payload = morning.build_payload_fallback(data, normalized_models, unsupported_models)
    else:
        payload = morning.build_payload(data, normalized_models, unsupported_models)
    return enrich_model_ranking_with_summary(payload)


def run_compute():
    subprocess.run([sys.executable, COMPUTE_PY], check=True, cwd=REPO_DIR)


def normalize_diff_value(value):
    if float(value).is_integer():
        return int(value)
    return round(float(value), 1)


def load_store_list_names():
    if not os.path.exists(STORE_LIST_JSON):
        return []
    try:
        with open(STORE_LIST_JSON, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
    except Exception:
        return []

    stores = payload.get("stores", []) if isinstance(payload, dict) else []
    names = []
    seen = set()
    for row in stores:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip()
        if not name or name in seen:
            continue
        names.append(name)
        seen.add(name)
    return names


def parse_machine_no(value):
    num = parse_number(value)
    if num is None:
        return None
    if not float(num).is_integer():
        return None
    tai = int(num)
    if tai <= 0:
        return None
    return tai


def detect_latest_data_date():
    latest_dt = None
    if not os.path.exists(RAW_DATA_CSV):
        return None
    with open(RAW_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("日付"))
            if dt is None:
                continue
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
    return latest_dt


def build_recent_seat_data_payload(day_window=30):
    store_order = load_store_list_names()
    payload = {"dates": [], "stores": store_order[:], "data": {}}
    if not os.path.exists(RAW_DATA_CSV):
        return payload

    latest_dt = detect_latest_data_date()
    if latest_dt is None:
        return payload

    end_date = latest_dt.date()
    start_date = end_date - timedelta(days=max(0, int(day_window) - 1))
    by_date = {}
    stores_with_data = set()

    with open(RAW_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("日付"))
            if dt is None:
                continue
            d = dt.date()
            if d < start_date or d > end_date:
                continue

            store = str(row.get("店名", "")).strip()
            model = str(row.get("機種名", "")).strip()
            machine_no = parse_machine_no(row.get("台番号"))
            diff = parse_number(row.get("差枚"))
            if not store or machine_no is None or diff is None:
                continue

            ymd = d.strftime("%Y-%m-%d")
            machine_map = by_date.setdefault(ymd, {}).setdefault(store, {})
            machine_map[machine_no] = {
                "machine_no": machine_no,
                "model": model,
                "diff": normalize_diff_value(diff),
            }
            stores_with_data.add(store)

    date_keys = sorted(by_date.keys(), reverse=True)
    store_set = set(store_order)
    extra_stores = sorted(stores_with_data - store_set, key=lambda s: s)
    if extra_stores:
        payload["stores"] = store_order + extra_stores

    ranked_stores = {name: i for i, name in enumerate(payload["stores"])}
    data_out = {}
    for ymd in date_keys:
        store_map = by_date.get(ymd, {})
        if not isinstance(store_map, dict):
            continue
        sorted_store_items = sorted(
            store_map.items(),
            key=lambda item: (ranked_stores.get(item[0], 10**9), item[0]),
        )
        day_out = {}
        for store, machine_map in sorted_store_items:
            if not isinstance(machine_map, dict) or not machine_map:
                continue
            machines = sorted(machine_map.values(), key=lambda row: (row.get("machine_no", 10**9)))
            if machines:
                day_out[store] = machines
        if day_out:
            data_out[ymd] = day_out

    payload["dates"] = date_keys
    payload["data"] = data_out
    return payload


def write_recent_seat_data_json(payload):
    with open(SEAT_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return SEAT_DATA_JSON


def main():
    parser = argparse.ArgumentParser(description="candidate_data.json と seat_data.json を生成します。")
    parser.add_argument(
        "--archive",
        action="store_true",
        help="日付付きのアーカイブJSON（candidate_data_YYYYMMDD.json）も生成する",
    )
    args = parser.parse_args()

    run_compute()

    payload = build_candidate_payload()
    seat_payload = build_recent_seat_data_payload(day_window=30)
    seat_out_json = write_recent_seat_data_json(seat_payload)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    if args.archive:
        data_date = str(payload.get("data_date") or datetime.now(JST).strftime("%Y-%m-%d"))
        archive_suffix = data_date.replace("-", "")
        out_archive_json = os.path.join(REPO_DIR, f"candidate_data_{archive_suffix}.json")
        with open(out_archive_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"generated: {out_archive_json}")

    print(f"generated: {OUT_JSON}")
    print(f"generated: {seat_out_json}")
    print(f"seat_dates: {len(seat_payload.get('dates', []))}")
    print(f"stores: {len(payload.get('stores', {}))}")


if __name__ == "__main__":
    main()
