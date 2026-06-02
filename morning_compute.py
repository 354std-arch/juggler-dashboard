import csv
import json
import math
import os
import argparse
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from compute import (
        DEFAULT_SPECIAL_DAYS,
        load_store_configs,
        normalize_store_name,
    )
except Exception:
    DEFAULT_SPECIAL_DAYS = [1, 11, 21, 31]

    def normalize_store_name(store_name):
        return str(store_name or "").strip()

    def load_store_configs():
        return {"specialByStore": {}}

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV = os.path.join(REPO_DIR, "raw_data.csv")
OUT_JSON = os.path.join(REPO_DIR, "morning_data.json")
PRECOMPUTED_JSON = os.path.join(REPO_DIR, "data.json")
JST = timezone(timedelta(hours=9))

# compute.py と同等の正規化ロジック/設定値を流用
MODEL_NAME_MAP = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラー",
    "ジャグラーガールズ": "ジャグラーガールズSS",
    "スマスロ ハナビ": "スマスロハナビ",
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
INSTALL_SEGMENT_GAP_DAYS = 21
MAX_MORNING_SOURCE_LAG_DAYS = 2
_SPECIAL_BY_STORE_CACHE = None

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
    compact = mapped.replace(" ", "")
    for tokens, canonical in SMART_SLOT_MODEL_PATTERNS:
        if all(token in compact for token in tokens):
            return canonical
    return mapped


def supports_setting_analysis(model):
    return model in MODEL_SETTINGS


def supports_diff_analysis(model):
    return model in MODEL_SETTINGS or model in SMART_SLOT_MODELS


def classify_diff_label(total_g, diff):
    if total_g >= 3500 and diff >= 2500:
        return "強上候補"
    if total_g >= 2500 and diff >= 800:
        return "上候補"
    if total_g < 1500:
        return "除外寄り"
    if diff <= -1500:
        return "除外寄り"
    return "中間"


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


def load_store_special_map():
    global _SPECIAL_BY_STORE_CACHE
    if _SPECIAL_BY_STORE_CACHE is not None:
        return _SPECIAL_BY_STORE_CACHE

    try:
        config = load_store_configs()
        raw_specials = config.get("specialByStore", {}) if isinstance(config, dict) else {}
    except Exception:
        raw_specials = {}

    specials = {}
    for store, days in (raw_specials or {}).items():
        key = normalize_store_name(store)
        if not key or not isinstance(days, list):
            continue
        values = []
        for value in days:
            try:
                day = int(value)
            except Exception:
                continue
            if 1 <= day <= 31:
                values.append(day)
        if values:
            specials[key] = sorted(set(values))

    _SPECIAL_BY_STORE_CACHE = specials
    return _SPECIAL_BY_STORE_CACHE


def is_generic_special_day(day):
    day_int = int(day)
    text = str(day_int)
    is_repdigit = len(text) >= 2 and len(set(text)) == 1
    return (day_int % 10 in (0, 7)) or is_repdigit


def is_store_special_day(store, day, special_by_store=None):
    try:
        day_int = int(day)
    except Exception:
        return False
    store_key = normalize_store_name(store)
    specials = special_by_store if isinstance(special_by_store, dict) else load_store_special_map()
    store_days = specials.get(store_key, DEFAULT_SPECIAL_DAYS)
    return day_int in set(store_days)


def is_special_day(day, store=None, special_by_store=None):
    if store:
        return is_store_special_day(store, day, special_by_store)
    return is_generic_special_day(day)


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


def date_only(value):
    if value is None:
        return None
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            return None
    return None


def build_payload_meta(now_jst, source_date):
    target_date = now_jst.date()
    source_day = date_only(source_date)
    source_ymd = source_day.strftime("%Y-%m-%d") if source_day else None
    lag_days = (target_date - source_day).days if source_day else None
    if lag_days is None:
        freshness_guard = {
            "actionable": False,
            "level": "unknown",
            "label": "鮮度不明",
            "message": "元データの日付を確認できないため、朝候補は参考扱いにします。",
        }
    elif lag_days > MAX_MORNING_SOURCE_LAG_DAYS:
        freshness_guard = {
            "actionable": False,
            "level": "stale",
            "label": f"{lag_days}日前データ",
            "message": f"元データが{lag_days}日前です。入替・傾向変化の影響が大きいため、朝候補は参考扱いにします。",
        }
    else:
        freshness_guard = {
            "actionable": True,
            "level": "fresh",
            "label": "鮮度OK",
            "message": "",
        }

    return {
        "generated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        # Backward compatible: existing UI/code treats data_date as the prediction target date.
        "data_date": target_date.strftime("%Y-%m-%d"),
        "target_date": target_date.strftime("%Y-%m-%d"),
        "source_data_date": source_ymd,
        "source_data_lag_days": lag_days,
        "freshness_guard": freshness_guard,
    }


