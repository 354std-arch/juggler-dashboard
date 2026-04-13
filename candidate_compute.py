import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import morning_compute as morning

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
COMPUTE_PY = os.path.join(REPO_DIR, "compute.py")
STORE_MODEL_SUMMARY_CSV = os.path.join(REPO_DIR, "store_model_summary.csv")
RAW_DATA_CSV = os.path.join(REPO_DIR, "raw_data.csv")
OUT_JSON = os.path.join(REPO_DIR, "candidate_data.json")
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


def normalize_tai_key(value):
    num = parse_number(value)
    if num is None:
        return ""
    if float(num).is_integer():
        return str(int(num))
    return str(num)


def normalize_diff_value(value):
    if float(value).is_integer():
        return int(value)
    return round(float(value), 1)


def build_seat_diff_by_date():
    by_date = {}
    if not os.path.exists(RAW_DATA_CSV):
        return by_date

    with open(RAW_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("日付"))
            store = str(row.get("店名", "")).strip()
            tai = normalize_tai_key(row.get("台番号"))
            diff = parse_number(row.get("差枚"))
            if dt is None or not store or not tai or diff is None:
                continue

            ymd = dt.strftime("%Y%m%d")
            store_bucket = by_date.setdefault(ymd, {}).setdefault(store, {})
            store_bucket[tai] = normalize_diff_value(diff)

    return by_date


def write_seat_data_json(date_suffix, payload):
    out_path = os.path.join(REPO_DIR, f"seat_data_{date_suffix}.json")
    sorted_payload = {}
    for store in sorted(payload.keys(), key=lambda v: str(v)):
        tai_map = payload.get(store, {})
        if not isinstance(tai_map, dict):
            continue
        sorted_tai = sorted(
            tai_map.items(),
            key=lambda item: (int(item[0]) if str(item[0]).isdigit() else 10**9, str(item[0])),
        )
        sorted_payload[store] = {str(tai): diff for tai, diff in sorted_tai}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sorted_payload, f, ensure_ascii=False, indent=2)

    return out_path


def main():
    run_compute()

    payload = build_candidate_payload()
    data_date = str(payload.get("data_date") or datetime.now(JST).strftime("%Y-%m-%d"))
    archive_suffix = data_date.replace("-", "")
    out_archive_json = os.path.join(REPO_DIR, f"candidate_data_{archive_suffix}.json")
    seat_by_date = build_seat_diff_by_date()
    seat_payload = seat_by_date.get(archive_suffix, {})
    seat_out_json = write_seat_data_json(archive_suffix, seat_payload)

    for path in (OUT_JSON, out_archive_json):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"generated: {OUT_JSON}")
    print(f"generated: {out_archive_json}")
    print(f"generated: {seat_out_json}")
    print(f"stores: {len(payload.get('stores', {}))}")


if __name__ == "__main__":
    main()
