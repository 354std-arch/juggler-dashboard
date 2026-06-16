import argparse
import json
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from scrape_juggler import (
    NORMAL_TYPE_KEYWORDS,
    STORE_LIST_JSON,
    is_target_machine,
    normalize_machine_name,
    save_model_summary_to_csv,
    save_to_csv,
    update_store_freshness,
    compact_model_summary_csv,
)

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(REPO_DIR, ".slorepo_browser_profile")
ACCESS_BLOCK_JSON = os.path.join(REPO_DIR, ".slorepo_access_block.json")
JST = timezone(timedelta(hours=9))

SLOREPO_CODE_BY_NAME = {
    "エスパス日拓新宿歌舞伎町": "e382a8e382b9e38391e382b9e697a5e68b93e696b0e5aebfe6ad8ce8889ee4bc8ee794bae5ba97code",
    "中山UNO": "e4b8ade5b1b1554e4fcode",
    "中山ZoRoN": "e4b8ade5b1b15a6f526f4ecode",
    "楽園蒲田店": "e6a5bde59c92e892b2e794b0e5ba97code",
    "マルハンメガシティ2000-蒲田7": "e3839ee383abe3838fe383b3e383a1e382ace382b7e38386e382a332303030e892b2e794b037code",
    "マルハンメガシティ2000-蒲田1": "e3839ee383abe3838fe383b3e892b2e794b0e9a785e69db1e5ba97code",
    "ヒロキ蒲田西口店": "e38392e383ade382ade892b2e794b0e8a5bfe58fa3e5ba97code",
    "ヒロキmax蒲田店": "e38392e383ade382ad33e58fb7e5ba97code",
}


def get_target_date():
    return (datetime.now(JST).date() - timedelta(days=1)).strftime("%Y-%m-%d")


