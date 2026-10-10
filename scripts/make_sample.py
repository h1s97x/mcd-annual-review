#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成贴近真实的样例订单 sample_orders.json（用真实餐品名 + 真实营养表算热量）。
仅用于开发期演示报告可视化；真实使用时由 fetch_orders.py 拉取用户真实订单覆盖。
"""
import json
import random
from datetime import datetime, timedelta

random.seed(20261010)

# 常见单品（名称必须与 list-nutrition-foods 中的 productName 完全一致，热量才能对上）
PRICE = {
    "巨无霸": 24, "麦辣鸡腿汉堡": 21, "板烧鸡腿堡": 22, "双层吉士汉堡": 23,
    "麦香鱼": 22, "麦香鸡": 17, "吉士汉堡包": 13,
    "中薯条": 12, "大薯条": 15, "小薯条": 9, "迷你薯条": 7,
    "麦辣鸡翅-2块": 12, "麦乐鸡5块": 15,
    "可乐中杯": 9, "可乐大杯": 11, "可乐小杯": 7,
    "雪碧中杯": 9, "雪碧大杯": 11, "雪碧小杯": 7,
    "圆筒冰淇淋": 5, "朱古力新地": 10, "草莓新地": 10,
    "奥利奥麦旋风": 13, "草莓麦旋风": 13, "香芋派": 7, "菠萝派": 7,
    "猪柳蛋麦满分": 14, "猪柳麦满分": 12, "烟肉蛋麦满分": 13, "火腿扒麦满分": 12,
    "大脆鸡扒麦满分": 18, "原味板烧鸡腿麦满分": 16,
    "双层原味板烧鸡腿麦满分": 20,
    "大杯玉米杯": 9, "小杯玉米杯": 6,
}

# 套餐模板（名称, 数量）—一份套餐即一笔订单的主体
COMBOS = [
    [("巨无霸", 1), ("中薯条", 1), ("可乐中杯", 1)],
    [("麦辣鸡腿汉堡", 1), ("中薯条", 1), ("雪碧中杯", 1)],
    [("板烧鸡腿堡", 1), ("小薯条", 1), ("可乐中杯", 1)],
    [("双层吉士汉堡", 1), ("中薯条", 1), ("可乐中杯", 1)],
    [("麦香鱼", 1), ("中薯条", 1), ("雪碧中杯", 1)],
    [("麦香鸡", 1), ("小薯条", 1), ("可乐小杯", 1)],
    [("猪柳蛋麦满分", 1), ("小杯玉米杯", 1)],
    [("大脆鸡扒麦满分", 1), ("迷你薯条", 1), ("可乐中杯", 1)],
]

SINGLES = [
    [("麦辣鸡翅-2块", 1)], [("麦乐鸡5块", 1)], [("奥利奥麦旋风", 1)],
    [("香芋派", 1)], [("菠萝派", 1)], [("圆筒冰淇淋", 1)],
    [("朱古力新地", 1)], [("草莓麦旋风", 1)], [("大薯条", 1), ("可乐大杯", 1)],
]

# 时段权重：午/晚为主，含下午茶、夜宵、早餐
HOURS = [8, 8, 12, 12, 12, 13, 13, 18, 18, 19, 19, 20, 15, 21, 22, 23, 9, 12, 19, 2]

STORES = ["中央广场店", "滨江路店", "高铁站店", "科技园店"]
CHANNELS = ["到店", "麦乐送", "麦乐送", "到店"]


def make_order(i):
    r = random.random()
    if r < 0.62:
        template = random.choice(COMBOS)
    else:
        template = random.choice(SINGLES)
    items = [{"name": n, "price": PRICE[n], "qty": q} for n, q in template]
    total = round(sum(it["price"] * it["qty"] for it in items), 2)
    day_offset = random.randint(0, 55)
    hour = random.choice(HOURS)
    minute = random.choice([0, 15, 30, 45])
    dt = datetime(2026, 10, 10, 0, 0) - timedelta(days=day_offset) + timedelta(hours=hour, minutes=minute)
    return {
        "order_id": "MCD%06d" % (100000 + i),
        "datetime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "channel": random.choice(CHANNELS),
        "store": random.choice(STORES),
        "status": "已完成",
        "items": items,
        "total": total,
    }


def load_reference():
    """读取参考数据（真实营养表 / 活动）。

    原先直接 open("orders.json") —— 一旦该文件不存在（全新克隆、
    或用户还没拉过真实订单），脚本就直接崩，且报错指向「文件不存在」，
    让人以为是路径问题。这里改为：按优先级依次尝试，全都拿不到就
    给出**可执行的补救指引**，并用空表降级（热量会算成 0）。
    """
    import os
    for cand in ("orders.json", "sample_orders.json"):
        if not os.path.exists(cand):
            continue
        try:
            with open(cand, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError) as e:
            print("[warn] %s 读取失败（%s），跳过" % (cand, e))
            continue
        if d.get("nutrition"):
            print("[info] 参考数据取自 %s" % cand)
            return d
    print("[warn] 未找到含营养表的参考文件，热量将全部按 0 计算。")
    print("       想拿到真实热量：先跑 python scripts/fetch_orders.py all")
    return {}


def main():
    real = load_reference()
    orders = [make_order(i) for i in range(1, 41)]
    orders.sort(key=lambda o: o["datetime"])
    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "sample (演示数据)",
        "orders": orders,
        "nutrition": real.get("nutrition", []),
        "campaigns": real.get("campaigns", []),
        "coupons": real.get("coupons", []),
    }
    with open("sample_orders.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved sample_orders.json | orders=%d nutrition=%d" % (len(orders), len(out["nutrition"])))


if __name__ == "__main__":
    main()
