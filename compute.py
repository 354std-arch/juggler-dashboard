import json, csv, math, os
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV  = os.path.join(REPO_DIR, "raw_data.csv")
STORE_FRESHNESS_JSON = os.path.join(REPO_DIR, "store_freshness.json")
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
    "マルハン都筑":              [1, 7, 10, 11, 17, 21, 22, 25, 27, 31],
    "エスパス日拓新宿歌舞伎町":  [1, 6, 7, 11, 16, 17, 22, 23, 24, 26, 27],
}

MODEL_NAME_MAP = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラー",
    "ジャグラーガールズ":     "ジャグラーガールズSS",
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
    "クランキーセレブレーション": {"syn":{1:160,2:154,3:146,4:137,5:129,6:120},"bb":{1:268,2:260,3:252,4:240,5:229,6:216},"rb":{1:400,2:375,3:349,4:320,5:293,6:265}},
}

def r1(v): return round(v*10)/10
def avg(arr): return sum(arr)/len(arr) if arr else 0
def wavg(vals, weights):
    if not vals: return 0
    tw = sum(weights)
    return sum(v*w for v,w in zip(vals,weights))/tw if tw else 0
def row_w(r): return r.get("weight", 1)
def weighted_total(rows): return sum(row_w(r) for r in rows)
def weighted_sum(rows, key): return sum(r[key] * row_w(r) for r in rows)
def weighted_avg_rows(rows, key):
    tw = weighted_total(rows)
    return weighted_sum(rows, key) / tw if tw else 0
def weighted_rate(rows, pred):
    tw = weighted_total(rows)
    if not tw: return 0
    return sum(row_w(r) for r in rows if pred(r)) / tw

def parse_num(s):
    if not s: return 0
    try: return float(str(s).replace(",","").replace("+","").strip())
    except: return 0

