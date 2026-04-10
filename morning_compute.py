import csv
import json
import math
import os
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

try:
    import pandas as pd
except Exception:
    pd = None

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV = os.path.join(REPO_DIR, "raw_data.csv")
OUT_JSON = os.path.join(REPO_DIR, "morning_data.json")
JST = timezone(timedelta(hours=9))

# compute.py と同等の正規化ロジック/設定値を流用
MODEL_NAME_MAP = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラー",
    "ジャグラーガールズ": "ジャグラーガールズSS",
    "スマスロ ハナビ": "スマスロハナビ",
}

MODEL_SETTINGS = {
    "ネオアイムジャグラー": {"syn": {1: 168, 2: 161, 3: 148, 4: 142, 5: 128, 6: 128}, "bb": {1: 273, 2: 269, 3: 269, 4: 259, 5: 259, 6: 255}, "rb": {1: 439, 2: 399, 3: 331, 4: 315, 5: 255, 6: 255}},
    "ウルトラミラクルジャグラー": {"syn": {1: 164, 2: 158, 3: 147, 4: 138, 5: 130, 6: 121}, "bb": {1: 267, 2: 261, 3: 256, 4: 242, 5: 233, 6: 216}, "rb": {1: 425, 2: 402, 3: 350, 4: 322, 5: 297, 6: 277}},
    "ミスタージャグラー": {"syn": {1: 156, 2: 152, 3: 145, 4: 134, 5: 124, 6: 118}, "bb": {1: 268, 2: 267, 3: 260, 4: 249, 5: 240, 6: 237}, "rb": {1: 374, 2: 354, 3: 331, 4: 291, 5: 257, 6: 237}},
    "ジャグラーガールズSS": {"syn": {1: 159, 2: 152, 3: 142, 4: 132, 5: 128, 6: 119}, "bb": {1: 273, 2: 270, 3: 260, 4: 250, 5: 243, 6: 226}, "rb": {1: 381, 2: 350, 3: 316, 4: 281, 5: 270, 6: 252}},
    "ゴーゴージャグラー3": {"syn": {1: 149, 2: 145, 3: 139, 4: 130, 5: 123, 6: 117}, "bb": {1: 259, 2: 258, 3: 257, 4: 254, 5: 247, 6: 234}, "rb": {1: 354, 2: 332, 3: 306, 4: 268, 5: 247, 6: 234}},
    "ハッピージャグラーVIII": {"syn": {1: 161, 2: 154, 3: 146, 4: 137, 5: 127, 6: 120}, "bb": {1: 273, 2: 270, 3: 263, 4: 254, 5: 239, 6: 226}, "rb": {1: 397, 2: 362, 3: 332, 4: 300, 5: 273, 6: 256}},
    "マイジャグラーV": {"syn": {1: 163, 2: 159, 3: 148, 4: 135, 5: 126, 6: 114}, "bb": {1: 273, 2: 270, 3: 266, 4: 254, 5: 240, 6: 229}, "rb": {1: 409, 2: 385, 3: 336, 4: 290, 5: 268, 6: 229}},
    "ファンキージャグラー2": {"syn": {1: 165, 2: 158, 3: 150, 4: 140, 5: 133, 6: 119}, "bb": {1: 266, 2: 259, 3: 256, 4: 249, 5: 240, 6: 219}, "rb": {1: 439, 2: 407, 3: 366, 4: 322, 5: 299, 6: 262}},
    "新ハナビ": {"syn": {1: 131, 2: 127, 3: 122, 4: 118, 5: 113, 6: 109}, "bb": {1: 240, 2: 234, 3: 228, 4: 221, 5: 214, 6: 205}, "rb": {1: 397, 2: 378, 3: 357, 4: 336, 5: 314, 6: 290}},
    "スマスロハナビ": {"syn": {1: 176, 2: 161, 3: 155, 4: 149, 5: 143, 6: 137}, "bb": {1: 282, 2: 270, 3: 261, 4: 252, 5: 243, 6: 234}, "rb": {1: 470, 2: 434, 3: 398, 4: 364, 5: 336, 6: 303}},
    "クランキーセレブレーション": {"syn": {1: 160, 2: 154, 3: 146, 4: 137, 5: 129, 6: 120}, "bb": {1: 268, 2: 260, 3: 252, 4: 240, 5: 229, 6: 216}, "rb": {1: 400, 2: 375, 3: 349, 4: 320, 5: 293, 6: 265}},
}

