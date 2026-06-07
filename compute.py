import json, csv, math, os, re
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict, deque

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV  = os.path.join(REPO_DIR, "raw_data.csv")
STORE_MODEL_SUMMARY_CSV = os.path.join(REPO_DIR, "store_model_summary.csv")
HALL_LAYOUTS_JSON = os.path.join(REPO_DIR, "hall_layouts.json")
STORE_FRESHNESS_JSON = os.path.join(REPO_DIR, "store_freshness.json")
STORE_LIST_JSON = os.path.join(REPO_DIR, "store_list.json")
JST = timezone(timedelta(hours=9))

WEEKDAY_COEFF = {0:1.0, 1:1.0, 2:1.0, 3:1.0, 4:1.1, 5:1.2, 6:1.2}
MONTHLY_TIMING_COEFF = {
    "early": 1.05,
    "mid": 1.0,
    "late": 0.95,
    "payday": 1.1,
}
# 店舗別係数の骨格。値が入れば推薦スコアに乗算される。
STORE_COEFFICIENTS = {}

STORE_SPECIAL = {
    "鶴見UNO":                  [1, 11, 21, 31],
    "中山UNO":                  [1, 11, 21, 31],
    "マルハン都築":              [1, 7, 10, 11, 17, 21, 22, 25, 27, 31],
    "エスパス日拓新宿歌舞伎町":  [1, 6, 7, 11, 16, 17, 22, 23, 24, 26, 27],
}

STORE_NAME_ALIASES = {
    "マルハン都筑": "マルハン都築",
    "エスパス新宿": "エスパス日拓新宿歌舞伎町",
}

MODEL_NAME_MAP = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラー",
    "ジャグラーガールズ":     "ジャグラーガールズSS",
    "スマスロ ハナビ":       "スマスロハナビ",
}

SMART_SLOT_MODEL_PATTERNS = [
    (("北斗", "転生"), "スマスロ北斗の拳 転生の章2"),
    (("北斗の拳",), "スマスロ北斗の拳"),
    (("北斗",), "スマスロ北斗の拳"),
    (("東京喰種",), "L 東京喰種"),
    (("グール",), "L 東京喰種"),
    (("喰種",), "L 東京喰種"),
    (("モンキーターン",), "L モンキーターンV"),
    (("ヴァルヴレイヴ", "2"), "L 革命機ヴァルヴレイヴ2"),
    (("ヴァルヴレイヴ", "２"), "L 革命機ヴァルヴレイヴ2"),
    (("ヴァルヴレイヴ", "Ⅱ"), "L 革命機ヴァルヴレイヴ2"),
    (("VVV", "2"), "L 革命機ヴァルヴレイヴ2"),
    (("VVV", "２"), "L 革命機ヴァルヴレイヴ2"),
    (("ＶＶＶ", "2"), "L 革命機ヴァルヴレイヴ2"),
    (("ＶＶＶ", "２"), "L 革命機ヴァルヴレイヴ2"),
    (("ヴヴヴ", "2"), "L 革命機ヴァルヴレイヴ2"),
    (("ヴヴヴ", "２"), "L 革命機ヴァルヴレイヴ2"),
]

SMART_SLOT_MODELS = {
    "スマスロ北斗の拳 転生の章2",
    "スマスロ北斗の拳",
    "L 東京喰種",
    "L モンキーターンV",
    "L 革命機ヴァルヴレイヴ2",
}

MODEL_SETTINGS = {
    "ネオアイムジャグラー":      {"syn":{1:168,2:161,3:148,4:142,5:128,6:128},"bb":{1:273,2:269,3:269,4:259,5:259,6:255},"rb":{1:439,2:399,3:331,4:315,5:255,6:255}},
    "ウルトラミラクルジャグラー": {"syn":{1:164,2:158,3:147,4:138,5:130,6:121},"bb":{1:267,2:261,3:256,4:242,5:233,6:216},"rb":{1:425,2:402,3:350,4:322,5:297,6:277}},
    "ミスタージャグラー":        {"syn":{1:156,2:152,3:145,4:134,5:124,6:118},"bb":{1:268,2:267,3:260,4:249,5:240,6:237},"rb":{1:374,2:354,3:331,4:291,5:257,6:237}},
    "ジャグラーガールズSS":      {"syn":{1:159,2:152,3:142,4:132,5:128,6:119},"bb":{1:273,2:270,3:260,4:250,5:243,6:226},"rb":{1:381,2:350,3:316,4:281,5:270,6:252}},
    "ゴーゴージャグラー3":       {"syn":{1:149,2:145,3:139,4:130,5:123,6:117},"bb":{1:259,2:258,3:257,4:254,5:247,6:234},"rb":{1:354,2:332,3:306,4:268,5:247,6:234}},
    "ハッピージャグラーVIII":    {"syn":{1:161,2:154,3:146,4:137,5:127,6:120},"bb":{1:273,2:270,3:263,4:254,5:239,6:226},"rb":{1:397,2:362,3:332,4:300,5:273,6:256}},
    "マイジャグラーV":           {"syn":{1:163,2:159,3:148,4:135,5:126,6:114},"bb":{1:273,2:270,3:266,4:254,5:240,6:229},"rb":{1:409,2:385,3:336,4:290,5:268,6:229}},
    "ファンキージャグラー2":     {"syn":{1:165,2:158,3:150,4:140,5:133,6:119},"bb":{1:266,2:259,3:256,4:249,5:240,6:219},"rb":{1:439,2:407,3:366,4:322,5:299,6:262}},
    "新ハナビ":                  {"syn":{1:131,2:127,3:122,4:118,5:113,6:109},"bb":{1:240,2:234,3:228,4:221,5:214,6:205},"rb":{1:397,2:378,3:357,4:336,5:314,6:290}},
    "スマスロハナビ":            {"syn":{1:176,2:161,3:155,4:149,5:143,6:137},"bb":{1:282,2:270,3:261,4:252,5:243,6:234},"rb":{1:470,2:434,3:398,4:364,5:336,6:303}},
    "クランキーセレブレーション": {"syn":{1:160,2:154,3:146,4:137,5:129,6:120},"bb":{1:268,2:260,3:252,4:240,5:229,6:216},"rb":{1:400,2:375,3:349,4:320,5:293,6:265}},
}

MODEL_HIGH_SETTING_MIN = {
    "新ハナビ": 2,
    "スマスロハナビ": 2,
}

MODEL_GOOD_SYN_THRESHOLD = {
    "新ハナビ": 148,
    "スマスロハナビ": 161,
}

STORE_EXCHANGE_RATE = {
    "鶴見UNO": 4.9,
    "マルハン都築": 5.0,
    "中山UNO": 5.0,
    "エスパス日拓新宿歌舞伎町": 5.17,
}
DEFAULT_EXCHANGE_RATE = 5.0
EMA_HALF_LIFE_DAYS = 180.0
DIFF_AUXILIARY_WEIGHT = 1.0 / 3.0
DIFF_AUXILIARY_MAX_DELTA = 9.0
DIFF_AUXILIARY_SCALE_PER_1000G = 700.0
PRIOR_DETAIL_MIN_SAMPLES = 10
PRIOR_MODEL_MIN_SAMPLES = 5
HOLDOVER_BONUS_MAX = 8.0
DEFAULT_SPECIAL_DAYS = [1, 11, 21, 31]
G_WEIGHT_FULL_THRESHOLD = 3000
G_WEIGHT_HALF_THRESHOLD = 1500
G_WEIGHT_FULL = 1.0
G_WEIGHT_HALF = 0.5
INSTALL_SEGMENT_GAP_DAYS = 21

MODEL_HOLDOVER_SYN_THRESHOLD = {
    "アイムジャグラー": 135,
    "マイジャグラー": 140,
    "ファンキージャグラー": 138,
    "ゴーゴージャグラー": 136,
    "新ハナビ": 148,
    "スマスロハナビ": 161,
}

ANALYTICS_CACHE = {}
DIFF_QUALITY_BY_STORE = {}

def r1(v): return round(v*10)/10
def avg(arr): return sum(arr)/len(arr) if arr else 0
def wavg(vals, weights):
    if not vals: return 0
    tw = sum(weights)
    return sum(v*w for v,w in zip(vals,weights))/tw if tw else 0
def row_w(r): return r.get("weight", 1)
def weighted_total(rows): return sum(row_w(r) for r in rows)
def has_trustworthy_diff(row):
    return bool(row.get("hasDiff")) and bool(row.get("diffReliable", True))
def diff_valid_rows(rows):
    return [r for r in rows if has_trustworthy_diff(r)]
def metric_rows(rows, key):
    return diff_valid_rows(rows) if key == "diff" else rows
def weighted_sum(rows, key):
    target_rows = metric_rows(rows, key)
    return sum(r[key] * row_w(r) for r in target_rows)
def weighted_total_if(rows, pred): return sum(row_w(r) for r in rows if pred(r))
def weighted_total_if_factor(rows, pred, factor_fn):
    return sum(row_w(r) * factor_fn(r) for r in rows if pred(r))
def weighted_avg_rows(rows, key):
    target_rows = metric_rows(rows, key)
    tw = weighted_total(target_rows)
    return weighted_sum(target_rows, key) / tw if tw else 0
def weighted_rate(rows, pred):
    tw = weighted_total(rows)
    if not tw: return 0
    return sum(row_w(r) for r in rows if pred(r)) / tw
def weighted_diff_rate(rows, pred):
    return weighted_rate(diff_valid_rows(rows), pred)
def weighted_mean_std(rows, key):
    target_rows = metric_rows(rows, key)
    tw = weighted_total(target_rows)
    if tw <= 0:
        return 0, 0
    mean = weighted_sum(target_rows, key) / tw
    var_num = 0.0
    for r in target_rows:
        d = r[key] - mean
        var_num += row_w(r) * d * d
    variance = var_num / tw if tw > 0 else 0.0
    return mean, math.sqrt(max(0.0, variance))

def g_confidence_weight(g):
    g_val = parse_num(g)
    if g_val >= G_WEIGHT_FULL_THRESHOLD:
        return G_WEIGHT_FULL
    if g_val >= G_WEIGHT_HALF_THRESHOLD:
        return G_WEIGHT_HALF
    return 0.0

def weighted_sum_with_factor(rows, key, factor_fn):
    return sum(r[key] * row_w(r) * factor_fn(r) for r in rows)

def weighted_total_with_factor(rows, factor_fn):
    return sum(row_w(r) * factor_fn(r) for r in rows)

def parse_num(s):
    if not s: return 0
    try: return float(str(s).replace(",","").replace("+","").strip())
    except: return 0

def parse_summary_number(value):
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

def parse_summary_win_rate(value):
    text = str(value or "")
    pct = parse_summary_number(text)
    match = re.search(r"\((\d+)\s*/\s*(\d+)\)", text)
    if not match:
        return pct, None, None
    wins = int(match.group(1))
    total = int(match.group(2))
    return pct, wins, total

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def normalize_store_name(store_name):
    name = str(store_name or "").strip()
    return STORE_NAME_ALIASES.get(name, name)

def calc_ema_weight(dt, today):
    days_ago = max(0, (today - dt.date()).days)
    return math.exp(-math.log(2.0) * (days_ago / EMA_HALF_LIFE_DAYS))

def get_store_exchange_rate(store):
    key = normalize_store_name(store)
    rate = STORE_EXCHANGE_RATE.get(key)
    if isinstance(rate, (int, float)) and rate > 0:
        return float(rate)
    return DEFAULT_EXCHANGE_RATE

def normalize_model_name(model_name):
    name = str(model_name or "").replace("　", " ").strip()
    mapped = MODEL_NAME_MAP.get(name, name)
    if mapped.replace(" ", "") == "スマスロハナビ":
        return "スマスロハナビ"
    compact = mapped.replace(" ", "")
    for tokens, canonical in SMART_SLOT_MODEL_PATTERNS:
        if all(token in compact for token in tokens):
            return canonical
    return mapped

def supports_setting_analysis(model):
    return model in MODEL_SETTINGS

def supports_diff_analysis(model):
    return model in MODEL_SETTINGS or model in SMART_SLOT_MODELS

def get_model_analysis_mode(model):
    return "setting" if supports_setting_analysis(model) else "diff"

def is_good_result_model(model, g, bb, rb):
    if g <= 0 or (bb + rb) <= 0:
        return False
    syn_threshold = MODEL_GOOD_SYN_THRESHOLD.get(model)
    if syn_threshold is not None:
        return (g / (bb + rb)) <= syn_threshold
    ms = MODEL_SETTINGS.get(model)
    if not ms or rb <= 0 or bb <= 0:
        return False
    return (g / rb) <= ms["rb"][4] and (g / bb) > ms["bb"][4]

def get_holdover_syn_threshold(model):
    name = str(model or "")
    for token, threshold in MODEL_HOLDOVER_SYN_THRESHOLD.items():
        if token in name:
            return threshold
    return None

def is_high_setting_syn_model(model, g, bb, rb):
    if g <= 0 or (bb + rb) <= 0:
        return False
    threshold = get_holdover_syn_threshold(model)
    if threshold is None:
        return False
    return (g / (bb + rb)) <= threshold

def extract_special_days(store_obj):
    if not isinstance(store_obj, dict):
        return None
    candidates = [
        "special_days", "specialDays", "special", "special_day",
        "specialDay", "tokutei_days", "tokuteiDays"
    ]
    for key in candidates:
        raw = store_obj.get(key)
        if not isinstance(raw, list):
            continue
        values = []
        for v in raw:
            try:
                i = int(v)
            except Exception:
                continue
            if 1 <= i <= 31:
                values.append(i)
        values = sorted(set(values))
        if values:
            return values
    return None

def load_store_configs():
    specials = {}
    exchange_rates = {}
    names = []
    seen = set()
    if os.path.exists(STORE_LIST_JSON):
        try:
            with open(STORE_LIST_JSON, encoding="utf-8-sig") as f:
                payload = json.load(f)
        except Exception:
            payload = {}
        stores = payload.get("stores", []) if isinstance(payload, dict) else []
        for store_obj in stores:
            if not isinstance(store_obj, dict):
                continue
            name = normalize_store_name(store_obj.get("name"))
            if not name:
                continue
            if name not in seen:
                names.append(name)
                seen.add(name)
            days = extract_special_days(store_obj)
            if days:
                specials[name] = days
            rate = store_obj.get("exchange_rate")
            if isinstance(rate, (int, float)) and rate > 0:
                exchange_rates[name] = float(rate)
    for fallback_name, fallback_days in STORE_SPECIAL.items():
        key = normalize_store_name(fallback_name)
        if key not in specials:
            specials[key] = sorted(set(int(v) for v in fallback_days if 1 <= int(v) <= 31))
    for store_name in names:
        if store_name not in specials:
            specials[store_name] = DEFAULT_SPECIAL_DAYS[:]
    return {
        "names": names,
        "specialByStore": specials,
        "exchangeRateByStore": exchange_rates,
    }

def load_hall_layouts():
    if not os.path.exists(HALL_LAYOUTS_JSON):
        return {}
    try:
        with open(HALL_LAYOUTS_JSON, encoding="utf-8-sig") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"⚠️ ホール図配置の読込に失敗: {e}")
        return {}
    if isinstance(payload, dict) and isinstance(payload.get("stores"), dict):
        return payload["stores"]
    return payload if isinstance(payload, dict) else {}

