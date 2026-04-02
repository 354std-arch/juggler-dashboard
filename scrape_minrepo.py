import json
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_LIST_JSON = os.path.join(REPO_DIR, "store_list.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

JST = timezone(timedelta(hours=9))


def jst_today_iso() -> str:
    return datetime.now(JST).date().isoformat()

# NOTE:
# みんレポのURL構造は運用変更されることがあるため、複数候補URLを順に試す。
# いずれも失敗した場合はエラーログを出して store_list.json は更新しない。
AREA_URL_CANDIDATES: Dict[str, List[str]] = {
    "横浜": [
        "https://min-repo.com/kanagawa/yokohama/",
        "https://min-repo.com/area/kanagawa/yokohama/",
    ],
    "川崎": [
        "https://min-repo.com/kanagawa/kawasaki/",
        "https://min-repo.com/area/kanagawa/kawasaki/",
    ],
    "鶴見": [
        "https://min-repo.com/kanagawa/tsurumi/",
        "https://min-repo.com/area/kanagawa/tsurumi/",
    ],
    "相模原": [
        "https://min-repo.com/kanagawa/sagamihara/",
        "https://min-repo.com/area/kanagawa/sagamihara/",
    ],
    "渋谷": [
        "https://min-repo.com/tokyo/shibuya/",
        "https://min-repo.com/area/tokyo/shibuya/",
    ],
    "新宿": [
        "https://min-repo.com/tokyo/shinjuku/",
        "https://min-repo.com/area/tokyo/shinjuku/",
    ],
    "品川": [
        "https://min-repo.com/tokyo/shinagawa/",
        "https://min-repo.com/area/tokyo/shinagawa/",
    ],
}

SEED_STORES = [
    {"name": "鶴見UNO", "area": "鶴見", "source": "manual", "added_date": jst_today_iso(), "score": 0.0},
    {"name": "マルハン都筑", "area": "横浜", "source": "manual", "added_date": jst_today_iso(), "score": 0.0},
    {"name": "中山UNO", "area": "横浜", "source": "manual", "added_date": jst_today_iso(), "score": 0.0},
    {"name": "エスパス新宿", "area": "新宿", "source": "manual", "added_date": jst_today_iso(), "score": 0.0},
]

JUGGLER_KEYWORDS = [
    "ジャグラー",
    "マイジャグラー",
    "ファンキージャグラー",
    "ゴーゴージャグラー",
    "アイムジャグラー",
    "ハッピージャグラー",
    "ミラクルジャグラー",
]

DATE_RE = re.compile(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})")
TOTAL_RE = re.compile(r"総差枚\s*[:：]?\s*([+-]?[\d,]+)")
AVERAGE_RE = re.compile(r"平均差枚\s*[:：]?\s*([+-]?[\d,]+)")
MODEL_RATING_RE = re.compile(r"([☆◎○▲])\s*([^\n\r]+)")


def write_json_atomic(path: str, payload: dict) -> None:
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".store_list.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def initialize_store_list_if_missing() -> None:
    if os.path.exists(STORE_LIST_JSON):
        return
    write_json_atomic(STORE_LIST_JSON, {"stores": SEED_STORES})
    logging.info("Created %s with 4 manual seed stores", STORE_LIST_JSON)