MODEL_SYN_T4 = {model: values["syn"][4] for model, values in MODEL_SETTINGS.items()}
MODEL_RB_T4 = {model: values["rb"][4] for model, values in MODEL_SETTINGS.items()}
UPPER_LABELS = {"強上候補", "上候補"}

DECAY = math.log(2.0) / 180.0
CHUNK_SIZE = 200_000

COLUMN_ALIASES = {
    "date": ["date", "日付", "data_date", "target_date"],
    "store": ["store", "店名", "store_name"],
    "model": ["model", "機種名", "model_name"],
    "tai": ["tai", "台番号", "tai_no", "machine_no"],
    "bb": ["bb", "BB", "big", "BIG"],
    "rb": ["rb", "RB", "reg", "REG"],
    "diff": ["diff", "差枚", "difference"],
    "total_g": ["total_g", "G数", "g", "game", "games"],
}


def normalize_model(model_name):
    name = str(model_name or "").replace("　", " ").strip()
    mapped = MODEL_NAME_MAP.get(name, name)
    if mapped.replace(" ", "") == "スマスロハナビ":
        return "スマスロハナビ"
    return mapped


def resolve_columns(columns):
    available = {str(c).strip(): c for c in columns}
    resolved = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        hit = None
        for alias in aliases:
            if alias in available:
                hit = available[alias]
                break
        if hit is None:
            raise ValueError(f"required column not found: {canonical} ({aliases})")
        resolved[canonical] = hit
    return resolved


def to_numeric(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.replace("+", "", regex=False).str.strip(),
        errors="coerce",
    )


def is_special_day(day):
    day_int = int(day)
    text = str(day_int)
    is_repdigit = len(text) >= 2 and len(set(text)) == 1
    return (day_int % 10 in (0, 7)) or is_repdigit


def parse_number(value, default=0.0):
    text = str(value or "").replace(",", "").replace("+", "").strip()
    if text == "":
        return default
    try:
        return float(text)
    except Exception:
        return default


def parse_date_value(value):
    text = str(value or "").strip()
    if not text:
        return None
    patterns = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def classify_label(total_g, bb, rb, diff, syn_threshold, rb_threshold):
    syn_ratio = (total_g / (bb + rb)) if (bb + rb) > 0 else None
    rb_ratio = (total_g / rb) if rb > 0 else None
    if (
        total_g >= 5000
        and rb_ratio is not None
        and syn_ratio is not None
        and rb_ratio <= rb_threshold
        and syn_ratio <= syn_threshold
    ):
        return "強上候補"
    if total_g >= 3500 and (
        (rb_ratio is not None and rb_ratio <= rb_threshold)
        or (syn_ratio is not None and syn_ratio <= syn_threshold)
    ):
        return "上候補"
    bb_bad = bb > 0 and (total_g / bb) < 240 and (rb_ratio is None or rb_ratio > rb_threshold)
    diff_bad = diff > 0 and (rb_ratio is None or rb_ratio > rb_threshold) and (
        syn_ratio is None or syn_ratio > syn_threshold
    )
    if total_g < 2500 or bb_bad or diff_bad:
        return "除外寄り"
    return "中間"