def load_store_freshness():
    if not os.path.exists(STORE_FRESHNESS_JSON):
        return {}
    try:
        with open(STORE_FRESHNESS_JSON, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

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


def load_raw():
    seen = set()
    rows = []
    today = jst_today()
    recent_cutoff = today - timedelta(days=90)
    if not os.path.exists(RAW_CSV):
        print(f"  ❌ CSVが見つかりません: {RAW_CSV}")
        return rows
    with open(RAW_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            date_str = str(row.get("日付", "")).strip()
            store = str(row.get("店名", "")).strip()
            tai = str(row.get("台番号", "")).strip()
            model_name = str(row.get("機種名", "")).strip()
            if not date_str or not store or not tai or not model_name:
                continue
            key = (date_str, store, tai, model_name)
            if key in seen: continue
            seen.add(key)
            model = MODEL_NAME_MAP.get(model_name, model_name)
            if model not in MODEL_SETTINGS: continue
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except: continue
            g    = parse_num(row.get("G数"))
            diff = parse_num(row.get("差枚"))
            bb   = parse_num(row.get("BB"))
            rb   = parse_num(row.get("RB"))
            tai_num = int(tai) if tai.isdigit() else 0
            s = str(tai_num)
            ms = MODEL_SETTINGS[model]
            is_high_set_rb = (rb > 0 and bb > 0 and g > 0 and (g/rb) <= ms["rb"][4] and (g/bb) > ms["bb"][4])
            rows.append({
                "dateStr": date_str, "date": dt,
                "store": store, "model": model,
                "tai": tai, "taiNum": tai_num,
                "g": g, "diff": diff, "bb": bb, "rb": rb,
                "weight": 2 if dt.date() >= recent_cutoff else 1,
                "day": dt.day, "weekday": (dt.weekday() + 1) % 7,
                "suef": tai_num % 10,
                "isZoro": len(s)>=2 and s[-1]==s[-2],
                "isRBLead": rb > bb,
                "isHighSetRBLead": is_high_set_rb,
            })
    rows.sort(key=lambda r: r["date"])
    print(f"合計 {len(rows)} 行読み込み完了")
    return rows

def calc_bayes_prob(model, total_g, total_bb, total_rb):
    ms = MODEL_SETTINGS.get(model)
    if not ms or total_g < 100: return None
    log_probs = []
    for s in [1,2,3,4,5,6]:
        log_l = 0
        if total_bb > 0:
            exp_bb = total_g / ms["bb"][s]
            log_l += total_bb * math.log(exp_bb) - exp_bb
        if total_rb > 0:
            exp_rb = total_g / ms["rb"][s]
            log_l += total_rb * math.log(exp_rb) - exp_rb
        log_probs.append(math.log(1/6) + log_l)
    max_log = max(log_probs)
    probs = [math.exp(p - max_log) for p in log_probs]
    total = sum(probs)
    probs = [p/total for p in probs]
    return round(sum(probs[3:]) * 100, 1)

def compute_day_stats(rows, special):
    by_day = defaultdict(lambda: {"rows":[], "plus":0, "total":0})
    for r in rows:
        by_day[r["day"]]["rows"].append(r)
        by_day[r["day"]]["total"] += 1
        if r["diff"] > 0: by_day[r["day"]]["plus"] += 1
    result = []
    for d in range(1, 32):
        b = by_day[d]
        day_rows = b["rows"]
        if not day_rows: continue
        m = weighted_avg_rows(day_rows, "diff")
        expanded_diffs = []
        for rr in day_rows:
            expanded_diffs.extend([rr["diff"]] * int(row_w(rr)))
        n = len(expanded_diffs)
        if n > 1:
            std = (sum((x-m)**2 for x in expanded_diffs)/(n-1))**0.5
            se = std / (n**0.5)
            ci_lower = round(m - 1.96*se, 1)
            ci_upper = round(m + 1.96*se, 1)
        else:
            ci_lower = ci_upper = round(m, 1)
        plus_rate = weighted_rate(day_rows, lambda x: x["diff"] > 0) * 100
        result.append({
            "day": d, "avg": r1(m), "total": b["total"],
            "plus": b["plus"], "plusRate": r1(plus_rate),
            "special": d in special, "ciLower": ci_lower, "ciUpper": ci_upper,
            "reliable": n >= 10,
        })
    return result

def compute_tai_detail(rows, special):
    by_tai = defaultdict(lambda: {
        "tai":None,"taiNum":0,"model":None,"store":None,
        "all":[], "sp":[], "nm":[],
    })
    for r in rows:
        k = f"{r['taiNum']}_{r['model']}_{r['store']}"
        t = by_tai[k]
        t["tai"]=r["tai"]; t["taiNum"]=r["taiNum"]
        t["model"]=r["model"]; t["store"]=r["store"]
        t["all"].append(r)
        if r["day"] in special:
            t["sp"].append(r)
        else:
            t["nm"].append(r)
    by_tai_date = defaultdict(list)
    for r in rows:
        by_tai_date[f"{r['tai']}_{r['store']}"].append(r)
    latest_date = max(r["date"] for r in rows)
    prev_lookup = {}
    for k, tai_rows in by_tai_date.items():
        sorted_rows = sorted(tai_rows, key=lambda r: r["date"])
        for i in range(1, len(sorted_rows)):
            curr = sorted_rows[i]; prev = sorted_rows[i-1]
            if (curr["date"] - prev["date"]).days == 1:
                prev_lookup[f"{curr['dateStr']}_{curr['tai']}_{curr['store']}"] = prev
    result = []
    for t in by_tai.values():
        tg=weighted_sum(t["all"], "g"); tb=weighted_sum(t["all"], "bb"); tr=weighted_sum(t["all"], "rb")
        sg=weighted_sum(t["sp"], "g"); sb=weighted_sum(t["sp"], "bb"); sr=weighted_sum(t["sp"], "rb")
        ng=weighted_sum(t["nm"], "g"); nb=weighted_sum(t["nm"], "bb"); nr=weighted_sum(t["nm"], "rb")
        n = len(t["all"])
        wn = weighted_total(t["all"])
        wplus_rate = weighted_rate(t["all"], lambda x: x["diff"] > 0) * 100
        latest_key = f"{latest_date.strftime('%Y-%m-%d')}_{t['tai']}_{t['store']}"
        prev = prev_lookup.get(latest_key)
        prev_row = {"dateStr":prev["dateStr"],"diff":prev["diff"],"bb":prev["bb"],"rb":prev["rb"],"g":prev["g"],"isRBLead":prev["isRBLead"],"isHighSetRBLead":prev["isHighSetRBLead"]} if prev else None
        result.append({
            "tai":t["tai"],"taiNum":t["taiNum"],"model":t["model"],"store":t["store"],
            "avg":r1(weighted_avg_rows(t["all"], "diff")),"count":n,
            "weightedCount": r1(wn),
            "plus":len([v for v in t["all"] if v["diff"]>0]),
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
            "bayesProbAll":calc_bayes_prob(t["model"],tg,tb,tr),
            "bayesProbSp":calc_bayes_prob(t["model"],sg,sb,sr),
            "bayesProbNm":calc_bayes_prob(t["model"],ng,nb,nr),
            "confidence":"高" if n>=30 else "中" if n>=15 else "低",
            "prevRow": prev_row,
        })
    result.sort(key=lambda x: x["taiNum"])
    return result

def compute_model_stats(rows, special):
    by_model = defaultdict(lambda: {"all":[],"sp":[],"nm":[],"this_month":[],"last_month":[]})
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
    result = []
    for model, m in by_model.items():
        tg=weighted_sum(m["all"], "g"); tb=weighted_sum(m["all"], "bb"); tr=weighted_sum(m["all"], "rb")
        total_in=tg*3; total_out=total_in+weighted_sum(m["all"], "diff")
        result.append({
            "model":model,"allAvg":r1(weighted_avg_rows(m["all"], "diff")),"count":len(m["all"]),
            "spAvg":r1(weighted_avg_rows(m["sp"], "diff")) if m["sp"] else None,"spCount":len(m["sp"]),
            "nmAvg":r1(weighted_avg_rows(m["nm"], "diff")) if m["nm"] else None,"nmCount":len(m["nm"]),
            "mechRitu":r1(total_out/total_in*100) if total_in>0 else None,
            "rbRate":round(tg/tr) if tr>0 else None,
            "synRate":round(tg/(tb+tr)) if (tb+tr)>0 else None,
            "thisMonthAvg":r1(weighted_avg_rows(m["this_month"], "diff")) if m["this_month"] else None,
            "thisMonthCount":len(m["this_month"]),
            "lastMonthAvg":r1(weighted_avg_rows(m["last_month"], "diff")) if m["last_month"] else None,
            "lastMonthCount":len(m["last_month"]),
        })
    return result

def compute_next_day(rows, special):
    by_tai = defaultdict(list)
    for r in rows:
        by_tai[f"{r['tai']}_{r['store']}"].append(r)
    pairs = []
    for tai_rows in by_tai.values():
        sorted_rows = sorted(tai_rows, key=lambda r: r["date"])
        for i in range(len(sorted_rows)-1):
            prev=sorted_rows[i]; nxt=sorted_rows[i+1]
            if (nxt["date"]-prev["date"]).days==1:
                pairs.append({"prev":prev,"next":nxt})
    baseline=weighted_avg_rows(rows, "diff")
    def calc(matched):
        next_rows=[p["next"] for p in matched]
        if not next_rows: return {"count":0,"avg":None,"plusRate":None,"vsBaseline":None}
        a=weighted_avg_rows(next_rows, "diff")
        plus_rate=weighted_rate(next_rows, lambda x: x["diff"] > 0) * 100
        return {"count":len(next_rows),"avg":r1(a),"plusRate":r1(plus_rate),"vsBaseline":r1(a-baseline)}
    return {
        "__baseline":{"label":"全期間平均","count":len(rows),"avg":r1(baseline),"plusRate":r1(weighted_rate(rows, lambda x: x["diff"] > 0)*100),"vsBaseline":0},
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
            "win":r1(weighted_rate(target_rows, lambda x: x["diff"] > 0) * 100),
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
            "win":r1(weighted_rate(target_rows, lambda x: x["diff"] > 0) * 100),
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
        if r["diff"] > 0: by_date[k]["plus"] += 1
    result = []
    for v in sorted(by_date.values(), key=lambda x: x["dateStr"]):
        day_rows = v["rows"]
        n = len(day_rows)
        result.append({
            "dateStr": v["dateStr"],"total": r1(weighted_sum(day_rows, "diff")),
            "count": n,"plus": v["plus"],
            "plusRate": r1(weighted_rate(day_rows, lambda x: x["diff"] > 0) * 100),
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
            "win":r1(weighted_rate(target_rows, lambda x: x["diff"] > 0) * 100),
            "set456":r1(weighted_rate(target_rows, lambda x: x["isHighSetRBLead"]) * 100),
            "count":v["count"]
        }
    return result

def compute_today_analysis(rows, special, today=None):
    if today is None:
        today = jst_today()
    day = today.day; weekday = today.weekday()
    is_special = day in special
    day_stats = compute_day_stats(rows, special)
    day_info = next((d for d in day_stats if d["day"] == day), None)
    wday_rows = [r for r in rows if r["weekday"] == weekday]
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
    tai_detail = compute_tai_detail(rows, special)
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
    next_stats = compute_next_day(rows, special)
    bl_avg = (next_stats.get("__baseline") or {}).get("avg") or 0
    scored_tais = []
    for t in tai_detail:
        score = 0; reasons = []
        ref = t["spAvg"] if is_special else t["nmAvg"]
        if ref is not None and t.get("weightedCount", t["count"]) >= 5:
            lift = r1(ref - bl_avg)
            pts = 3 if lift>=150 else 2 if lift>=80 else 1 if lift>=30 else 0 if lift>=-30 else -1
            score += pts; reasons.append({"label":"過去成績","val":f"{ref:+}枚","pts":pts})
        bayes = t["bayesProbSp"] if is_special else t["bayesProbNm"]
        if bayes is not None:
            pts = 2 if bayes>=60 else 1 if bayes>=45 else 0 if bayes>=30 else -1
            score += pts; reasons.append({"label":"P(設定4以上)","val":f"{bayes}%","pts":pts})
        prev = t.get("prevRow")
        if prev:
            diff = prev["diff"]
            ckey = ("凹み_2000以上" if diff<=-2000 else "凹み_1000_2000" if diff<=-1000 else
                    "凹み_500_1000" if diff<=-500 else "凹み_0_500" if diff<0 else
                    "プラス500以上" if diff>=500 else "プラス")
            ns = next_stats.get(ckey,{})
            if ns.get("count",0)>=10 and ns.get("avg") is not None:
                lift = r1(ns["avg"]-bl_avg)
                pts = 2 if lift>=150 else 1 if lift>=80 else 0 if lift>=-30 else -1
                score += pts; reasons.append({"label":f"前日({ckey})","val":f"前日{diff:+}枚","pts":pts})
        rank = "本命" if score>=4 else "対抗" if score>=2 else "保留" if score>=1 else "注意"
        scored_tais.append({**t,"totalScore":score,"rank":rank,"reasons":reasons})
    scored_tais.sort(key=lambda x: -x["totalScore"])
    return {
        "date":today.strftime("%Y-%m-%d"),"day":day,"weekday":weekday,
        "isSpecial":is_special,"dayJudge":day_judge,"dayScore":day_score,
        "verdict":verdict,"dayInfo":day_info,"wdayAvg":wday_avg,
        "baseline":baseline,"modelStrength":model_strength,"topTargets":scored_tais[:20]
    }

def build_store_recommendations(store, store_rows, special, tai_detail, today=None):
    if today is None:
        today = jst_today()
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

    recent_cutoff = today - timedelta(days=90)
    three_month_cutoff = today - timedelta(days=92)
    recent_counts = defaultdict(int)
    tail_rows_by_model = defaultdict(list)
    recent_rows_by_tai_num = defaultdict(list)
    recent_context_rows_by_tai = defaultdict(list)
    for r in store_rows:
        if r["date"].date() >= recent_cutoff:
            recent_counts[(r["tai"], r["model"])] += 1
            recent_rows_by_tai_num[r["taiNum"]].append(r)
        tail_rows_by_model[(r["model"], r["suef"])].append(r)
        if r["date"].date() >= three_month_cutoff and (r["day"] == recommendation_day or r["weekday"] == recommendation_weekday_data):
            recent_context_rows_by_tai[(r["tai"], r["model"])].append(r)

    recs = []
    for t in tai_detail:
        recent_count = recent_counts.get((t["tai"], t["model"]), 0)
        if recent_count < 3:
            continue
        bayes = t.get("bayesProbSp") if is_special else t.get("bayesProbNm")
        if bayes is None:
            bayes = t.get("bayesProbAll")
        if bayes is None or bayes < 60:
            continue
        weighted_score = bayes * weekday_coeff * monthly_timing_coeff * store_coeff
        reasons = []
        if is_special:
            reasons.append("今日は特定日")
        if is_special_next_day:
            reasons.append("特定日翌日")
        if t["taiNum"] > 0:
            tail_digit = t["taiNum"] % 10
            tail_rows = tail_rows_by_model.get((t["model"], tail_digit), [])
            if weighted_total(tail_rows) >= 5 and weighted_avg_rows(tail_rows, "diff") > 0:
                reasons.append(f"末尾{tail_digit}が好調")
            neighbor_rows = recent_rows_by_tai_num.get(t["taiNum"] - 1, []) + recent_rows_by_tai_num.get(t["taiNum"] + 1, [])
            if weighted_total(neighbor_rows) >= 3 and weighted_avg_rows(neighbor_rows, "diff") > 0:
                reasons.append("隣台が直近好調")
        context_rows = recent_context_rows_by_tai.get((t["tai"], t["model"]), [])
        if weighted_total(context_rows) >= 3 and weighted_avg_rows(context_rows, "diff") > 0:
            reasons.append("同日同曜が3ヶ月好調")
        if weekday_coeff >= 1.1:
            reasons.append("曜日係数1.1以上")
        if monthly_timing_coeff >= 1.0:
            reasons.append("月内係数1.0以上")
        recs.append({
            "store": store,
            "tai": t["tai"],
            "model": t["model"],
            "bayes_score": bayes,
            "expected_hourly": r1(bayes * 16.6),
            "confidence": "★★★" if bayes >= 75 else "★★" if bayes >= 65 else "★",
            "day_type": "特定日" if is_special else "特定日翌日",
            "recent_count_3m": recent_count,
            "reasons": reasons,
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
        special = payload.get("special", [1,11,21,31])
        is_special = today.day in special
        for t in payload.get("taiDetail", []):
            p = t["bayesProbSp"] if is_special else t["bayesProbNm"]
            if p is not None and p >= 60:
                hit_targets.append({
                    "machine_id": t["tai"],
                    "store": store,
                    "model": t["model"],
                    "p_setting4plus": p,
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
    today = jst_today()
    rows = load_raw()
    if not rows:
        print("データがありません。終了します。")
        exit(1)
    all_stores = sorted(set(r["store"] for r in rows))
    main_stores = [s for s in all_stores if s != "中山ZoRoN"]
    output = {
        "updated_at": datetime.now(JST).date().strftime("%Y-%m-%d"),
        "store_freshness": load_store_freshness(),
        "stores": main_stores,
        "specialByStore": STORE_SPECIAL,
        "score_coefficients": {
            "weekday": WEEKDAY_COEFF,
            "monthly_timing": MONTHLY_TIMING_COEFF,
            "note": "係数は暫定値です。店舗別の微調整は byStore[店名].store_coefficients と STORE_COEFFICIENTS による拡張を想定しています。",
        },
        "byStore": {},
        "recommendations": [],
        "predictionAccuracy": {"overall": None, "byStore": {}},
    }
    recommendation_pool = []
    for store in all_stores:
        special = STORE_SPECIAL.get(store, [1,11,21,31])
        store_rows = [r for r in rows if r["store"]==store]
        tai_detail = compute_tai_detail(store_rows, special)
        print(f"集計中: {store} ({len(store_rows)}行) 特定日:{special}")
        output["byStore"][store] = {
            "special": special,
            "store_coefficients": STORE_COEFFICIENTS.get(store, {}),
            "dayStats": compute_day_stats(store_rows, special),
            "modelStats": compute_model_stats(store_rows, special),
            "nextStats": compute_next_day(store_rows, special),
            "heatmap": compute_heatmap(store_rows),
            "weekMatrix": compute_week_matrix(store_rows),
            "dayWdayMatrix": compute_day_wday_matrix(store_rows),
            "taiDetail": tai_detail,
            "dateSummary": compute_date_summary(store_rows, special),
            "weekdayStats": compute_weekday_stats(store_rows),
            "todayAnalysis": compute_today_analysis(store_rows, special, today=today),
        }
        try:
            recommendation_pool.extend(build_store_recommendations(store, store_rows, special, tai_detail, today=today))
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
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"✅ data.json出力完了: {out_path}")