def load_store_list() -> dict:
    if not os.path.exists(STORE_LIST_JSON):
        return {"stores": []}
    try:
        with open(STORE_LIST_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Failed to read %s: %s", STORE_LIST_JSON, e)
        return {"stores": []}
    if not isinstance(data, dict):
        return {"stores": []}
    stores = data.get("stores")
    if not isinstance(stores, list):
        data["stores"] = []
    return data


def fetch_soup(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            logging.error("HTTP %s for %s", resp.status_code, url)
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logging.error("Request failed for %s: %s", url, e)
        return None


def parse_store_links(area: str) -> Tuple[List[Tuple[str, str]], bool]:
    urls = AREA_URL_CANDIDATES.get(area, [])
    soup = None
    used_url = None
    for candidate in urls:
        soup = fetch_soup(candidate)
        if soup is not None:
            used_url = candidate
            break

    if soup is None or used_url is None:
        logging.error("Area page fetch failed for %s", area)
        return [], True

    links: Dict[str, str] = {}
    for a in soup.select("a[href]"):
        name = a.get_text(strip=True)
        href = a.get("href", "")
        if not name or not href:
            continue
        lower_href = href.lower()
        if "/shop/" not in lower_href and "/store/" not in lower_href and "min-repo.com" not in lower_href:
            continue
        if len(name) <= 1:
            continue
        abs_url = urljoin(used_url, href)
        links[name] = abs_url

    if not links:
        logging.error("No store links found for area %s (%s)", area, used_url)
        return [], True

    return sorted(links.items(), key=lambda x: x[0]), False


def parse_int(text: Optional[str]) -> Optional[int]:
    if text is None:
        return None
    cleaned = text.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def normalize_date(raw_text: str) -> Optional[str]:
    m = DATE_RE.search(raw_text)
    if not m:
        return None
    y, mm, dd = m.groups()
    return f"{int(y):04d}-{int(mm):02d}-{int(dd):02d}"


def parse_store_page(store_name: str, store_url: str, area: str) -> Tuple[List[dict], bool]:
    soup = fetch_soup(store_url)
    if soup is None:
        logging.error("Store page fetch failed: %s (%s)", store_name, store_url)
        return [], True

    records: List[dict] = []

    date_nodes = []
    for node in soup.find_all(string=DATE_RE):
        text = str(node)
        norm = normalize_date(text)
        if norm:
            date_nodes.append((node.parent, norm))

    if not date_nodes:
        page_text = soup.get_text("\n", strip=True)
        text_date = normalize_date(page_text)
        if text_date:
            date_nodes.append((soup, text_date))

    for base_node, d in date_nodes:
        block_text = ""
        current = base_node
        for _ in range(5):
            if current is None:
                break
            block_text += "\n" + current.get_text("\n", strip=True)
            current = current.parent

        total_match = TOTAL_RE.search(block_text)
        avg_match = AVERAGE_RE.search(block_text)

        total_diff = parse_int(total_match.group(1)) if total_match else None
        avg_diff = parse_int(avg_match.group(1)) if avg_match else None

        model_ratings: List[Tuple[str, str]] = []
        for rating, model_name in MODEL_RATING_RE.findall(block_text):
            model = model_name.strip()
            if not model:
                continue
            model_ratings.append((rating, model))

        if not model_ratings:
            for tr in soup.select("tr"):
                tds = [td.get_text(" ", strip=True) for td in tr.select("td")]
                if len(tds) < 2:
                    continue
                left = tds[0]
                right = tds[1]
                rm = re.search(r"([☆◎○▲])", left)
                if rm:
                    model_ratings.append((rm.group(1), right))

        if not model_ratings and avg_diff is None and total_diff is None:
            continue

        records.append(
            {
                "store": store_name,
                "area": area,
                "date": d,
                "total_diff": total_diff,
                "avg_diff": avg_diff,
                "models": [{"rating": r, "name": n} for r, n in model_ratings],
            }
        )

    dedup: Dict[str, dict] = {}
    for rec in records:
        key = rec["date"]
        if key not in dedup:
            dedup[key] = rec
            continue
        existing = dedup[key]
        if len(rec["models"]) > len(existing["models"]):
            dedup[key] = rec

    final_records = sorted(dedup.values(), key=lambda r: r["date"])

    if not final_records:
        logging.error("No usable records parsed: %s (%s)", store_name, store_url)
        return [], True

    return final_records, False


def is_juggler_model(name: str) -> bool:
    return any(k in name for k in JUGGLER_KEYWORDS)


def qualify_premium(records: List[dict]) -> Tuple[bool, float]:
    if len(records) < 30:
        return False, 0.0

    positive_dates = 0
    has_high_juggler = False
    high_juggler_hits = 0
    total_juggler_rated = 0

    for rec in records:
        avg_diff = rec.get("avg_diff")
        if isinstance(avg_diff, int) and avg_diff > 0:
            positive_dates += 1

        for m in rec.get("models", []):
            model_name = str(m.get("name", ""))
            rating = str(m.get("rating", ""))
            if not is_juggler_model(model_name):
                continue
            total_juggler_rated += 1
            if rating in ("☆", "◎"):
                has_high_juggler = True
                high_juggler_hits += 1

    if not has_high_juggler:
        return False, 0.0

    positive_ratio = positive_dates / len(records)
    if positive_ratio < 0.65:
        return False, 0.0

    star_ratio = (high_juggler_hits / total_juggler_rated) if total_juggler_rated else 0.0
    # score: positive ratio + juggler high-rating ratio + data volume
    score = min(100.0, (positive_ratio * 70.0) + (star_ratio * 20.0) + min(len(records), 100) * 0.1)
    return True, round(score, 1)


def append_new_premium_stores(store_list: dict, new_stores: List[dict]) -> int:
    stores = store_list.setdefault("stores", [])
    existing_names: Set[str] = {str(s.get("name", "")).strip() for s in stores if isinstance(s, dict)}

    added = 0
    for s in new_stores:
        name = s["name"].strip()
        if not name or name in existing_names:
            continue
        stores.append(s)
        existing_names.add(name)
        added += 1
    return added


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    file_existed_before = os.path.exists(STORE_LIST_JSON)
    initialize_store_list_if_missing()
    store_list = load_store_list()

    had_error = False
    area_store_map: List[Tuple[str, str, str]] = []

    for area in AREA_URL_CANDIDATES.keys():
        store_links, failed = parse_store_links(area)
        if failed:
            had_error = True
            continue
        for store_name, store_url in store_links:
            area_store_map.append((area, store_name, store_url))

    parsed_by_store: Dict[str, dict] = {}
    for area, store_name, store_url in area_store_map:
        records, failed = parse_store_page(store_name, store_url, area)
        if failed:
            had_error = True
            continue
        parsed_by_store[store_name] = {
            "area": area,
            "records": records,
        }

    premium_candidates: List[dict] = []
    today = jst_today_iso()
    for store_name, payload in parsed_by_store.items():
        records = payload["records"]
        area = payload["area"]
        ok, score = qualify_premium(records)
        if not ok:
            continue
        premium_candidates.append(
            {
                "name": store_name,
                "area": area,
                "source": "minrepo",
                "added_date": today,
                "score": score,
            }
        )

    if had_error and file_existed_before:
        logging.error("Scrape had failures. Existing store_list.json left unchanged.")
        return 1

    added = append_new_premium_stores(store_list, premium_candidates)
    if added > 0 or not file_existed_before:
        write_json_atomic(STORE_LIST_JSON, store_list)
    logging.info("Premium store candidates: %d / added: %d", len(premium_candidates), added)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