def rate_table(df, group_keys):
    if df.empty:
        cols = list(group_keys) + ["strong_rate", "upper_rate", "sample"]
        return pd.DataFrame(columns=cols)
    grouped = (
        df.groupby(group_keys, sort=False)["label"]
        .agg(
            sample="size",
            strong=lambda s: (s == "強上候補").sum(),
            upper=lambda s: s.isin(UPPER_LABELS).sum(),
        )
        .reset_index()
    )
    grouped["strong_rate"] = grouped["strong"] / grouped["sample"]
    grouped["upper_rate"] = grouped["upper"] / grouped["sample"]
    return grouped[group_keys + ["strong_rate", "upper_rate", "sample"]]


def read_labeled_rows_fallback():
    with open(RAW_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        resolved_cols = resolve_columns(reader.fieldnames or [])

        normalized_models = {}
        unsupported_models = set()
        rows = []

        for src in reader:
            raw_store = str(src.get(resolved_cols["store"], "")).strip()
            raw_model = str(src.get(resolved_cols["model"], "")).replace("　", " ").strip()
            normalized_model = normalize_model(raw_model)

            if raw_model:
                normalized_models[raw_model] = normalized_model

            dt = parse_date_value(src.get(resolved_cols["date"]))
            tai_raw = parse_number(src.get(resolved_cols["tai"]), default=float("nan"))
            total_g = parse_number(src.get(resolved_cols["total_g"]), default=0.0)
            bb = parse_number(src.get(resolved_cols["bb"]), default=0.0)
            rb = parse_number(src.get(resolved_cols["rb"]), default=0.0)
            diff = parse_number(src.get(resolved_cols["diff"]), default=0.0)

            if dt is None or not raw_store or not math.isfinite(tai_raw) or total_g <= 0:
                continue

            if normalized_model not in MODEL_SETTINGS:
                if normalized_model:
                    unsupported_models.add(normalized_model)
                continue

            tai = int(tai_raw)
            syn_threshold = MODEL_SYN_T4[normalized_model]
            rb_threshold = MODEL_RB_T4[normalized_model]
            label = classify_label(total_g, bb, rb, diff, syn_threshold, rb_threshold)

            rows.append(
                {
                    "date": dt,
                    "store": raw_store,
                    "model": normalized_model,
                    "tai": tai,
                    "bb": bb,
                    "rb": rb,
                    "diff": diff,
                    "total_g": total_g,
                    "weekday": dt.weekday(),
                    "is_special": is_special_day(dt.day),
                    "label": label,
                }
            )

    return rows, normalized_models, sorted(unsupported_models)


def read_labeled_rows():
    if pd is None:
        return read_labeled_rows_fallback()

    header = pd.read_csv(RAW_CSV, encoding="utf-8-sig", nrows=0)
    resolved_cols = resolve_columns(header.columns.tolist())
    usecols = list(dict.fromkeys(resolved_cols.values()))

    normalized_models = {}
    unsupported_models = set()
    frames = []

    for chunk in pd.read_csv(
        RAW_CSV,
        encoding="utf-8-sig",
        dtype=str,
        usecols=usecols,
        chunksize=CHUNK_SIZE,
    ):
        for canonical, original in resolved_cols.items():
            chunk[canonical] = chunk[original]

        chunk["store"] = chunk["store"].fillna("").astype(str).str.strip()
        chunk["model_raw"] = chunk["model"].fillna("").astype(str).str.replace("　", " ", regex=False).str.strip()
        chunk["model"] = chunk["model_raw"].map(normalize_model)

        model_pairs = chunk.loc[chunk["model_raw"] != "", ["model_raw", "model"]].drop_duplicates()
        for raw_name, normalized in model_pairs.itertuples(index=False):
            normalized_models[raw_name] = normalized

        chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
        chunk["tai"] = to_numeric(chunk["tai"])
        chunk["bb"] = to_numeric(chunk["bb"]).fillna(0.0)
        chunk["rb"] = to_numeric(chunk["rb"]).fillna(0.0)
        chunk["diff"] = to_numeric(chunk["diff"]).fillna(0.0)
        chunk["total_g"] = to_numeric(chunk["total_g"]).fillna(0.0)

        valid_mask = (
            chunk["date"].notna()
            & (chunk["store"] != "")
            & chunk["tai"].notna()
            & (chunk["total_g"] > 0)
        )
        chunk = chunk.loc[valid_mask].copy()
        if chunk.empty:
            continue

        supported_mask = chunk["model"].isin(MODEL_SETTINGS)
        unsupported = chunk.loc[~supported_mask, "model"].dropna().astype(str).str.strip()
        for name in unsupported:
            if name:
                unsupported_models.add(name)
        chunk = chunk.loc[supported_mask].copy()
        if chunk.empty:
            continue

        chunk["tai"] = chunk["tai"].astype(int)
        chunk["weekday"] = chunk["date"].dt.weekday.astype(int)
        chunk["day"] = chunk["date"].dt.day.astype(int)
        chunk["is_special"] = chunk["day"].isin([11, 22]) | chunk["day"].mod(10).isin([0, 7])

        bonus_total = chunk["bb"] + chunk["rb"]
        chunk["syn_ratio"] = (chunk["total_g"] / bonus_total).where(bonus_total > 0)
        chunk["rb_ratio"] = (chunk["total_g"] / chunk["rb"]).where(chunk["rb"] > 0)
        chunk["bb_ratio"] = (chunk["total_g"] / chunk["bb"]).where(chunk["bb"] > 0)

        chunk["syn_threshold"] = chunk["model"].map(MODEL_SYN_T4)
        chunk["rb_threshold"] = chunk["model"].map(MODEL_RB_T4)

        cond1 = (
            (chunk["total_g"] >= 5000)
            & (chunk["rb_ratio"] <= chunk["rb_threshold"])
            & (chunk["syn_ratio"] <= chunk["syn_threshold"])
        )
        cond2 = (
            (chunk["total_g"] >= 3500)
            & (
                (chunk["rb_ratio"] <= chunk["rb_threshold"])
                | (chunk["syn_ratio"] <= chunk["syn_threshold"])
            )
        )
        rb_bad_or_none = chunk["rb_ratio"].isna() | (chunk["rb_ratio"] > chunk["rb_threshold"])
        syn_bad_or_none = chunk["syn_ratio"].isna() | (chunk["syn_ratio"] > chunk["syn_threshold"])
        cond3 = (
            (chunk["total_g"] < 2500)
            | ((chunk["bb"] > 0) & (chunk["bb_ratio"] < 240) & rb_bad_or_none)
            | ((chunk["diff"] > 0) & rb_bad_or_none & syn_bad_or_none)
        )

        chunk["label"] = "中間"
        chunk.loc[cond3, "label"] = "除外寄り"
        chunk.loc[cond2, "label"] = "上候補"
        chunk.loc[cond1, "label"] = "強上候補"

        frames.append(
            chunk[
                [
                    "date",
                    "store",
                    "model",
                    "tai",
                    "bb",
                    "rb",
                    "diff",
                    "total_g",
                    "weekday",
                    "is_special",
                    "label",
                ]
            ]
        )

    if not frames:
        return pd.DataFrame(), normalized_models, sorted(unsupported_models)
    return pd.concat(frames, ignore_index=True), normalized_models, sorted(unsupported_models)


def build_payload_fallback(rows, normalized_models, unsupported_models):
    now_jst = datetime.now(JST)
    today_date = now_jst.date()
    today_weekday = now_jst.weekday()
    today_special = is_special_day(now_jst.day)

    if not rows:
        return {
            "generated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
            "data_date": now_jst.strftime("%Y-%m-%d"),
            "normalized_models": dict(sorted(normalized_models.items())),
            "unsupported_models": sorted(unsupported_models),
            "stores": {},
        }

    def add_rate_stat(container, key, label):
        stat = container.setdefault(key, {"total": 0, "strong": 0, "upper": 0})
        stat["total"] += 1
        if label == "強上候補":
            stat["strong"] += 1
        if label in UPPER_LABELS:
            stat["upper"] += 1

    store_day = {}
    store_model_day = {}
    store_tail = {}
    today_label_counter = defaultdict(Counter)
    by_tai = defaultdict(list)

    for r in rows:
        store = r["store"]
        weekday = int(r["weekday"])
        is_special = bool(r["is_special"])
        label = r["label"]
        model = r["model"]
        tai = int(r["tai"])

        add_rate_stat(store_day, (store, weekday, is_special), label)
        add_rate_stat(store_model_day, (store, model, weekday, is_special), label)
        add_rate_stat(store_tail, (store, tai % 10), label)

        if weekday == today_weekday and is_special == today_special:
            today_label_counter[store][label] += 1
        by_tai[(store, tai)].append(r)

    store_day_lookup = {}
    for key, stat in store_day.items():
        total = stat["total"]
        upper_rate = (stat["upper"] / total) if total else 0.0
        store_day_lookup[key] = (upper_rate, total)

    model_day_lookup = {}
    for key, stat in store_model_day.items():
        total = stat["total"]
        upper_rate = (stat["upper"] / total) if total else 0.0
        model_day_lookup[key] = (upper_rate, total)

    model_rankings = defaultdict(list)
    for (store, model, weekday, is_special), stat in store_model_day.items():
        if weekday != today_weekday or is_special != today_special:
            continue
        total = stat["total"]
        upper_rate = (stat["upper"] / total) if total else 0.0
        model_rankings[store].append(
            {
                "model": model,
                "score": round(upper_rate, 6),
                "reason": f"上候補以上率{upper_rate:.0%}({total}件)",
                "sample": total,
            }
        )
    for store in list(model_rankings.keys()):
        model_rankings[store].sort(key=lambda x: x["score"], reverse=True)
        model_rankings[store] = model_rankings[store][:5]

    tail_rankings = defaultdict(list)
    for (store, tail), stat in store_tail.items():
        total = stat["total"]
        upper_rate = (stat["upper"] / total) if total else 0.0
        tail_rankings[store].append(
            {"tail": int(tail), "score": round(upper_rate, 6), "sample": total}
        )
    for store in list(tail_rankings.keys()):
        tail_rankings[store].sort(key=lambda x: x["score"], reverse=True)

    candidate_by_store = defaultdict(list)
    recent_cutoff = (now_jst - timedelta(days=90)).replace(tzinfo=None)
    for (store, tai), tai_rows in by_tai.items():
        tai_rows.sort(key=lambda x: x["date"])
        last_change_date = None
        prev_model = None
        for r in tai_rows:
            if prev_model is not None and r["model"] != prev_model:
                last_change_date = r["date"]
            prev_model = r["model"]

        recent_model = tai_rows[-1]["model"]
        eligible = [
            r for r in tai_rows
            if last_change_date is None or r["date"] > last_change_date
        ]
        if not eligible:
            continue

        sample = len(eligible)
        weight_sum = 0.0
        upper_weight = 0.0
        strong_weight = 0.0
        overall_upper_count = 0
        recent_upper_count = 0
        recent_count = 0

        for r in eligible:
            days_ago = max(0, (today_date - r["date"].date()).days)
            weight = math.exp(-DECAY * days_ago)
            weight_sum += weight
            if r["label"] in UPPER_LABELS:
                upper_weight += weight
                overall_upper_count += 1
                if r["date"] >= recent_cutoff:
                    recent_upper_count += 1
            if r["label"] == "強上候補":
                strong_weight += weight
            if r["date"] >= recent_cutoff:
                recent_count += 1

        if weight_sum <= 0:
            continue

        tai_upper_rate = upper_weight / weight_sum
        overall_upper = overall_upper_count / sample if sample else 0.0
        recent_upper = recent_upper_count / recent_count if recent_count else overall_upper
        if recent_upper > overall_upper + 0.05:
            trend = "上昇"
        elif recent_upper < overall_upper - 0.05:
            trend = "下降"
        else:
            trend = "横ばい"

        store_day_score, _ = store_day_lookup.get((store, today_weekday, today_special), (0.0, 0))
        model_score, _ = model_day_lookup.get((store, recent_model, today_weekday, today_special), (0.0, 0))
        total_score = 0.35 * store_day_score + 0.40 * model_score + 0.25 * tai_upper_rate

        warnings = []
        if sample < 10:
            warnings.append("サンプル数が10件未満")
        if last_change_date is not None:
            days_since_change = (today_date - last_change_date.date()).days
            if days_since_change <= 90:
                warnings.append(f"台番号変動あり（直近{days_since_change}日）")

        candidate_by_store[store].append(
            {
                "tai": int(tai),
                "model": recent_model,
                "score": round(total_score, 6),
                "reasons": [
                    f"上候補以上率{tai_upper_rate:.0%}",
                    f"サンプル{sample}件",
                    f"推移{trend}",
                ][:3],
                "warnings": warnings[:2],
            }
        )

    for store in list(candidate_by_store.keys()):
        candidate_by_store[store].sort(key=lambda x: x["score"], reverse=True)

    stores_payload = {}
    store_names = sorted({r["store"] for r in rows})
    for store in store_names:
        today_score, today_sample = store_day_lookup.get((store, today_weekday, today_special), (0.0, 0))
        if today_score >= 0.4:
            today_label = "強い"
        elif today_score < 0.2:
            today_label = "弱い"
        else:
            today_label = "普通"

        counter = today_label_counter.get(store, Counter())
        mode_label = counter.most_common(1)[0][0] if counter else "データ不足"
        stores_payload[store] = {
            "today_score": round(float(today_score), 6),
            "today_label": today_label,
            "today_reason": [
                f"同条件上候補率{today_score:.0%}",
                f"サンプル{today_sample}件",
                f"最多ラベル{mode_label}",
            ][:3],
            "model_ranking": model_rankings.get(store, []),
            "tail_ranking": tail_rankings.get(store, []),
            "candidates": candidate_by_store.get(store, []),
        }

    return {
        "generated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "data_date": now_jst.strftime("%Y-%m-%d"),
        "normalized_models": dict(sorted(normalized_models.items())),
        "unsupported_models": sorted(unsupported_models),
        "stores": stores_payload,
    }


def build_payload(df, normalized_models, unsupported_models):
    now_jst = datetime.now(JST)
    today_date = now_jst.date()
    today_weekday = now_jst.weekday()
    today_special = is_special_day(now_jst.day)

    if df.empty:
        return {
            "generated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
            "data_date": now_jst.strftime("%Y-%m-%d"),
            "normalized_models": dict(sorted(normalized_models.items())),
            "unsupported_models": unsupported_models,
            "stores": {},
        }

    store_day_stats = rate_table(df, ["store", "weekday", "is_special"])
    store_model_day_stats = rate_table(df, ["store", "model", "weekday", "is_special"])
    tail_df = df.copy()
    tail_df["tail"] = tail_df["tai"] % 10
    store_tail_stats = rate_table(tail_df, ["store", "tail"])

    store_day_lookup = {
        (r.store, int(r.weekday), bool(r.is_special)): (float(r.upper_rate), int(r.sample))
        for r in store_day_stats.itertuples(index=False)
    }
    model_day_lookup = {
        (r.store, r.model, int(r.weekday), bool(r.is_special)): (float(r.upper_rate), int(r.sample))
        for r in store_model_day_stats.itertuples(index=False)
    }

    df_sorted = df.sort_values(["store", "tai", "date"]).copy()
    df_sorted["prev_model"] = df_sorted.groupby(["store", "tai"])["model"].shift(1)
    df_sorted["model_changed"] = (
        df_sorted["prev_model"].notna() & (df_sorted["model"] != df_sorted["prev_model"])
    )
    last_change = (
        df_sorted.loc[df_sorted["model_changed"], ["store", "tai", "date"]]
        .groupby(["store", "tai"], sort=False)["date"]
        .max()
        .rename("last_change_date")
    )
    df_sorted = df_sorted.join(last_change, on=["store", "tai"])
    df_sorted["tai_eligible"] = df_sorted["last_change_date"].isna() | (
        df_sorted["date"] > df_sorted["last_change_date"]
    )
    days_ago = (today_date - df_sorted["date"].dt.date).map(lambda d: max(0, int(d.days)))
    df_sorted["weight"] = days_ago.map(lambda d: math.exp(-DECAY * d))
    df_sorted["is_upper"] = df_sorted["label"].isin(UPPER_LABELS)
    df_sorted["is_strong"] = df_sorted["label"] == "強上候補"

    recent_model_by_tai = (
        df_sorted.groupby(["store", "tai"], sort=False)["model"].last().to_dict()
    )
    last_change_by_tai = {
        (k[0], int(k[1])): v for k, v in last_change.to_dict().items()
    }

    eligible = df_sorted.loc[df_sorted["tai_eligible"]].copy()
    eligible["w_upper"] = eligible["weight"] * eligible["is_upper"].astype(float)
    eligible["w_strong"] = eligible["weight"] * eligible["is_strong"].astype(float)

    tai_weighted = (
        eligible.groupby(["store", "tai"], sort=False)
        .agg(
            sample=("label", "size"),
            weight_sum=("weight", "sum"),
            upper_weight=("w_upper", "sum"),
            strong_weight=("w_strong", "sum"),
        )
        .reset_index()
    )
    weight_nonzero = tai_weighted["weight_sum"].replace(0, pd.NA)
    tai_weighted["tai_upper_rate"] = (tai_weighted["upper_weight"] / weight_nonzero).fillna(0.0)
    tai_weighted["tai_strong_rate"] = (tai_weighted["strong_weight"] / weight_nonzero).fillna(0.0)

    overall_upper = (
        eligible.groupby(["store", "tai"], sort=False)["is_upper"]
        .mean()
        .rename("overall_upper")
    )
    recent_cutoff = (now_jst - timedelta(days=90)).replace(tzinfo=None)
    recent_upper = (
        eligible.loc[eligible["date"] >= recent_cutoff]
        .groupby(["store", "tai"], sort=False)["is_upper"]
        .mean()
        .rename("recent_upper")
    )
    tai_weighted = tai_weighted.join(overall_upper, on=["store", "tai"])
    tai_weighted = tai_weighted.join(recent_upper, on=["store", "tai"])
    tai_weighted["recent_upper"] = tai_weighted["recent_upper"].fillna(tai_weighted["overall_upper"])

    today_rows = df.loc[(df["weekday"] == today_weekday) & (df["is_special"] == today_special)]
    today_label_mode = (
        today_rows.groupby("store")["label"].agg(lambda s: s.value_counts().idxmax()).to_dict()
    )

    model_today = store_model_day_stats.loc[
        (store_model_day_stats["weekday"] == today_weekday)
        & (store_model_day_stats["is_special"] == today_special)
    ].copy()
    model_rankings = {}
    for store, rows in model_today.groupby("store", sort=False):
        sorted_rows = rows.sort_values("upper_rate", ascending=False).head(5)
        ranking = []
        for r in sorted_rows.itertuples(index=False):
            ranking.append(
                {
                    "model": r.model,
                    "score": round(float(r.upper_rate), 6),
                    "reason": f"上候補以上率{float(r.upper_rate):.0%}({int(r.sample)}件)",
                    "sample": int(r.sample),
                }
            )
        model_rankings[store] = ranking

    tail_rankings = {}
    for store, rows in store_tail_stats.groupby("store", sort=False):
        sorted_rows = rows.sort_values("upper_rate", ascending=False)
        ranking = []
        for r in sorted_rows.itertuples(index=False):
            ranking.append(
                {
                    "tail": int(r.tail),
                    "score": round(float(r.upper_rate), 6),
                    "sample": int(r.sample),
                }
            )
        tail_rankings[store] = ranking

    candidate_by_store = {}
    for store, rows in tai_weighted.groupby("store", sort=False):
        store_day_score, _ = store_day_lookup.get((store, today_weekday, today_special), (0.0, 0))
        candidates = []
        for r in rows.itertuples(index=False):
            tai_key = (store, int(r.tai))
            model = recent_model_by_tai.get(tai_key, "")
            model_score, _ = model_day_lookup.get((store, model, today_weekday, today_special), (0.0, 0))
            tai_score = float(r.tai_upper_rate)
            total_score = 0.35 * store_day_score + 0.40 * model_score + 0.25 * tai_score

            overall = float(r.overall_upper) if pd.notna(r.overall_upper) else 0.0
            recent = float(r.recent_upper) if pd.notna(r.recent_upper) else overall
            if recent > overall + 0.05:
                trend = "上昇"
            elif recent < overall - 0.05:
                trend = "下降"
            else:
                trend = "横ばい"

            reasons = [
                f"上候補以上率{tai_score:.0%}",
                f"サンプル{int(r.sample)}件",
                f"推移{trend}",
            ][:3]

            warnings = []
            if int(r.sample) < 10:
                warnings.append("サンプル数が10件未満")
            lc = last_change_by_tai.get(tai_key)
            if lc is not None:
                days_since_change = (today_date - lc.date()).days
                if days_since_change <= 90:
                    warnings.append(f"台番号変動あり（直近{days_since_change}日）")

            candidates.append(
                {
                    "tai": int(r.tai),
                    "model": model,
                    "score": round(total_score, 6),
                    "reasons": reasons,
                    "warnings": warnings[:2],
                }
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        candidate_by_store[store] = candidates

    stores_payload = {}
    store_names = sorted(df["store"].dropna().astype(str).unique().tolist())
    for store in store_names:
        today_score, today_sample = store_day_lookup.get((store, today_weekday, today_special), (0.0, 0))
        if today_score >= 0.4:
            today_label = "強い"
        elif today_score < 0.2:
            today_label = "弱い"
        else:
            today_label = "普通"

        mode_label = today_label_mode.get(store, "データ不足")
        today_reason = [
            f"同条件上候補率{today_score:.0%}",
            f"サンプル{today_sample}件",
            f"最多ラベル{mode_label}",
        ][:3]

        stores_payload[store] = {
            "today_score": round(float(today_score), 6),
            "today_label": today_label,
            "today_reason": today_reason,
            "model_ranking": model_rankings.get(store, []),
            "tail_ranking": tail_rankings.get(store, []),
            "candidates": candidate_by_store.get(store, []),
        }

    return {
        "generated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "data_date": now_jst.strftime("%Y-%m-%d"),
        "normalized_models": dict(sorted(normalized_models.items())),
        "unsupported_models": sorted(unsupported_models),
        "stores": stores_payload,
    }


def main():
    data, normalized_models, unsupported_models = read_labeled_rows()
    if pd is None:
        payload = build_payload_fallback(data, normalized_models, unsupported_models)
    else:
        payload = build_payload(data, normalized_models, unsupported_models)
    data_date = str(payload.get("data_date") or datetime.now(JST).strftime("%Y-%m-%d"))
    archive_suffix = data_date.replace("-", "")
    out_archive_json = os.path.join(REPO_DIR, f"morning_data_{archive_suffix}.json")

    for path in (OUT_JSON, out_archive_json):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"generated: {OUT_JSON}")
    print(f"generated: {out_archive_json}")
    print(f"stores: {len(payload.get('stores', {}))}")


if __name__ == "__main__":
    main()
