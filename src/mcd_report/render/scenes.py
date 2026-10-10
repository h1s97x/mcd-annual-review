# -*- coding: utf-8 -*-
"""场景层：把 model 渲染成「一屏一主题」的章节 DOM。

设计原则（P5R 波普朋克版）
------------------------
1. **每屏结构不套模板**：按内容选用不同的信息层级组合——
   有的主打「大字金句 + 数据」，有的主打「图表 + 小字注解」，
   有的主打「超大字 + 一行总结」。拒绝平铺直叙。
2. **信息必须分级**：每屏至少包含
   大字（.hero-num / .rant）· 中字（.title-slab / .tile-v）· 小字（.line / .footnote）
   三类中的两类以上，形成视觉层级。
3. **逐步演出**：元素按 ``data-beat`` 分拍，引擎一拍一拍放出来；
   点一下可加速。同一拍的多个元素同时入场。
4. **动效只挂 data 属性**：场景层不写 CSS 动画、不写 JS。
5. **不溢出**：每屏内容量受控，字号用 clamp/vh 双约束，避免超出视口。

返回 ``<section class="scene">`` 片段列表，由 ``page.py`` 组装。
"""
from . import charts, deco
import re as _re

# ---------------------------------------------------------------- 小工具


def _tile(k, v, d="", accent=False, beat=0, anim="fade"):
    """一张数据卡。v 若为纯数字/金额则自动放大（.num）。"""
    raw = _re.sub(r"<[^>]+>", "", str(v))          # 去掉可能的标签再判断
    is_num = bool(_re.fullmatch(
        r"[¥$]?[\d,]+(\.\d+)?\s*[%单份个天次元]?", raw.strip()))
    cls = "num" if is_num else ""
    if accent:
        cls += " acc"
    return ('<div class="tile" data-anim="%s" data-beat="%d">'
            '<div class="tile-k">%s</div>'
            '<div class="tile-v%s">%s</div>'
            '%s</div>') % (anim, beat, k, (" " + cls) if cls else "", v,
                           ('<div class="tile-d">%s</div>' % d) if d else "")


def _tiles(tiles, cls=""):
    return '<div class="tiles %s">%s</div>' % (cls, "".join(tiles))


def _count(value, prefix="", suffix="", decimals=0, cls="", dur=1250,
           beat=0, anim="fade"):
    """滚动计数的大数字。

    HTML 里写**真实值**（而不是 0），这样：
    - 禁用 JS / 动画被节流时，用户看到的仍是正确数字；
    - 屏幕阅读器与 PDF 导出拿到的是真值。
    JS 启用动效时会从这个真值"从 0 滚上来"，属渐进增强。
    """
    shown = ("{:,}".format(round(value)) if decimals == 0
             else "{:,.{d}f}".format(value, d=decimals))
    return ('<span class="hero-num %s" data-count="%s" data-prefix="%s" '
            'data-suffix="%s" data-decimals="%d" data-count-dur="%d" '
            'data-anim="%s" data-beat="%d">%s%s%s</span>'
            % (cls, value, prefix, suffix, decimals, dur, anim, beat,
               prefix, shown, suffix))


def _hero(inner, beat=0, anim="fade", unit=""):
    u = ('<span class="hero-unit">%s</span>' % unit) if unit else ""
    return ('<div class="hero" data-anim="%s" data-beat="%d">%s%s</div>'
            % (anim, beat, inner, u))


def _kicker(text, beat=0):
    return ('<div class="kicker" data-anim="slash" data-beat="%d">%s</div>'
            % (beat, text))


def _rant(html, beat=1, anim="fade", cls=""):
    return '<p class="rant %s" data-anim="%s" data-beat="%d">%s</p>' % (
        cls, anim, beat, html)


def _line(html, beat=0, anim="fade", cls=""):
    return '<div class="line %s" data-anim="%s" data-beat="%d">%s</div>' % (
        cls, anim, beat, html)


def _foot(html, beat=0):
    return '<div class="footnote" data-anim="fade" data-beat="%d">%s</div>' % (
        beat, html)