def normalize_date_key(value):
    dt = parse_date_value(value)
    if dt is not None:
        return dt.strftime("%Y-%m-%d")
    text = str(value or "").strip()
    return text[:10] if len(text) >= 10 else text


def unique_items(values, limit=None):
    out = []
    seen = set()
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
        if limit is not None and len(out) >= limit:
            break
    return out


def get_target_analysis(store_data, target_ymd):
    analyses = store_data.get("targetAnalyses") if isinstance(store_data, dict) else {}
    if isinstance(analyses, dict) and target_ymd in analyses:
        return analyses[target_ymd] or {}

    today_analysis = store_data.get("todayAnalysis") if isinstance(store_data, dict) else None
    if isinstance(today_analysis, dict):
        today_ymd = normalize_date_key(
            today_analysis.get("date")
            or today_analysis.get("targetDate")
            or today_analysis.get("data_date")
        )
        if today_ymd == target_ymd:
            return today_analysis
    return None


def load_evidence_guards(target_ymd):
    try:
        with open(PRECOMPUTED_JSON, "r", encoding="utf-8-sig") as f:
            precomputed = json.load(f)
    except Exception:
        return {}

    guards = {}
    by_store = precomputed.get("byStore", {}) if isinstance(precomputed, dict) else {}
    for store, store_data in by_store.items():
        if not isinstance(store_data, dict):
            continue
        analysis = get_target_analysis(store_data, target_ymd) or {}
        backtest = store_data.get("evidenceBacktest", {}) if isinstance(store_data, dict) else {}
        summary = backtest.get("summary", {}) if isinstance(backtest, dict) else {}
        decision = analysis.get("evidenceDecision") or summary.get("decision") or None
        targets = analysis.get("topTargets") if isinstance(analysis.get("topTargets"), list) else []
        target_tais = set()
        target_lookup = {}
        for target in targets:
            if not isinstance(target, dict):
                continue
            try:
                tai = int(target.get("tai", target.get("taiNum")))
            except Exception:
                continue
            target_tais.add(tai)
            target_lookup[tai] = target

        if isinstance(decision, dict) and decision.get("actionable") is False:
            actionable = False
        elif target_tais:
            actionable = True
        elif isinstance(decision, dict):
            actionable = decision.get("actionable") is not False
        else:
            actionable = False

        label = decision.get("label") if isinstance(decision, dict) else ""
        detail = decision.get("message") if isinstance(decision, dict) else ""
        if not label:
            label = "検証候補あり" if target_tais else "検証未接続"
        if not detail:
            detail = f"検証を通った候補 {len(target_tais)}台" if target_tais else "この店舗の検証済み根拠はまだ表示できません。"

        guards[normalize_store_name(store)] = {
            "actionable": actionable,
            "label": label,
            "detail": detail,
            "target_tais": sorted(target_tais),
            "target_lookup": target_lookup,
        }
    return guards


