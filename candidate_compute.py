import csv
import json
import os
import argparse
import re
from datetime import datetime, timedelta, timezone

import morning_compute as morning

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
MORNING_DATA_JSON = os.path.join(REPO_DIR, "morning_data.json")
STORE_MODEL_SUMMARY_CSV = os.path.join(REPO_DIR, "store_model_summary.csv")
STORE_LIST_JSON = os.path.join(REPO_DIR, "store_list.json")
RAW_DATA_CSV = os.path.join(REPO_DIR, "raw_data.csv")
LINE_SLOT_DATA_CSV = os.path.join(REPO_DIR, "line_slot_data.csv")
OUT_JSON = os.path.join(REPO_DIR, "candidate_data.json")
SEAT_DATA_JSON = os.path.join(REPO_DIR, "seat_data.json")
JST = timezone(timedelta(hours=9))


def parse_number(value):
    text = str(value or "").replace(",", "").replace("+", "").replace("枚", "").replace("%", "").strip()
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None


def parse_int(value):
    n = parse_number(value)
    if n is None:
        return None
    return int(round(n))


def parse_line_note_values(note):
    values = {}
    for part in str(note or "").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        parsed = parse_int(value)
        if key and parsed is not None:
            values[key] = parsed
    return values


def build_line_treatment_payload(payload):
    total_game = parse_int(payload.get("totalGame"))
    max_payout = parse_int(payload.get("maxPayout"))
    graph_trend = str(payload.get("graphTrend") or "").strip()
    graph_movement = parse_int(payload.get("graphMovement"))

    score = 0
    signals = []

    graph_score = {
        "上げ": 38,
        "V字": 32,
        "山型": 18,
        "荒い": 8,
        "下げ": -22,
    }.get(graph_trend, 0)
    if graph_trend:
        score += graph_score
        signals.append(f"グラフ傾向 {graph_trend}")

    if graph_movement is not None:
        if graph_movement >= 3000:
            score += 28
            signals.append(f"グラフ上昇幅 +{graph_movement:,}")
        elif graph_movement >= 1000:
            score += 16
            signals.append(f"グラフ上昇幅 +{graph_movement:,}")
        elif graph_movement <= -2000:
            score -= 16
            signals.append(f"グラフ下落幅 {graph_movement:,}")

    if total_game is not None:
        if total_game >= 8000:
            score += 15
            signals.append(f"高稼働 {total_game:,}G")
        elif total_game >= 6000:
            score += 10
            signals.append(f"稼働強め {total_game:,}G")
        elif total_game >= 3000:
            score += 4
            signals.append(f"稼働あり {total_game:,}G")
        elif total_game <= 1500:
            score -= 5
            signals.append(f"稼働浅め {total_game:,}G")

    if max_payout is not None:
        if max_payout >= 10000:
            score += 10
            signals.append(f"最大放出大 {max_payout:,}枚")
        elif max_payout >= 5000:
            score += 6
            signals.append(f"最大放出注目 {max_payout:,}枚")
        elif max_payout >= 2000:
            score += 3
            signals.append(f"最大放出あり {max_payout:,}枚")

    has_graph = bool(graph_trend) or graph_movement is not None
    has_context = total_game is not None or max_payout is not None
    if not has_graph and not has_context:
        label = "データ不足"
        signals.append("グラフ/稼働の根拠が未入力")
    elif not has_graph and score < 20:
        label = "件数少"
        signals.append("グラフ未入力のため参考")
    elif score >= 55:
        label = "強め推移"
    elif score >= 25:
        label = "注目変化"
    elif score <= -10:
        label = "落ち気味"
    else:
        label = "要観察"

    if payload.get("graphNote"):
        signals.append(f"グラフメモ {payload.get('graphNote')}")

    score = max(0, min(100, int(round(score))))
    return {
        "treatmentScore": score,
        "treatmentLabel": label,
        "treatmentSignals": signals[:6],
        "sourceQuality": "グラフ中心" if has_graph else "参考値",
        # 旧UIとの互換。UI側は treatment* を優先して読む。
        "lineStrengthScore": score,
        "lineStrengthLabel": label,
        "lineSignals": signals[:6],
    }


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