def _box(html, beat=0):
    return '<div class="chart-box" data-anim="scale" data-beat="%d">%s</div>' % (
        beat, html)


def _decor_layers():
    """P5R 装饰层：斜切色块 + 涂鸦线条。每个场景都铺一层。"""
    strokes = (
        '<svg viewBox="0 0 400 700" preserveAspectRatio="none" aria-hidden="true">'
        '<path d="M-20 120 L200 96" stroke-width="3" opacity=".55"/>'
        '<path d="M120 40 L150 210" stroke-width="2" opacity=".35"/>'
        '<path d="M330 300 L420 268" stroke-width="3" opacity=".5"/>'
        '<path d="M-10 470 L180 440" stroke-width="2" opacity=".32"/>'
        '<path d="M240 560 L400 524" stroke-width="3" opacity=".45"/>'
        '<path d="M60 640 L250 604" stroke-width="2" opacity=".3"/>'
        '</svg>')
    return ('<div class="slabs" aria-hidden="true"><i></i><i></i><i></i></div>'
            '<div class="strokes" aria-hidden="true">%s</div>' % strokes)


def _num(v, dec=0):
    return ("{:,}".format(round(v, dec)) if dec == 0
            else "{:,.1f}".format(v))


# ---------------------------------------------------------------- 场景


def scene_cover(m):
    """封面：超大字 + 衬底年份水印 + 进入按钮。"""
    per = m["period"]
    src = m["source"]
    badge = ("演示数据（非真实订单）" if src == "demo"
             else "麦当劳 MCP 实时数据")
    inner = (
        _kicker("McWrapped · 麦门年度账本", 0)
        + '<div class="cover-year" aria-hidden="true" data-anim="fade" data-beat="0">%s</div>'
        % per["year"]
        + _rant('这一年，<br/>你在麦门<br/>留下了 <span class="tilt">%d</span> 个瞬间'
                % m["overview"]["total_orders"], 1, "slide", "rant-cover")
        + _foot('数据来源：%s' % badge, 3)
        + '<button class="btn" id="startBtn" type="button" data-anim="scale" '
          'data-beat="2">翻开账本 ✦</button>'
        + _foot('<span class="check">✓</span> 授权麦当劳 MCP 对本人账号订餐数据'
                '做年度统计与展示', 3)
    )
    return _scene("cover", 0, "封面", inner, extra_class="scene-cover",
                  particles=26, decor="burger")


def scene_overview(m):
    """年度总览：主数字（下单次数）+ 金句 + 数据卡。"""
    ov, per = m["overview"], m["period"]
    inner = (
        _kicker("第一章 · 年度总览", 0)
        + _hero(_count(ov["total_orders"], dur=1300, beat=1), 1, "scale", "次下单")
        + _rant('平均每 <b>%s</b> 天，<br/>你就想再来一次' % ov["freq_days"], 2)
        + _tiles([
            _tile("主战场", ov["top_store"],
                  "在此下了 %d 单" % ov["top_store_orders"], True, 3),
            _tile("最常光顾", "%s" % m["peaks"]["weekday"]["label"],
                  "%d 单落在这天" % m["peaks"]["weekday"]["count"], False, 3),
            _tile("到店 / 外送",
                  "%d / %d" % (ov["total_orders"] - ov["takeout_orders"],
                               ov["takeout_orders"]),
                  "堂食与外送之比", False, 4),
            _tile("跨域时间", "%d 天" % per["span_days"],
                  "%s 起" % per["first_date"], False, 4),
        ])
    )
    return _scene("overview", 1, "年度总览", inner, particles=16, decor="fries")