def summarize_verified_target(target):
    if not isinstance(target, dict):
        return [], [], []
    evidence_rows = []
    for item in (target.get("evidence") or [])[:3]:
        if not isinstance(item, dict):
            continue
        validation = item.get("validation") if isinstance(item.get("validation"), dict) else {}
        verdict = item.get("validationVerdict") if isinstance(item.get("validationVerdict"), dict) else {}
        evidence_rows.append({
            "label": item.get("label") or item.get("key") or "検証根拠",
            "lift": validation.get("lift", item.get("lift")),
            "avg": validation.get("avg", item.get("avg")),
            "count": validation.get("count", item.get("count")),
            "plusRate": validation.get("plusRate"),
            "topHitRate": validation.get("topHitRate"),
            "verdict": verdict.get("label") or "予測実績あり",
        })
    hall_evidence_rows = []
    for item in (target.get("hallEvidence") or [])[:2]:
        if not isinstance(item, dict):
            continue
        validation = item.get("validation") if isinstance(item.get("validation"), dict) else {}
        verdict = item.get("validationVerdict") if isinstance(item.get("validationVerdict"), dict) else {}
        hall_evidence_rows.append({
            "label": item.get("label") or item.get("key") or "ホール図根拠",
            "lift": validation.get("lift", item.get("lift")),
            "avg": validation.get("avg", item.get("avg")),
            "count": validation.get("count", item.get("count")),
            "plusRate": validation.get("plusRate"),
            "topHitRate": validation.get("topHitRate"),
            "verdict": verdict.get("label") or "予測実績あり",
        })
    caution_rows = []
    for item in (target.get("cautions") or [])[:2]:
        if isinstance(item, dict):
            label = item.get("label") or "注意"
            message = item.get("message") or ""
            caution_rows.append(f"{label}: {message}" if message else str(label))
        else:
            caution_rows.append(str(item))
    return evidence_rows, caution_rows, hall_evidence_rows


def apply_evidence_guards(stores_payload, target_ymd):
    guards = load_evidence_guards(target_ymd)
    if not guards:
        return stores_payload

    for store, payload in stores_payload.items():
        guard = guards.get(normalize_store_name(store))
        if not guard or not isinstance(payload, dict):
            continue
        target_tais = set(guard.get("target_tais") or [])
        target_lookup = guard.get("target_lookup") or {}
        payload["evidence_guard"] = {
            "actionable": bool(guard.get("actionable")),
            "label": guard.get("label", ""),
            "detail": guard.get("detail", ""),
            "target_tais": sorted(target_tais),
        }
        candidates = payload.get("candidates")
        if not isinstance(candidates, list):
            continue

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            try:
                tai = int(candidate.get("tai"))
            except Exception:
                tai = None
            is_verified_target = tai in target_tais
            candidate["verified_target"] = bool(is_verified_target)
            if is_verified_target:
                target = target_lookup.get(tai) or {}
                evidence_rows, caution_rows, hall_evidence_rows = summarize_verified_target(target)
                candidate["verified_rank"] = target.get("rank") or "検証候補"
                candidate["verified_score"] = target.get("totalScore")
                candidate["verified_evidence"] = evidence_rows
                if target.get("smartTreatment"):
                    candidate["smart_treatment"] = target.get("smartTreatment")
                if hall_evidence_rows:
                    candidate["verified_hall_evidence"] = hall_evidence_rows
                if caution_rows:
                    candidate["verified_cautions"] = caution_rows
                if target.get("rank") == "本命":
                    candidate["action"] = "main"
                    candidate["action_label"] = "検証本命"
                else:
                    candidate["action"] = "candidate"
                    candidate["action_label"] = "検証候補"
                candidate["actionable"] = True

            if guard.get("actionable") is False and not is_verified_target:
                note = f"店舗検証: {guard.get('label', '検証弱め')}。{guard.get('detail', '過去検証では候補を強く出せません。')}"
                candidate["warnings"] = unique_items([*(candidate.get("warnings") or []), note], limit=3)
                candidate["cautions"] = unique_items([*(candidate.get("cautions") or []), "店舗検証が弱い"], limit=4)
                candidate["action"] = "watch"
                candidate["action_label"] = "参考"
                candidate["actionable"] = False

        candidates.sort(key=morning_candidate_sort_key, reverse=True)
    return stores_payload


def apply_freshness_guard(stores_payload, payload_meta):
    guard = payload_meta.get("freshness_guard") if isinstance(payload_meta, dict) else None
    if not isinstance(guard, dict) or guard.get("actionable") is not False:
        return stores_payload
    note = guard.get("message") or "元データが古いため、朝候補は参考扱いにします。"
    for payload in stores_payload.values():
        if not isinstance(payload, dict):
            continue
        payload["freshness_guard"] = guard
        candidates = payload.get("candidates")
        if not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            candidate["stale_source"] = True
            candidate["warnings"] = unique_items([*(candidate.get("warnings") or []), f"データ鮮度: {note}"], limit=3)
            candidate["cautions"] = unique_items([*(candidate.get("cautions") or []), "データ鮮度が古い"], limit=4)
            candidate["action"] = "watch"
            candidate["action_label"] = "参考"
            candidate["actionable"] = False
    return stores_payload