def parse_args():
    parser = argparse.ArgumentParser(description="スロレポを低速ブラウザ取得して既存CSVへ保存します。")
    parser.add_argument("--start-date", help="取得開始日 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="取得終了日 (YYYY-MM-DD)")
    parser.add_argument("--stores", default=os.environ.get("SLOREPO_STORES", "エスパス日拓新宿歌舞伎町"), help="対象店舗名をカンマ区切りで指定")
    parser.add_argument("--flush-every", type=int, default=0, help="指定件数ごとにCSVへ途中保存。0なら最後だけ保存")
    parser.add_argument("--store-interval-sec", type=float, default=float(os.environ.get("SLOREPO_STORE_INTERVAL_SEC", "300")), help="店舗間の待機秒数")
    parser.add_argument("--page-interval-sec", type=float, default=float(os.environ.get("SLOREPO_PAGE_INTERVAL_SEC", "30")), help="ページ間の待機秒数")
    parser.add_argument("--jitter-sec", type=float, default=float(os.environ.get("SLOREPO_JITTER_SEC", "15")), help="待機秒数に足すランダム揺らぎの最大秒数")
    parser.add_argument("--max-detail-pages", type=int, default=int(os.environ.get("SLOREPO_MAX_DETAIL_PAGES", "0")), help="1店舗日あたりの機種詳細ページ上限。0なら無制限")
    parser.add_argument("--stop-on-consecutive-failures", type=int, default=1, help="連続失敗が指定件数に達したら停止。0なら止めない")
    parser.add_argument("--cloudflare-timeout-sec", type=float, default=60.0, help="Cloudflare待機画面の最大待機秒数")
    parser.add_argument("--headless", action="store_true", default=os.environ.get("SLOREPO_HEADLESS") == "1", help="ブラウザをheadlessで起動")
    parser.add_argument("--browser-channel", default=os.environ.get("SLOREPO_BROWSER_CHANNEL", "chrome"), help="Playwrightのブラウザchannel。例: chrome")
    return parser.parse_args()


def parse_date_str(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_target_dates(start_date, end_date):
    dates = []
    cursor = start_date
    while cursor <= end_date:
        dates.append(cursor.strftime("%Y-%m-%d"))
        cursor += timedelta(days=1)
    return dates


def parse_csv_list(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_store_entries():
    if not os.path.exists(STORE_LIST_JSON):
        return []
    try:
        with open(STORE_LIST_JSON, encoding="utf-8-sig") as fh:
            payload = json.load(fh)
    except Exception as exc:
        print(f"⚠️  store_list.json 読み込み失敗: {exc}")
        return []
    stores = payload.get("stores", []) if isinstance(payload, dict) else []
    return stores if isinstance(stores, list) else []


def slorepo_code_for_store(store):
    if not isinstance(store, dict):
        return ""
    for key in ("slorepo_code", "slorepoCode"):
        value = str(store.get(key, "")).strip()
        if value:
            return value
    sources = store.get("sources")
    if isinstance(sources, dict):
        slorepo = sources.get("slorepo")
        if isinstance(slorepo, dict):
            value = str(slorepo.get("code", "")).strip()
            if value:
                return value
    return SLOREPO_CODE_BY_NAME.get(str(store.get("name", "")).strip(), "")


def resolve_target_stores(selected_names):
    entries = load_store_entries()
    by_name = {str(store.get("name", "")).strip(): store for store in entries if isinstance(store, dict)}
    names = selected_names or [name for name in by_name if name]
    resolved = []
    seen = set()
    for name in names:
        if name in seen:
            continue
        store = by_name.get(name, {"name": name})
        code = slorepo_code_for_store(store)
        if not code:
            print(f"  ⚠️  {name}: slorepo_code未設定のためスキップ")
            continue
        resolved.append((name, code))
        seen.add(name)
    return resolved


def parse_num(value):
    text = str(value or "").replace(",", "").replace("+", "").strip()
    if not text or text in {"-", "－"}:
        return 0
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0
    number = float(match.group(0))
    return int(round(number))


def format_signed(value):
    number = int(round(value))
    sign = "+" if number > 0 else ""
    return f"{sign}{number:,}"


def format_probability(g_count, count):
    g_val = parse_num(g_count)
    count_val = parse_num(count)
    if g_val <= 0 or count_val <= 0:
        return ""
    return f"1/{g_val / count_val:.1f}"


def format_win_rate(value):
    text = str(value or "").strip()
    match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if not match:
        return text
    wins = int(match.group(1))
    total = int(match.group(2))
    if total <= 0:
        return text
    return f"{wins / total * 100:.1f}%({wins}/{total})"


def win_rate_total(value):
    match = re.search(r"(\d+)\s*/\s*(\d+)", str(value or ""))
    return int(match.group(2)) if match else 0


def slow_wait(page, base_sec, jitter_sec=0):
    wait_sec = max(0.0, float(base_sec or 0))
    if jitter_sec and jitter_sec > 0:
        wait_sec += random.uniform(0, float(jitter_sec))
    if wait_sec > 0:
        page.wait_for_timeout(int(wait_sec * 1000))


def is_normal_type_model(model_name):
    return any(keyword in str(model_name or "") for keyword in NORMAL_TYPE_KEYWORDS)


def slorepo_date_path(target_date):
    return target_date.replace("-", "")


def store_day_url(code, target_date):
    return f"https://www.slorepo.com/hole/{code}/{slorepo_date_path(target_date)}/"


def mark_access_block(url, store_name, target_date, reason, title=""):
    payload = {
        "blocked_at": datetime.now(JST).isoformat(timespec="seconds"),
        "source": "slorepo",
        "url": url,
        "store": store_name,
        "target_date": target_date,
        "reason": reason,
        "title": title,
    }
    with open(ACCESS_BLOCK_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def clear_access_block():
    try:
        if os.path.exists(ACCESS_BLOCK_JSON):
            os.remove(ACCESS_BLOCK_JSON)
    except Exception as exc:
        print(f"    ↳ スロレポアクセス制限メモ削除失敗: {exc}")


def is_cloudflare_wait(title, body_text):
    text = f"{title}\n{body_text}".lower()
    return (
        "just a moment" in text
        or "enable javascript and cookies" in text
        or "checking if the site connection is secure" in text
        or "__cf_chl" in text
    )


def is_captcha_like(body_text):
    text = str(body_text or "").lower()
    return (
        "captcha" in text
        or "verify you are human" in text
        or "人間であること" in text
        or "ロボット" in text
    )


def wait_until_readable(page, url, store_name, target_date, timeout_sec, record_block=True):
    deadline = time.monotonic() + timeout_sec
    last_title = ""
    last_text = ""
    while time.monotonic() < deadline:
        try:
            last_title = page.title()
            last_text = page.locator("body").inner_text(timeout=3000)[:2000]
            table_count = page.locator("table").count()
        except Exception:
            table_count = 0
        if is_captcha_like(last_text):
            if not record_block:
                return False, "captcha"
            mark_access_block(url, store_name, target_date, "captcha", last_title)
            return False, "captcha"
        if table_count > 0 and not is_cloudflare_wait(last_title, last_text):
            clear_access_block()
            return True, ""
        page.wait_for_timeout(2000)
    if record_block:
        mark_access_block(url, store_name, target_date, "cloudflare_timeout", last_title)
    return False, "cloudflare_timeout"


def table_rows(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue
        rows.append([cell.get_text("\n", strip=True) for cell in cells])
    return rows


def normalize_header(text):
    return "".join(str(text or "").replace("\u3000", " ").split()).lower()


def extract_model_summary_and_links(html, target_date, store_name, base_url, target_models=None):
    soup = BeautifulSoup(html, "html.parser")
    summary_rows = []
    detail_links = []
    seen_detail = set()

    for table in soup.find_all("table"):
        rows = table_rows(table)
        if len(rows) < 2:
            continue
        headers = [normalize_header(cell) for cell in rows[0]]
        if not (len(headers) >= 4 and "機種" in headers[0] and "平均差枚" in headers[1] and "平均g数" in headers[2] and "勝率" in headers[3]):
            continue
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if len(cells) < 4:
                continue
            cols = [cell.get_text(strip=True) for cell in cells]
            raw_model = cols[0]
            model_name = normalize_machine_name(raw_model)
            if not model_name or "少台数機種" in model_name:
                continue
            avg_diff = cols[1]
            avg_g = cols[2]
            win_rate = cols[3]
            total_count = win_rate_total(win_rate)
            summary_rows.append({
                "date": target_date,
                "store": store_name,
                "model": model_name,
                "total_diff": format_signed(parse_num(avg_diff) * total_count) if total_count else "",
                "avg_diff": format_signed(parse_num(avg_diff)),
                "avg_g": f"{parse_num(avg_g):,}" if parse_num(avg_g) else avg_g,
                "win_rate": format_win_rate(win_rate),
            })

            if target_models and model_name not in target_models:
                continue
            if not target_models and not is_target_machine(model_name):
                continue
            link = cells[0].find("a", href=True)
            if not link:
                continue
            href = urljoin(base_url, link["href"])
            key = (model_name, href)
            if key in seen_detail:
                continue
            detail_links.append((model_name, href))
            seen_detail.add(key)

    detail_links.sort(key=lambda item: (0 if is_normal_type_model(item[0]) else 1, item[0]))
    return summary_rows, detail_links


def extract_detail_rows(html, target_date, store_name, model_name):
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for table in soup.find_all("table"):
        rows = table_rows(table)
        if len(rows) < 2:
            continue
        headers = [normalize_header(cell) for cell in rows[0]]
        joined = " ".join(headers)
        if not ("台番" in joined and "差枚" in joined and "g数" in joined):
            continue
        data_rows = rows[1:]
        candidates.append((len(data_rows), rows))

    if not candidates:
        return []
    candidates.sort(key=lambda item: item[0], reverse=True)
    rows = candidates[0][1]
    headers = [normalize_header(cell) for cell in rows[0]]

    def find_idx(*tokens):
        for idx, header in enumerate(headers):
            if all(token in header for token in tokens):
                return idx
        return None

    tai_idx = find_idx("台番")
    diff_idx = find_idx("差枚")
    g_idx = find_idx("g数")
    bb_idx = find_idx("bb")
    rb_idx = find_idx("rb")
    syn_idx = find_idx("合成")

    out = []
    for cols in rows[1:]:
        tai = cols[tai_idx] if tai_idx is not None and tai_idx < len(cols) else ""
        if not tai or "平均" in tai:
            continue
        diff = cols[diff_idx] if diff_idx is not None and diff_idx < len(cols) else ""
        g_count = cols[g_idx] if g_idx is not None and g_idx < len(cols) else ""
        bb = cols[bb_idx] if bb_idx is not None and bb_idx < len(cols) else ""
        rb = cols[rb_idx] if rb_idx is not None and rb_idx < len(cols) else ""
        syn = cols[syn_idx] if syn_idx is not None and syn_idx < len(cols) else ""
        out.append({
            "日付": target_date,
            "店名": store_name,
            "機種名": model_name,
            "台番号": str(parse_num(tai) or tai),
            "G数": f"{parse_num(g_count):,}" if parse_num(g_count) else g_count,
            "差枚": format_signed(parse_num(diff)),
            "BB": str(parse_num(bb)) if bb != "" else "",
            "RB": str(parse_num(rb)) if rb != "" else "",
            "合成確率": syn,
            "BB確率": format_probability(g_count, bb),
            "RB確率": format_probability(g_count, rb),
        })
    return out


def fetch_page_html(page, url, store_name, target_date, timeout_sec, record_block=True):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeoutError:
        if record_block:
            mark_access_block(url, store_name, target_date, "navigation_timeout", "")
        return None, "navigation_timeout"
    ok, reason = wait_until_readable(page, url, store_name, target_date, timeout_sec, record_block=record_block)
    if not ok:
        return None, reason
    return page.content(), ""


def scrape_store_day(page, target_date, store_name, code, page_interval_sec, jitter_sec, cloudflare_timeout_sec, max_detail_pages):
    url = store_day_url(code, target_date)
    html, reason = fetch_page_html(page, url, store_name, target_date, cloudflare_timeout_sec)
    if html is None:
        print(f"  ❌ {store_name} {target_date}: {reason}")
        return [], [], False

    model_summary_rows, detail_links = extract_model_summary_and_links(html, target_date, store_name, url)
    if max_detail_pages and max_detail_pages > 0:
        detail_links = detail_links[:max_detail_pages]
    detail_rows = []
    for idx, (model_name, detail_url) in enumerate(detail_links, start=1):
        print(f"    機種詳細 {idx}/{len(detail_links)}: {model_name}")
        if idx > 1 and page_interval_sec > 0:
            slow_wait(page, page_interval_sec, jitter_sec)
        detail_html, reason = fetch_page_html(page, detail_url, store_name, target_date, cloudflare_timeout_sec, record_block=False)
        if detail_html is None:
            print(f"    ⚠️  {model_name}: {reason} / 以降の機種詳細は次回に回します")
            break
        detail_rows.extend(extract_detail_rows(detail_html, target_date, store_name, model_name))

    print(f"  ✅ {store_name} {target_date}: 台別{len(detail_rows)}行 / 機種別{len(model_summary_rows)}行取得")
    return detail_rows, model_summary_rows, True


def launch_context(playwright, args):
    kwargs = {
        "headless": args.headless,
        "locale": "ja-JP",
        "viewport": {"width": 1280, "height": 900},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    if args.browser_channel:
        kwargs["channel"] = args.browser_channel
    try:
        return playwright.chromium.launch_persistent_context(PROFILE_DIR, **kwargs)
    except PlaywrightError:
        if not args.browser_channel:
            raise
        print(f"⚠️  browser channel '{args.browser_channel}' を起動できないため、標準Chromiumへフォールバックします")
        kwargs.pop("channel", None)
        return playwright.chromium.launch_persistent_context(PROFILE_DIR, **kwargs)


def main():
    args = parse_args()
    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            raise SystemExit("❌ --start-date と --end-date は同時に指定してください")
        start = parse_date_str(args.start_date)
        end = parse_date_str(args.end_date)
        if start > end:
            raise SystemExit("❌ 開始日が終了日より後です")
    else:
        start = end = parse_date_str(get_target_date())

    target_dates = build_target_dates(start, end)
    stores = resolve_target_stores(parse_csv_list(args.stores))
    print(f"=== スロレポ取得期間: {target_dates[0]} 〜 {target_dates[-1]} ({len(target_dates)}日) ===")
    print(f"=== 対象店舗: {len(stores)}件 ===")
    if not stores:
        raise SystemExit("❌ slorepo_code付きの対象店舗がありません")

    all_rows = []
    all_model_summary_rows = []
    saved_total = 0
    model_saved_total = 0
    latest_by_store = {}
    scraped_store_count = set()
    consecutive_failures = 0
    plan = [(target_date, store_name, code) for target_date in target_dates for store_name, code in stores]

    def flush_buffers(reason):
        nonlocal all_rows, all_model_summary_rows, saved_total, model_saved_total
        if not all_rows and not all_model_summary_rows:
            return
        print(f"  💾 途中保存: {reason} / 台別{len(all_rows)}行 / 機種別{len(all_model_summary_rows)}行")
        saved_total += save_to_csv(all_rows)
        model_saved_total += save_model_summary_to_csv(all_model_summary_rows)
        all_rows = []
        all_model_summary_rows = []

    with sync_playwright() as playwright:
        context = launch_context(playwright, args)
        page = context.new_page()
        try:
            previous_date = None
            for idx, (target_date, store_name, code) in enumerate(plan, start=1):
                if target_date != previous_date:
                    day_idx = target_dates.index(target_date) + 1
                    print(f"\n--- {target_date} ({day_idx}/{len(target_dates)}) ---")
                rows, model_summary_rows, ok = scrape_store_day(
                    page,
                    target_date,
                    store_name,
                    code,
                    args.page_interval_sec,
                    args.jitter_sec,
                    args.cloudflare_timeout_sec,
                    args.max_detail_pages,
                )
                all_rows.extend(rows)
                all_model_summary_rows.extend(model_summary_rows)
                if ok:
                    consecutive_failures = 0
                    latest_by_store[store_name] = max(latest_by_store.get(store_name, ""), target_date)
                    scraped_store_count.add(store_name)
                else:
                    consecutive_failures += 1
                    if args.stop_on_consecutive_failures and consecutive_failures >= args.stop_on_consecutive_failures:
                        print(f"  🛑 連続失敗 {consecutive_failures}件のため停止します")
                        break

                if args.flush_every and idx % args.flush_every == 0:
                    flush_buffers(f"{idx}件処理")

                if idx < len(plan) and args.store_interval_sec > 0:
                    slow_wait(page, args.store_interval_sec, args.jitter_sec)
                previous_date = target_date
        finally:
            context.close()

    for store_name, latest_data_date in latest_by_store.items():
        update_store_freshness(store_name, latest_data_date)

    flush_buffers("最終")
    model_compacted = compact_model_summary_csv()
    if model_compacted:
        print(f"  🧹 機種別集計の重複 {model_compacted}行を整理")
    print(f"✅ 完了（台別更新/追加: {saved_total}行, 機種別更新/追加: {model_saved_total}行, freshness更新: {len(scraped_store_count)}店舗）")


if __name__ == "__main__":
    try:
        main()
    except PlaywrightTimeoutError as exc:
        raise SystemExit(f"❌ Playwright timeout: {exc}") from exc
