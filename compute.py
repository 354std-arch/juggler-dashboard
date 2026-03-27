
import json, csv, math
from datetime import datetime, date, timedelta
from collections import defaultdict

REPO_DIR = "/Users/shichidayutarou/Desktop/juggler-dashboard"
RAW_FILES = [
    "/Users/shichidayutarou/Downloads/RAW_final.csv",
    "/Users/shichidayutarou/Desktop/maruhan_juggler.csv",
    "/Users/shichidayutarou/Desktop/juggler_0320_0321.csv",
]

# ===== 店舗別特定日（アナスロから取得） =====
STORE_SPECIAL = {
    "鶴見UNO":                  [1, 11, 21, 31],
    "中山UNO":                  [1, 11, 21, 31],
    "マルハン都築":              [1, 7, 10, 11, 17, 21, 22, 25, 27, 31],
    "エスパス日拓新宿歌舞伎町":  [1, 6, 7, 11, 16, 17, 22, 23, 24, 26, 27],
}

MODEL_NAME_MAP = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラー",
    "ジャグラーガールズ": "ジャグラーガールズSS",
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
}

def r1(v): return round(v*10)/10
def avg(arr): return sum(arr)/len(arr) if arr else 0

def parse_num(s):
    if not s: return 0
    try: return float(str(s).replace(",","").replace("+","").strip())
    except: return 0