def classify_morning_candidate(total_score, store_score, store_sample, model_score, model_sample, tai_score, tai_sample, warnings):
    cautions = [str(w) for w in (warnings or []) if str(w).strip()]
    if store_sample < 30:
        cautions.append("店条件サンプル不足")
    if model_sample < 20:
        cautions.append("機種条件サンプル不足")
    if tai_sample < 20:
        cautions.append("台番号サンプル不足")
    if store_score < 0.2:
        cautions.append("店条件が弱い")
    if model_score < 0.2:
        cautions.append("機種条件が弱い")

    enough_sample = store_sample >= 30 and model_sample >= 20 and tai_sample >= 20
    if (
        enough_sample
        and total_score >= 0.38
        and store_score >= 0.28
        and model_score >= 0.32
        and tai_score >= 0.18
    ):
        return {
            "action": "main",
            "action_label": "本命",
            "actionable": True,
            "cautions": cautions[:4],
        }
    if (
        enough_sample
        and total_score >= 0.30
        and store_score >= 0.20
        and (model_score >= 0.25 or tai_score >= 0.22)
    ):
        return {
            "action": "candidate",
            "action_label": "候補",
            "actionable": True,
            "cautions": cautions[:4],
        }
    return {
        "action": "watch",
        "action_label": "観察",
        "actionable": False,
        "cautions": cautions[:4],
    }


def morning_candidate_sort_key(row):
    action_priority = {"main": 2, "candidate": 1, "watch": 0}
    verified_priority = 1 if row.get("verified_target") else 0
    return (verified_priority, action_priority.get(row.get("action"), 0), float(row.get("score") or 0))


def classify_morning_model_sample(sample):
    try:
        n = int(sample)
    except (TypeError, ValueError):
        n = 0
    if n >= 50:
        return {"sample_label": "通常評価", "sample_strength": "high", "sample_usable": True}
    if n >= 20:
        return {"sample_label": "参考", "sample_strength": "medium", "sample_usable": True}
    return {"sample_label": "薄い", "sample_strength": "thin", "sample_usable": False}


def format_morning_model_reason(model, upper_rate, sample):
    metric = "上候補以上率" if supports_setting_analysis(model) else "強挙動率"
    return f"{metric}{upper_rate:.0%}({sample}件)"


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


def classify_coverage_level(day_count, row_count):
    if day_count >= 120 and row_count >= 300:
        return {"label": "長期", "strength": "high"}
    if day_count >= 45 and row_count >= 100:
        return {"label": "中期", "strength": "medium"}
    if day_count >= 15 and row_count >= 30:
        return {"label": "短期", "strength": "low"}
    return {"label": "薄い", "strength": "thin"}


def build_model_coverage_from_rows(rows):
    buckets = {}
    for r in rows:
        store = str(r.get("store") or "").strip()
        model = str(r.get("model") or "").strip()
        dt = r.get("date")
        tai = r.get("tai")
        if not store or not model or dt is None:
            continue
        bucket = buckets.setdefault(
            (store, model),
            {"first": None, "last": None, "rows": 0, "days": set(), "tais": set()},
        )
        bucket["rows"] += 1
        bucket["days"].add(dt.date())
        try:
            bucket["tais"].add(int(tai))
        except Exception:
            pass
        if bucket["first"] is None or dt < bucket["first"]:
            bucket["first"] = dt
        if bucket["last"] is None or dt > bucket["last"]:
            bucket["last"] = dt

    coverage = defaultdict(dict)
    for (store, model), bucket in buckets.items():
        day_count = len(bucket["days"])
        row_count = int(bucket["rows"])
        level = classify_coverage_level(day_count, row_count)
        coverage[store][model] = {
            "first_date": bucket["first"].strftime("%Y-%m-%d") if bucket["first"] else None,
            "last_date": bucket["last"].strftime("%Y-%m-%d") if bucket["last"] else None,
            "row_count": row_count,
            "day_count": day_count,
            "tai_count": len(bucket["tais"]),
            "coverage_label": level["label"],
            "coverage_strength": level["strength"],
        }
    return {store: dict(models) for store, models in coverage.items()}


