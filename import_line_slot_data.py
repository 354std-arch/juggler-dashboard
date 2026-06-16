import argparse
import csv
import os
from datetime import datetime


REPO_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(REPO_DIR, "line_slot_data.csv")

CSV_HEADER = [
    "date",
    "store",
    "rate",
    "model",
    "machine_no",
    "total_game",
    "big",
    "reg",
    "at_art",
    "combined_rate",
    "at_art_rate",
    "last_game",
    "max_payout",
    "graph_trend",
    "graph_movement",
    "graph_note",
    "source",
    "note",
]


def normalize_date(value):
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    raise ValueError("--date は YYYY-MM-DD 形式で指定してください")


def load_existing_rows():
    if not os.path.exists(OUT_CSV):
        return []
    with open(OUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(rows):
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in CSV_HEADER})


def upsert_row(row):
    rows = load_existing_rows()
    key = (row["date"], row["store"], row["machine_no"])
    replaced = False
    out = []
    for existing in rows:
        existing_key = (
            str(existing.get("date", "")).strip(),
            str(existing.get("store", "")).strip(),
            str(existing.get("machine_no", "")).strip(),
        )
        if existing_key == key:
            out.append(row)
            replaced = True
        else:
            out.append(existing)
    if not replaced:
        out.append(row)
    out.sort(key=lambda r: (r.get("date", ""), r.get("store", ""), int(str(r.get("machine_no") or "0"))))
    write_rows(out)
    return replaced


def main():
    parser = argparse.ArgumentParser(description="LINE公開の台データを line_slot_data.csv に登録します。")
    parser.add_argument("--date", required=True, help="データ日 YYYY-MM-DD")
    parser.add_argument("--store", required=True, help="店舗名")
    parser.add_argument("--rate", default="", help="例: 21.7スロ")
    parser.add_argument("--model", required=True, help="機種名")
    parser.add_argument("--machine-no", required=True, help="台番号")
    parser.add_argument("--total-game", default="", help="累計ゲーム")
    parser.add_argument("--big", default="")
    parser.add_argument("--reg", default="")
    parser.add_argument("--at-art", default="")
    parser.add_argument("--bonus-today", default="", help="台一覧の本日BONUS")
    parser.add_argument("--bonus-1d", default="", help="台一覧の1日前BONUS")
    parser.add_argument("--bonus-2d", default="", help="台一覧の2日前BONUS")
    parser.add_argument("--combined-rate", default="", help="例: 1/71.4")
    parser.add_argument("--at-art-rate", default="", help="例: 1/80.1")
    parser.add_argument("--last-game", default="")
    parser.add_argument("--max-payout", default="")
    parser.add_argument("--graph-trend", default="", help="例: 上げ / 下げ / V字 / 山型 / 荒い / 不明")
    parser.add_argument("--graph-movement", default="", help="推移グラフから見たおおよその上げ下げ幅")
    parser.add_argument("--graph-note", default="", help="推移グラフの補足メモ")
    parser.add_argument("--source", default="line")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    row = {
        "date": normalize_date(args.date),
        "store": args.store.strip(),
        "rate": args.rate.strip(),
        "model": args.model.strip(),
        "machine_no": str(args.machine_no).strip(),
        "total_game": str(args.total_game).strip(),
        "big": str(args.big).strip(),
        "reg": str(args.reg).strip(),
        "at_art": str(args.at_art).strip(),
        "combined_rate": str(args.combined_rate).strip(),
        "at_art_rate": str(args.at_art_rate).strip(),
        "last_game": str(args.last_game).strip(),
        "max_payout": str(args.max_payout).strip(),
        "graph_trend": str(args.graph_trend).strip(),
        "graph_movement": str(args.graph_movement).strip(),
        "graph_note": str(args.graph_note).strip(),
        "source": args.source.strip() or "line",
        "note": args.note.strip(),
    }
    bonus_notes = []
    if args.bonus_today:
        bonus_notes.append(f"bonus_today={str(args.bonus_today).strip()}")
    if args.bonus_1d:
        bonus_notes.append(f"bonus_1d={str(args.bonus_1d).strip()}")
    if args.bonus_2d:
        bonus_notes.append(f"bonus_2d={str(args.bonus_2d).strip()}")
    if bonus_notes:
        row["note"] = ";".join([part for part in [row["note"], *bonus_notes] if part])
    if not row["store"] or not row["model"] or not row["machine_no"]:
        raise ValueError("store/model/machine-no は必須です")

    replaced = upsert_row(row)
    print(("updated" if replaced else "added") + f": {row['date']} {row['store']} {row['machine_no']} {row['model']}")


if __name__ == "__main__":
    main()