def normalize_hall_layout_cells(layout):
    if not isinstance(layout, dict):
        return []
    if isinstance(layout.get("cells"), list):
        cells = []
        for value in layout["cells"]:
            if isinstance(value, dict):
                cells.append(None)
                continue
            tai = int(parse_num(value))
            cells.append(tai if tai > 0 else None)
        return cells
    placements = layout.get("placements")
    if not isinstance(placements, dict):
        return []
    indices = []
    for key in placements.keys():
        try:
            indices.append(int(key))
        except (TypeError, ValueError):
            pass
    if not indices:
        return []
    cells = [None] * (max(indices) + 1)
    for key, value in placements.items():
        try:
            idx = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            continue
        tai = int(parse_num(value))
        cells[idx] = tai if tai > 0 else None
    return cells

def build_hall_layout_feature_map(layouts):
    result = {}
    meta = {}
    for raw_store, layout in (layouts or {}).items():
        store = normalize_store_name(raw_store)
        if not store or not isinstance(layout, dict):
            continue
        cells = normalize_hall_layout_cells(layout)
        cols = int(parse_num(layout.get("cols") or layout.get("columns") or 0))
        if cols <= 0 or not cells:
            continue
        occupied = {idx: int(tai) for idx, tai in enumerate(cells) if isinstance(tai, int) and tai > 0}
        if not occupied:
            continue
        rows = math.ceil(len(cells) / cols)
        occupied_set = set(occupied)
        adjacent_pairs = 0
        neighbors_by_idx = {}
        for idx in occupied:
            row = idx // cols
            col = idx % cols
            raw_neighbors = [
                idx - 1 if col > 0 else None,
                idx + 1 if col < cols - 1 else None,
                idx - cols if row > 0 else None,
                idx + cols if row < rows - 1 else None,
            ]
            neighbors = [n for n in raw_neighbors if n in occupied_set]
            neighbors_by_idx[idx] = neighbors
            if idx + 1 in occupied_set and idx // cols == (idx + 1) // cols:
                adjacent_pairs += 1
            if idx + cols in occupied_set:
                adjacent_pairs += 1
        occupied_count = len(occupied)
        analysis_ready = adjacent_pairs >= max(4, occupied_count * 0.20)
        component_no_by_idx = {}
        component_meta = {}
        visited = set()
        components = []
        for start in sorted(occupied):
            if start in visited:
                continue
            stack = [start]
            visited.add(start)
            component = []
            while stack:
                idx = stack.pop()
                component.append(idx)
                for nxt in neighbors_by_idx.get(idx, []):
                    if nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            components.append(sorted(component))
        components.sort(key=lambda items: (min(items), len(items)))
        for component_no, component in enumerate(components, start=1):
            horizontal_links = 0
            vertical_links = 0
            component_set = set(component)
            for idx in component:
                if idx + 1 in component_set and idx // cols == (idx + 1) // cols:
                    horizontal_links += 1
                if idx + cols in component_set:
                    vertical_links += 1
            if horizontal_links > vertical_links:
                shape = "横島"
            elif vertical_links > horizontal_links:
                shape = "縦島"
            else:
                shape = "複合島" if len(component) >= 3 else "小島"
            for idx in component:
                component_no_by_idx[idx] = component_no
                component_meta[idx] = {
                    "size": len(component),
                    "shape": shape,
                }
        store_features = {}
        for idx, tai in occupied.items():
            row = idx // cols
            col = idx % cols
            features = []
            if analysis_ready:
                neighbor_count = len(neighbors_by_idx.get(idx, []))
                if neighbor_count <= 1:
                    features.append(("hall_edge", "島端", "ホール図:島端"))
                    features.append(("hall_corner", "角/端", "ホール図:角/端"))
                elif neighbor_count >= 3:
                    features.append(("hall_edge", "島中", "ホール図:島中"))
                component_no = component_no_by_idx.get(idx)
                component = component_meta.get(idx) or {}
                if component_no and component.get("size", 0) >= 3:
                    features.append(("hall_island", f"島{component_no}", f"ホール図:島{component_no}"))
                    features.append(("hall_island_shape", component.get("shape", "島"), f"ホール図:{component.get('shape', '島')}"))
                if col <= max(1, cols * 0.25):
                    features.append(("hall_col_band", "左側", "ホール図:左側"))
                elif col >= cols * 0.75:
                    features.append(("hall_col_band", "右側", "ホール図:右側"))
                else:
                    features.append(("hall_col_band", "中央", "ホール図:中央"))
                if row <= max(1, rows * 0.25):
                    features.append(("hall_row_band", "上段", "ホール図:上段"))
                elif row >= rows * 0.75:
                    features.append(("hall_row_band", "下段", "ホール図:下段"))
                else:
                    features.append(("hall_row_band", "中段", "ホール図:中段"))
            store_features[str(tai)] = features
        result[store] = store_features
        meta[store] = {
            "cols": cols,
            "cells": len(cells),
            "occupied": occupied_count,
            "adjacentPairs": adjacent_pairs,
            "islands": len(components),
            "analysisReady": analysis_ready,
        }
    return result, meta

def apply_hall_layout_features(rows, feature_map):
    if not feature_map:
        return
    for row in rows:
        store_features = feature_map.get(row.get("store")) or {}
        features = store_features.get(str(row.get("tai"))) or store_features.get(str(row.get("taiNum")))
        if features:
            row["hallFeatures"] = features

def build_analytics_cache(rows):
    prior_l4 = defaultdict(lambda: {"plus": 0, "total": 0})
    prior_l3 = defaultdict(lambda: {"plus": 0, "total": 0})
    prior_l2 = defaultdict(lambda: {"plus": 0, "total": 0})
    holdover = defaultdict(lambda: {"num": 0, "den": 0})
    prev_by_tai = {}
    for r in rows:
        store = r["store"]
        model = r["model"]
        weekday = r["weekday"]
        is_special = bool(r["isSpecialDay"])
        is_plus = r["diff"] > 0
        k4 = (store, model, weekday, is_special)
        k3 = (store, model, is_special)
        k2 = (store, is_special)
        prior_l4[k4]["total"] += 1
        prior_l3[k3]["total"] += 1
        prior_l2[k2]["total"] += 1
        if is_plus:
            prior_l4[k4]["plus"] += 1
            prior_l3[k3]["plus"] += 1
            prior_l2[k2]["plus"] += 1

        tk = r.get("installSegment") or (store, r["tai"], model)
        prev = prev_by_tai.get(tk)
        if prev and (r["date"] - prev["date"]).days == 1 and prev["isHighSettingSyn"]:
            holdover[store]["den"] += 1
            if r["isHighSettingSyn"]:
                holdover[store]["num"] += 1
        prev_by_tai[tk] = r

    holdover_rate = {}
    for store, stat in holdover.items():
        den = stat["den"]
        holdover_rate[store] = {
            "numerator": stat["num"],
            "denominator": den,
            "rate": (stat["num"] / den) if den > 0 else 0.0,
        }
    return {
        "prior_l4": dict(prior_l4),
        "prior_l3": dict(prior_l3),
        "prior_l2": dict(prior_l2),
        "holdover_rate": holdover_rate,
    }

def get_daytype_token(is_special):
    return "special" if bool(is_special) else "normal"

def get_dynamic_prior_high_prob(store, model, weekday, is_special, tai=None):
    cache = ANALYTICS_CACHE or {}
    l4 = cache.get("prior_l4", {})
    l3 = cache.get("prior_l3", {})
    l2 = cache.get("prior_l2", {})
    k4 = (store, model, weekday, bool(is_special))
    stat = l4.get(k4)
    raw_prob = 0.5
    raw_source = "default"
    raw_samples = 0
    if stat and stat["total"] >= PRIOR_DETAIL_MIN_SAMPLES:
        raw_prob = clamp(stat["plus"] / stat["total"], 0.01, 0.99)
        raw_source = "store_model_weekday_daytype"
        raw_samples = int(stat["total"])
    else:
        k3 = (store, model, bool(is_special))
        stat = l3.get(k3)
        if stat and stat["total"] >= PRIOR_MODEL_MIN_SAMPLES:
            raw_prob = clamp(stat["plus"] / stat["total"], 0.01, 0.99)
            raw_source = "store_model_daytype"
            raw_samples = int(stat["total"])
        else:
            k2 = (store, bool(is_special))
            stat = l2.get(k2)
            if stat and stat["total"] > 0:
                raw_prob = clamp(stat["plus"] / stat["total"], 0.01, 0.99)
                raw_source = "store_daytype"
                raw_samples = int(stat["total"])

    return raw_prob, raw_source, raw_samples

def get_holdover_rate(store):
    data = (ANALYTICS_CACHE or {}).get("holdover_rate", {}).get(store, {})
    return float(data.get("rate", 0.0))