def scene_spend(m):
    """真金白银：超大字金额（主角）+ 换算金句 + 两张卡。"""
    ov, fu, per = m["overview"], m["fun"], m["period"]
    inner = (
        _kicker("第二章 · 真金白银", 0)
        + _hero(_count(int(round(ov["total_spend"])), prefix="¥", dur=1500,
                       beat=1, cls="acc"), 1, "scale")
        + _rant('折合 <span class="big">%d</span> 个巨无霸，<br/>'
                '<span class="sm">平均每天为快乐买单 ¥%.1f</span>'
                % (fu["big_mac_count"],
                   ov["total_spend"] / max(1, per["span_days"])), 2)
        + _tiles([
            _tile("客单价", "¥%.1f" % ov["avg_spend"], "每单出手", True, 3),
            _tile("最贵一单", "¥%.0f" % ov["max_order_spend"],
                  ov["max_order_name"], False, 4),
        ], "three")
    )
    return _scene("spend", 2, "真金白银", inner, particles=18, decor="drink")


def scene_calories(m):
    """热量账本：折线图为主角（生长入场）+ 一行总结 + 两张卡。"""
    ov, wk, fu = m["overview"], m["weekly"], m["fun"]
    chart = charts.line_chart(wk["calories_series"], wk["labels"],
                              baseline=wk["budget"], unit="kcal")
    inner = (
        _kicker("第三章 · 热量账本", 0)
        + _hero(_count(ov["total_calories"], cls="acc wide", dur=1600,
                       beat=1), 1, "scale", "kcal")
        + _rant('大约要跑 <span class="big">%d</span> 小时<br/>'
                '<span class="sm">才能消耗掉这一年的快乐</span>'
                % fu["run_hours"], 2)
        + _box(chart, 3)
        + _foot('虚线为建议周预算 %s kcal · 有 <b>%d</b> 周超标'
                % ("{:,}".format(wk["budget"]), wk["over_budget_weeks"]), 4)
    )
    return _scene("calories", 3, "热量账本", inner, particles=14, decor="cone")


def scene_category(m):
    """品类偏好：环形图 + 金句点题（主角是图）。"""
    cats = m["categories"] or [{"name": "暂无数据", "spend": 1,
                                "calories": 0, "count": 0}]
    donut = charts.donut_chart(cats, "spend", center_label="总花费", unit="¥")
    top = cats[0]
    total_spend = sum(c["spend"] for c in cats) or 1
    share = top["spend"] / total_spend * 100
    rest = cats[1:4]
    legend = " · ".join("%s %d%%" % (c["name"], round(c["spend"] / total_spend * 100))
                        for c in rest)
    inner = (
        _kicker("第四章 · 品类偏好", 0)
        + '<div data-anim="scale" data-beat="1" style="width:100%%">%s</div>' % donut
        + _hero(_count(int(round(top["spend"])), prefix="¥", dur=1400,
                       beat=2, cls="sm acc"), 2, "fade")
        + _rant('你的胃，<br/>最偏向 <b>%s</b>' % top["name"], 3)
        + _foot('<b>%.0f%%</b> 的花费都给了它 · %s' % (share, legend), 4)
    )
    return _scene("category", 4, "品类偏好", inner, particles=12, decor="burger")


def scene_top_items(m):
    """心头好：条形图（生长）+ 一句数据白话。"""
    items = m["top_items"] or [{"name": "暂无数据", "count": 0, "spend": 0}]
    chart = charts.hbar_chart(
        [{"name": it["name"], "count": it["count"]} for it in items],
        formatter=lambda v: "%d 份" % v)
    top = items[0]
    inner = (
        _kicker("第五章 · 心头好", 0)
        + _hero(_count(top["count"], cls="acc", dur=1400, beat=1), 1, "scale", "份")
        + _rant('陪你最多的，<br/>是 <b>%s</b>' % top["name"], 2, "slide")
        + _box(chart, 3)
        + _foot('一共点了 <b>%d</b> 份 · 花费 ¥%s'
                % (top["count"], _num(top["spend"])), 4)
    )
    return _scene("top_items", 5, "心头好", inner, particles=12, decor="fries")


