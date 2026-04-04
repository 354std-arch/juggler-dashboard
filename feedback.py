import csv
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_JSON = os.path.join(REPO_DIR, "sessions.json")
RAW_CSV = os.path.join(REPO_DIR, "raw_data.csv")
FEEDBACK_JSON = os.path.join(REPO_DIR, "feedback_data.json")
JST = timezone(timedelta(hours=9))

P_HIGH_THRESHOLD = 60.0
EMA_DECAY = 0.90
BASE_ALPHA = 1.0
BASE_BETA = 1.0

MODEL_NAME_MAP = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラー",
    "ジャグラーガールズ": "ジャグラーガールズSS",
    "スマスロ ハナビ": "スマスロハナビ",
}


def parse_num(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(",", "").replace("+", "").replace("%", "").strip()
    try:
        return float(s)
    except Exception:
        return None


def parse_syn_rate(syn_text, g, bb, rb):
    syn = None
    text = str(syn_text or "").strip()
    if "/" in text:
        right = text.split("/")[-1].strip()
        syn = parse_num(right)
    elif text:
        syn = parse_num(text)
    if syn is not None and syn > 0:
        return syn
    if g and (bb + rb) > 0:
        return g / (bb + rb)
    return None


def normalize_store(store):
    return str(store or "").replace("　", " ").strip()


def normalize_tai(tai):
    s = str(tai or "").strip()
    if not s:
        return ""
    if s.isdigit():
        return str(int(s))
    m = re.search(r"\d+", s)
    if m:
        return str(int(m.group(0)))
    return s


def normalize_model_name(model_name):
    name = str(model_name or "").replace("　", " ").strip()
    mapped = MODEL_NAME_MAP.get(name, name)
    if mapped.replace(" ", "") == "スマスロハナビ":
        return "スマスロハナビ"
    return mapped


def normalize_date_str(value):
    s = str(value or "").strip()
    if not s:
        return ""
    if "T" in s:
        s = s.split("T", 1)[0]
    s = s.replace("/", "-")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


def first_value(obj, keys):
    if not isinstance(obj, dict):
        return None
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return None


def build_session_id(session):
    key = {
        "date": session.get("date"),
        "store": session.get("store"),
        "tai": session.get("tai"),
        "model": session.get("model"),
        "g": session.get("g"),
        "big": session.get("big"),
        "reg": session.get("reg"),
        "diff": session.get("diff"),
        "bayes": session.get("bayes"),
    }
    raw = json.dumps(key, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def load_sessions():
    if not os.path.exists(SESSIONS_JSON):
        return []
    try:
        with open(SESSIONS_JSON, encoding="utf-8-sig") as f:
            parsed = json.load(f)
    except Exception as exc:
        print(f"⚠️ sessions.json読み込み失敗: {exc}")
        return []
    if not isinstance(parsed, list):
        print("⚠️ sessions.jsonが配列形式ではありません")
        return []
    sessions = []
    for row in parsed:
        date = normalize_date_str(first_value(row, ["date", "日付"]))
        store = normalize_store(first_value(row, ["store", "店舗", "店名"]))
        tai = normalize_tai(first_value(row, ["tai", "台番号"]))
        model = normalize_model_name(first_value(row, ["model", "機種", "機種名"]))
        bayes = parse_num(
            first_value(
                row,
                ["bayesProbOver4", "bayes_score", "p_setting4plus", "ベイズスコア", "ベイズ"],
            )
        )
        g = parse_num(first_value(row, ["g", "G数"]))
        big = parse_num(first_value(row, ["big", "BB"]))
        reg = parse_num(first_value(row, ["reg", "RB"]))
        diff = parse_num(first_value(row, ["diff", "差枚"]))
        if not date or not store or not tai:
            continue
        session = {
            "date": date,
            "store": store,
            "tai": tai,
            "model": model,
            "bayes": bayes,
            "g": g,
            "big": big,
            "reg": reg,
            "diff": diff,
        }
        session["session_id"] = build_session_id(session)
        sessions.append(session)
    return sessions


def default_feedback_data():
    return {
        "updated_at": "",
        "threshold_p_high": P_HIGH_THRESHOLD,
        "ema_decay": EMA_DECAY,
        "base_alpha": BASE_ALPHA,
        "base_beta": BASE_BETA,
        "alpha": BASE_ALPHA,
        "beta": BASE_BETA,
        "posterior_mean": 0.5,
        "total_hits": 0,
        "total_misses": 0,
        "processed_session_ids": [],
        "updates": [],
    }


def load_feedback_data():
    if not os.path.exists(FEEDBACK_JSON):
        return default_feedback_data()
    try:
        with open(FEEDBACK_JSON, encoding="utf-8-sig") as f:
            parsed = json.load(f)
    except Exception as exc:
        print(f"⚠️ feedback_data.json読み込み失敗: {exc}")
        return default_feedback_data()
    base = default_feedback_data()
    if not isinstance(parsed, dict):
        return base
    base.update(parsed)
    if not isinstance(base.get("processed_session_ids"), list):
        base["processed_session_ids"] = []
    if not isinstance(base.get("updates"), list):
        base["updates"] = []
    return base


def get_threshold_by_model(model):
    name = normalize_model_name(model)
    compact = name.replace(" ", "")
    if compact == "新ハナビ":
        return 148
    if compact == "スマスロハナビ":
        return 161
    if "アイムジャグラー" in name:
        return 135
    if "マイジャグラー" in name:
        return 140
    if "ファンキージャグラー" in name:
        return 138
    if "ゴーゴージャグラー" in name:
        return 136
    if "ジャグラー" in name:
        return 140
    return None


def collect_latest_raw_rows(target_keys):
    latest = {}
    if not target_keys:
        return latest
    if not os.path.exists(RAW_CSV):
        print(f"⚠️ raw_data.csvが見つかりません: {RAW_CSV}")
        return latest
    with open(RAW_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            date = normalize_date_str(row.get("日付"))
            store = normalize_store(row.get("店名"))
            tai = normalize_tai(row.get("台番号"))
            if not date or not store or not tai:
                continue
            key = (date, store, tai)
            if key not in target_keys:
                continue
            g = parse_num(row.get("G数")) or 0
            bb = parse_num(row.get("BB")) or 0
            rb = parse_num(row.get("RB")) or 0
            syn = parse_syn_rate(row.get("合成確率"), g, bb, rb)
            current = latest.get(key)
            if current is None or g > current["g"]:
                latest[key] = {
                    "date": date,
                    "store": store,
                    "tai": tai,
                    "model": normalize_model_name(row.get("機種名")),
                    "g": g,
                    "bb": bb,
                    "rb": rb,
                    "syn": syn,
                }
    return latest


def recompute_ema_posterior(updates, decay):
    alpha = BASE_ALPHA
    beta = BASE_BETA
    sorted_updates = sorted(
        [u for u in updates if isinstance(u, dict)],
        key=lambda x: (str(x.get("date", "")), str(x.get("session_id", ""))),
    )
    for u in sorted_updates:
        alpha = BASE_ALPHA + (alpha - BASE_ALPHA) * decay
        beta = BASE_BETA + (beta - BASE_BETA) * decay
        outcome = str(u.get("outcome", "")).lower()
        if outcome == "hit":
            alpha += 1.0
        elif outcome == "miss":
            beta += 1.0
    posterior = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
    return alpha, beta, posterior


def main():
    now = datetime.now(JST)
    sessions = load_sessions()
    feedback = load_feedback_data()
    decay = parse_num(feedback.get("ema_decay")) or EMA_DECAY

    processed_ids = set(str(x) for x in feedback.get("processed_session_ids", []))
    target_sessions = [s for s in sessions if s["session_id"] not in processed_ids]
    target_keys = {(s["date"], s["store"], s["tai"]) for s in target_sessions}
    raw_lookup = collect_latest_raw_rows(target_keys)

    updates = [u for u in feedback.get("updates", []) if isinstance(u, dict)]
    new_updates = []
    new_processed_ids = set()
    pending_count = 0
    skipped_low_p_count = 0
    skipped_unsupported_count = 0

    for session in target_sessions:
        key = (session["date"], session["store"], session["tai"])
        matched = raw_lookup.get(key)
        if matched is None:
            pending_count += 1
            continue

        bayes = session.get("bayes")
        if bayes is None:
            new_processed_ids.add(session["session_id"])
            continue
        if bayes < P_HIGH_THRESHOLD:
            skipped_low_p_count += 1
            new_processed_ids.add(session["session_id"])
            continue

        model = matched.get("model") or session.get("model")
        threshold = get_threshold_by_model(model)
        syn_rate = matched.get("syn")
        if threshold is None:
            skipped_unsupported_count += 1
            new_processed_ids.add(session["session_id"])
            continue
        if syn_rate is None or syn_rate <= 0:
            pending_count += 1
            continue

        is_good = syn_rate <= threshold
        new_updates.append(
            {
                "session_id": session["session_id"],
                "date": session["date"],
                "store": session["store"],
                "tai": session["tai"],
                "session_model": session.get("model"),
                "final_model": model,
                "bayes_prob_over4": round(float(bayes), 1),
                "syn_rate": round(float(syn_rate), 4),
                "threshold": threshold,
                "is_good_result": bool(is_good),
                "outcome": "hit" if is_good else "miss",
            }
        )
        new_processed_ids.add(session["session_id"])

    if new_updates:
        updates.extend(new_updates)

    alpha, beta, posterior = recompute_ema_posterior(updates, decay)
    total_hits = len([u for u in updates if str(u.get("outcome", "")).lower() == "hit"])
    total_misses = len([u for u in updates if str(u.get("outcome", "")).lower() == "miss"])

    feedback_out = {
        "updated_at": now.strftime("%Y-%m-%d"),
        "threshold_p_high": P_HIGH_THRESHOLD,
        "ema_decay": decay,
        "base_alpha": BASE_ALPHA,
        "base_beta": BASE_BETA,
        "alpha": round(alpha, 6),
        "beta": round(beta, 6),
        "posterior_mean": round(posterior, 6),
        "total_hits": total_hits,
        "total_misses": total_misses,
        "processed_session_ids": sorted(processed_ids | new_processed_ids),
        "updates": updates,
        "last_run": {
            "sessions_total": len(sessions),
            "sessions_target": len(target_sessions),
            "new_updates": len(new_updates),
            "pending_sessions": pending_count,
            "skipped_low_p": skipped_low_p_count,
            "skipped_unsupported_model": skipped_unsupported_count,
        },
    }

    with open(FEEDBACK_JSON, "w", encoding="utf-8-sig") as f:
        json.dump(feedback_out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("=== feedback.py 完了 ===")
    print(f"sessions={len(sessions)} target={len(target_sessions)} new_updates={len(new_updates)}")
    print(f"posterior_mean={feedback_out['posterior_mean']} alpha={feedback_out['alpha']} beta={feedback_out['beta']}")


if __name__ == "__main__":
    main()