def build_model_coverage_from_df(df):
    if df.empty:
        return {}

    coverage = defaultdict(dict)
    grouped = (
        df.groupby(["store", "model"], sort=False)
        .agg(
            first_date=("date", "min"),
            last_date=("date", "max"),
            row_count=("date", "size"),
            day_count=("date", lambda s: s.dt.date.nunique()),
            tai_count=("tai", "nunique"),
        )
        .reset_index()
    )
    for r in grouped.itertuples(index=False):
        day_count = int(r.day_count)
        row_count = int(r.row_count)
        level = classify_coverage_level(day_count, row_count)
        coverage[str(r.store)][str(r.model)] = {
            "first_date": r.first_date.strftime("%Y-%m-%d") if pd.notna(r.first_date) else None,
            "last_date": r.last_date.strftime("%Y-%m-%d") if pd.notna(r.last_date) else None,
            "row_count": row_count,
            "day_count": day_count,
            "tai_count": int(r.tai_count),
            "coverage_label": level["label"],
            "coverage_strength": level["strength"],
        }
    return {store: dict(models) for store, models in coverage.items()}


def read_labeled_rows_fallback():
    special_by_store = load_store_special_map()
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

            if not supports_diff_analysis(normalized_model):
                if normalized_model:
                    unsupported_models.add(normalized_model)
                continue

            tai = int(tai_raw)
            if supports_setting_analysis(normalized_model):
                syn_threshold = MODEL_SYN_T4[normalized_model]
                rb_threshold = MODEL_RB_T4[normalized_model]
                label = classify_label(total_g, bb, rb, diff, syn_threshold, rb_threshold)
                analysis_mode = "setting"
            else:
                label = classify_diff_label(total_g, diff)
                analysis_mode = "diff"

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
                    "is_special": is_store_special_day(raw_store, dt.day, special_by_store),
                    "label": label,
                    "analysis_mode": analysis_mode,
                }
            )

    return rows, normalized_models, sorted(unsupported_models)


