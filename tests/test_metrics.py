#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""领域层**数值正确性**测试（补齐原 test_report.py 只测字符串的缺口）。

运行:
  python -m unittest tests.test_metrics -v
"""
import json
import os
import sys
import unittest
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from mcd_report.domain import metrics as M  # noqa: E402
from mcd_report import config as C  # noqa: E402


def make_order(oid, dt, items, total=None):
    """items: [(name, price, qty), ...]"""
    norm = [{"name": n, "price": p, "qty": q} for n, p, q in items]
    return {
        "order_id": oid,
        "datetime": dt,
        "channel": "到店",
        "store": "测试店",
        "items": norm,
        "total": total if total is not None else sum(i["price"] * i["qty"] for i in norm),
    }


class TestParsing(unittest.TestCase):
    def test_parse_dt_variants(self):
        self.assertEqual(M.parse_dt("2026-10-01T12:30:00"), datetime(2026, 10, 1, 12, 30))
        self.assertEqual(M.parse_dt("2026-10-01 12:30:00"), datetime(2026, 10, 1, 12, 30))
        self.assertEqual(M.parse_dt("2026-10-01"), datetime(2026, 10, 1))
        self.assertIsNone(M.parse_dt(""))
        self.assertIsNone(M.parse_dt("not a date"))
        self.assertIsNone(M.parse_dt(None))

    def test_categorize(self):
        self.assertEqual(M.categorize("巨无霸"), "主餐")
        self.assertEqual(M.categorize("中薯条"), "小吃")
        self.assertEqual(M.categorize("可乐中杯"), "饮品")
        self.assertEqual(M.categorize("草莓麦旋风"), "甜品")
        self.assertEqual(M.categorize("不明物体"), "其他")
        self.assertEqual(M.categorize(""), "其他")

    def test_time_bucket_including_midnight(self):
        self.assertEqual(M.time_bucket(7), "早 (5-9)")
        self.assertEqual(M.time_bucket(12), "午 (10-13)")
        self.assertEqual(M.time_bucket(15), "下午 (14-16)")
        self.assertEqual(M.time_bucket(19), "晚 (17-20)")
        self.assertEqual(M.time_bucket(23), "夜 (21-4)")
        self.assertEqual(M.time_bucket(2), "夜 (21-4)")   # 跨零点
        self.assertEqual(M.time_bucket(4), "夜 (21-4)")   # 闭合边界
        self.assertEqual(M.time_bucket(5), "早 (5-9)")

    def test_week_start_is_monday(self):
        # 2026-10-07 是周三
        self.assertEqual(M.week_start(datetime(2026, 10, 7)).strftime("%Y-%m-%d"), "2026-10-05")


class TestNumbers(unittest.TestCase):
    """核心：数值必须能被独立复算。"""

    def setUp(self):
        self.nutri = {"巨无霸": 500.0, "中薯条": 340.0, "可乐中杯": 150.0}
        self.data = {
            "nutrition": [{"productName": k, "energyKcal": str(v)}
                          for k, v in self.nutri.items()],
            "campaigns": [],
            "orders": [
                make_order("A", "2026-10-05T12:00:00",
                           [("巨无霸", 24, 1), ("中薯条", 12, 1), ("可乐中杯", 9, 1)]),
                make_order("B", "2026-10-06T19:30:00", [("巨无霸", 24, 2)]),
                make_order("C", "2026-10-12T23:10:00", [("中薯条", 12, 3)]),
            ],
        }
        self.model = M.build_model(self.data, now=datetime(2026, 10, 12))

    def test_total_spend_equals_sum(self):
        expected = 45 + 48 + 36
        self.assertEqual(self.model["overview"]["total_spend"], expected)

    def test_total_calories_equals_itemwise_sum(self):
        # (500+340+150) + (500*2) + (340*3) = 990 + 1000 + 1020
        expected = 990 + 1000 + 1020
        self.assertEqual(self.model["overview"]["total_calories"], expected)

    def test_avg_spend_and_calories(self):
        # A: ¥45 / 990kcal，B: ¥48 / 1000kcal，C: ¥36 / 1020kcal
        self.assertEqual(self.model["overview"]["avg_spend"], round(129 / 3, 2))
        self.assertEqual(self.model["overview"]["avg_calories"], round(3010 / 3))

    def test_category_spend_partitions_total(self):
        total = sum(c["spend"] for c in self.model["categories"])
        self.assertAlmostEqual(total, self.model["overview"]["total_spend"], places=2)

    def test_category_calories_partitions_total(self):
        total = sum(c["calories"] for c in self.model["categories"])
        self.assertEqual(total, self.model["overview"]["total_calories"])

    def test_weekly_series_sums_to_total(self):
        self.assertEqual(sum(self.model["weekly"]["calories_series"]),
                         self.model["overview"]["total_calories"])
        self.assertAlmostEqual(sum(self.model["weekly"]["spend_series"]),
                               self.model["overview"]["total_spend"], places=2)

    def test_top_items_ordering(self):
        names = [t["name"] for t in self.model["top_items"]]
        self.assertEqual(names[0], "中薯条")   # 1+3 = 4 份
        self.assertEqual(names[1], "巨无霸")   # 3 份
        counts = {t["name"]: t["count"] for t in self.model["top_items"]}
        self.assertEqual(counts["中薯条"], 4)
        self.assertEqual(counts["巨无霸"], 3)

    def test_time_of_day_counts(self):
        tod = {r["label"]: r["count"] for r in self.model["time_of_day"]}
        self.assertEqual(tod["午 (10-13)"], 1)
        self.assertEqual(tod["晚 (17-20)"], 1)
        self.assertEqual(tod["夜 (21-4)"], 1)
        self.assertEqual(sum(tod.values()), 3)

    def test_span_days_uses_provided_now(self):
        # 首单 10-05 → now=10-12，含首尾 = 8 天
        self.assertEqual(self.model["period"]["span_days"], 8)

    def test_fun_metrics(self):
        # 总花费 129 → 129 // 25 = 5 个巨无霸
        self.assertEqual(self.model["fun"]["big_mac_count"], 5)
        self.assertEqual(self.model["fun"]["late_night_orders"], 1)
        self.assertEqual(self.model["fun"]["breakfast_orders"], 0)

    def test_max_order_picks_biggest(self):
        self.assertEqual(self.model["overview"]["max_order_spend"], 48)
        self.assertEqual(self.model["overview"]["max_order_name"], "巨无霸")
        self.assertEqual(self.model["overview"]["max_order_calories"], 1020)

    def test_schema_version_present(self):
        self.assertIn("schema_version", self.model)


class TestEdgeCases(unittest.TestCase):
    def test_empty_orders_returns_none(self):
        self.assertIsNone(M.build_model({"orders": [], "nutrition": []}))

    def test_bad_datetime_skipped(self):
        m = M.build_model({"orders": [make_order("X", "垃圾时间", [("巨无霸", 24, 1)])]})
        self.assertIsNone(m)   # 唯一一单时间非法 → 视作空

    def test_nutrition_none_keeps_calories_zero_but_not_crash(self):
        m = M.build_model({"orders": [make_order("X", "2026-10-05T12:00:00",
                                                 [("神秘新品", 20, 2)])]})
        self.assertEqual(m["overview"]["total_calories"], 0)
        self.assertEqual(m["overview"]["total_spend"], 40)

    def test_bad_price_falls_back_to_total(self):
        o = make_order("X", "2026-10-05T12:00:00", [("巨无霸", 24, 1)])
        o["items"][0]["price"] = "不是数字"   # 单价坏掉
        m = M.build_model({"orders": [o], "nutrition": []})
        # 单价解析失败记 0，但订单 total 是独立字段，仍然可信
        self.assertEqual(m["overview"]["total_spend"], 24)

    def test_bad_total_falls_back_to_zero(self):
        o = make_order("X", "2026-10-05T12:00:00", [("巨无霸", 24, 1)])
        o["total"] = "None"
        m = M.build_model({"orders": [o], "nutrition": []})
        self.assertEqual(m["overview"]["total_spend"], 0)

    def test_persona_fallback_when_no_rule_matches(self):
        m = M.build_model({"orders": [make_order("X", "2026-10-07T12:00:00",
                                                 [("巨无霸", 24, 1)])]})
        self.assertEqual(m["persona"]["main"], "麦门常客")

    def test_persona_late_night_rule(self):
        orders = [make_order("l%d" % i, "2026-10-0%dT23:30:00" % i, [("中薯条", 12, 1)])
                  for i in range(1, 5)]
        orders.append(make_order("y", "2026-10-05T12:00:00", [("中薯条", 12, 1)]))
        m = M.build_model({"orders": orders})
        # 4/5 = 80% > 25% 阈值
        self.assertEqual(m["persona"]["main"], "深夜碳水战士")

    def test_highlight_has_main(self):
        m = M.build_model({"orders": [make_order("X", "2026-10-06T12:00:00", [("巨无霸", 24, 1)])]})
        self.assertIn("main", m["highlight"])
        self.assertIn("value", m["highlight"]["main"])


class TestSampleFixture(unittest.TestCase):
    """拿真实演示数据做一次端到端数值自洽校验。"""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(ROOT, "sample_orders.json")
        if not os.path.exists(path):
            raise unittest.SkipTest("sample_orders.json 不存在")
        with open(path, encoding="utf-8") as f:
            cls.data = json.load(f)
        cls.model = M.build_model(cls.data)

    def test_model_not_none(self):
        self.assertIsNotNone(self.model)

    def test_partitions(self):
        m = self.model
        self.assertEqual(sum(c["calories"] for c in m["categories"]),
                         m["overview"]["total_calories"])
        self.assertAlmostEqual(sum(c["spend"] for c in m["categories"]),
                               m["overview"]["total_spend"], places=1)

    def test_no_negative_values(self):
        ov = self.model["overview"]
        for k in ("total_orders", "total_spend", "total_calories", "avg_spend"):
            self.assertGreaterEqual(ov[k], 0, k)


if __name__ == "__main__":
    unittest.main(verbosity=2)