def detect_latest_line_slot_date():
    if not os.path.exists(LINE_SLOT_DATA_CSV):
        return None
    latest = None
    with open(LINE_SLOT_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("date") or row.get("日付"))
            if dt is not None and (latest is None or dt > latest):
                latest = dt
    return latest


def merge_line_slot_rows(by_date, stores_with_data, start_date=None, end_date=None):
    if not os.path.exists(LINE_SLOT_DATA_CSV):
        return
    with open(LINE_SLOT_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("date") or row.get("日付"))
            if dt is None:
                continue
            d = dt.date()
            if start_date is not None and d < start_date:
                continue
            if end_date is not None and d > end_date:
                continue

            store = str(row.get("store") or row.get("店名") or "").strip()
            model = str(row.get("model") or row.get("機種名") or "").strip()
            machine_no = parse_int(row.get("machine_no") or row.get("台番号"))
            if not store or machine_no is None:
                continue

            payload = {
                "machine_no": machine_no,
                "model": model or "不明",
                "diff": None,
                "source": str(row.get("source") or "line").strip() or "line",
                "line": True,
            }
            optional_fields = [
                ("rate", "rate"),
                ("total_game", "totalGame"),
                ("big", "big"),
                ("reg", "reg"),
                ("at_art", "atArt"),
                ("combined_rate", "combinedRate"),
                ("at_art_rate", "atArtRate"),
                ("last_game", "lastGame"),
                ("max_payout", "maxPayout"),
                ("graph_trend", "graphTrend"),
                ("graph_movement", "graphMovement"),
                ("graph_note", "graphNote"),
                ("note", "note"),
            ]
            for src_key, out_key in optional_fields:
                raw_value = row.get(src_key)
                if raw_value is None:
                    continue
                text = str(raw_value).strip()
                if not text:
                    continue
                if out_key in {"totalGame", "big", "reg", "atArt", "lastGame", "maxPayout"}:
                    parsed = parse_int(text)
                    if parsed is not None:
                        payload[out_key] = parsed
                else:
                    payload[out_key] = text
            payload.update(build_line_treatment_payload(payload))

            ymd = d.strftime("%Y-%m-%d")
            machine_map = by_date.setdefault(ymd, {}).setdefault(store, {})
            existing = machine_map.get(machine_no) or {}
            merged = {**payload, **existing}
            merged["line"] = True
            if existing.get("diff") is not None:
                merged["diff"] = existing.get("diff")
            machine_map[machine_no] = merged
            stores_with_data.add(store)


def load_store_model_condition_stats():
    model_stats = {}
    store_stats = {}
    if not os.path.exists(STORE_MODEL_SUMMARY_CSV):
        return model_stats, store_stats

    special_by_store = morning.load_store_special_map()
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
            is_special = morning.is_store_special_day(store, dt.day, special_by_store)
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
    data_date = parse_date(payload.get("target_date") or payload.get("data_date")) or datetime.now(JST).replace(tzinfo=None)
    weekday = data_date.weekday()
    special_by_store = morning.load_store_special_map()
    model_summary, store_summary = load_store_model_condition_stats()

    stores_payload = payload.get("stores", {})
    if not isinstance(stores_payload, dict):
        return payload

    for store, store_data in stores_payload.items():
        if not isinstance(store_data, dict):
            continue
        is_special = morning.is_store_special_day(store, data_date.day, special_by_store)
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