def read_labeled_rows():
    if pd is None:
        return read_labeled_rows_fallback()

    special_by_store = load_store_special_map()
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

        supported_models = set(MODEL_SETTINGS) | SMART_SLOT_MODELS
        supported_mask = chunk["model"].isin(supported_models)
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
        chunk["is_special"] = [
            is_store_special_day(store, day, special_by_store)
            for store, day in zip(chunk["store"], chunk["day"])
        ]

        bonus_total = chunk["bb"] + chunk["rb"]
        chunk["syn_ratio"] = (chunk["total_g"] / bonus_total).where(bonus_total > 0)
        chunk["rb_ratio"] = (chunk["total_g"] / chunk["rb"]).where(chunk["rb"] > 0)
        chunk["bb_ratio"] = (chunk["total_g"] / chunk["bb"]).where(chunk["bb"] > 0)

        chunk["analysis_mode"] = chunk["model"].map(
            lambda model: "setting" if supports_setting_analysis(model) else "diff"
        )
        setting_mask = chunk["analysis_mode"] == "setting"
        chunk["syn_threshold"] = chunk["model"].map(MODEL_SYN_T4)
        chunk["rb_threshold"] = chunk["model"].map(MODEL_RB_T4)

        cond1 = (
            setting_mask
            &
            (chunk["total_g"] >= 5000)
            & (chunk["rb_ratio"] <= chunk["rb_threshold"])
            & (chunk["syn_ratio"] <= chunk["syn_threshold"])
        )
        cond2 = (
            setting_mask
            &
            (chunk["total_g"] >= 3500)
            & (
                (chunk["rb_ratio"] <= chunk["rb_threshold"])
                | (chunk["syn_ratio"] <= chunk["syn_threshold"])
            )
        )
        rb_bad_or_none = chunk["rb_ratio"].isna() | (chunk["rb_ratio"] > chunk["rb_threshold"])
        syn_bad_or_none = chunk["syn_ratio"].isna() | (chunk["syn_ratio"] > chunk["syn_threshold"])
        cond3 = (
            setting_mask
            & (
                (chunk["total_g"] < 2500)
                | ((chunk["bb"] > 0) & (chunk["bb_ratio"] < 240) & rb_bad_or_none)
                | ((chunk["diff"] > 0) & rb_bad_or_none & syn_bad_or_none)
            )
        )

        chunk["label"] = "中間"
        chunk.loc[cond3, "label"] = "除外寄り"
        chunk.loc[cond2, "label"] = "上候補"
        chunk.loc[cond1, "label"] = "強上候補"
        diff_mode_mask = chunk["analysis_mode"] == "diff"
        chunk.loc[diff_mode_mask & (chunk["total_g"] >= 2500) & (chunk["diff"] >= 800), "label"] = "上候補"
        chunk.loc[diff_mode_mask & (chunk["total_g"] >= 3500) & (chunk["diff"] >= 2500), "label"] = "強上候補"
        chunk.loc[diff_mode_mask & ((chunk["total_g"] < 1500) | (chunk["diff"] <= -1500)), "label"] = "除外寄り"

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
                    "analysis_mode",
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
    special_by_store = load_store_special_map()
    payload_meta = build_payload_meta(now_jst, max((r["date"] for r in rows), default=None))
    model_coverage = build_model_coverage_from_rows(rows)

    if not rows:
        return {
            **payload_meta,
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
        target_special = is_store_special_day(store, now_jst.day, special_by_store)

        add_rate_stat(store_day, (store, weekday, is_special), label)
        add_rate_stat(store_model_day, (store, model, weekday, is_special), label)
        add_rate_stat(store_tail, (store, tai % 10), label)

        if weekday == today_weekday and is_special == target_special:
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
        target_special = is_store_special_day(store, now_jst.day, special_by_store)
        if weekday != today_weekday or is_special != target_special:
            continue
        total = stat["total"]
        upper_rate = (stat["upper"] / total) if total else 0.0
        sample_meta = classify_morning_model_sample(total)
        model_rankings[store].append(
            {
                "model": model,
                "analysis_mode": "setting" if supports_setting_analysis(model) else "diff",
                "score": round(upper_rate if sample_meta["sample_usable"] else upper_rate * 0.25, 6),
                "raw_score": round(upper_rate, 6),
                "reason": format_morning_model_reason(model, upper_rate, total),
                "sample": total,
                **sample_meta,
                "coverage": model_coverage.get(store, {}).get(model, {}),
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
        target_special = is_store_special_day(store, now_jst.day, special_by_store)
        tai_rows.sort(key=lambda x: x["date"])
        last_change_date = None
        prev_model = None
        prev_date = None
        for r in tai_rows:
            gap_days = (r["date"].date() - prev_date.date()).days if prev_date is not None else 0
            if prev_model is not None and (
                r["model"] != prev_model or gap_days > INSTALL_SEGMENT_GAP_DAYS
            ):
                last_change_date = r["date"]
            prev_model = r["model"]
            prev_date = r["date"]

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

        store_day_score, store_day_sample = store_day_lookup.get((store, today_weekday, target_special), (0.0, 0))
        model_score, model_sample = model_day_lookup.get((store, recent_model, today_weekday, target_special), (0.0, 0))
        total_score = 0.35 * store_day_score + 0.40 * model_score + 0.25 * tai_upper_rate

        warnings = []
        if sample < 10:
            warnings.append("サンプル数が10件未満")
        if last_change_date is not None:
            days_since_change = (today_date - last_change_date.date()).days
            if days_since_change <= 90:
                warnings.append(f"台番号変動あり（直近{days_since_change}日）")
        decision = classify_morning_candidate(
            total_score,
            store_day_score,
            store_day_sample,
            model_score,
            model_sample,
            tai_upper_rate,
            sample,
            warnings,
        )

        candidate_by_store[store].append(
            {
                "tai": int(tai),
                "model": recent_model,
                "analysis_mode": "setting" if supports_setting_analysis(recent_model) else "diff",
                "model_coverage": model_coverage.get(store, {}).get(recent_model, {}),
                "score": round(total_score, 6),
                "action": decision["action"],
                "action_label": decision["action_label"],
                "actionable": decision["actionable"],
                "reasons": [
                    f"{'上候補以上率' if supports_setting_analysis(recent_model) else '強挙動率'}{tai_upper_rate:.0%}",
                    f"サンプル{sample}件",
                    f"推移{trend}",
                ][:3],
                "warnings": warnings[:2],
                "cautions": decision["cautions"],
            }
        )

    for store in list(candidate_by_store.keys()):
        candidate_by_store[store].sort(key=morning_candidate_sort_key, reverse=True)

    stores_payload = {}
    store_names = sorted({r["store"] for r in rows})
    for store in store_names:
        target_special = is_store_special_day(store, now_jst.day, special_by_store)
        today_score, today_sample = store_day_lookup.get((store, today_weekday, target_special), (0.0, 0))
        if today_score >= 0.4:
            today_label = "強い"
        elif today_score < 0.2:
            today_label = "弱い"
        else:
            today_label = "普通"

        counter = today_label_counter.get(store, Counter())
        mode_label = counter.most_common(1)[0][0] if counter else "データ不足"
        stores_payload[store] = {
            "target_is_special": bool(target_special),
            "target_day_type": "特定日" if target_special else "通常日",
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
            "model_coverage": model_coverage.get(store, {}),
        }

    apply_evidence_guards(stores_payload, payload_meta["target_date"])
    apply_freshness_guard(stores_payload, payload_meta)

    return {
        **payload_meta,
        "normalized_models": dict(sorted(normalized_models.items())),
        "unsupported_models": sorted(unsupported_models),
        "stores": stores_payload,
    }


def build_payload(df, normalized_models, unsupported_models):
    now_jst = datetime.now(JST)
    today_date = now_jst.date()
    today_weekday = now_jst.weekday()
    special_by_store = load_store_special_map()
    payload_meta = build_payload_meta(now_jst, None if df.empty else df["date"].max())
    model_coverage = build_model_coverage_from_df(df)

    if df.empty:
        return {
            **payload_meta,
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
    store_names_for_target = sorted(df["store"].dropna().astype(str).unique().tolist())
    target_special_by_store = {
        store: is_store_special_day(store, now_jst.day, special_by_store)
        for store in store_names_for_target
    }

    df_sorted = df.sort_values(["store", "tai", "date"]).copy()
    df_sorted["prev_model"] = df_sorted.groupby(["store", "tai"])["model"].shift(1)
    df_sorted["prev_date"] = df_sorted.groupby(["store", "tai"])["date"].shift(1)
    df_sorted["gap_days"] = df_sorted["date"].sub(df_sorted["prev_date"]).dt.days.fillna(0)
    df_sorted["segment_changed"] = (
        df_sorted["prev_model"].notna()
        & (
            (df_sorted["model"] != df_sorted["prev_model"])
            | (df_sorted["gap_days"] > INSTALL_SEGMENT_GAP_DAYS)
        )
    )
    last_change = (
        df_sorted.loc[df_sorted["segment_changed"], ["store", "tai", "date"]]
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

    target_special_series = df["store"].map(
        lambda store: target_special_by_store.get(
            str(store), is_store_special_day(store, now_jst.day, special_by_store)
        )
    )
    today_rows = df.loc[
        (df["weekday"] == today_weekday)
        & (df["is_special"].astype(bool) == target_special_series.astype(bool))
    ]
    today_label_mode = (
        today_rows.groupby("store")["label"].agg(lambda s: s.value_counts().idxmax()).to_dict()
    )

    model_today_mask = store_model_day_stats.apply(
        lambda r: int(r["weekday"]) == today_weekday
        and bool(r["is_special"]) == target_special_by_store.get(
            str(r["store"]), is_store_special_day(r["store"], now_jst.day, special_by_store)
        ),
        axis=1,
    )
    model_today = store_model_day_stats.loc[model_today_mask].copy()
    model_rankings = {}
    for store, rows in model_today.groupby("store", sort=False):
        rows = rows.copy()
        rows["sample_meta"] = rows["sample"].map(classify_morning_model_sample)
        rows["ranking_score"] = rows.apply(
            lambda r: float(r.upper_rate) if r["sample_meta"]["sample_usable"] else float(r.upper_rate) * 0.25,
            axis=1,
        )
        sorted_rows = rows.sort_values("ranking_score", ascending=False).head(5)
        ranking = []
        for r in sorted_rows.itertuples(index=False):
            sample_meta = r.sample_meta
            ranking.append(
                {
                    "model": r.model,
                    "analysis_mode": "setting" if supports_setting_analysis(r.model) else "diff",
                    "score": round(float(r.ranking_score), 6),
                    "raw_score": round(float(r.upper_rate), 6),
                    "reason": format_morning_model_reason(r.model, float(r.upper_rate), int(r.sample)),
                    "sample": int(r.sample),
                    **sample_meta,
                    "coverage": model_coverage.get(store, {}).get(r.model, {}),
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
        target_special = target_special_by_store.get(
            store, is_store_special_day(store, now_jst.day, special_by_store)
        )
        store_day_score, store_day_sample = store_day_lookup.get((store, today_weekday, target_special), (0.0, 0))
        candidates = []
        for r in rows.itertuples(index=False):
            tai_key = (store, int(r.tai))
            model = recent_model_by_tai.get(tai_key, "")
            model_score, model_sample = model_day_lookup.get((store, model, today_weekday, target_special), (0.0, 0))
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

            tai_metric = "上候補以上率" if supports_setting_analysis(model) else "強挙動率"
            reasons = [
                f"{tai_metric}{tai_score:.0%}",
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
            decision = classify_morning_candidate(
                total_score,
                store_day_score,
                store_day_sample,
                model_score,
                model_sample,
                tai_score,
                int(r.sample),
                warnings,
            )

            candidates.append(
                {
                    "tai": int(r.tai),
                    "model": model,
                    "analysis_mode": "setting" if supports_setting_analysis(model) else "diff",
                    "model_coverage": model_coverage.get(store, {}).get(model, {}),
                    "score": round(total_score, 6),
                    "action": decision["action"],
                    "action_label": decision["action_label"],
                    "actionable": decision["actionable"],
                    "reasons": reasons,
                    "warnings": warnings[:2],
                    "cautions": decision["cautions"],
                }
            )

        candidates.sort(key=morning_candidate_sort_key, reverse=True)
        candidate_by_store[store] = candidates

    stores_payload = {}
    store_names = store_names_for_target
    for store in store_names:
        target_special = target_special_by_store.get(
            store, is_store_special_day(store, now_jst.day, special_by_store)
        )
        today_score, today_sample = store_day_lookup.get((store, today_weekday, target_special), (0.0, 0))
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
            "target_is_special": bool(target_special),
            "target_day_type": "特定日" if target_special else "通常日",
            "today_score": round(float(today_score), 6),
            "today_label": today_label,
            "today_reason": today_reason,
            "model_ranking": model_rankings.get(store, []),
            "tail_ranking": tail_rankings.get(store, []),
            "candidates": candidate_by_store.get(store, []),
            "model_coverage": model_coverage.get(store, {}),
        }

    apply_evidence_guards(stores_payload, payload_meta["target_date"])
    apply_freshness_guard(stores_payload, payload_meta)

    return {
        **payload_meta,
        "normalized_models": dict(sorted(normalized_models.items())),
        "unsupported_models": sorted(unsupported_models),
        "stores": stores_payload,
    }


def main():
    parser = argparse.ArgumentParser(description="morning_data.json を生成します。")
    parser.add_argument(
        "--archive",
        action="store_true",
        help="日付付きのアーカイブJSON（morning_data_YYYYMMDD.json）も生成する",
    )
    args = parser.parse_args()

    data, normalized_models, unsupported_models = read_labeled_rows()
    if pd is None:
        payload = build_payload_fallback(data, normalized_models, unsupported_models)
    else:
        payload = build_payload(data, normalized_models, unsupported_models)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    if args.archive:
        data_date = str(payload.get("data_date") or datetime.now(JST).strftime("%Y-%m-%d"))
        archive_suffix = data_date.replace("-", "")
        out_archive_json = os.path.join(REPO_DIR, f"morning_data_{archive_suffix}.json")
        with open(out_archive_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"generated: {out_archive_json}")

    print(f"generated: {OUT_JSON}")
    print(f"stores: {len(payload.get('stores', {}))}")


if __name__ == "__main__":
    main()
