# -*- coding: utf-8 -*-
"""领域层：聚合与指标（**纯函数，无 IO、无全局状态**）。

输入 orders.json 的原始 dict，输出 model dict（前后端唯一契约）。
所有阈值/预算/分类关键词来自 ``config``，本模块只负责算。
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from .._schema import SCHEMA_VERSION
from .. import config as C

# --------------------------------------------------------------- 基础解析


def parse_dt(s):
    """宽容地解析时间字符串，失败返回 None。"""
    if not isinstance(s, str) or not s.strip():
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def categorize(name):
    """按关键词把单品名归类。规则见 config.CATEGORY_RULES。"""
    n = name or ""
    for label, keywords in C.CATEGORY_RULES:
        if any(k in n for k in keywords):
            return label
    return C.CATEGORY_FALLBACK


def week_start(d):
    return d - timedelta(days=d.weekday())


def time_bucket(hour):
    """把小时映射到 config.TIME_BUCKETS 里的标签。"""
    for label, start, end in C.TIME_BUCKETS:
        if start <= end:
            if start <= hour <= end:
                return label
        elif hour >= start or hour <= end:  # 跨零点
            return label
    return C.TIME_BUCKETS[-1][0]


def build_nutrition_map(data):
    """{单品名: kcal}；无法解析的记为 None（保持「匹配不上」与「0 热量」可区分）。"""
    out = {}
    for row in data.get("nutrition", []) or []:
        if not isinstance(row, dict):
            continue
        name = row.get("productName") or row.get("name")
        if not name:
            continue
        raw = row.get("energyKcal")
        try:
            out[name] = float(raw)
        except (TypeError, ValueError):
            out[name] = None
    return out


# --------------------------------------------------------------- 归一化

def normalize_orders(data, nutri):
    """orders.json → [{dt, hour, week, total, calories, items[]}]，跳过时间非法的单。"""
    orders = []
    for raw in data.get("orders", []) or []:
        if not isinstance(raw, dict):
            continue
        dt = parse_dt(raw.get("datetime", ""))
        if dt is None:
            continue
        items, cal = [], 0.0
        for it in raw.get("items", []) or []:
            if not isinstance(it, dict):
                continue
            name = it.get("name", "") or ""
            try:
                qty = int(it.get("qty", 1) or 1)
            except (TypeError, ValueError):
                qty = 1
            try:
                price = float(it.get("price", 0) or 0)
            except (TypeError, ValueError):
                price = 0.0
            unit_kcal = nutri.get(name)
            kcal = unit_kcal * qty if isinstance(unit_kcal, (int, float)) else 0.0
            cal += kcal
            items.append({
                "name": name, "qty": qty, "price": price,
                "category": categorize(name), "calories": kcal,
            })
        try:
            total = float(raw.get("total", 0) or 0)
        except (TypeError, ValueError):
            total = 0.0
        orders.append({
            "id": raw.get("order_id", "") or "",
            "dt": dt, "hour": dt.hour, "week": week_start(dt),
            "channel": raw.get("channel", "") or "",
            "store": raw.get("store", "") or "",
            "total": total, "calories": cal, "items": items,
        })
    return orders


# --------------------------------------------------------------- 指标

def _weekly(orders):
    acc = defaultdict(lambda: {"cal": 0.0, "spend": 0.0, "n": 0})
    for o in orders:
        w = acc[o["week"]]
        w["cal"] += o["calories"]
        w["spend"] += o["total"]
        w["n"] += 1
    keys = sorted(acc)
    return [
        {
            "label": "%d/%d" % (w.month, w.day),
            "start": w.strftime("%Y-%m-%d"),
            "calories": round(acc[w]["cal"]),
            "spend": round(acc[w]["spend"], 2),
            "orders": acc[w]["n"],
        }
        for w in keys
    ]


def _categories(orders):
    spend, cal, cnt = defaultdict(float), defaultdict(float), defaultdict(int)
    for o in orders:
        for it in o["items"]:
            c = it["category"]
            spend[c] += it["price"] * it["qty"]
            cal[c] += it["calories"]
            cnt[c] += it["qty"]
    rows = [
        {"name": k, "spend": round(v, 2), "calories": round(cal[k]), "count": cnt[k]}
        for k, v in spend.items()
    ]
    order_index = {n: i for i, n in enumerate(C.CATEGORY_ORDER)}
    rows.sort(key=lambda r: (order_index.get(r["name"], 99), -r["spend"]))
    return rows


def _top_items(orders, limit):
    cnt, spend = Counter(), defaultdict(float)
    for o in orders:
        for it in o["items"]:
            cnt[it["name"]] += it["qty"]
            spend[it["name"]] += it["price"] * it["qty"]
    return [
        {"name": n, "count": c, "spend": round(spend[n], 2)}
        for n, c in cnt.most_common(limit)
    ]


def _time_of_day(orders):
    c = Counter(time_bucket(o["hour"]) for o in orders)
    return [{"label": lab, "count": c.get(lab, 0)} for lab, _, _ in C.TIME_BUCKETS]


def _weekdays(orders):
    c = Counter(o["dt"].weekday() for o in orders)
    return [{"label": nm, "count": c.get(i, 0)} for i, nm in enumerate(C.WEEKDAY_NAMES)]


def derive_persona(orders):
    """消费人格：只依赖已算好的计数与阈值，规则集中在 config。"""
    n = len(orders)
    if n == 0:
        return {"tags": [], "main": "麦门常客", "desc": "稳定的幸福，是一份熟悉的味道。",
                "keywords": []}
    late = sum(1 for o in orders if o["hour"] >= C.LATE_NIGHT_FROM or o["hour"] <= C.LATE_NIGHT_TO)
    breakfast = sum(1 for o in orders if C.BREAKFAST_FROM <= o["hour"] <= C.BREAKFAST_TO)
    avg = sum(o["total"] for o in orders) / n
    cats = _categories(orders)
    top_cat = cats[0]["name"] if cats else "主餐"
    wd = Counter(o["dt"].weekday() for o in orders)
    top_wd = max(wd.items(), key=lambda x: x[1])

    tags = []
    if late / n > C.PERSONA_LATE_NIGHT_RATE:
        tags.append({"name": "深夜碳水战士", "why": "夜深了，麦麦才是你的加油站。"})
    elif breakfast / n > C.PERSONA_BREAKFAST_RATE:
        tags.append({"name": "早起元气派", "why": "一天的好状态从麦满分开始。"})
    if top_wd[0] == 2 and top_wd[1] >= C.PERSONA_WEEKDAY_MIN:
        tags.append({"name": "周三快乐汉堡人", "why": "周三的快乐，是巨无霸给的。"})
    if avg > C.PERSONA_BIG_SPENDER:
        tags.append({"name": "麦门土豪", "why": "套餐加购从不手软。"})
    if not tags:
        tags.append({"name": "麦门常客", "why": "稳定的幸福，是一份熟悉的味道。"})
    if top_cat == "甜品":
        tags.append({"name": "甜度超标", "why": "正餐可以省，甜品不能少。"})

    return {
        "tags": tags,
        "main": tags[0]["name"],
        "desc": "；".join(t["why"] for t in tags),
        "keywords": [t["name"] for t in tags] + [top_cat],
    }


def compute_metrics(orders, campaigns=None, now=None):
    """核心指标。``orders`` 由 normalize_orders 产出；空列表 → 返回 None（走空态）。"""
    campaigns = campaigns or []
    if not orders:
        return None

    n = len(orders)
    total_spend = sum(o["total"] for o in orders)
    total_cal = sum(o["calories"] for o in orders)
    dts = [o["dt"] for o in orders]
    first, last = min(dts), max(dts)
    # span_days 按「自然日」计：首尾都归零到当天 00:00 再相减。
    # 否则 10-05 12:00 → 10-12 00:00 会被算成 6 天（丢掉首日半天）。
    day0 = lambda d: d.replace(hour=0, minute=0, second=0, microsecond=0)  # noqa: E731
    end = day0(now or C.TODAY or last)
    span_days = max(1, (end - day0(first)).days + 1)

    weekly = _weekly(orders)
    categories = _categories(orders)
    top_items = _top_items(orders, C.TOP_ITEMS_LIMIT)
    tod = _time_of_day(orders)
    weekdays = _weekdays(orders)
    persona = derive_persona(orders)

    late_night = sum(1 for o in orders if o["hour"] >= C.LATE_NIGHT_FROM or o["hour"] <= C.LATE_NIGHT_TO)
    breakfast = sum(1 for o in orders if C.BREAKFAST_FROM <= o["hour"] <= C.BREAKFAST_TO)
    big = max(orders, key=lambda o: o["total"])
    max_cal_order = max(orders, key=lambda o: o["calories"])
    stores = Counter(o["store"] for o in orders if o["store"])
    top_store, top_store_n = stores.most_common(1)[0] if stores else ("—", 0)
    peak = max(tod, key=lambda x: x["count"])
    top_wd = max(weekdays, key=lambda x: x["count"])
    top_week = max(weekly, key=lambda x: x["calories"]) if weekly else None
    busiest_day = Counter(o["dt"].strftime("%Y-%m-%d") for o in orders).most_common(1)[0]

    spend_series = [w["spend"] for w in weekly]

    model = {
        "schema_version": SCHEMA_VERSION,
        "source": "unknown",   # 由 caller（cli）覆盖为 real / demo
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "period": {
            "first_date": first.strftime("%Y-%m-%d"),
            "last_date": last.strftime("%Y-%m-%d"),
            "span_days": span_days,
            "year": last.strftime("%Y"),
            "month": last.strftime("%m"),
        },
        "overview": {
            "total_orders": n,
            "total_spend": round(total_spend, 2),
            "total_calories": round(total_cal),
            "avg_spend": round(total_spend / n, 2),
            "avg_calories": round(total_cal / n),
            "freq_days": round(span_days / n, 1),
            "max_order_spend": round(big["total"], 2),
            "max_order_name": (big["items"][0]["name"] if big["items"] else "——"),
            "max_order_calories": round(max_cal_order["calories"]),
            "max_order_calories_name": (max_cal_order["items"][0]["name"]
                                        if max_cal_order["items"] else "——"),
            "top_store": top_store,
            "top_store_orders": top_store_n,
            "store_count": len(stores),
            "channels": dict(Counter(o["channel"] for o in orders if o["channel"])),
            "takeout_orders": sum(1 for o in orders if o["channel"] not in ("到店", "")),
        },
        "weekly": {
            "points": weekly,
            "budget": C.WEEKLY_CAL_BUDGET,
            "calories_series": [w["calories"] for w in weekly],
            "spend_series": spend_series,
            "labels": [w["label"] for w in weekly],
            "max_calories": max((w["calories"] for w in weekly), default=0),
            "avg_calories": round(sum(w["calories"] for w in weekly) / len(weekly)) if weekly else 0,
            "over_budget_weeks": sum(1 for w in weekly if w["calories"] > C.WEEKLY_CAL_BUDGET),
            "peak": top_week,
        },
        "categories": categories,
        "top_items": top_items,
        "time_of_day": tod,
        "weekdays": weekdays,
        "persona": persona,
        "campaigns": [
            {"date": (c.get("date") or "").strip(),
             "title": (c.get("title") or "").strip(),
             "desc": (c.get("desc") or "").strip()}
            for c in campaigns if isinstance(c, dict)
        ][:C.CAMPAIGN_LIMIT],
        "fun": {
            "big_mac_count": int(total_spend // C.BIG_MAC_PRICE),
            "run_hours": max(1, round(total_cal / C.RUN_KCAL_PER_HOUR)),
            "late_night_orders": late_night,
            "breakfast_orders": breakfast,
            "takeout_rate": round(
                sum(1 for o in orders if o["channel"] not in ("到店", "")) / n, 3),
        },
        "peaks": {
            "time_of_day": peak,
            "weekday": top_wd,
            "busiest_day": {"date": busiest_day[0], "orders": busiest_day[1]},
        },
    }
    model["highlight"] = _highlight(model)
    return model


def _highlight(model):
    """高光时刻：挑出最有「话题度」的一条，供高光屏做主角。"""
    ov, peaks = model["overview"], model["peaks"]
    cands = [
        {"kind": "spend", "title": "最贵的一单",
         "value": "¥%.0f" % ov["max_order_spend"], "note": ov["max_order_name"]},
        {"kind": "calories", "title": "最猛的一单",
         "value": "%d kcal" % ov["max_order_calories"], "note": ov["max_order_calories_name"]},
        {"kind": "late", "title": "深夜出没",
         "value": "%d 次" % model["fun"]["late_night_orders"], "note": "21 点后 / 凌晨下单"},
        {"kind": "store", "title": "主场餐厅",
         "value": ov["top_store"], "note": "共 %d 单" % ov["top_store_orders"]},
        {"kind": "day", "title": "最忙的一天",
         "value": peaks["busiest_day"]["date"], "note": "%d 单" % peaks["busiest_day"]["orders"]},
    ]
    # 以「深夜占比」为主角判据：超过阈值就让深夜上头条。
    late_ratio = model["fun"]["late_night_orders"] / max(1, ov["total_orders"])
    if late_ratio > C.PERSONA_LATE_NIGHT_RATE:
        main = next(c for c in cands if c["kind"] == "late")
    elif model["weekly"]["peak"]:
        w = model["weekly"]["peak"]
        main = {"kind": "week", "title": "热量巅峰周",
                "value": "%d kcal" % w["calories"], "note": "从 %s 那一周开始" % w["label"]}
    else:
        main = cands[0]
    return {"main": main, "others": [c for c in cands if c is not main][:3]}


def build_model(data, now=None):
    """统一入口：orders.json dict → model dict（或 None 表示空态）。"""
    nutri = build_nutrition_map(data)
    orders = normalize_orders(data, nutri)
    return compute_metrics(orders, data.get("campaigns"), now=now)