def load_morning_payload():
    if not os.path.exists(MORNING_DATA_JSON):
        raise FileNotFoundError(
            "morning_data.json が見つかりません。先に morning_compute.py を実行してください。"
        )
    with open(MORNING_DATA_JSON, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("morning_data.json の形式が不正です")
    return payload


def build_candidate_payload():
    payload = load_morning_payload()
    return enrich_model_ranking_with_summary(payload)


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


def finalize_seat_data_payload(store_order, by_date, stores_with_data, available_dates=None):
    payload = {"dates": [], "stores": store_order[:], "data": {}}
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
    if available_dates is not None:
        payload["available_dates"] = sorted(set(available_dates), reverse=True)
    payload["data"] = data_out
    return payload


def build_recent_seat_data_payload(day_window=30):
    store_order = load_store_list_names()
    if not os.path.exists(RAW_DATA_CSV):
        return {"dates": [], "stores": store_order[:], "data": {}}

    latest_candidates = [dt for dt in [detect_latest_data_date(), detect_latest_line_slot_date()] if dt is not None]
    latest_dt = max(latest_candidates) if latest_candidates else None
    if latest_dt is None:
        return {"dates": [], "stores": store_order[:], "data": {}}

    end_date = latest_dt.date()
    start_date = end_date - timedelta(days=max(0, int(day_window) - 1))
    by_date = {}
    stores_with_data = set()
    available_dates = set()

    with open(RAW_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("日付"))
            if dt is None:
                continue
            d = dt.date()
            available_dates.add(d.strftime("%Y-%m-%d"))
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

    merge_line_slot_rows(by_date, stores_with_data, start_date, end_date)
    available_dates.update(by_date.keys())
    return finalize_seat_data_payload(store_order, by_date, stores_with_data, available_dates)


def build_monthly_seat_data_payloads():
    store_order = load_store_list_names()
    if not os.path.exists(RAW_DATA_CSV):
        return {}

    by_month_date = {}
    stores_by_month = {}
    with open(RAW_DATA_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row.get("日付"))
            if dt is None:
                continue

            store = str(row.get("店名", "")).strip()
            model = str(row.get("機種名", "")).strip()
            machine_no = parse_machine_no(row.get("台番号"))
            diff = parse_number(row.get("差枚"))
            if not store or machine_no is None or diff is None:
                continue

            ymd = dt.strftime("%Y-%m-%d")
            month_key = ymd[:7]
            machine_map = by_month_date.setdefault(month_key, {}).setdefault(ymd, {}).setdefault(store, {})
            machine_map[machine_no] = {
                "machine_no": machine_no,
                "model": model,
                "diff": normalize_diff_value(diff),
            }
            stores_by_month.setdefault(month_key, set()).add(store)

    line_by_date = {}
    line_stores = set()
    merge_line_slot_rows(line_by_date, line_stores)
    for ymd, store_map in line_by_date.items():
        month_key = ymd[:7]
        month_bucket = by_month_date.setdefault(month_key, {})
        month_day = month_bucket.setdefault(ymd, {})
        for store, machine_map in store_map.items():
            target = month_day.setdefault(store, {})
            for machine_no, payload in machine_map.items():
                existing = target.get(machine_no) or {}
                target[machine_no] = {**payload, **existing, "line": True}
                if existing.get("diff") is not None:
                    target[machine_no]["diff"] = existing.get("diff")
            stores_by_month.setdefault(month_key, set()).add(store)

    return {
        month_key: finalize_seat_data_payload(store_order, by_date, stores_by_month.get(month_key, set()))
        for month_key, by_date in by_month_date.items()
    }


def write_recent_seat_data_json(payload):
    with open(SEAT_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return SEAT_DATA_JSON


def write_monthly_seat_data_json(payloads):
    written = []
    for month_key, payload in sorted((payloads or {}).items()):
        if not payload.get("dates"):
            continue
        out_path = os.path.join(REPO_DIR, f"seat_data_{month_key}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        written.append(out_path)
    return written


def main():
    parser = argparse.ArgumentParser(description="candidate_data.json と seat_data.json を生成します。")
    parser.add_argument(
        "--archive",
        action="store_true",
        help="日付付きのアーカイブJSON（candidate_data_YYYYMMDD.json）も生成する",
    )
    args = parser.parse_args()

    payload = build_candidate_payload()
    seat_payload = build_recent_seat_data_payload(day_window=30)
    seat_out_json = write_recent_seat_data_json(seat_payload)
    monthly_out_json = write_monthly_seat_data_json(build_monthly_seat_data_payloads())

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
    print(f"generated monthly seat_data: {len(monthly_out_json)} files")
    print(f"seat_dates: {len(seat_payload.get('dates', []))}")
    print(f"stores: {len(payload.get('stores', {}))}")


if __name__ == "__main__":
    main()