def scene_time_of_day(m):
    """时间线：进度条组 + 点题金句（主角是条形）。"""
    tod = m["time_of_day"]
    peak = m["peaks"]["time_of_day"]
    inner = (
        _kicker("第六章 · 时间线", 0)
        + _rant('你最爱在 <b>%s</b><br/>按下下单键' % peak["label"], 1, "slide")
        + _tiles([
            _tile("最高频时段", peak["label"], "%d 单落在这里" % peak["count"],
                  True, 2),
            _tile("深夜下单", "%d 单" % m["fun"]["late_night_orders"],
                  "凌晨的快乐", False, 2),
            _tile("早餐时段", "%d 单" % m["fun"]["breakfast_orders"],
                  "一天从麦开始", False, 3),
        ], "three")
        + '<div style="width:100%%;max-width:520px" data-anim="fade" '
          'data-beat="4">%s</div>' % charts.progress_rows(tod)
    )
    return _scene("time_of_day", 6, "时间线", inner, particles=10, decor="drink")


def scene_weekday(m):
    """一周节律：柱状图 + 快乐日金句。"""
    wd = m["weekdays"]
    top = m["peaks"]["weekday"]
    total_orders = sum(r["count"] for r in wd) or 1
    inner = (
        _kicker("第七章 · 一周节律", 0)
        + _hero(_count(top["count"], dur=1300, beat=1), 1, "scale", "单")
        + _rant('<b>%s</b><br/>是你的快乐日' % top["label"], 2, "slide")
        + _box(charts.vbar_chart(wd), 3)
        + _foot('这天下了 <b>%d</b> 单，占全周的 <b>%.0f%%</b>'
                % (top["count"], top["count"] / total_orders * 100), 4)
    )
    return _scene("weekday", 7, "一周节律", inner, particles=12, decor="pie")


def scene_highlights(m):
    """高光时刻：一个大主角 + 若干备选。"""
    hl = m["highlight"]
    main, others = hl["main"], hl["others"]
    rows = "".join(
        _tile(c["title"], c["value"], c["note"], False, 3 + i)
        for i, c in enumerate(others))
    inner = (
        _kicker("第八章 · 高光时刻", 0)
        + _rant('%s' % main["title"], 1, "slide")
        + _hero('<span class="hero-num sm acc wide">%s</span>' % main["value"],
                2, "scale")
        + _line('%s' % main["note"], 2)
        + _tiles(rows, "dense" if len(others) > 4 else "")
    )
    return _scene("highlights", 8, "高光时刻", inner, particles=20, decor="cone")