def load_store_freshness():
    if not os.path.exists(STORE_FRESHNESS_JSON):
        return {}
    try:
        with open(STORE_FRESHNESS_JSON, encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def load_store_list_names():
    return load_store_configs().get("names", [])

def build_store_display_order(stores_with_data):
    if not stores_with_data:
        return []
    data_set = set(stores_with_data)
    ordered = []
    seen = set()
    for name in load_store_list_names():
        if name in data_set and name not in seen:
            ordered.append(name)
            seen.add(name)
    for name in sorted(data_set):
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered

def build_setting_priors(model, high_prob=0.5):
    high_prob = clamp(float(high_prob), 0.01, 0.99)
    high_min = MODEL_HIGH_SETTING_MIN.get(model, 4)
    high_settings = [s for s in range(high_min, 7)]
    low_settings = [s for s in range(1, 7) if s < high_min]
    if not high_settings:
        return {s: 1/6 for s in [1,2,3,4,5,6]}
    priors = {}
    if low_settings:
        low_each = (1 - high_prob) / len(low_settings)
        for s in low_settings:
            priors[s] = low_each
    high_each = high_prob / len(high_settings)
    for s in high_settings:
        priors[s] = high_each
    for s in [1,2,3,4,5,6]:
        if s not in priors:
            priors[s] = 1e-9
    total = sum(priors.values())
    if total <= 0:
        return {s: 1/6 for s in [1,2,3,4,5,6]}
    return {s: max(1e-9, priors[s] / total) for s in [1,2,3,4,5,6]}

def get_monthly_timing_coeff(day: int) -> float:
    if day in (24, 25, 26):
        return MONTHLY_TIMING_COEFF["payday"]
    if 1 <= day <= 10:
        return MONTHLY_TIMING_COEFF["early"]
    if 11 <= day <= 20:
        return MONTHLY_TIMING_COEFF["mid"]
    return MONTHLY_TIMING_COEFF["late"]

def get_store_coeff(store: str, weekday: int, day: int) -> float:
    coeff_cfg = STORE_COEFFICIENTS.get(store, {})
    if not isinstance(coeff_cfg, dict):
        return 1.0
    coeff = 1.0
    base = coeff_cfg.get("base")
    if isinstance(base, (int, float)):
        coeff *= float(base)
    weekday_map = coeff_cfg.get("weekday")
    if isinstance(weekday_map, dict):
        wv = weekday_map.get(weekday)
        if isinstance(wv, (int, float)):
            coeff *= float(wv)
    monthly_map = coeff_cfg.get("monthly_timing")
    if isinstance(monthly_map, dict):
        if day in (24, 25, 26):
            bucket = "payday"
        elif 1 <= day <= 10:
            bucket = "early"
        elif 11 <= day <= 20:
            bucket = "mid"
        else:
            bucket = "late"
        mv = monthly_map.get(bucket)
        if isinstance(mv, (int, float)):
            coeff *= float(mv)
    return coeff

def jst_today() -> date:
    return datetime.now(JST).date()


def parse_ymd_date(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def load_raw(special_by_store):
    seen = set()
    rows = []
    today = jst_today()
    if not os.path.exists(RAW_CSV):
        print(f"  ❌ CSVが見つかりません: {RAW_CSV}")
        return rows
    with open(RAW_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            date_str = str(row.get("日付", "")).strip()
            store = normalize_store_name(row.get("店名", ""))
            tai = str(row.get("台番号", "")).strip()
            model_name = str(row.get("機種名", "")).strip()
            if not date_str or not store or not tai or not model_name:
                continue
            key = (date_str, store, tai, model_name)
            if key in seen: continue
            seen.add(key)
            model = normalize_model_name(model_name)
            if not supports_diff_analysis(model): continue
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except: continue
            g    = parse_num(row.get("G数"))
            diff = parse_num(row.get("差枚"))
            diff_raw = str(row.get("差枚", "")).strip()
            bb   = parse_num(row.get("BB"))
            rb   = parse_num(row.get("RB"))
            tai_num = int(tai) if tai.isdigit() else 0
            s = str(tai_num)
            day = dt.day
            is_high_set_rb = is_good_result_model(model, g, bb, rb)
            is_special_day = day in special_by_store.get(store, DEFAULT_SPECIAL_DAYS)
            rows.append({
                "dateStr": date_str, "date": dt,
                "store": store, "model": model,
                "tai": tai, "taiNum": tai_num,
                "g": g, "diff": diff, "bb": bb, "rb": rb,
                "weight": calc_ema_weight(dt, today),
                "day": day, "weekday": (dt.weekday() + 1) % 7,
                "suef": tai_num % 10,
                "isZoro": day >= 11 and len(str(day)) == 2 and str(day)[0] == str(day)[1],
                "isTaiZoro": len(s)>=2 and s[-1]==s[-2],
                "isRBLead": rb > bb,
                "isHighSetRBLead": is_high_set_rb,
                "isSpecialDay": is_special_day,
                "hasDiff": diff_raw != "",
                "isHighSettingSyn": is_high_setting_syn_model(model, g, bb, rb),
                "analysisMode": get_model_analysis_mode(model),
                "supportsSettingAnalysis": supports_setting_analysis(model),
            })
    rows.sort(key=lambda r: r["date"])
    global DIFF_QUALITY_BY_STORE
    DIFF_QUALITY_BY_STORE = annotate_diff_quality(rows)
    annotate_install_segments(rows)
    print(f"合計 {len(rows)} 行読み込み完了")
    return rows

def annotate_install_segments(rows):
    by_slot = defaultdict(list)
    for r in rows:
        by_slot[(r["store"], r["tai"])].append(r)
    for (store, tai), slot_rows in by_slot.items():
        slot_rows.sort(key=lambda r: (r["date"], r["model"]))
        segment_index = 0
        segment_started_at = None
        prev_model = None
        prev_date = None
        for r in slot_rows:
            date_value = r["date"].date()
            gap_days = (date_value - prev_date).days if prev_date else 0
            starts_new_segment = (
                prev_model is None
                or r["model"] != prev_model
                or gap_days > INSTALL_SEGMENT_GAP_DAYS
            )
            if starts_new_segment:
                segment_index += 1
                segment_started_at = date_value
            r["installSegmentIndex"] = segment_index
            r["installSegment"] = f"{store}|{tai}|{segment_index}"
            r["installSegmentStartedAt"] = segment_started_at.strftime("%Y-%m-%d") if segment_started_at else r["dateStr"]
            prev_model = r["model"]
            prev_date = date_value

def annotate_diff_quality(rows):
    by_store = defaultdict(lambda: {"rows": 0, "present": 0, "nonzero": 0})
    for r in rows:
        stat = by_store[r["store"]]
        stat["rows"] += 1
        if r.get("hasDiff"):
            stat["present"] += 1
            if r.get("diff") != 0:
                stat["nonzero"] += 1

    quality = {}
    for store, stat in by_store.items():
        present = stat["present"]
        nonzero = stat["nonzero"]
        present_rate = present / stat["rows"] if stat["rows"] else 0.0
        nonzero_rate = nonzero / present if present else 0.0
        reliable = present >= 100 and nonzero_rate >= 0.01
        quality[store] = {
            "rows": stat["rows"],
            "diffPresent": present,
            "diffPresentRate": r1(present_rate * 100),
            "nonzeroDiff": nonzero,
            "nonzeroDiffRate": r1(nonzero_rate * 100),
            "diffReliable": reliable,
            "message": "" if reliable else "差枚が未取得または0固定の可能性が高いため、差枚根拠から除外しています。",
        }

    for r in rows:
        meta = quality.get(r["store"], {})
        r["diffReliable"] = bool(meta.get("diffReliable", False))
        if not r["diffReliable"]:
            r["hasDiff"] = False
    return quality

def get_current_install_segment_ids(rows):
    latest_date_by_store = {}
    for r in rows:
        store = r["store"]
        current = latest_date_by_store.get(store)
        if current is None or r["date"].date() > current:
            latest_date_by_store[store] = r["date"].date()
    return set(
        r.get("installSegment")
        for r in rows
        if r.get("installSegment") and r["date"].date() == latest_date_by_store.get(r["store"])
    )

def calc_setting_posterior(model, total_g, total_bb, total_rb, prior_high_prob=0.5):
    ms = MODEL_SETTINGS.get(model)
    if not ms or total_g < 100:
        return None
    priors = build_setting_priors(model, prior_high_prob)
    log_probs = []
    for s in [1,2,3,4,5,6]:
        log_l = 0
        if total_bb > 0:
            exp_bb = total_g / ms["bb"][s]
            log_l += total_bb * math.log(exp_bb) - exp_bb
        if total_rb > 0:
            exp_rb = total_g / ms["rb"][s]
            log_l += total_rb * math.log(exp_rb) - exp_rb
        log_probs.append(math.log(max(1e-9, priors[s])) + log_l)
    max_log = max(log_probs)
    probs = [math.exp(p - max_log) for p in log_probs]
    total = sum(probs)
    if total <= 0:
        return None
    return [p/total for p in probs]

def calc_bayes_prob(model, total_g, total_bb, total_rb, prior_high_prob=0.5, total_diff=None, diff_weighted_count=0):
    probs = calc_setting_posterior(model, total_g, total_bb, total_rb, prior_high_prob=prior_high_prob)
    if not probs:
        return None
    high_min = MODEL_HIGH_SETTING_MIN.get(model, 4)
    start_idx = max(1, min(6, int(high_min))) - 1
    base_prob = sum(probs[start_idx:]) * 100.0
    if total_diff is None or diff_weighted_count <= 0 or total_g <= 0:
        return round(base_prob, 1)
    diff_per_1000g = (total_diff * 1000.0) / total_g
    reliability = clamp(diff_weighted_count / 10.0, 0.0, 1.0)
    diff_signal = math.tanh(diff_per_1000g / DIFF_AUXILIARY_SCALE_PER_1000G)
    diff_delta = diff_signal * DIFF_AUXILIARY_MAX_DELTA * reliability
    adjusted = clamp(base_prob + (diff_delta * DIFF_AUXILIARY_WEIGHT), 0.0, 100.0)
    return round(adjusted, 1)

def compute_day_stats(rows, special):
    by_day = defaultdict(lambda: {"rows":[], "plus":0, "total":0})
    for r in rows:
        if not has_trustworthy_diff(r):
            continue
        by_day[r["day"]]["rows"].append(r)
        by_day[r["day"]]["total"] += 1
        if r["diff"] > 0: by_day[r["day"]]["plus"] += 1
    result = []
    for d in range(1, 32):
        b = by_day[d]
        day_rows = b["rows"]
        if not day_rows: continue
        m, std = weighted_mean_std(day_rows, "diff")
        n_eff = weighted_total(day_rows)
        if n_eff > 1:
            se = std / (n_eff**0.5)
            ci_lower = round(m - 1.96*se, 1)
            ci_upper = round(m + 1.96*se, 1)
        else:
            ci_lower = ci_upper = round(m, 1)
        plus_rate = weighted_diff_rate(day_rows, lambda x: x["diff"] > 0) * 100
        result.append({
            "day": d, "avg": r1(m), "total": b["total"],
            "plus": b["plus"], "plusRate": r1(plus_rate),
            "special": d in special, "ciLower": ci_lower, "ciUpper": ci_upper,
            "reliable": n_eff >= 10,
        })
    return result

def classify_model_coverage_level(day_count, row_count):
    if day_count >= 120 and row_count >= 300:
        return {"label": "長期", "strength": "high"}
    if day_count >= 45 and row_count >= 100:
        return {"label": "中期", "strength": "medium"}
    if day_count >= 15 and row_count >= 30:
        return {"label": "短期", "strength": "low"}
    return {"label": "薄い", "strength": "thin"}

def build_model_coverage_meta(rows):
    if not rows:
        return {
            "firstDate": None,
            "lastDate": None,
            "dayCount": 0,
            "taiCount": 0,
            "rowCount": 0,
            "coverageLabel": "薄い",
            "coverageStrength": "thin",
        }
    dates = sorted({r["date"].date() for r in rows if r.get("date")})
    tais = {
        int(r["taiNum"])
        for r in rows
        if isinstance(r.get("taiNum"), int) and r.get("taiNum") > 0
    }
    day_count = len(dates)
    row_count = len(rows)
    level = classify_model_coverage_level(day_count, row_count)
    return {
        "firstDate": dates[0].strftime("%Y-%m-%d") if dates else None,
        "lastDate": dates[-1].strftime("%Y-%m-%d") if dates else None,
        "dayCount": day_count,
        "taiCount": len(tais),
        "rowCount": row_count,
        "coverageLabel": level["label"],
        "coverageStrength": level["strength"],
    }

def get_tai_band_label(tai_num):
    try:
        tai = int(tai_num)
    except (TypeError, ValueError):
        return "番号帯不明"
    return f"{(tai // 10) * 10}番台"

def classify_smart_treatment_sample(count, scope):
    if scope == "model":
        if count >= 40:
            return {"label": "厚い", "strength": "high", "usable": True}
        if count >= 20:
            return {"label": "中", "strength": "medium", "usable": True}
    else:
        if count >= 20:
            return {"label": "厚い", "strength": "high", "usable": True}
        if count >= 10:
            return {"label": "中", "strength": "medium", "usable": True}
    if count >= 5:
        return {"label": "参考", "strength": "low", "usable": False}
    return {"label": "薄い", "strength": "thin", "usable": False}

def summarize_diff_treatment(rows, label):
    valid = diff_valid_rows(rows)
    if not valid:
        return {"label": label, "count": 0, "avg": None, "plusRate": None}
    plus = sum(1 for r in valid if r["diff"] > 0)
    return {
        "label": label,
        "count": len(valid),
        "avg": r1(weighted_avg_rows(valid, "diff")),
        "plusRate": r1(plus / len(valid) * 100),
    }

def compute_tai_detail(rows, special, context_weekday, context_is_special):
    current_segment_ids = get_current_install_segment_ids(rows)
    current_rows = [
        r for r in rows
        if not current_segment_ids or r.get("installSegment") in current_segment_ids
    ]
    model_coverage_by_name = {}
    rows_by_model_for_coverage = defaultdict(list)
    for r in current_rows:
        rows_by_model_for_coverage[r["model"]].append(r)
    for model, model_rows in rows_by_model_for_coverage.items():
        model_coverage_by_name[model] = build_model_coverage_meta(model_rows)
    by_tai = defaultdict(lambda: {
        "tai":None,"taiNum":0,"model":None,"store":None,
        "installSegment":None,"installStartedAt":None,"installLastSeenAt":None,
        "hallFeatures": [],
        "all":[], "sp":[], "nm":[],
    })
    for r in current_rows:
        k = r.get("installSegment") or f"{r['taiNum']}_{r['model']}_{r['store']}"
        t = by_tai[k]
        t["tai"]=r["tai"]; t["taiNum"]=r["taiNum"]
        t["model"]=r["model"]; t["store"]=r["store"]
        t["installSegment"] = r.get("installSegment")
        t["installStartedAt"] = r.get("installSegmentStartedAt")
        t["installLastSeenAt"] = r["dateStr"]
        if r.get("hallFeatures"):
            t["hallFeatures"] = r.get("hallFeatures") or []
        t["all"].append(r)
        if r["day"] in special:
            t["sp"].append(r)
        else:
            t["nm"].append(r)
    by_tai_date = defaultdict(list)
    for r in current_rows:
        by_tai_date[r.get("installSegment") or f"{r['tai']}_{r['store']}"].append(r)
    if not current_rows:
        return []
    latest_date = max(r["date"] for r in current_rows)
    recent_cutoff = latest_date.date() - timedelta(days=30)
    smart_recent_rows = [
        r for r in current_rows
        if r.get("model") in SMART_SLOT_MODELS
        and has_trustworthy_diff(r)
        and r["date"].date() >= recent_cutoff
    ]
    smart_recent_by_model = defaultdict(list)
    smart_recent_by_band = defaultdict(list)
    for r in smart_recent_rows:
        smart_recent_by_model[r["model"]].append(r)
        smart_recent_by_band[get_tai_band_label(r.get("taiNum"))].append(r)
    smart_treatment_by_model = {
        model: {
            **summarize_diff_treatment(model_rows, model),
            **classify_smart_treatment_sample(len(diff_valid_rows(model_rows)), "model"),
        }
        for model, model_rows in smart_recent_by_model.items()
    }
    smart_treatment_by_band = {
        band: {
            **summarize_diff_treatment(band_rows, band),
            **classify_smart_treatment_sample(len(diff_valid_rows(band_rows)), "band"),
        }
        for band, band_rows in smart_recent_by_band.items()
    }
    prev_lookup = {}
    for k, tai_rows in by_tai_date.items():
        sorted_rows = sorted(tai_rows, key=lambda r: r["date"])
        for i in range(1, len(sorted_rows)):
            curr = sorted_rows[i]; prev = sorted_rows[i-1]
            if (curr["date"] - prev["date"]).days == 1:
                prev_lookup[f"{curr['dateStr']}_{curr['tai']}_{curr['store']}_{curr.get('installSegment') or ''}"] = prev
    result = []
    for t in by_tai.values():
        tg=weighted_sum(t["all"], "g"); tb=weighted_sum(t["all"], "bb"); tr=weighted_sum(t["all"], "rb")
        sg=weighted_sum(t["sp"], "g"); sb=weighted_sum(t["sp"], "bb"); sr=weighted_sum(t["sp"], "rb")
        ng=weighted_sum(t["nm"], "g"); nb=weighted_sum(t["nm"], "bb"); nr=weighted_sum(t["nm"], "rb")
        g_factor = lambda row: g_confidence_weight(row.get("g"))
        bayes_tg_all = weighted_sum_with_factor(t["all"], "g", g_factor)
        bayes_tb_all = weighted_sum_with_factor(t["all"], "bb", g_factor)
        bayes_tr_all = weighted_sum_with_factor(t["all"], "rb", g_factor)
        bayes_tg_sp = weighted_sum_with_factor(t["sp"], "g", g_factor)
        bayes_tb_sp = weighted_sum_with_factor(t["sp"], "bb", g_factor)
        bayes_tr_sp = weighted_sum_with_factor(t["sp"], "rb", g_factor)
        bayes_tg_nm = weighted_sum_with_factor(t["nm"], "g", g_factor)
        bayes_tb_nm = weighted_sum_with_factor(t["nm"], "bb", g_factor)
        bayes_tr_nm = weighted_sum_with_factor(t["nm"], "rb", g_factor)
        bayes_w_all = weighted_total_with_factor(t["all"], g_factor)
        bayes_w_sp = weighted_total_with_factor(t["sp"], g_factor)
        bayes_w_nm = weighted_total_with_factor(t["nm"], g_factor)
        td=weighted_sum(t["all"], "diff")
        sd=weighted_sum(t["sp"], "diff")
        nd=weighted_sum(t["nm"], "diff")
        diff_n_all = weighted_total_if_factor(t["all"], lambda x: x.get("hasDiff"), g_factor)
        diff_n_sp = weighted_total_if_factor(t["sp"], lambda x: x.get("hasDiff"), g_factor)
        diff_n_nm = weighted_total_if_factor(t["nm"], lambda x: x.get("hasDiff"), g_factor)
        n = len(t["all"])
        wn = weighted_total(t["all"])
        wplus_rate = weighted_diff_rate(t["all"], lambda x: x["diff"] > 0) * 100
        latest_key = f"{latest_date.strftime('%Y-%m-%d')}_{t['tai']}_{t['store']}_{t.get('installSegment') or ''}"
        prev = prev_lookup.get(latest_key)
        prev_row = {
            "dateStr":prev["dateStr"],"diff":prev["diff"],"bb":prev["bb"],"rb":prev["rb"],
            "g":prev["g"],"isRBLead":prev["isRBLead"],"isHighSetRBLead":prev["isHighSetRBLead"],
            "isHighSettingSyn": prev["isHighSettingSyn"],
        } if prev else None
        prior_all, prior_all_source, prior_all_n = get_dynamic_prior_high_prob(
            t["store"], t["model"], context_weekday, context_is_special, tai=t["tai"]
        )
        prior_sp, prior_sp_source, prior_sp_n = get_dynamic_prior_high_prob(
            t["store"], t["model"], context_weekday, True, tai=t["tai"]
        )
        prior_nm, prior_nm_source, prior_nm_n = get_dynamic_prior_high_prob(
            t["store"], t["model"], context_weekday, False, tai=t["tai"]
        )
        bayes_all = calc_bayes_prob(
            t["model"], bayes_tg_all, bayes_tb_all, bayes_tr_all, prior_high_prob=prior_all,
            total_diff=td, diff_weighted_count=diff_n_all
        )
        bayes_sp = calc_bayes_prob(
            t["model"], bayes_tg_sp, bayes_tb_sp, bayes_tr_sp, prior_high_prob=prior_sp,
            total_diff=sd, diff_weighted_count=diff_n_sp
        )
        bayes_nm = calc_bayes_prob(
            t["model"], bayes_tg_nm, bayes_tb_nm, bayes_tr_nm, prior_high_prob=prior_nm,
            total_diff=nd, diff_weighted_count=diff_n_nm
        )
        smart_treatment = None
        if t["model"] in SMART_SLOT_MODELS:
            band_label = get_tai_band_label(t["taiNum"])
            smart_treatment = {
                "model": smart_treatment_by_model.get(t["model"], {
                    **summarize_diff_treatment([], t["model"]),
                    **classify_smart_treatment_sample(0, "model"),
                }),
                "band": smart_treatment_by_band.get(band_label, {
                    **summarize_diff_treatment([], band_label),
                    **classify_smart_treatment_sample(0, "band"),
                }),
                "windowDays": 30,
                "mode": "diff_treatment",
            }
        result.append({
            "tai":t["tai"],"taiNum":t["taiNum"],"model":t["model"],"store":t["store"],
            "installSegment": t.get("installSegment"),
            "installStartedAt": t.get("installStartedAt"),
            "installLastSeenAt": t.get("installLastSeenAt"),
            "hallFeatures": t.get("hallFeatures") or [],
            "historyScope": "current_install_segment",
            "analysisMode": get_model_analysis_mode(t["model"]),
            "supportsSettingAnalysis": supports_setting_analysis(t["model"]),
            "modelCategory": "smart_slot" if t["model"] in SMART_SLOT_MODELS else "normal",
            "smartTreatment": smart_treatment,
            "modelCoverage": model_coverage_by_name.get(t["model"], build_model_coverage_meta([])),
            "avg":r1(weighted_avg_rows(t["all"], "diff")),"count":n,
            "weightedCount": r1(wn),
            "plus":len([v for v in t["all"] if has_trustworthy_diff(v) and v["diff"]>0]),
            "plusRate":r1(wplus_rate),
            "spAvg":r1(weighted_avg_rows(t["sp"], "diff")) if t["sp"] else None,
            "nmAvg":r1(weighted_avg_rows(t["nm"], "diff")) if t["nm"] else None,
            "spCount":len(t["sp"]),"nmCount":len(t["nm"]),
            "totalG":tg,"totalBB":tb,"totalRB":tr,
            "avgG":r1(tg/wn) if wn else 0,
            "rbRate":round(tg/tr) if tr>0 else None,
            "synRate":round(tg/(tb+tr)) if (tb+tr)>0 else None,
            "spRbRate":round(sg/sr) if sr>0 else None,
            "nmRbRate":round(ng/nr) if nr>0 else None,
            "bayesProbAll":bayes_all,
            "bayesProbSp":bayes_sp,
            "bayesProbNm":bayes_nm,
            "bayesMeta": {
                "all": {
                    "effectiveGames": r1(bayes_tg_all),
                    "confidenceWeight": r1(bayes_w_all),
                    "eligible": bayes_all is not None,
                },
                "special": {
                    "effectiveGames": r1(bayes_tg_sp),
                    "confidenceWeight": r1(bayes_w_sp),
                    "eligible": bayes_sp is not None,
                },
                "normal": {
                    "effectiveGames": r1(bayes_tg_nm),
                    "confidenceWeight": r1(bayes_w_nm),
                    "eligible": bayes_nm is not None,
                },
            },
            "confidence":"高" if n>=30 else "中" if n>=15 else "低",
            "prevRow": prev_row,
        })
    result.sort(key=lambda x: x["taiNum"])
    return result

def compute_model_stats(rows, special):
    if not rows:
        return []
    by_model = defaultdict(lambda: {
        "all":[],"sp":[],"nm":[],"this_month":[],"last_month":[],
        "by_day": defaultdict(list),
        "digit": defaultdict(list),
        "zoro": [],
    })
    latest = max(r["date"] for r in rows)
    this_m = date(latest.year, latest.month, 1)
    last_m = date(latest.year, latest.month-1, 1) if latest.month>1 else date(latest.year-1,12,1)
    last_m_end = date(latest.year, latest.month, 1) - timedelta(days=1)
    for r in rows:
        m = by_model[r["model"]]
        m["all"].append(r)
        if r["day"] in special: m["sp"].append(r)
        else: m["nm"].append(r)
        d = r["date"].date()
        if d >= this_m: m["this_month"].append(r)
        elif last_m <= d <= last_m_end: m["last_month"].append(r)
        # 日にち別・末尾digit別・ゾロ目
        m["by_day"][r["day"]].append(r)
        m["digit"][r["day"] % 10].append(r)
        if r["isZoro"]:
            m["zoro"].append(r)
    result = []
    for model, m in by_model.items():
        coverage_meta = build_model_coverage_meta(m["all"])
        tg=weighted_sum(m["all"], "g"); tb=weighted_sum(m["all"], "bb"); tr=weighted_sum(m["all"], "rb")
        total_in=tg*3; total_out=total_in+weighted_sum(m["all"], "diff")
        all_diff_rows = metric_rows(m["all"], "diff")
        plus_rate = len([row for row in all_diff_rows if row["diff"] > 0]) / len(all_diff_rows) * 100 if all_diff_rows else None
        # byDay: {1: avg, 2: avg, ...} (平均差枚のみ。app.jsのavg()に渡すため配列で格納)
        by_day_out = {day: [row["diff"] for row in day_rows]
                      for day, day_rows in m["by_day"].items()}
        # digitAvg: {0: avg, 1: avg, ...}
        digit_avg = {}
        for digit, digit_rows in m["digit"].items():
            digit_avg[str(digit)] = {
                "avg": r1(weighted_avg_rows(digit_rows, "diff")) if digit_rows else None,
                "count": len(digit_rows),
            }
        zoro_avg = r1(weighted_avg_rows(m["zoro"], "diff")) if m["zoro"] else None
        result.append({
            "model":model,"allAvg":r1(weighted_avg_rows(m["all"], "diff")),"count":len(m["all"]),
            **coverage_meta,
            "analysisMode": get_model_analysis_mode(model),
            "supportsSettingAnalysis": supports_setting_analysis(model),
            "modelCategory": "smart_slot" if model in SMART_SLOT_MODELS else "normal",
            "avgG": r1(weighted_avg_rows(m["all"], "g")),
            "winRate": r1(plus_rate) if plus_rate is not None else None,
            "spAvg":r1(weighted_avg_rows(m["sp"], "diff")) if m["sp"] else None,"spCount":len(m["sp"]),
            "nmAvg":r1(weighted_avg_rows(m["nm"], "diff")) if m["nm"] else None,"nmCount":len(m["nm"]),
            "mechRitu":r1(total_out/total_in*100) if total_in>0 else None,
            "rbRate":round(tg/tr) if tr>0 else None,
            "synRate":round(tg/(tb+tr)) if (tb+tr)>0 else None,
            "thisMonthAvg":r1(weighted_avg_rows(m["this_month"], "diff")) if m["this_month"] else None,
            "thisMonthCount":len(m["this_month"]),
            "lastMonthAvg":r1(weighted_avg_rows(m["last_month"], "diff")) if m["last_month"] else None,
            "lastMonthCount":len(m["last_month"]),
            "byDay": by_day_out,
            "digitAvg": digit_avg,
            "zoroAvg": zoro_avg,
            "zoroCount": len(m["zoro"]),
        })
    return result

def _summary_metric(entries):
    if not entries:
        return {"avgDiff": None, "avgG": None, "winRate": None, "avgInstallCount": None, "count": 0}
    diff_sum = 0.0
    install_sum = 0.0
    avg_diff_sum = 0.0
    avg_diff_count = 0
    avg_g_sum = 0.0
    avg_g_weight = 0.0
    win_sum = 0.0
    win_total = 0.0
    win_rate_sum = 0.0
    win_rate_count = 0
    install_daily_sum = 0.0
    install_daily_count = 0
    for entry in entries:
        avg_diff = entry.get("avgDiff")
        total_diff = entry.get("totalDiff")
        avg_g = entry.get("avgG")
        win_rate = entry.get("winRate")
        wins = entry.get("wins")
        install_count = entry.get("installCount")
        if install_count:
            install_daily_sum += install_count
            install_daily_count += 1
        if total_diff is not None and install_count:
            diff_sum += total_diff
            install_sum += install_count
        elif avg_diff is not None and install_count:
            diff_sum += avg_diff * install_count
            install_sum += install_count
        elif avg_diff is not None:
            avg_diff_sum += avg_diff
            avg_diff_count += 1
        if avg_g is not None:
            weight = install_count or 1
            avg_g_sum += avg_g * weight
            avg_g_weight += weight
        if wins is not None and install_count:
            win_sum += wins
            win_total += install_count
        elif win_rate is not None:
            win_rate_sum += win_rate
            win_rate_count += 1
    if install_sum > 0:
        avg_diff_out = diff_sum / install_sum
    elif avg_diff_count > 0:
        avg_diff_out = avg_diff_sum / avg_diff_count
    else:
        avg_diff_out = None
    if win_total > 0:
        win_rate_out = win_sum / win_total * 100
    elif win_rate_count > 0:
        win_rate_out = win_rate_sum / win_rate_count
    else:
        win_rate_out = None
    return {
        "avgDiff": r1(avg_diff_out) if avg_diff_out is not None else None,
        "avgG": r1(avg_g_sum / avg_g_weight) if avg_g_weight > 0 else None,
        "winRate": r1(win_rate_out) if win_rate_out is not None else None,
        "avgInstallCount": r1(install_daily_sum / install_daily_count) if install_daily_count > 0 else None,
        "count": len(entries),
    }

def compute_summary_model_stats(store, special, latest_data_date):
    if not os.path.exists(STORE_MODEL_SUMMARY_CSV):
        return []
    by_model = defaultdict(lambda: {
        "all": [], "sp": [], "nm": [], "this_month": [], "last_month": [],
        "by_day": defaultdict(list), "digit": defaultdict(list), "zoro": [],
    })
    latest = latest_data_date if isinstance(latest_data_date, date) else jst_today()
    this_m = date(latest.year, latest.month, 1)
    last_m = date(latest.year, latest.month - 1, 1) if latest.month > 1 else date(latest.year - 1, 12, 1)
    last_m_end = date(latest.year, latest.month, 1) - timedelta(days=1)
    with open(STORE_MODEL_SUMMARY_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            row_store = normalize_store_name(row.get("store", ""))
            if row_store != store:
                continue
            model = normalize_model_name(row.get("model", ""))
            if not supports_diff_analysis(model):
                continue
            dt = parse_ymd_date(row.get("date"))
            if not dt:
                continue
            avg_diff = parse_summary_number(row.get("avg_diff"))
            total_diff = parse_summary_number(row.get("total_diff"))
            avg_g = parse_summary_number(row.get("avg_g"))
            win_rate, wins, install_count = parse_summary_win_rate(row.get("win_rate"))
            if avg_diff is None and total_diff is None:
                continue
            if avg_diff is None and total_diff is not None and install_count:
                avg_diff = total_diff / install_count
            entry = {
                "date": dt,
                "day": dt.day,
                "avgDiff": avg_diff,
                "totalDiff": total_diff,
                "avgG": avg_g,
                "winRate": win_rate,
                "wins": wins,
                "installCount": install_count,
            }
            bucket = by_model[model]
            bucket["all"].append(entry)
            if dt.day in special: bucket["sp"].append(entry)
            else: bucket["nm"].append(entry)
            if dt >= this_m: bucket["this_month"].append(entry)
            elif last_m <= dt <= last_m_end: bucket["last_month"].append(entry)
            bucket["by_day"][dt.day].append(entry)
            bucket["digit"][dt.day % 10].append(entry)
            if dt.day >= 11 and len(str(dt.day)) == 2 and str(dt.day)[0] == str(dt.day)[1]:
                bucket["zoro"].append(entry)

    result = []
    for model, bucket in by_model.items():
        all_metric = _summary_metric(bucket["all"])
        if not all_metric["count"] or all_metric["avgDiff"] is None:
            continue
        dates = sorted({entry["date"] for entry in bucket["all"] if entry.get("date")})
        row_proxy = int(round((all_metric["avgInstallCount"] or 1) * all_metric["count"]))
        coverage_level = classify_model_coverage_level(all_metric["count"], row_proxy)
        sp_metric = _summary_metric(bucket["sp"])
        nm_metric = _summary_metric(bucket["nm"])
        this_metric = _summary_metric(bucket["this_month"])
        last_metric = _summary_metric(bucket["last_month"])
        zoro_metric = _summary_metric(bucket["zoro"])
        by_day_out = {
            day: [entry["avgDiff"] for entry in entries if entry.get("avgDiff") is not None]
            for day, entries in bucket["by_day"].items()
        }
        digit_avg = {}
        for digit, entries in bucket["digit"].items():
            metric = _summary_metric(entries)
            digit_avg[str(digit)] = {"avg": metric["avgDiff"], "count": metric["count"]}
        avg_g = all_metric["avgG"]
        avg_diff = all_metric["avgDiff"]
        total_in = avg_g * 3 if avg_g else 0
        result.append({
            "model": model,
            "allAvg": avg_diff,
            "count": all_metric["count"],
            "summaryDays": all_metric["count"],
            "firstDate": dates[0].strftime("%Y-%m-%d") if dates else None,
            "lastDate": dates[-1].strftime("%Y-%m-%d") if dates else None,
            "dayCount": all_metric["count"],
            "taiCount": int(round(all_metric["avgInstallCount"] or 0)),
            "rowCount": row_proxy,
            "coverageLabel": coverage_level["label"],
            "coverageStrength": coverage_level["strength"],
            "summarySource": "store_model_summary",
            "analysisMode": get_model_analysis_mode(model),
            "supportsSettingAnalysis": supports_setting_analysis(model),
            "modelCategory": "smart_slot" if model in SMART_SLOT_MODELS else "normal",
            "avgG": avg_g,
            "winRate": all_metric["winRate"],
            "avgInstallCount": all_metric["avgInstallCount"],
            "spAvg": sp_metric["avgDiff"], "spCount": sp_metric["count"],
            "nmAvg": nm_metric["avgDiff"], "nmCount": nm_metric["count"],
            "mechRitu": r1((total_in + avg_diff) / total_in * 100) if total_in > 0 else None,
            "rbRate": None,
            "synRate": None,
            "thisMonthAvg": this_metric["avgDiff"], "thisMonthCount": this_metric["count"],
            "lastMonthAvg": last_metric["avgDiff"], "lastMonthCount": last_metric["count"],
            "byDay": by_day_out,
            "digitAvg": digit_avg,
            "zoroAvg": zoro_metric["avgDiff"],
            "zoroCount": zoro_metric["count"],
        })
    return result

def merge_model_stats_with_summary(raw_stats, summary_stats):
    existing = {row.get("model") for row in raw_stats}
    merged = list(raw_stats)
    merged.extend(row for row in summary_stats if row.get("model") not in existing)
    return merged

def _trend_window_metrics(rows, latest_date, days, offset_days=0):
    if not rows or not isinstance(latest_date, date):
        return {
            "label": f"直近{days}日" if offset_days == 0 else f"{offset_days + days}〜{offset_days + 1}日前",
            "count": 0,
            "activeDays": 0,
            "avgDiff": None,
            "totalDiff": None,
            "avgG": None,
            "winRate": None,
        }
    end = latest_date - timedelta(days=offset_days)
    start = end - timedelta(days=days - 1)
    window_rows = [
        r for r in rows
        if start <= r["date"].date() <= end and has_trustworthy_diff(r)
    ]
    if not window_rows:
        return {
            "label": f"直近{days}日" if offset_days == 0 else f"{offset_days + days}〜{offset_days + 1}日前",
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
            "count": 0,
            "activeDays": 0,
            "avgDiff": None,
            "totalDiff": None,
            "avgG": None,
            "winRate": None,
        }
    return {
        "label": f"直近{days}日" if offset_days == 0 else f"{offset_days + days}〜{offset_days + 1}日前",
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "count": len(window_rows),
        "activeDays": len({r["date"].date() for r in window_rows}),
        "avgDiff": r1(weighted_avg_rows(window_rows, "diff")),
        "totalDiff": r1(weighted_sum(window_rows, "diff")),
        "avgG": r1(weighted_avg_rows(window_rows, "g")),
        "winRate": r1(weighted_diff_rate(window_rows, lambda r: r["diff"] > 0) * 100),
    }

def _classify_trend_label(avg_diff, delta, count):
    if not count or count < 10:
        return {"label": "件数少", "tone": "thin"}
    if avg_diff is None:
        return {"label": "未取得", "tone": "muted"}
    if delta is not None and delta >= 150:
        return {"label": "注目変化", "tone": "up"}
    if avg_diff >= 150 or (delta is not None and delta >= 60):
        return {"label": "強め推移", "tone": "up"}
    if delta is not None and delta <= -150:
        return {"label": "落ち気味", "tone": "down"}
    return {"label": "横ばい", "tone": "flat"}

def _format_model_trend_source(row):
    if row.get("summarySource") == "store_model_summary":
        return "機種日別サマリー"
    return "台別データ"

EXTERNAL_EVENT_LAYERS = [
    {
        "key": "old_event",
        "label": "旧イベ",
        "description": "日付・曜日・店舗の旧イベント傾向を、店/機種/ホール図の推移へ重ねる枠です。",
    },
    {
        "key": "media",
        "label": "取材",
        "description": "取材・媒体告知・来店などを、日付単位の注記として重ねる枠です。",
    },
    {
        "key": "replacement",
        "label": "入替",
        "description": "新台入替・増台・撤去を、機種推移と台履歴へ重ねる枠です。",
    },
    {
        "key": "memo",
        "label": "SNS/メモ",
        "description": "SNSや手入力メモを、あとから確認材料として重ねる枠です。",
    },
]

def build_external_events_frame(scope="global", store=None):
    return {
        "version": 1,
        "enabled": False,
        "status": "not_connected",
        "scope": scope,
        "store": store,
        "items": [],
        "sources": [],
        "layers": EXTERNAL_EVENT_LAYERS,
        "overlayTargets": ["overview", "trends", "combination", "layout", "models", "tai"],
        "note": "旧イベ日・取材・入替・SNS/メモなどは将来ここへ重ねます。v1では外部情報を自動取得しません。",
    }

def build_trend_view(store, store_rows, special, model_stats, tai_detail, latest_data_date, data_quality=None):
    diff_rows = diff_valid_rows(store_rows)
    latest = max((r["date"].date() for r in diff_rows), default=latest_data_date)
    first = min((r["date"].date() for r in diff_rows), default=None)
    baseline_avg = r1(weighted_avg_rows(diff_rows, "diff")) if diff_rows else None
    recent30 = _trend_window_metrics(diff_rows, latest, 30, 0)
    prior30 = _trend_window_metrics(diff_rows, latest, 30, 30)
    recent90 = _trend_window_metrics(diff_rows, latest, 90, 0)
    prior90 = _trend_window_metrics(diff_rows, latest, 90, 90)
    delta30 = None
    if recent30["avgDiff"] is not None and prior30["avgDiff"] is not None:
        delta30 = r1(recent30["avgDiff"] - prior30["avgDiff"])
    delta90 = None
    if recent90["avgDiff"] is not None and prior90["avgDiff"] is not None:
        delta90 = r1(recent90["avgDiff"] - prior90["avgDiff"])
    store_status = _classify_trend_label(recent30["avgDiff"], delta30, recent30["count"])

    model_trends = []
    for row in model_stats or []:
        this_avg = row.get("thisMonthAvg")
        last_avg = row.get("lastMonthAvg")
        delta = None
        if this_avg is not None and last_avg is not None:
            delta = r1(this_avg - last_avg)
        count = int(row.get("thisMonthCount") or row.get("count") or 0)
        trend = _classify_trend_label(this_avg if this_avg is not None else row.get("allAvg"), delta, count)
        avg_all = row.get("allAvg")
        lift_vs_store = None
        if avg_all is not None and baseline_avg is not None:
            lift_vs_store = r1(avg_all - baseline_avg)
        model_trends.append({
            "model": row.get("model"),
            "category": row.get("modelCategory") or ("smart_slot" if row.get("model") in SMART_SLOT_MODELS else "normal"),
            "analysisMode": row.get("analysisMode") or get_model_analysis_mode(row.get("model", "")),
            "source": _format_model_trend_source(row),
            "label": trend["label"],
            "tone": trend["tone"],
            "allAvg": row.get("allAvg"),
            "avgG": row.get("avgG"),
            "winRate": row.get("winRate"),
            "mechRitu": row.get("mechRitu"),
            "thisMonthAvg": this_avg,
            "thisMonthCount": row.get("thisMonthCount"),
            "lastMonthAvg": last_avg,
            "lastMonthCount": row.get("lastMonthCount"),
            "deltaMonth": delta,
            "liftVsStore": lift_vs_store,
            "count": row.get("count"),
            "firstDate": row.get("firstDate"),
            "lastDate": row.get("lastDate"),
            "coverageLabel": row.get("coverageLabel"),
            "coverageStrength": row.get("coverageStrength"),
        })
    model_trends.sort(key=lambda x: (
        0 if x["tone"] == "up" else 1 if x["tone"] == "flat" else 2,
        -(x.get("deltaMonth") if x.get("deltaMonth") is not None else -9999),
        -(x.get("allAvg") if x.get("allAvg") is not None else -9999),
    ))

    tai_trends = []
    for row in tai_detail or []:
        count = int(row.get("count") or 0)
        avg_diff = row.get("avg")
        trend = _classify_trend_label(avg_diff, None, count)
        features = []
        for feature in row.get("hallFeatures") or []:
            if isinstance(feature, dict):
                label = feature.get("label") or feature.get("key") or feature.get("type")
            else:
                label = str(feature)
            if label and label not in features:
                features.append(label)
        tai_trends.append({
            "tai": row.get("tai"),
            "taiNum": row.get("taiNum"),
            "model": row.get("model"),
            "label": trend["label"],
            "tone": trend["tone"],
            "avgDiff": avg_diff,
            "count": count,
            "plusRate": row.get("plusRate"),
            "avgG": row.get("avgG"),
            "spAvg": row.get("spAvg"),
            "nmAvg": row.get("nmAvg"),
            "rbRate": row.get("rbRate"),
            "synRate": row.get("synRate"),
            "features": features[:4],
            "historyScope": row.get("historyScope") or "current_install_segment",
        })
    tai_trends.sort(key=lambda x: (
        0 if x["tone"] == "up" else 1 if x["tone"] == "flat" else 2,
        -(x.get("avgDiff") if x.get("avgDiff") is not None else -9999),
        -(x.get("count") or 0),
        x.get("taiNum") or 0,
    ))

    return {
        "version": 1,
        "store": store,
        "specialDays": special,
        "dataFreshness": {
            "firstDataDate": first.strftime("%Y-%m-%d") if first else None,
            "latestDataDate": latest.strftime("%Y-%m-%d") if latest else None,
            "rowCount": len(store_rows),
            "diffRowCount": len(diff_rows),
            "quality": data_quality or {},
        },
        "storeTrend": {
            "label": store_status["label"],
            "tone": store_status["tone"],
            "baselineAvgDiff": baseline_avg,
            "recent30": recent30,
            "prior30": prior30,
            "delta30": delta30,
            "recent90": recent90,
            "prior90": prior90,
            "delta90": delta90,
        },
        "modelTrends": model_trends,
        "taiTrends": tai_trends,
        "externalEvents": build_external_events_frame(scope="store", store=store),
    }

def compute_next_day(rows, special):
    by_tai = defaultdict(list)
    for r in rows:
        by_tai[r.get("installSegment") or f"{r['tai']}_{r['store']}_{r['model']}"].append(r)
    pairs = []
    for tai_rows in by_tai.values():
        sorted_rows = sorted(tai_rows, key=lambda r: r["date"])
        for i in range(len(sorted_rows)-1):
            prev=sorted_rows[i]; nxt=sorted_rows[i+1]
            if (nxt["date"]-prev["date"]).days==1:
                if has_trustworthy_diff(prev) and has_trustworthy_diff(nxt):
                    pairs.append({"prev":prev,"next":nxt})
    baseline=weighted_avg_rows(rows, "diff")
    def calc(matched):
        next_rows=[p["next"] for p in matched]
        if not next_rows: return {"count":0,"avg":None,"plusRate":None,"vsBaseline":None}
        a=weighted_avg_rows(next_rows, "diff")
        plus_rate=weighted_diff_rate(next_rows, lambda x: x["diff"] > 0) * 100
        return {"count":len(next_rows),"avg":r1(a),"plusRate":r1(plus_rate),"vsBaseline":r1(a-baseline)}
    return {
        "__baseline":{"label":"全期間平均","count":len(diff_valid_rows(rows)),"avg":r1(baseline),"plusRate":r1(weighted_diff_rate(rows, lambda x: x["diff"] > 0)*100),"vsBaseline":0},
        "凹み_2000以上":  {"label":"前日差枚 -2000以下",    **calc([p for p in pairs if p["prev"]["diff"]<=-2000])},
        "凹み_1000_2000": {"label":"前日差枚 -1000〜-2000", **calc([p for p in pairs if -2000<p["prev"]["diff"]<=-1000])},
        "凹み_500_1000":  {"label":"前日差枚 -500〜-1000",  **calc([p for p in pairs if -1000<p["prev"]["diff"]<=-500])},
        "凹み_0_500":     {"label":"前日差枚 0〜-500",      **calc([p for p in pairs if -500<p["prev"]["diff"]<0])},
        "プラス":         {"label":"前日差枚 プラス",        **calc([p for p in pairs if p["prev"]["diff"]>0])},
        "プラス500以上":  {"label":"前日差枚 +500以上",      **calc([p for p in pairs if p["prev"]["diff"]>=500])},
        "RB先行":         {"label":"前日RB先行不発",        **calc([p for p in pairs if p["prev"]["isRBLead"] and p["prev"]["diff"]<0])},
        "凹み_非特定日翌日":{"label":"前日凹み（翌日が特定日でない）",**calc([p for p in pairs if p["prev"]["diff"]<0 and p["next"]["day"] not in special])},
        "凹み_特定日翌日":  {"label":"前日凹み（翌日が特定日）",      **calc([p for p in pairs if p["prev"]["diff"]<0 and p["next"]["day"] in special])},
        "特定日翌日":       {"label":"特定日翌日の台",                **calc([p for p in pairs if p["prev"]["day"] in special])},
    }

EVIDENCE_BACKTEST_CONFIG = {
    "version": 4,
    "min_train_days": 14,
    "min_store_rows": 50,
    "min_feature_samples": 50,
    "min_lift": 150,
    "min_validation_samples": 12,
    "min_validation_lift": 30,
    "min_validation_avg": 0,
    "min_validation_top_hit_rate": 20,
    "require_positive_avg": True,
    "top_k": 3,
    "top_hit_rate": 0.2,
    "training_window_days": None,
    "robustness_windows": [180, 90],
    "min_candidate_score": 140,
    "require_non_tai_evidence": True,
    "type_weights": {
        "day": 0.9,
        "weekday": 0.65,
        "week": 0.6,
        "day_digit": 0.75,
        "monthly_phase": 0.55,
        "model": 0.9,
        "tail": 0.85,
        "day_model": 1.15,
        "day_tail": 1.05,
        "weekday_model": 0.95,
        "weekday_tail": 0.9,
        "day_digit_model": 1.0,
        "day_digit_tail": 0.95,
        "prev_state": 0.8,
        "prev_state_model": 0.9,
        "prev_state_tail": 0.85,
        "hall_edge": 0.75,
        "hall_edge_model": 0.85,
        "hall_corner": 0.75,
        "hall_corner_model": 0.85,
        "hall_island": 0.55,
        "hall_island_model": 0.75,
        "hall_island_shape": 0.45,
        "hall_col_band": 0.45,
        "hall_row_band": 0.45,
        "tai_install": 0.35,
    },
    "type_score_caps": {
        "tai_install": 120,
        "default": 500,
    },
}

def get_prev_state_label(prev):
    if not prev:
        return None
    diff = prev.get("diff", 0)
    if supports_setting_analysis(prev.get("model")):
        if prev.get("isHighSettingSyn") or prev.get("isHighSetRBLead"):
            return "前日強挙動"
        if prev.get("isRBLead") and diff < 0:
            return "前日RB先行不発"
    if diff <= -2000:
        return "前日-2000以下"
    if diff <= -1000:
        return "前日-1000〜-2000"
    if diff <= -500:
        return "前日-500〜-1000"
    if diff < 0:
        return "前日0〜-500"
    if diff >= 500:
        return "前日+500以上"
    if diff > 0:
        return "前日プラス"
    return None

WEEKDAY_LABELS_DATA = ["日曜", "月曜", "火曜", "水曜", "木曜", "金曜", "土曜"]

def get_weekday_label(weekday):
    try:
        w = int(weekday)
    except (TypeError, ValueError):
        return None
    if 0 <= w < len(WEEKDAY_LABELS_DATA):
        return WEEKDAY_LABELS_DATA[w]
    return None

def get_monthly_phase_label(day):
    try:
        d = int(day)
    except (TypeError, ValueError):
        return None
    if d in (24, 25, 26):
        return "給料日前後"
    if 1 <= d <= 10:
        return "月前半"
    if 11 <= d <= 20:
        return "月中盤"
    if 21 <= d <= 31:
        return "月後半"
    return None

def build_evidence_feature_keys(row, prev=None):
    day = row.get("day")
    day_digit = None
    week = None
    try:
        day_int = int(day)
        day_digit = day_int % 10
        week = (day_int - 1) // 7 + 1
    except (TypeError, ValueError):
        day_int = None
    model = row.get("model") or "不明"
    suef = row.get("suef")
    tai = str(row.get("tai") or "")
    weekday_label = get_weekday_label(row.get("weekday"))
    monthly_phase = get_monthly_phase_label(day)
    install_segment = row.get("installSegment")
    keys = [
        ("day", f"{day}日", f"{day}日"),
        ("model", model, model),
        ("tail", f"末尾{suef}", f"末尾{suef}"),
        ("day_model", f"{day}日|{model}", f"{day}日×{model}"),
        ("day_tail", f"{day}日|末尾{suef}", f"{day}日×末尾{suef}"),
    ]
    if weekday_label:
        keys.extend([
            ("weekday", weekday_label, weekday_label),
            ("weekday_model", f"{weekday_label}|{model}", f"{weekday_label}×{model}"),
            ("weekday_tail", f"{weekday_label}|末尾{suef}", f"{weekday_label}×末尾{suef}"),
        ])
    if week is not None:
        keys.append(("week", f"第{week}週", f"第{week}週"))
    if day_digit is not None:
        keys.extend([
            ("day_digit", f"日付末尾{day_digit}", f"日付末尾{day_digit}"),
            ("day_digit_model", f"日付末尾{day_digit}|{model}", f"日付末尾{day_digit}×{model}"),
            ("day_digit_tail", f"日付末尾{day_digit}|末尾{suef}", f"日付末尾{day_digit}×末尾{suef}"),
        ])
    if monthly_phase:
        keys.append(("monthly_phase", monthly_phase, monthly_phase))
    if install_segment:
        keys.append(("tai_install", install_segment, f"{tai}番台設置期間"))
    else:
        keys.append(("tai_install", f"{tai}|{model}", f"{tai}番台設置期間"))
    prev_label = get_prev_state_label(prev)
    if prev_label:
        keys.append(("prev_state", prev_label, prev_label))
        keys.append(("prev_state_model", f"{prev_label}|{model}", f"{prev_label}×{model}"))
        keys.append(("prev_state_tail", f"{prev_label}|末尾{suef}", f"{prev_label}×末尾{suef}"))
    for feature in row.get("hallFeatures") or []:
        if isinstance(feature, (list, tuple)) and len(feature) >= 3:
            f_type = str(feature[0])
            f_key = str(feature[1])
            label = str(feature[2])
            keys.append((f_type, f_key, label))
            if f_type in ("hall_edge", "hall_corner", "hall_island"):
                keys.append((f"{f_type}_model", f"{f_key}|{model}", f"{label}×{model}"))
    return keys

def score_evidence_item(evidence, cfg):
    f_type = evidence.get("type")
    weights = cfg.get("type_weights") or {}
    caps = cfg.get("type_score_caps") or {}
    weight = float(weights.get(f_type, 1.0))
    cap = float(caps.get(f_type, caps.get("default", 500)))
    validation = evidence.get("validation") if isinstance(evidence.get("validation"), dict) else {}
    raw_count = evidence.get("count", 0)
    validation_count = validation.get("count", 0)
    raw_lift = evidence.get("lift", 0)
    validation_lift = validation.get("lift")
    lift = min(raw_lift, validation_lift) if validation_lift is not None else raw_lift
    count = max(raw_count, validation_count)
    sample_floor = max(cfg.get("min_validation_samples", cfg["min_feature_samples"]), 2)
    sample_factor = min(1.0, math.log(count + 1) / math.log(sample_floor))
    return min(lift, cap) * sample_factor * weight

def make_validation_stat():
    return {
        "count": 0,
        "sum": 0.0,
        "sumLift": 0.0,
        "plus": 0,
        "topHit": 0,
        "label": "",
        "type": "",
    }

def update_validation_stat(stat, event):
    stat["count"] += 1
    stat["sum"] += event["diff"]
    stat["sumLift"] += event["lift"]
    stat["plus"] += 1 if event["diff"] > 0 else 0
    stat["topHit"] += 1 if event.get("topHit") else 0
    stat["label"] = event.get("label") or stat.get("label") or ""
    stat["type"] = event.get("type") or stat.get("type") or ""

def remove_validation_stat(stat, event):
    stat["count"] -= 1
    stat["sum"] -= event["diff"]
    stat["sumLift"] -= event["lift"]
    stat["plus"] -= 1 if event["diff"] > 0 else 0
    stat["topHit"] -= 1 if event.get("topHit") else 0

def summarize_validation_stat(stat):
    count = stat.get("count", 0)
    if not count:
        return {
            "count": 0,
            "avg": None,
            "lift": None,
            "plusRate": None,
            "topHitRate": None,
        }
    return {
        "count": count,
        "avg": r1(stat["sum"] / count),
        "lift": r1(stat["sumLift"] / count),
        "plusRate": r1(stat.get("plus", 0) / count * 100),
        "topHitRate": r1(stat.get("topHit", 0) / count * 100),
    }

def classify_validated_evidence(validation, cfg):
    count = validation.get("count") or 0
    avg_diff = validation.get("avg")
    lift = validation.get("lift")
    top_hit = validation.get("topHitRate")
    if count < cfg.get("min_validation_samples", 12):
        return {
            "level": "pending",
            "label": "検証待ち",
            "usable": False,
            "message": "過去に予測として使った回数がまだ不足しています。",
        }
    if avg_diff is None or lift is None:
        return {
            "level": "pending",
            "label": "検証待ち",
            "usable": False,
            "message": "予測実績の集計が不足しています。",
        }
    if (
        avg_diff >= cfg.get("min_validation_avg", 0)
        and lift >= cfg.get("min_validation_lift", 30)
        and (top_hit or 0) >= cfg.get("min_validation_top_hit_rate", 20)
    ):
        return {
            "level": "usable",
            "label": "予測実績あり",
            "usable": True,
            "message": "過去にこの根拠で選んだ時、店平均より上回っています。",
        }
    return {
        "level": "failed",
        "label": "予測実績弱い",
        "usable": False,
        "message": "過去にこの根拠で選んでも十分な改善が出ていません。",
    }

def attach_validation_to_evidence(payload, validation_stats, cfg):
    key = (payload.get("type"), payload.get("key"))
    stat = validation_stats.get(key)
    validation = summarize_validation_stat(stat or {})
    verdict = classify_validated_evidence(validation, cfg)
    return {
        **payload,
        "validation": validation,
        "validationVerdict": verdict,
        "validated": bool(verdict.get("usable")),
    }

def classify_evidence_summary(summary):
    pick_count = summary.get("pickCount") or 0
    pick_avg = summary.get("pickAvg")
    lift = summary.get("lift")
    top_hit = summary.get("topHitRate")
    plus_rate = summary.get("plusRate")
    if not pick_count or pick_avg is None or lift is None:
        return {
            "level": "no_data",
            "label": "根拠不足",
            "actionable": False,
            "message": "検証できる候補がまだありません。",
        }
    if pick_count < 30:
        return {
            "level": "sample_low",
            "label": "サンプル不足",
            "actionable": False,
            "message": "候補数が少ないため、狙い根拠としては保留です。",
        }
    if pick_avg >= 100 and lift >= 80 and (top_hit or 0) >= 23:
        return {
            "level": "main",
            "label": "本命候補あり",
            "actionable": True,
            "message": "候補平均・平均との差・上位命中が揃っています。",
        }
    if pick_avg >= 0 and lift >= 50 and (top_hit or 0) >= 21:
        return {
            "level": "stable",
            "label": "安定候補あり",
            "actionable": True,
            "message": "強さは限定的ですが、候補として見る価値があります。",
        }
    if lift >= 30:
        return {
            "level": "relative",
            "label": "見送り寄り",
            "actionable": False,
            "message": "店平均よりは上ですが、候補平均が弱く実戦根拠としては不足です。",
        }
    return {
        "level": "skip",
        "label": "見送り",
        "actionable": False,
        "message": "検証上、候補を出す根拠が弱いです。",
    }

def summarize_evidence_robustness(primary_summary, window_runs):
    periods = [{
        "label": "全期間",
        "trainingWindowDays": None,
        "summary": primary_summary,
        "decision": classify_evidence_summary(primary_summary),
    }]
    for run in window_runs:
        summary = run.get("summary", {})
        periods.append({
            "label": run.get("label"),
            "trainingWindowDays": run.get("trainingWindowDays"),
            "summary": summary,
            "decision": classify_evidence_summary(summary),
        })
    actionable_count = sum(1 for p in periods if p["decision"].get("actionable"))
    positive_lift_count = sum(1 for p in periods if (p["summary"].get("lift") or 0) > 0)
    positive_pick_count = sum(1 for p in periods if (p["summary"].get("pickAvg") or -999999) > 0)
    if actionable_count == len(periods):
        level = "stable"
        label = "期間耐性あり"
        message = "全期間・直近期間の両方で候補として機能しています。"
    elif actionable_count >= 1 and positive_lift_count == len(periods):
        level = "mixed"
        label = "期間で強弱あり"
        message = "店平均よりは上ですが、期間によって候補の強さが揺れます。"
    elif positive_lift_count >= 1:
        level = "weak"
        label = "参考止まり"
        message = "一部期間では改善しますが、安定した狙い根拠ではありません。"
    else:
        level = "failed"
        label = "期間耐性なし"
        message = "期間を変えても候補として機能していません。"
    return {
        "level": level,
        "label": label,
        "message": message,
        "actionablePeriodCount": actionable_count,
        "positiveLiftPeriodCount": positive_lift_count,
        "positivePickPeriodCount": positive_pick_count,
        "periods": periods,
    }

def combine_evidence_decision_with_robustness(summary, robustness):
    decision = classify_evidence_summary(summary)
    if not decision.get("actionable"):
        return decision
    if not isinstance(robustness, dict) or robustness.get("level") == "stable":
        return decision
    return {
        "level": "period_mixed",
        "label": "期間ブレあり",
        "actionable": False,
        "message": "全期間では候補になりますが、直近期間で弱さが出るため狙い候補は抑制します。",
    }

def build_evidence_backtest_core(store_rows, special, config=None, include_candidates=True):
    cfg = {**EVIDENCE_BACKTEST_CONFIG, **(config or {})}
    store_rows = diff_valid_rows(store_rows)
    if not store_rows:
        return {"version": cfg["version"], "config": cfg, "summary": {"pickCount": 0}, "candidatesByDate": {}, "topEvidence": [], "rejectedEvidence": []}

    rows_sorted = sorted(store_rows, key=lambda r: (r["date"], r["taiNum"]))
    rows_by_segment_date = defaultdict(dict)
    for r in rows_sorted:
        segment_key = r.get("installSegment") or f"{r['tai']}|{r['model']}"
        rows_by_segment_date[segment_key][r["date"].date()] = r

    def prev_for(r):
        segment_key = r.get("installSegment") or f"{r['tai']}|{r['model']}"
        return rows_by_segment_date.get(segment_key, {}).get(r["date"].date() - timedelta(days=1))

    rows_by_date = defaultdict(list)
    for r in rows_sorted:
        rows_by_date[r["date"].date()].append(r)
    sorted_dates = sorted(rows_by_date)

    base_count = 0
    base_sum = 0.0
    feature_stats = defaultdict(lambda: {"count": 0, "sum": 0.0})
    validation_stats = defaultdict(make_validation_stat)
    validation_events = []
    feature_pick_stats = defaultdict(lambda: {"count": 0, "sum": 0.0, "sumLift": 0.0, "plus": 0, "topHit": 0, "label": "", "type": ""})
    rejected_stats = defaultdict(lambda: {"count": 0, "sum": 0.0, "sumLift": 0.0, "plus": 0, "topHit": 0, "label": "", "type": ""})
    candidates_by_date = {}
    picked_diffs = []
    picked_plus = 0
    picked_top_hit = 0
    picked_baseline_sum = 0.0
    tested_days = 0
    trained_days = 0
    rolling_window_days = cfg.get("training_window_days")
    rolling_mode = bool(rolling_window_days)
    rolling_dates = deque()
    rolling_validation_events = deque()
    rolling_base_count = 0
    rolling_base_sum = 0.0
    rolling_feature_stats = defaultdict(lambda: {"count": 0, "sum": 0.0})
    rolling_validation_stats = defaultdict(make_validation_stat)

    def add_feature_stat(stats, row, sign=1):
        prev = prev_for(row)
        for f_type, f_key, label in build_evidence_feature_keys(row, prev):
            stat = stats[(f_type, f_key)]
            stat["count"] += sign
            stat["sum"] += sign * row["diff"]

    def add_rolling_date(train_date):
        nonlocal rolling_base_count, rolling_base_sum
        rolling_dates.append(train_date)
        for train_row in rows_by_date[train_date]:
            rolling_base_count += 1
            rolling_base_sum += train_row["diff"]
            add_feature_stat(rolling_feature_stats, train_row, sign=1)

    def remove_rolling_date(train_date):
        nonlocal rolling_base_count, rolling_base_sum
        for train_row in rows_by_date[train_date]:
            rolling_base_count -= 1
            rolling_base_sum -= train_row["diff"]
            add_feature_stat(rolling_feature_stats, train_row, sign=-1)

    def prune_rolling_window(current_date):
        if not rolling_mode:
            return
        cutoff = current_date - timedelta(days=int(rolling_window_days))
        while rolling_dates and rolling_dates[0] < cutoff:
            remove_rolling_date(rolling_dates.popleft())
        while rolling_validation_events and rolling_validation_events[0]["date"] < cutoff:
            event = rolling_validation_events.popleft()
            remove_validation_stat(rolling_validation_stats[(event["type"], event["key"])], event)

    for current_date in sorted_dates:
        todays = sorted(rows_by_date[current_date], key=lambda r: r["taiNum"])
        prune_rolling_window(current_date)
        if rolling_mode:
            day_trained_days = len(rolling_dates)
            day_base_count = rolling_base_count
            day_base_sum = rolling_base_sum
            day_feature_stats = rolling_feature_stats
            day_validation_stats = rolling_validation_stats
        else:
            day_trained_days = trained_days
            day_base_count = base_count
            day_base_sum = base_sum
            day_feature_stats = feature_stats
            day_validation_stats = validation_stats
        if day_trained_days >= cfg["min_train_days"] and day_base_count >= cfg["min_store_rows"]:
            store_baseline = day_base_sum / day_base_count if day_base_count else 0.0
            scored = []
            validation_updates = []
            today_diffs = sorted([r["diff"] for r in todays], reverse=True)
            top_count = max(1, math.ceil(len(today_diffs) * cfg["top_hit_rate"]))
            top_threshold = today_diffs[min(len(today_diffs) - 1, top_count - 1)] if today_diffs else None
            day_avg = avg([r["diff"] for r in todays])

            for r in todays:
                evidence = []
                cautions = []
                ignored_positive = []
                prev = prev_for(r)
                for f_type, f_key, label in build_evidence_feature_keys(r, prev):
                    stat = day_feature_stats[(f_type, f_key)]
                    count = stat["count"]
                    if count < cfg["min_feature_samples"]:
                        continue
                    feature_avg = stat["sum"] / count
                    lift = feature_avg - store_baseline
                    payload = {
                        "type": f_type,
                        "key": f_key,
                        "label": label,
                        "count": count,
                        "avg": r1(feature_avg),
                        "lift": r1(lift),
                    }
                    if lift >= cfg["min_lift"] and (not cfg["require_positive_avg"] or feature_avg > 0):
                        validation_updates.append({
                            "date": current_date,
                            "type": f_type,
                            "key": f_key,
                            "label": label,
                            "diff": r["diff"],
                            "lift": r["diff"] - day_avg,
                            "topHit": top_threshold is not None and r["diff"] >= top_threshold,
                        })
                        validated_payload = attach_validation_to_evidence(payload, day_validation_stats, cfg)
                        if validated_payload["validated"]:
                            evidence.append(validated_payload)
                        else:
                            ignored_positive.append(validated_payload)
                    elif lift <= -cfg["min_lift"]:
                        cautions.append(payload)

                if not evidence:
                    for item in ignored_positive:
                        verdict = item.get("validationVerdict") or {}
                        if verdict.get("level") == "failed":
                            key = (item["type"], item["key"])
                            rs = rejected_stats[key]
                            validation = item.get("validation") or {}
                            rs["count"] += 1
                            rs["sum"] += r["diff"]
                            rs["sumLift"] += r["diff"] - day_avg
                            rs["plus"] += 1 if r["diff"] > 0 else 0
                            rs["topHit"] += 1 if top_threshold is not None and r["diff"] >= top_threshold else 0
                            rs["label"] = item["label"]
                            rs["type"] = item["type"]
                            rs["validation"] = validation
                    continue
                if cfg.get("require_non_tai_evidence") and not any(e.get("type") != "tai_install" for e in evidence):
                    continue
                score = 0.0
                for e in evidence:
                    score += score_evidence_item(e, cfg)
                if score < cfg.get("min_candidate_score", 0):
                    continue
                scored.append((score, r, evidence, cautions))

            scored.sort(key=lambda x: (-x[0], x[1]["taiNum"]))
            selected = scored[:cfg["top_k"]]
            if selected:
                tested_days += 1
                day_items = []
                for rank, (score, r, evidence, cautions) in enumerate(selected, start=1):
                    diff = r["diff"]
                    is_top_hit = top_threshold is not None and diff >= top_threshold
                    picked_diffs.append(diff)
                    picked_baseline_sum += day_avg
                    if diff > 0:
                        picked_plus += 1
                    if is_top_hit:
                        picked_top_hit += 1
                    for e in evidence[:3]:
                        key = (e["type"], e["key"])
                        ps = feature_pick_stats[key]
                        ps["count"] += 1
                        ps["sum"] += diff
                        ps["sumLift"] += diff - day_avg
                        ps["plus"] += 1 if diff > 0 else 0
                        ps["topHit"] += 1 if is_top_hit else 0
                        ps["label"] = e["label"]
                        ps["type"] = e["type"]
                    for c in cautions[:2]:
                        key = (c["type"], c["key"])
                        rs = rejected_stats[key]
                        rs["count"] += 1
                        rs["sum"] += diff
                        rs["sumLift"] += diff - day_avg
                        rs["plus"] += 1 if diff > 0 else 0
                        rs["topHit"] += 1 if is_top_hit else 0
                        rs["label"] = c["label"]
                        rs["type"] = c["type"]

                    day_items.append({
                        "rank": rank,
                        "tai": r["tai"],
                        "taiNum": r["taiNum"],
                        "model": r["model"],
                        "score": r1(score),
                        "evidence": evidence[:3],
                        "cautions": cautions[:2],
                        "result": {
                            "diff": diff,
                            "plus": diff > 0,
                            "topHit": bool(is_top_hit),
                            "dayAvg": r1(day_avg),
                        },
                    })
                if include_candidates:
                    candidates_by_date[current_date.strftime("%Y-%m-%d")] = day_items
            for event in validation_updates:
                update_validation_stat(validation_stats[(event["type"], event["key"])], event)
                validation_events.append(event)
                if rolling_mode:
                    update_validation_stat(rolling_validation_stats[(event["type"], event["key"])], event)
                    rolling_validation_events.append(event)

        if rolling_mode:
            add_rolling_date(current_date)
        else:
            for r in todays:
                base_count += 1
                base_sum += r["diff"]
                add_feature_stat(feature_stats, r, sign=1)
            trained_days += 1

    pick_count = len(picked_diffs)
    pick_avg = avg(picked_diffs)
    baseline_avg = picked_baseline_sum / pick_count if pick_count else None
    summary = {
        "pickCount": pick_count,
        "testDayCount": tested_days,
        "pickAvg": r1(pick_avg) if pick_count else None,
        "baselineAvg": r1(baseline_avg) if baseline_avg is not None else None,
        "lift": r1(pick_avg - baseline_avg) if pick_count and baseline_avg is not None else None,
        "plusRate": r1(picked_plus / pick_count * 100) if pick_count else None,
        "topHitRate": r1(picked_top_hit / pick_count * 100) if pick_count else None,
    }
    summary["decision"] = classify_evidence_summary(summary)

    def summarize_feature(stat_items, min_count=5):
        out = []
        for (f_type, f_key), s in stat_items:
            if s["count"] < min_count:
                continue
            avg_diff = s["sum"] / s["count"]
            avg_lift = s.get("sumLift", 0.0) / s["count"] if s.get("sumLift") is not None else None
            out.append({
                "type": s["type"] or f_type,
                "key": f_key,
                "label": s["label"] or f_key,
                "pickCount": s["count"],
                "pickAvg": r1(avg_diff),
                "lift": r1(avg_lift) if avg_lift is not None else None,
                "plusRate": r1(s.get("plus", 0) / s["count"] * 100) if s.get("plus") is not None else None,
                "topHitRate": r1(s.get("topHit", 0) / s["count"] * 100) if s.get("topHit") is not None else None,
            })
        out.sort(key=lambda x: (x.get("lift") if x.get("lift") is not None else -999999, x["pickAvg"], x["pickCount"]), reverse=True)
        return out[:8]

    def summarize_validated_features(stat_items, min_count=None, usable=None, limit=80):
        min_count = min_count if min_count is not None else cfg.get("min_validation_samples", 12)
        out = []
        for (f_type, f_key), s in stat_items:
            if s["count"] < min_count:
                continue
            validation = summarize_validation_stat(s)
            verdict = classify_validated_evidence(validation, cfg)
            if usable is not None and bool(verdict.get("usable")) != bool(usable):
                continue
            out.append({
                "type": s["type"] or f_type,
                "key": f_key,
                "label": s["label"] or f_key,
                "validationCount": validation["count"],
                "validationAvg": validation["avg"],
                "validationLift": validation["lift"],
                "plusRate": validation["plusRate"],
                "topHitRate": validation["topHitRate"],
                "verdict": verdict,
            })
        out.sort(key=lambda x: (
            x["validationLift"] if x["validationLift"] is not None else -999999,
            x["topHitRate"] if x["topHitRate"] is not None else -999999,
            x["validationCount"],
        ), reverse=True)
        return out[:limit] if limit else out

    return {
        "version": cfg["version"],
        "config": cfg,
        "summary": summary,
        "candidatesByDate": candidates_by_date,
        "topEvidence": summarize_feature(feature_pick_stats.items()),
        "validatedEvidence": summarize_validated_features(validation_stats.items(), usable=True, limit=200),
        "rejectedEvidence": summarize_feature(rejected_stats.items()),
        "failedEvidence": summarize_validated_features(validation_stats.items(), usable=False, limit=80),
        "note": "各日より前のデータだけで候補を出し、当日結果で検証した簡易バックテストです。",
    }

def build_evidence_backtest(store_rows, special, config=None):
    cfg = {**EVIDENCE_BACKTEST_CONFIG, **(config or {})}
    primary = build_evidence_backtest_core(store_rows, special, cfg, include_candidates=True)
    window_runs = []
    for days in cfg.get("robustness_windows", []):
        run_cfg = {**cfg, "training_window_days": int(days)}
        run = build_evidence_backtest_core(store_rows, special, run_cfg, include_candidates=False)
        window_runs.append({
            "label": f"直近{int(days)}日",
            "trainingWindowDays": int(days),
            "summary": run.get("summary", {}),
        })
    primary["robustness"] = summarize_evidence_robustness(primary.get("summary", {}), window_runs)
    primary["summary"]["decision"] = combine_evidence_decision_with_robustness(
        primary.get("summary", {}),
        primary.get("robustness", {}),
    )
    return primary

def get_evidence_decision(evidence_backtest):
    if not isinstance(evidence_backtest, dict):
        return {
            "level": "no_data",
            "label": "根拠不足",
            "actionable": False,
            "message": "検証データが不足しています。",
        }
    summary = evidence_backtest.get("summary") if isinstance(evidence_backtest.get("summary"), dict) else {}
    decision = summary.get("decision") if isinstance(summary.get("decision"), dict) else {}
    return {
        "level": decision.get("level", "no_data"),
        "label": decision.get("label", "根拠不足"),
        "actionable": bool(decision.get("actionable", False)),
        "message": decision.get("message", "検証データが不足しています。"),
    }

def build_validated_today_targets(tai_detail, target_day, evidence_backtest, top_k=20, target_weekday=None, target_date=None):
    decision = get_evidence_decision(evidence_backtest)
    if not decision["actionable"]:
        return []
    cfg = (evidence_backtest or {}).get("config") or EVIDENCE_BACKTEST_CONFIG
    validated_items = (evidence_backtest or {}).get("validatedEvidence") or []
    validated_map = {
        (item.get("type"), item.get("key")): item
        for item in validated_items
        if isinstance(item, dict) and item.get("verdict", {}).get("usable", True)
    }
    if not validated_map:
        return []

    target_date_obj = target_date.date() if isinstance(target_date, datetime) else target_date
    if isinstance(target_date_obj, str):
        target_date_obj = parse_ymd_date(target_date_obj)
    expected_prev_date = target_date_obj - timedelta(days=1) if target_date_obj else None

    targets = []
    for t in tai_detail:
        tai_num = int(t.get("taiNum") or 0)
        raw_prev_row = t.get("prevRow") if isinstance(t.get("prevRow"), dict) else None
        raw_prev_date = parse_ymd_date(raw_prev_row.get("dateStr")) if raw_prev_row else None
        prev_row = raw_prev_row if expected_prev_date and raw_prev_date == expected_prev_date else None
        target_cautions = []
        model_coverage = t.get("modelCoverage") if isinstance(t.get("modelCoverage"), dict) else {}
        coverage_strength = model_coverage.get("coverageStrength") or model_coverage.get("coverage_strength") or ""
        coverage_label = model_coverage.get("coverageLabel") or model_coverage.get("coverage_label") or ""
        coverage_days = model_coverage.get("dayCount") or model_coverage.get("day_count") or 0
        coverage_rows = model_coverage.get("rowCount") or model_coverage.get("row_count") or 0
        if coverage_strength == "thin":
            target_cautions.append({
                "label": "機種データ薄い",
                "message": f"{coverage_label or '薄い'}: {coverage_days}日/{coverage_rows}件のため候補から除外します。",
            })
            continue
        coverage_score_factor = 1.0
        rank_cap = None
        if coverage_strength == "low":
            coverage_score_factor = 0.85
            rank_cap = "対抗"
            target_cautions.append({
                "label": "機種データ短期",
                "message": f"{coverage_label or '短期'}: {coverage_days}日/{coverage_rows}件。短期傾向としてスコアを抑制しています。",
            })
        if expected_prev_date and raw_prev_row and raw_prev_date != expected_prev_date:
            target_cautions.append({
                "label": "前日条件なし",
                "message": "対象日前日の台データがないため、前日凹み/RB先行根拠は使っていません。",
            })
        elif expected_prev_date and not raw_prev_row:
            target_cautions.append({
                "label": "前日条件なし",
                "message": "対象日前日の台データがないため、前日根拠は使っていません。",
            })
        pseudo_row = {
            "day": target_day,
            "weekday": target_weekday,
            "model": t.get("model") or "不明",
            "suef": tai_num % 10,
            "tai": t.get("tai") or str(tai_num),
            "taiNum": tai_num,
            "installSegment": t.get("installSegment"),
            "hallFeatures": t.get("hallFeatures") or [],
        }
        matched = []
        for f_type, f_key, label in build_evidence_feature_keys(pseudo_row, prev_row):
            root = validated_map.get((f_type, f_key))
            if not root:
                continue
            validation = {
                "count": root.get("validationCount", 0),
                "avg": root.get("validationAvg"),
                "lift": root.get("validationLift"),
                "plusRate": root.get("plusRate"),
                "topHitRate": root.get("topHitRate"),
            }
            verdict = root.get("verdict") or classify_validated_evidence(validation, cfg)
            if not verdict.get("usable"):
                continue
            matched.append({
                "type": f_type,
                "key": f_key,
                "label": label,
                "count": validation["count"],
                "avg": validation["avg"],
                "lift": validation["lift"],
                "validation": validation,
                "validationVerdict": verdict,
                "validated": True,
            })
        if not matched:
            continue
        if cfg.get("require_non_tai_evidence") and not any(item.get("type") != "tai_install" for item in matched):
            continue
        score = sum(score_evidence_item(item, cfg) for item in matched) * coverage_score_factor
        if score < cfg.get("min_candidate_score", 0):
            continue
        matched.sort(key=lambda item: (
            item["validation"].get("lift") if item.get("validation") else item.get("lift") or -999999,
            item["validation"].get("count") if item.get("validation") else item.get("count") or 0,
        ), reverse=True)
        reasons = []
        for item in matched[:3]:
            lift = item.get("validation", {}).get("lift")
            avg_diff = item.get("validation", {}).get("avg")
            pts = 3 if (lift or 0) >= 250 else 2 if (lift or 0) >= 120 else 1
            reasons.append({
                "label": item["label"],
                "val": f"予測{lift:+}枚 / 平均{avg_diff:+}枚" if lift is not None and avg_diff is not None else "予測実績あり",
                "pts": pts,
            })
        rank = "本命" if score >= 260 else "対抗" if score >= 180 else "保留"
        if rank_cap == "対抗" and rank == "本命":
            rank = "対抗"
        hall_evidence = [
            item for item in matched
            if str(item.get("type", "")).startswith("hall_")
        ][:2]
        targets.append({
            **t,
            "prevRow": prev_row,
            "totalScore": r1(score),
            "rank": rank,
            "reasons": reasons,
            "evidence": matched[:3],
            "hallEvidence": hall_evidence,
            "cautions": target_cautions,
            "modelCoverage": model_coverage,
            "scoreSource": "validated_evidence",
        })
    targets.sort(key=lambda item: (-item["totalScore"], item.get("taiNum") or 0))
    return targets[:top_k]

def compute_heatmap(rows):
    heat = defaultdict(lambda: {"rows":[], "count":0})
    def add(key, r):
        heat[key]["rows"].append(r)
        heat[key]["count"] += 1
    for r in rows:
        dk=r["day"]%10; tk=r["suef"]
        add(f"{dk}_{tk}",r)
        if r["isZoro"]: add(f"zoro_{tk}",r)
        if r["day"]==r["date"].month: add(f"tsuki_{tk}",r)
        last_day=(date(r["date"].year,r["date"].month%12+1,1)-timedelta(days=1)).day
        if r["day"]==last_day: add(f"end_{tk}",r)
    result={}
    for k,v in heat.items():
        if v["count"]<3: continue
        target_rows = v["rows"]
        ti=weighted_sum(target_rows, "g")*3
        to=ti+weighted_sum(target_rows, "diff")
        result[k]={
            "avg":r1(weighted_avg_rows(target_rows, "diff")),
            "ritu":r1(to/ti*100) if ti>0 else None,
            "win":r1(weighted_diff_rate(target_rows, lambda x: x["diff"] > 0) * 100),
            "set456":r1(weighted_rate(target_rows, lambda x: x["isHighSetRBLead"]) * 100),
            "count":v["count"],
        }
    return result

def compute_week_matrix(rows):
    wm=defaultdict(lambda: {"rows":[],"count":0})
    for r in rows:
        week=(r["day"]-1)//7+1; key=f"{week}_{r['weekday']}"
        wm[key]["rows"].append(r)
        wm[key]["count"]+=1
    result={}
    for k,v in wm.items():
        if v["count"]<3: continue
        target_rows = v["rows"]
        ti=weighted_sum(target_rows, "g")*3
        to=ti+weighted_sum(target_rows, "diff")
        result[k]={
            "avg":r1(weighted_avg_rows(target_rows, "diff")),
            "ritu":r1(to/ti*100) if ti>0 else None,
            "win":r1(weighted_diff_rate(target_rows, lambda x: x["diff"] > 0) * 100),
            "set456":r1(weighted_rate(target_rows, lambda x: x["isHighSetRBLead"]) * 100),
            "count":v["count"],
        }
    return result

def compute_date_summary(rows, special):
    by_date = {}
    for r in rows:
        k = r["dateStr"]
        if k not in by_date:
            by_date[k] = {"dateStr":k,"day":r["day"],"rows":[],"plus":0}
        by_date[k]["rows"].append(r)
        if has_trustworthy_diff(r) and r["diff"] > 0: by_date[k]["plus"] += 1
    result = []
    for v in sorted(by_date.values(), key=lambda x: x["dateStr"]):
        day_rows = v["rows"]
        n = len(day_rows)
        result.append({
            "dateStr": v["dateStr"],"total": r1(weighted_sum(day_rows, "diff")),
            "count": n,"plus": v["plus"],
            "plusRate": r1(weighted_diff_rate(day_rows, lambda x: x["diff"] > 0) * 100),
            "day": v["day"],"special": v["day"] in special,
        })
    return result

def compute_weekday_stats(rows):
    by_wday = defaultdict(list)
    for r in rows:
        by_wday[r["weekday"]].append(r)
    result = {}
    for wday, v in by_wday.items():
        result[str(wday)] = {"avg": r1(weighted_avg_rows(v, "diff")), "count": len(v)}
    return result

def compute_day_wday_matrix(rows):
    dwm = defaultdict(lambda: {"rows":[],"count":0})
    def add_dw(row_key, wday, r):
        key = f"{row_key}_{wday}"
        dwm[key]["rows"].append(r)
        dwm[key]["count"] += 1
    for r in rows:
        wday = r["weekday"]; suef = r["day"] % 10
        add_dw(str(suef), wday, r)
        if r["isZoro"]: add_dw("zoro", wday, r)
        if r["day"] == r["date"].month: add_dw("tsuki", wday, r)
        last_day = (date(r["date"].year, r["date"].month % 12 + 1, 1) - timedelta(days=1)).day
        if r["day"] == last_day: add_dw("end", wday, r)
    result = {}
    for k, v in dwm.items():
        if v["count"] < 3: continue
        target_rows = v["rows"]
        ti = weighted_sum(target_rows, "g")*3
        to = ti+weighted_sum(target_rows, "diff")
        result[k] = {
            "avg":r1(weighted_avg_rows(target_rows, "diff")),
            "ritu":r1(to/ti*100) if ti>0 else None,
            "win":r1(weighted_diff_rate(target_rows, lambda x: x["diff"] > 0) * 100),
            "set456":r1(weighted_rate(target_rows, lambda x: x["isHighSetRBLead"]) * 100),
            "count":v["count"]
        }
    return result

def compute_today_analysis(rows, special, today=None, tai_detail=None, evidence_backtest=None):
    if today is None:
        today = jst_today()
    day = today.day
    weekday = today.weekday()
    weekday_data = (weekday + 1) % 7
    is_special = day in special
    day_stats = compute_day_stats(rows, special)
    day_info = next((d for d in day_stats if d["day"] == day), None)
    wday_rows = [r for r in rows if r["weekday"] == weekday_data]
    wday_avg = r1(weighted_avg_rows(wday_rows, "diff")) if wday_rows else None
    baseline = r1(weighted_avg_rows(rows, "diff")) if rows else 0
    if day_info:
        if day_info["avg"] > 100: day_judge = "🔥 かなり強い日"; day_score = 3
        elif day_info["avg"] > 0: day_judge = "🟡 やや強い日"; day_score = 2
        elif day_info["avg"] > -100: day_judge = "⬜ 普通の日"; day_score = 1
        else: day_judge = "❄️ 弱い日"; day_score = 0
    else:
        day_judge = "データなし"; day_score = 0
    verdict = (
        "✅ 狙う価値あり" if is_special and day_score >= 2 else
        "🟡 条件次第" if is_special and day_score >= 1 else
        "🟡 非特定日だが強い傾向" if not is_special and day_score >= 2 else
        "⬜ 普通・慎重に" if not is_special and day_score >= 1 else
        "❌ 見送りを推奨"
    )
    if tai_detail is None:
        tai_detail = compute_tai_detail(rows, special, weekday_data, is_special)
    evidence_decision = get_evidence_decision(evidence_backtest)
    holdover_rate = get_holdover_rate(rows[0]["store"]) if rows else 0.0
    by_model = defaultdict(lambda: {"sp":[],"nm":[]})
    for r in rows:
        if r["day"] in special: by_model[r["model"]]["sp"].append(r)
        else: by_model[r["model"]]["nm"].append(r)
    model_strength = []
    for model, m in by_model.items():
        target = m["sp"] if is_special else m["nm"]
        if not target: continue
        model_avg = r1(weighted_avg_rows(target, "diff")); lift = r1(model_avg - baseline)
        model_strength.append({"model":model,"avg":model_avg,"lift":lift,"count":len(target),
            "label":"有力" if lift>80 else "対抗" if lift>30 else "標準" if lift>-30 else "弱め"})
    model_strength.sort(key=lambda x: -x["lift"])
    scored_tais = build_validated_today_targets(
        tai_detail,
        day,
        evidence_backtest,
        top_k=20,
        target_weekday=weekday_data,
        target_date=today,
    )
    return {
        "date":today.strftime("%Y-%m-%d"),"day":day,"weekday":weekday,
        "isSpecial":is_special,"dayJudge":day_judge,"dayScore":day_score,
        "verdict":verdict,"dayInfo":day_info,"wdayAvg":wday_avg,
        "baseline":baseline,"modelStrength":model_strength,"topTargets":scored_tais[:20],
        "evidenceDecision": evidence_decision,
        "targetSuppressed": not evidence_decision["actionable"],
        "suppressionReason": evidence_decision["message"] if not evidence_decision["actionable"] else "",
    }

def build_store_recommendations(store, store_rows, special, tai_detail, today=None, evidence_backtest=None):
    if today is None:
        today = jst_today()
    evidence_decision = get_evidence_decision(evidence_backtest)
    if not evidence_decision["actionable"]:
        return []
    yesterday = today - timedelta(days=1)
    recommendation_day = today.day
    recommendation_weekday = today.weekday()
    recommendation_weekday_data = (recommendation_weekday + 1) % 7
    weekday_coeff = WEEKDAY_COEFF.get(recommendation_weekday, 1.0)
    monthly_timing_coeff = get_monthly_timing_coeff(recommendation_day)
    store_coeff = get_store_coeff(store, recommendation_weekday, recommendation_day)
    is_special = today.day in special
    is_special_next_day = yesterday.day in special
    if not (is_special or is_special_next_day):
        return []

    targets = build_validated_today_targets(
        tai_detail,
        recommendation_day,
        evidence_backtest,
        top_k=8,
        target_weekday=recommendation_weekday_data,
        target_date=today,
    )
    recs = []
    for t in targets:
        score = float(t.get("totalScore") or 0)
        reasons = []
        if is_special:
            reasons.append("今日は特定日")
        if is_special_next_day:
            reasons.append("特定日翌日")
        reasons.append(f"検証済み根拠: {evidence_decision['label']}")
        for item in (t.get("evidence") or [])[:3]:
            validation = item.get("validation") or {}
            lift = validation.get("lift")
            avg_diff = validation.get("avg")
            if lift is not None and avg_diff is not None:
                reasons.append(f"{item.get('label')}: 予測{lift:+}枚 / 平均{avg_diff:+}枚")
            else:
                reasons.append(f"{item.get('label')}: 予測実績あり")
        weighted_score = score * weekday_coeff * monthly_timing_coeff * store_coeff
        recs.append({
            "store": store,
            "tai": t["tai"],
            "model": t["model"],
            "bayes_score": None,
            "final_score": r1(score),
            "evidence_label": evidence_decision["label"],
            "evidence_message": evidence_decision["message"],
            "confidence": "★★★" if t.get("rank") == "本命" else "★★" if t.get("rank") == "対抗" else "★",
            "day_type": "特定日" if is_special else "特定日翌日",
            "recent_count_3m": t.get("weightedCount") or t.get("count") or 0,
            "reasons": reasons,
            "cautions": t.get("cautions", []),
            "score": weighted_score,
        })
    recs.sort(key=lambda x: (-x["score"], -x["recent_count_3m"], x["store"], x["tai"]))
    return recs

def build_answer_check(by_store, today=None, actual_settings=None):
    if today is None:
        today = jst_today()
    if actual_settings is None:
        actual_settings = {}
    hit_targets = []
    for store, payload in by_store.items():
        targets = ((payload.get("todayAnalysis") or {}).get("topTargets") or [])[:3]
        for t in targets:
            hit_targets.append({
                "machine_id": t.get("tai"),
                "store": store,
                "model": t.get("model"),
                "validated_score": t.get("totalScore"),
                "rank": t.get("rank"),
            })
    hit_count = 0
    all_have_actual = True
    for target in hit_targets:
        store = target["store"]
        machine_id = str(target["machine_id"])
        actual_store = actual_settings.get(store, {}) if isinstance(actual_settings, dict) else {}
        actual = actual_store.get(machine_id) if isinstance(actual_store, dict) else None
        if actual is None:
            all_have_actual = False
            continue
        if actual >= 4:
            hit_count += 1
    accuracy = r1(hit_count / len(hit_targets) * 100) if hit_targets and all_have_actual else None
    return {
        "date": today.strftime("%Y-%m-%d"),
        "hit_targets": hit_targets,
        "actual_settings": actual_settings,
        "accuracy": accuracy,
    }

def build_store_accuracy(by_store, answer_check):
    hit_targets = answer_check.get("hit_targets", [])
    actual_settings = answer_check.get("actual_settings", {})
    by_name = {}
    for store in by_store.keys():
        by_name[store] = {"hit_count": 0, "target_count": 0, "accuracy": None}
    for target in hit_targets:
        store = target["store"]
        machine_id = str(target["machine_id"])
        if store not in by_name:
            by_name[store] = {"hit_count": 0, "target_count": 0, "accuracy": None}
        by_name[store]["target_count"] += 1
        actual_store = actual_settings.get(store, {}) if isinstance(actual_settings, dict) else {}
        actual = actual_store.get(machine_id) if isinstance(actual_store, dict) else None
        if actual is not None and actual >= 4:
            by_name[store]["hit_count"] += 1
    for store, stat in by_name.items():
        actual_store = actual_settings.get(store, {}) if isinstance(actual_settings, dict) else {}
        all_have_actual = True
        for target in hit_targets:
            if target["store"] != store:
                continue
            machine_id = str(target["machine_id"])
            if not isinstance(actual_store, dict) or actual_store.get(machine_id) is None:
                all_have_actual = False
                break
        stat["accuracy"] = r1(stat["hit_count"] / stat["target_count"] * 100) if stat["target_count"] > 0 and all_have_actual else None
    return by_name

if __name__ == "__main__":
    print("=== compute.py 開始 ===")
    store_cfg = load_store_configs()
    for store_name, rate in store_cfg.get("exchangeRateByStore", {}).items():
        STORE_EXCHANGE_RATE[normalize_store_name(store_name)] = rate
    store_special_map = {
        normalize_store_name(k): v[:] for k, v in store_cfg.get("specialByStore", {}).items()
    }
    today = jst_today()
    rows = load_raw(store_special_map)
    if not rows:
        print("データがありません。終了します。")
        exit(1)
    latest_data_date = max((r["date"].date() for r in rows), default=today)
    hall_layout_feature_map, hall_layout_meta = build_hall_layout_feature_map(load_hall_layouts())
    if hall_layout_feature_map:
        apply_hall_layout_features(rows, hall_layout_feature_map)
        ready_count = sum(1 for meta in hall_layout_meta.values() if meta.get("analysisReady"))
        print(f"ホール図配置読込: {len(hall_layout_meta)}店舗 / 分析利用 {ready_count}店舗")
    all_stores = sorted(set(r["store"] for r in rows))
    for store in all_stores:
        if store not in store_special_map:
            store_special_map[store] = DEFAULT_SPECIAL_DAYS[:]
    ANALYTICS_CACHE = build_analytics_cache(rows)
    holdover_summary = {
        s: r1(v.get("rate", 0.0) * 100)
        for s, v in ANALYTICS_CACHE.get("holdover_rate", {}).items()
    }
    print(f"据え置き率キャッシュ作成: {len(holdover_summary)}店舗")
    rows_by_store = defaultdict(list)
    for r in rows:
        rows_by_store[r["store"]].append(r)
    display_stores = build_store_display_order(all_stores)
    output = {
        "updated_at": datetime.now(JST).date().strftime("%Y-%m-%d"),
        "data_date": latest_data_date.strftime("%Y-%m-%d"),
        "store_freshness": load_store_freshness(),
        "stores": display_stores,
        "specialByStore": store_special_map,
        "score_coefficients": {
            "weekday": WEEKDAY_COEFF,
            "monthly_timing": MONTHLY_TIMING_COEFF,
            "note": "係数は暫定値です。店舗別の微調整は byStore[店名].store_coefficients と STORE_COEFFICIENTS による拡張を想定しています。",
        },
        "hallLayoutEvidence": hall_layout_meta,
        "externalEvents": build_external_events_frame(scope="global"),
        "byStore": {},
        "recommendations": [],
        "predictionAccuracy": {"overall": None, "byStore": {}},
    }
    recommendation_pool = []
    for store in all_stores:
        special = store_special_map.get(store, DEFAULT_SPECIAL_DAYS)
        store_rows = rows_by_store.get(store, [])
        diff_store_rows = diff_valid_rows(store_rows)
        is_special_today = today.day in special
        weekday_data = (today.weekday() + 1) % 7
        tai_detail = compute_tai_detail(store_rows, special, weekday_data, is_special_today)
        evidence_backtest = build_evidence_backtest(diff_store_rows, special)
        today_analysis = compute_today_analysis(
            diff_store_rows,
            special,
            today=today,
            tai_detail=tai_detail,
            evidence_backtest=evidence_backtest,
        )
        tomorrow = today + timedelta(days=1)
        tomorrow_analysis = compute_today_analysis(
            diff_store_rows,
            special,
            today=tomorrow,
            tai_detail=tai_detail,
            evidence_backtest=evidence_backtest,
        )
        print(f"集計中: {store} ({len(store_rows)}行) 特定日:{special}")
        model_stats = compute_model_stats(diff_store_rows, special)
        model_stats = merge_model_stats_with_summary(
            model_stats,
            compute_summary_model_stats(store, special, latest_data_date),
        )
        output["byStore"][store] = {
            "special": special,
            "dataQuality": DIFF_QUALITY_BY_STORE.get(store, {}),
            "store_coefficients": STORE_COEFFICIENTS.get(store, {}),
            "dayStats": compute_day_stats(diff_store_rows, special),
            "modelStats": model_stats,
            "nextStats": compute_next_day(diff_store_rows, special),
            "heatmap": compute_heatmap(diff_store_rows),
            "weekMatrix": compute_week_matrix(diff_store_rows),
            "dayWdayMatrix": compute_day_wday_matrix(diff_store_rows),
            "taiDetail": tai_detail,
            "dateSummary": compute_date_summary(diff_store_rows, special),
            "weekdayStats": compute_weekday_stats(diff_store_rows),
            "todayAnalysis": today_analysis,
            "targetAnalyses": {
                today_analysis["date"]: today_analysis,
                tomorrow_analysis["date"]: tomorrow_analysis,
            },
            "trendView": build_trend_view(
                store,
                store_rows,
                special,
                model_stats,
                tai_detail,
                latest_data_date,
                data_quality=DIFF_QUALITY_BY_STORE.get(store, {}),
            ),
            "evidenceBacktest": evidence_backtest,
            "holdoverRate": {
                "rate": r1(get_holdover_rate(store) * 100),
                "source": "auto",
            },
        }
        try:
            recommendation_pool.extend(
                build_store_recommendations(
                    store,
                    store_rows,
                    special,
                    tai_detail,
                    today=today,
                    evidence_backtest=evidence_backtest,
                )
            )
        except Exception as e:
            print(f"⚠️ 推薦抽出エラー({store}): {e}")
    try:
        recommendation_pool.sort(key=lambda x: (-x["score"], -x["recent_count_3m"], x["store"], x["tai"]))
        output["recommendations"] = [
            {k: v for k, v in rec.items() if k != "score"} for rec in recommendation_pool[:3]
        ]
    except Exception as e:
        print(f"⚠️ 推薦集約エラー: {e}")
        output["recommendations"] = []
    output["answer_check"] = build_answer_check(output["byStore"], today=today)
    output["store_accuracy"] = build_store_accuracy(output["byStore"], output["answer_check"])
    output["predictionAccuracy"] = {
        "overall": output["answer_check"].get("accuracy"),
        "byStore": output["store_accuracy"],
    }
    out_path = os.path.join(REPO_DIR, "data.json")
    with open(out_path, "w", encoding="utf-8-sig") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"✅ data.json出力完了: {out_path}")