def load_raw():
    seen = set()
    rows = []
    for filepath in RAW_FILES:
        try:
            with open(filepath, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    key = (row["日付"], row["店名"], row["台番号"], row["機種名"])
                    if key in seen: continue
                    seen.add(key)
                    model = MODEL_NAME_MAP.get(row["機種名"], row["機種名"])
                    if model not in MODEL_SETTINGS: continue
                    try:
                        dt = datetime.strptime(row["日付"], "%Y-%m-%d")
                    except: continue
                    g    = parse_num(row["G数"])
                    diff = parse_num(row["差枚"])
                    bb   = parse_num(row["BB"])
                    rb   = parse_num(row["RB"])
                    tai  = row["台番号"].strip()
                    if not tai: continue
                    tai_num = int(tai) if tai.isdigit() else 0
                    s = str(tai_num)
                    ms = MODEL_SETTINGS[model]
                    is_high_set_rb = (
                        rb > 0 and bb > 0 and g > 0 and
                        (g/rb) <= ms["rb"][4] and (g/bb) > ms["bb"][4]
                    )
                    rows.append({
                        "dateStr": row["日付"], "date": dt,
                        "store": row["店名"].strip(), "model": model,
                        "tai": tai, "taiNum": tai_num,
                        "g": g, "diff": diff, "bb": bb, "rb": rb,
                        "day": dt.day, "weekday": dt.weekday(),
                        "suef": tai_num % 10,
                        "isZoro": len(s)>=2 and s[-1]==s[-2],
                        "isRBLead": rb > bb,
                        "isHighSetRBLead": is_high_set_rb,
                    })
            print(f"  OK: {filepath}")
        except Exception as e:
            print(f"  NG: {filepath}: {e}")
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
    by_day = defaultdict(lambda: {"diffs":[], "plus":0, "total":0})
    for r in rows:
        by_day[r["day"]]["diffs"].append(r["diff"])
        by_day[r["day"]]["total"] += 1
        if r["diff"] > 0: by_day[r["day"]]["plus"] += 1
    result = []
    for d in range(1, 32):
        b = by_day[d]
        if not b["diffs"]: continue
        m = avg(b["diffs"])
        n = len(b["diffs"])
        if n > 1:
            std = (sum((x-m)**2 for x in b["diffs"])/(n-1))**0.5
            se = std / (n**0.5)
            ci_lower = round(m - 1.96*se, 1)
            ci_upper = round(m + 1.96*se, 1)
        else:
            ci_lower = ci_upper = round(m, 1)
        result.append({
            "day": d, "avg": r1(m), "total": b["total"],
            "plus": b["plus"],
            "plusRate": r1(b["plus"]/b["total"]*100),
            "special": d in special,
            "ciLower": ci_lower, "ciUpper": ci_upper,
            "reliable": n >= 10,
        })
    return result

def compute_tai_detail(rows, special):
    by_tai = defaultdict(lambda: {
        "tai":None,"taiNum":0,"model":None,"store":None,
        "all":[],"sp":[],"nm":[],
        "g":[],"bb":[],"rb":[],
        "spG":[],"spBB":[],"spRB":[],
        "nmG":[],"nmBB":[],"nmRB":[],
    })
    for r in rows:
        k = f"{r['taiNum']}_{r['model']}_{r['store']}"
        t = by_tai[k]
        t["tai"]=r["tai"]; t["taiNum"]=r["taiNum"]
        t["model"]=r["model"]; t["store"]=r["store"]
        t["all"].append(r["diff"])
        t["g"].append(r["g"]); t["bb"].append(r["bb"]); t["rb"].append(r["rb"])
        if r["day"] in special:
            t["sp"].append(r["diff"])
            t["spG"].append(r["g"]); t["spBB"].append(r["bb"]); t["spRB"].append(r["rb"])
        else:
            t["nm"].append(r["diff"])
            t["nmG"].append(r["g"]); t["nmBB"].append(r["bb"]); t["nmRB"].append(r["rb"])
    result = []
    for t in by_tai.values():
        tg=sum(t["g"]); tb=sum(t["bb"]); tr=sum(t["rb"])
        sg=sum(t["spG"]); sb=sum(t["spBB"]); sr=sum(t["spRB"])
        ng=sum(t["nmG"]); nb=sum(t["nmBB"]); nr=sum(t["nmRB"])
        n = len(t["all"])
        result.append({
            "tai":t["tai"],"taiNum":t["taiNum"],
            "model":t["model"],"store":t["store"],
            "avg":r1(avg(t["all"])),"count":n,
            "plus":len([v for v in t["all"] if v>0]),
            "plusRate":r1(len([v for v in t["all"] if v>0])/n*100),
            "spAvg":r1(avg(t["sp"])) if t["sp"] else None,
            "nmAvg":r1(avg(t["nm"])) if t["nm"] else None,
            "spCount":len(t["sp"]),"nmCount":len(t["nm"]),
            "totalG":tg,"totalBB":tb,"totalRB":tr,
            "avgG":r1(tg/n) if n else 0,
            "rbRate":round(tg/tr) if tr>0 else None,
            "synRate":round(tg/(tb+tr)) if (tb+tr)>0 else None,
            "spRbRate":round(sg/sr) if sr>0 else None,
            "nmRbRate":round(ng/nr) if nr>0 else None,
            "bayesProbAll":calc_bayes_prob(t["model"],tg,tb,tr),
            "bayesProbSp":calc_bayes_prob(t["model"],sg,sb,sr),
            "bayesProbNm":calc_bayes_prob(t["model"],ng,nb,nr),
            "confidence":"高" if n>=30 else "中" if n>=15 else "低",
        })
    result.sort(key=lambda x: x["taiNum"])
    return result

def compute_model_stats(rows, special):
    by_model = defaultdict(lambda: {"all":[],"sp":[],"nm":[],"g":[],"bb":[],"rb":[],"this_month":[],"last_month":[]})
    latest = max(r["date"] for r in rows)
    this_m = date(latest.year, latest.month, 1)
    last_m = date(latest.year, latest.month-1, 1) if latest.month>1 else date(latest.year-1,12,1)
    last_m_end = date(latest.year, latest.month, 1) - timedelta(days=1)
    for r in rows:
        m = by_model[r["model"]]
        m["all"].append(r["diff"]); m["g"].append(r["g"]); m["bb"].append(r["bb"]); m["rb"].append(r["rb"])
        if r["day"] in special: m["sp"].append(r["diff"])
        else: m["nm"].append(r["diff"])
        d = r["date"].date()
        if d >= this_m: m["this_month"].append(r["diff"])
        elif last_m <= d <= last_m_end: m["last_month"].append(r["diff"])
    result = []
    for model, m in by_model.items():
        tg=sum(m["g"]); tb=sum(m["bb"]); tr=sum(m["rb"])
        total_in=tg*3; total_out=total_in+sum(m["all"])
        result.append({
            "model":model,
            "allAvg":r1(avg(m["all"])),"count":len(m["all"]),
            "spAvg":r1(avg(m["sp"])) if m["sp"] else None,"spCount":len(m["sp"]),
            "nmAvg":r1(avg(m["nm"])) if m["nm"] else None,"nmCount":len(m["nm"]),
            "mechRitu":r1(total_out/total_in*100) if total_in>0 else None,
            "rbRate":round(tg/tr) if tr>0 else None,
            "synRate":round(tg/(tb+tr)) if (tb+tr)>0 else None,
            "thisMonthAvg":r1(avg(m["this_month"])) if m["this_month"] else None,
            "thisMonthCount":len(m["this_month"]),
            "lastMonthAvg":r1(avg(m["last_month"])) if m["last_month"] else None,
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
    all_diffs=[r["diff"] for r in rows]
    baseline=avg(all_diffs)
    def calc(matched):
        diffs=[p["next"]["diff"] for p in matched]
        if not diffs: return {"count":0,"avg":None,"plusRate":None,"vsBaseline":None}
        a=avg(diffs)
        return {"count":len(diffs),"avg":r1(a),"plusRate":r1(len([v for v in diffs if v>0])/len(diffs)*100),"vsBaseline":r1(a-baseline)}
    return {
        "__baseline":{"label":"全期間平均","count":len(all_diffs),"avg":r1(baseline),"plusRate":r1(len([v for v in all_diffs if v>0])/len(all_diffs)*100),"vsBaseline":0},
        "凹み_2000以上":    {"label":"前日差枚 -2000以下",           **calc([p for p in pairs if p["prev"]["diff"]<=-2000])},
        "凹み_1000_2000":   {"label":"前日差枚 -1000〜-2000",        **calc([p for p in pairs if -2000<p["prev"]["diff"]<=-1000])},
        "凹み_500_1000":    {"label":"前日差枚 -500〜-1000",         **calc([p for p in pairs if -1000<p["prev"]["diff"]<=-500])},
        "凹み_0_500":       {"label":"前日差枚 0〜-500",             **calc([p for p in pairs if -500<p["prev"]["diff"]<0])},
        "プラス":           {"label":"前日差枚 プラス",               **calc([p for p in pairs if p["prev"]["diff"]>0])},
        "プラス500以上":    {"label":"前日差枚 +500以上",             **calc([p for p in pairs if p["prev"]["diff"]>=500])},
        "RB先行":           {"label":"前日RB先行不発",               **calc([p for p in pairs if p["prev"]["isRBLead"] and p["prev"]["diff"]<0])},
        "凹み_非特定日翌日":{"label":"前日凹み（翌日が特定日でない）",**calc([p for p in pairs if p["prev"]["diff"]<0 and p["next"]["day"] not in special])},
        "凹み_特定日翌日":  {"label":"前日凹み（翌日が特定日）",      **calc([p for p in pairs if p["prev"]["diff"]<0 and p["next"]["day"] in special])},
        "特定日翌日":       {"label":"特定日翌日の台",                **calc([p for p in pairs if p["prev"]["day"] in special])},
    }

def compute_heatmap(rows):
    heat = defaultdict(lambda: {"diffs":[],"g":[],"count":0,"highSet":0})
    def add(key, r):
        heat[key]["diffs"].append(r["diff"]); heat[key]["g"].append(r["g"])
        heat[key]["count"]+=1
        if r["isHighSetRBLead"]: heat[key]["highSet"]+=1
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
        ti=sum(v["g"])*3; to=ti+sum(v["diffs"])
        result[k]={"avg":r1(avg(v["diffs"])),"ritu":r1(to/ti*100) if ti>0 else None,"win":r1(len([d for d in v["diffs"] if d>0])/v["count"]*100),"set456":r1(v["highSet"]/v["count"]*100),"count":v["count"]}
    return result

def compute_week_matrix(rows):
    wm=defaultdict(lambda: {"diffs":[],"g":[],"count":0,"highSet":0})
    for r in rows:
        week=(r["day"]-1)//7+1; key=f"{week}_{r['weekday']}"
        wm[key]["diffs"].append(r["diff"]); wm[key]["g"].append(r["g"])
        wm[key]["count"]+=1
        if r["isHighSetRBLead"]: wm[key]["highSet"]+=1
    result={}
    for k,v in wm.items():
        if v["count"]<3: continue
        ti=sum(v["g"])*3; to=ti+sum(v["diffs"])
        result[k]={"avg":r1(avg(v["diffs"])),"ritu":r1(to/ti*100) if ti>0 else None,"win":r1(len([d for d in v["diffs"] if d>0])/v["count"]*100),"set456":r1(v["highSet"]/v["count"]*100),"count":v["count"]}
    return result

if __name__ == "__main__":
    print("=== compute.py 開始 ===")
    rows = load_raw()
    stores = list(set(r["store"] for r in rows))

    output = {
        "updated_at": date.today().strftime("%Y-%m-%d"),
        "stores": stores,
        "specialByStore": STORE_SPECIAL,
        "byStore": {}
    }

    for store in stores:
        special = STORE_SPECIAL.get(store, [1,11,21,31])
        store_rows = [r for r in rows if r["store"]==store]
        print(f"集計中: {store} ({len(store_rows)}行) 特定日:{special}")
        output["byStore"][store] = {
            "special": special,
            "dayStats": compute_day_stats(store_rows, special),
            "modelStats": compute_model_stats(store_rows, special),
            "nextStats": compute_next_day(store_rows, special),
            "heatmap": compute_heatmap(store_rows),
            "weekMatrix": compute_week_matrix(store_rows),
            "taiDetail": compute_tai_detail(store_rows, special),
        }

    with open(f"{REPO_DIR}/data.json","w",encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)
    print("✅ data.json出力完了")
