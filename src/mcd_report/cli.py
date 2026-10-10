# -*- coding: utf-8 -*-
"""编排层：把 ingest → domain → render 串起来，落盘产物。

这是唯一知道「整个流程长什么样」的地方；上面三层互不知道彼此存在。
"""
import json
import os
import sys

from . import config as C
from ._schema import ENGINE, SCHEMA_VERSION
from .domain import metrics
from .render import page


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def detect_source(data, path):
    """判定 real / demo。宁可标 demo，也不要让观众误以为是真的。"""
    if data.get("demo") is True:
        return "demo"
    src = str(data.get("source", "")).lower()
    if any(k in src for k in ("sample", "demo", "演示", "mock", "fake")):
        return "demo"
    low = str(path).lower()
    if any(k in low for k in ("sample", "demo", "mock", "fake")):
        return "demo"
    return "real"


def generate(in_path, out_path, theme=None, engine=ENGINE, scenes=None, quiet=False):
    """端到端生成一份报告，返回 (out_path, summary dict)。"""
    data = load_json(in_path)
    model = metrics.build_model(data)

    source = detect_source(data, in_path)
    if model is not None:
        model["source"] = source
    else:
        # 空态也要带来源信息，供徽章渲染
        model = None

    html = page.build_html(
        model,
        theme=theme or "dark",
        enabled=_resolve_scenes(scenes),
        engine=engine,
    )
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    summary = {
        "out": out_path,
        "source": source,
        "engine": engine,
        "schema_version": SCHEMA_VERSION,
        "bytes": len(html.encode("utf-8")),
        "empty": model is None,
    }
    if model is not None:
        summary.update({
            "orders": model["overview"]["total_orders"],
            "spend": model["overview"]["total_spend"],
            "calories": model["overview"]["total_calories"],
            "persona": model["persona"]["main"],
        })
    if not quiet:
        _print_summary(summary)
    return out_path, summary


def _resolve_scenes(override):
    """命令行 --only/--skip 覆盖 config 的板块开关。"""
    enabled = dict(C.SCENES_ENABLED)
    if not override:
        return enabled
    only, skip = override
    if only:
        wanted = {s.strip() for s in only.split(",") if s.strip()}
        for k in enabled:
            enabled[k] = k in wanted
        # cover/outro 是叙事骨架，始终保留
        enabled["cover"] = enabled["outro"] = True
    if skip:
        for s in skip.split(","):
            enabled[s.strip()] = False
    return enabled


def _print_summary(s):
    if s["empty"]:
        print("[ok] %s  (无订单 → 空态引导屏, %d KB)" % (s["out"], s["bytes"] // 1024))
        return
    print("[ok] %s" % s["out"])
    print("     引擎 %s · schema %s · %d KB"
          % (s["engine"], s["schema_version"], s["bytes"] // 1024))
    print("     订单 %d 单 · ¥%.0f · %d kcal · 人格「%s」 · 来源 %s"
          % (s["orders"], s["spend"], s["calories"], s["persona"], s["source"]))
    if s["source"] == "demo":
        print("     提示：当前为演示数据，报告内已标注水印")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if any(a in ("-h", "--help") for a in argv):
        print(__doc__)
        return 0

    in_path, out_path = "orders.json", "report.html"
    theme, engine, only, skip = None, ENGINE, None, None

    i = 0
    positional = []
    while i < len(argv):
        a = argv[i]
        if a == "--theme" and i + 1 < len(argv):
            theme = argv[i + 1]; i += 2; continue
        if a == "--engine" and i + 1 < len(argv):
            engine = argv[i + 1]; i += 2; continue
        if a == "--only" and i + 1 < len(argv):
            only = argv[i + 1]; i += 2; continue
        if a == "--skip" and i + 1 < len(argv):
            skip = argv[i + 1]; i += 2; continue
        if a.startswith("-"):
            i += 1; continue
        positional.append(a); i += 1

    if positional:
        in_path = positional[0]
    if len(positional) > 1:
        out_path = positional[1]
    if not os.path.exists(in_path):
        print("[err] 找不到输入文件：%s" % in_path, file=sys.stderr)
        print("      先跑 python scripts/make_sample.py 生成演示数据，"
              "或 python scripts/fetch_orders.py all 拉真实订单。", file=sys.stderr)
        return 2

    generate(in_path, out_path, theme=theme, engine=engine,
             scenes=(only, skip))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