def scene_persona(m):
    """消费人格：人格名（超大）+ 解读 + 标签。"""
    p = m["persona"]
    tags = "".join(
        '<span class="tag%s" data-anim="fade" data-beat="%d">%s</span>'
        % (" hot" if i == 0 else "", 3 + (i // 3), t["name"])
        for i, t in enumerate(p["tags"]))
    oth = "".join(
        '<span class="tag" data-anim="fade" data-beat="4">%s</span>' % k
        for k in p["keywords"])
    inner = (
        _kicker("第九章 · 消费人格", 0)
        + _rant('测出来，你是<br/><span class="tilt">%s</span>' % p["main"],
                1, "scale")
        + _line(p["desc"], 2)
        + '<div class="tags" data-anim="fade" data-beat="3">%s</div>' % tags
        + '<div class="tags" data-anim="fade" data-beat="4">%s</div>' % oth
    )
    return _scene("persona", 9, "消费人格", inner, particles=22, decor="burger")


def scene_outro(m):
    """尾声：总结数字 + 重新开始。"""
    ov, per = m["overview"], m["period"]
    inner = (
        _kicker("尾声 · %s" % per["year"], 0)
        + _rant('感谢这一年，<br/>有<b>麦门</b>陪你', 1, "slide")
        + _line('<b>%d</b> 次相遇 · <b>¥%s</b> 投入 · <b>%s</b> kcal 的快乐<br/>'
                '%s ~ %s'
                % (ov["total_orders"], _num(ov["total_spend"]),
                   "{:,}".format(ov["total_calories"]),
                   per["first_date"], per["last_date"]), 2)
        + '<div class="btn-row" data-anim="fade" data-beat="3">'
          '<button class="btn ghost" type="button" id="btnReplayEnd" '
          'onclick="McWrapped.reset()">↺ 重新翻阅</button>'
          '<button class="btn ghost" type="button" id="btnReplay" '
          'onclick="McWrapped.replay()">⟳ 重播本屏</button>'
          '<button class="btn ghost" type="button" id="btnPrint" '
          'onclick="window.print()">🖨 存为 PDF</button>'
          '</div>'
    )
    return _scene("outro", 10, "尾声", inner, particles=24, decor="fries")


# ---------------------------------------------------------------- 空态


def scene_empty(m):
    """订单为空时的优雅引导屏（而不是一片 0）。"""
    inner = (
        _kicker("McWrapped", 0)
        + _rant('你的麦门故事，<br/>还没开始书写', 1, "slide")
        + _line('当前账号没有检测到麦当劳历史订单。<br/>'
                '三步就能生成属于你自己的年度报告：', 2)
        + _tiles([
            _tile("STEP 01", "申请 MCP Token",
                  "在 open.mcd.cn/mcp 激活并复制 Token", True, 3),
            _tile("STEP 02", "拉取真实订单",
                  "python scripts/fetch_orders.py all", False, 3),
            _tile("STEP 03", "生成报告",
                  "python scripts/generate_report.py orders.json", False, 4),
        ], "one")
        + _foot('当前展示的示例报告基于演示数据', 5)
    )
    return _scene("empty", 0, "空态", inner, extra_class="scene-cover",
                  particles=14, decor="cone")


# ---------------------------------------------------------------- 装配


def _scene(key, chapter_no, chapter_name, inner, extra_class="",
           particles=0, decor=""):
    """组装一屏（含 P5R 装饰层、粒子宿主、装饰插画）。

    图层（自下而上）：
      .aura（粒子宿主，模糊光晕）→ .slabs/.strokes（P5R 斜切与涂鸦）
      → .grid-lines/.grain/.vignette（纹理）→ .deco（角落插画）→ .scene-inner（内容）
    插画只出现一次：放在内容层之下、纹理之上，避免重复绘制。
    """
    decor_html = deco.render_decor(decor) if decor else ""
    return ('<section class="scene %s" data-scene="%s" data-chapter="%d" '
            'data-chapter-name="%s" data-particles="%d" data-decor="%s" '
            'aria-hidden="true" role="group" aria-label="%s">'
            '<div class="aura" aria-hidden="true"></div>'
            '%s'
            '<div class="grid-lines" aria-hidden="true"></div>'
            '<div class="grain" aria-hidden="true"></div>'
            '<div class="vignette" aria-hidden="true"></div>'
            '%s'
            '<div class="scene-inner">%s</div>'
            '</section>' % (extra_class, key, chapter_no, chapter_name,
                            particles, decor, chapter_name,
                            _decor_layers(), decor_html, inner))


#: 场景顺序 = 叙事顺序。改这里即可调整/裁剪章节。
SCENE_ORDER = [
    ("cover", scene_cover),
    ("overview", scene_overview),
    ("spend", scene_spend),
    ("calories", scene_calories),
    ("category", scene_category),
    ("top_items", scene_top_items),
    ("time_of_day", scene_time_of_day),
    ("weekday", scene_weekday),
    ("highlights", scene_highlights),
    ("persona", scene_persona),
    ("outro", scene_outro),
]


def render_scenes(model, enabled=None):
    """产出所有场景 HTML（按 SCENE_ORDER 顺序）。

    ``enabled`` 语义（明确区分「没传」和「传了但没列」）：
    - ``None``        → 全部开启；
    - 传 dict         → **该 dict 即权威白名单**，未出现的场景一律关闭。
      这样 ``{"cover": True, "outro": True}`` 才会真的只出两屏。
    """
    if model is None:
        return [scene_empty(None)]

    parts = []
    for key, fn in SCENE_ORDER:
        if enabled is not None and not enabled.get(key, False):
            continue
        try:
            parts.append(fn(model))
        except Exception as exc:  # noqa: BLE001
            # 单屏渲染失败不应让整份报告崩掉
            parts.append(_scene(key, 0, "!",
                                '<div class="line">该章节渲染失败：%s</div>'
                                % str(exc).replace("<", "&lt;")))
    return parts
