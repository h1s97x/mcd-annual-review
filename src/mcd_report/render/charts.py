# -*- coding: utf-8 -*-
"""图表层：内联 SVG 图表（零依赖，颜色走 CSS 变量以随主题重着色）。

每个图表都自带**入场动画钩子**，与 ``motion_js`` 通过 data-* 契约对接：

- 折线/面积：``data-anim="draw"`` + ``--len``（JS 用 getTotalLength 补精确值）
- 横向条形：``data-anim="grow"``（scaleX 0→1）
- 环形：``.donut-seg`` + ``data-len`` / ``data-circ``（JS 算描出偏移）
- 网格/坐标轴：``data-anim="fade"``

单位与格式化都在本层处理，调用方传数字即可。
"""
import math

from .theme import CHART_PALETTE


def _fmt(v, unit=""):
    if v >= 10000:
        return "%.1f万" % (v / 10000)
    if v >= 1000:
        return "{:,}".format(int(round(v)))
    return "%g" % round(v, 1)


# ---------------------------------------------------------------- 折线 / 面积
def line_chart(series, labels, baseline=None, unit="", height=250, accent="var(--accent)"):
    """周趋势折线 + 渐变面积 + 可选基准虚线。"""
    W, H = 720, height
    pl, pr, pt, pb = 52, 18, 24, 42
    iw, ih = W - pl - pr, H - pt - pb
    n = len(series)
    if n == 0:
        return ('<svg viewBox="0 0 %d %d" class="chart" role="img" aria-label="暂无数据">'
                '<text x="%d" y="%d" fill="var(--muted)" font-size="13" '
                'text-anchor="middle">暂无趋势数据</text></svg>' % (W, H, W // 2, H // 2))

    top = max(series + ([baseline] if baseline else [])) or 1
    maxv = top * 1.18
    step = iw / max(n - 1, 1)

    pts = []
    for i, v in enumerate(series):
        pts.append((pl + step * i, pt + ih - (v / maxv) * ih))

    # 网格与 Y 轴刻度（淡入）
    grid = ""
    for g in range(5):
        gy = pt + ih - (g / 4) * ih
        grid += ('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--grid)" '
                 'stroke-width="1" data-anim="fade" data-anim-delay="%d"/>'
                 % (pl, gy, W - pr, gy, 60 + g * 40))
        grid += ('<text x="%d" y="%.1f" fill="var(--faint)" font-size="10" '
                 'text-anchor="end">%s</text>' % (pl - 8, gy + 3.5, _fmt((g / 4) * maxv)))

    poly = " ".join("%.1f,%.1f" % p for p in pts)
    area_d = "M%.1f,%.1f L%s L%.1f,%.1f Z" % (pts[0][0], pt + ih, poly, pts[-1][0], pt + ih)
    line_d = "M" + " L".join("%.1f,%.1f" % p for p in pts)

    # 基准线
    base = ""
    if baseline:
        by = pt + ih - (baseline / maxv) * ih
        base = ('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--warn)" '
                'stroke-width="1.5" stroke-dasharray="7 5" data-anim="fade" '
                'data-anim-delay="500"/>'
                '<text x="%d" y="%.1f" fill="var(--warn)" font-size="10" '
                'data-anim="fade" data-anim-delay="560">周预算 %s</text>'
                % (pl, by, W - pr, by, pl + 6, by - 7, _fmt(baseline)))

    # X 轴标签（抽稀，避免重叠）
    xl = ""
    lab_step = max(1, math.ceil(n / 7))
    for i, lab in enumerate(labels):
        if i % lab_step != 0 and i != n - 1:
            continue
        x = pl + step * i
        anchor = "start" if i == 0 else ("end" if i == n - 1 else "middle")
        xl += ('<text x="%.1f" y="%d" fill="var(--faint)" font-size="10" '
               'text-anchor="%s">%s</text>' % (x, H - 14, anchor, lab))

    dots = "".join(
        '<circle cx="%.1f" cy="%.1f" r="3.5" fill="%s" data-anim="scale" '
        'data-anim-delay="%d"/>' % (p[0], p[1], accent, 900 + i * 55)
        for i, p in enumerate(pts))

    max_idx = series.index(max(series))
    mark = ('<circle cx="%.1f" cy="%.1f" r="7" fill="none" stroke="var(--warn)" '
            'stroke-width="2" opacity=".85" data-anim="scale" data-anim-delay="1200"/>'
            % (pts[max_idx][0], pts[max_idx][1])) if n > 1 else ""

    return (
        '<svg viewBox="0 0 %d %d" class="chart" role="img" aria-label="趋势折线图">'
        '<defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s" stop-opacity=".30"/>'
        '<stop offset="1" stop-color="%s" stop-opacity="0"/>'
        '</linearGradient></defs>'
        '%s%s'
        '<path d="%s" fill="url(#areaGrad)" data-anim="fade" data-anim-delay="620"/>'
        '<path d="%s" fill="none" stroke="%s" stroke-width="2.6" stroke-linecap="round" '
        'stroke-linejoin="round" data-anim="draw" data-anim-delay="260" '
        'style="--dur:1.5s"/>'
        '%s%s%s'
        '</svg>' % (W, H, accent, accent, grid, base, area_d, line_d, accent,
                    mark, dots, xl))


# ---------------------------------------------------------------- 环形
def donut_chart(rows, value_key="spend", center_label="总花费", unit="¥"):
    """品类占比环形 + 图例。rows: [{'name','spend','calories','count'}]"""
    total = sum(r.get(value_key, 0) for r in rows) or 1
    cx, cy, r = 130, 130, 88
    sw = 30
    circ = 2 * math.pi * r

    segs, legend = "", ""
    offset = 0.0
    for i, row in enumerate(rows):
        val = row.get(value_key, 0)
        frac = val / total
        length = frac * circ
        color = CHART_PALETTE[i % len(CHART_PALETTE)]
        segs += ('<circle class="donut-seg" cx="%d" cy="%d" r="%d" fill="none" '
                 'stroke="%s" stroke-width="%d" stroke-linecap="butt" '
                 'stroke-dasharray="%.2f %.2f" stroke-dashoffset="%.2f" '
                 'transform="rotate(-90 %d %d)" '
                 'data-len="%.2f" data-circ="%.2f" data-name="%s"/>'
                 % (cx, cy, r, color, sw, length, circ - length, -offset,
                    cx, cy, length, circ, row["name"]))
        offset += length
        legend += (
            '<div class="legend-row" data-anim="fade" data-anim-delay="%d">'
            '<span class="legend-dot" style="background:%s"></span>'
            '<span>%s</span>'
            '<span class="legend-val">%s%s · %.0f%%</span>'
            '</div>' % (420 + i * 90, color, row["name"], unit, _fmt(val),
                        frac * 100))

    center = ('<text x="%d" y="%d" fill="var(--text)" font-size="26" font-weight="800" '
              'text-anchor="middle" data-anim="scale" data-anim-delay="900">%s%s</text>'
              '<text x="%d" y="%d" fill="var(--muted)" font-size="11" '
              'text-anchor="middle">%s</text>'
              % (cx, cy - 2, unit, _fmt(total), cx, cy + 20, center_label))

    return (
        '<div class="donut-wrap" style="display:flex;gap:26px;align-items:center;'
        'justify-content:center;flex-wrap:wrap;width:100%%">'
        '<svg viewBox="0 0 260 260" class="chart" style="max-width:260px;flex:0 1 260px" '
        'role="img" aria-label="品类占比环形图" data-donut="1">'
        '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="var(--grid)" '
        'stroke-width="%d" data-anim="fade"/>'
        '%s%s</svg>'
        '<div class="legend" style="flex:1 1 220px;min-width:180px">%s</div>'
        '</div>' % (cx, cy, r, sw, segs, center, legend))


# ---------------------------------------------------------------- 横向条形
def hbar_chart(rows, unit="", formatter=None, max_rows=None):
    """横向条形排行。rows: [{'name'/'label','count'/'value'}]"""
    if max_rows:
        rows = rows[:max_rows]
    if not rows:
        return '<svg viewBox="0 0 720 60" class="chart"></svg>'

    W, rh, top = 720, 42, 8
    pl, pr = 12, 84
    H = top + len(rows) * rh + 8
    vals = [r.get("value", r.get("count", 0)) for r in rows]
    maxv = max(vals) or 1
    bar_x = pl + 132
    bar_w = W - bar_x - pr

    body = ""
    for i, row in enumerate(rows):
        label = row.get("name", row.get("label", ""))
        val = row.get("value", row.get("count", 0))
        y = top + i * rh
        w = max(2.0, bar_w * (val / maxv))
        color = CHART_PALETTE[i % len(CHART_PALETTE)]
        text = formatter(val) if formatter else "%s%s" % (unit, _fmt(val))
        body += (
            '<text x="%d" y="%d" fill="var(--text)" font-size="13" '
            'data-anim="fade" data-anim-delay="%d">%s</text>'
            '<rect x="%d" y="%d" width="%.1f" height="20" rx="10" fill="%s" '
            'fill-opacity=".92" data-anim="grow" data-anim-delay="%d" '
            'style="--dur:.9s" transform-origin="%dpx %dpx"/>'
            '<text x="%d" y="%d" fill="var(--muted)" font-size="12" '
            'text-anchor="end" data-anim="fade" data-anim-delay="%d">%s</text>'
            % (pl, y + 18, 120 + i * 80, label,
               bar_x, y + 3, w, color, 180 + i * 90, bar_x, y + 3 + 10,
               W - 8, y + 18, 620 + i * 60, text))
    return ('<svg viewBox="0 0 %d %d" class="chart" role="img" aria-label="排行条形图">'
            '%s</svg>' % (W, H, body))


# ---------------------------------------------------------------- 柱状（星期）
def vbar_chart(rows, unit="", highlight_max=True):
    """纵向柱状图，用于「周几最常来」这类少量分桶。"""
    n = len(rows)
    if not n:
        return '<svg viewBox="0 0 720 200" class="chart"></svg>'
    W, H = 720, 232
    pl, pr, pt, pb = 24, 24, 30, 40
    iw, ih = W - pl - pr, H - pt - pb
    vals = [r.get("count", r.get("value", 0)) for r in rows]
    maxv = max(vals) or 1
    slot = iw / n
    bw = min(52.0, slot * 0.56)
    max_i = vals.index(max(vals)) if highlight_max else -1

    body = ""
    for i, row in enumerate(rows):
        v = vals[i]
        h = max(2.0, ih * (v / maxv))
        x = pl + slot * i + (slot - bw) / 2
        y = pt + ih - h
        on = (i == max_i)
        color = "var(--accent)" if on else "var(--panel2)"
        stroke = "none" if on else "var(--border)"
        body += (
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="7" fill="%s" '
            'stroke="%s" data-anim="grow" data-anim-delay="%d" style="--dur:.8s" '
            'transform-origin="%.1fpx %.1fpx"/>'
            '<text x="%.1f" y="%.1f" fill="%s" font-size="13" font-weight="700" '
            'text-anchor="middle" data-anim="fade" data-anim-delay="%d">%s</text>'
            '<text x="%.1f" y="%d" fill="var(--muted)" font-size="12" '
            'text-anchor="middle">%s</text>'
            % (x, y, bw, h, color, stroke, 180 + i * 70, x, y + h,
               x + bw / 2, y - 8, "var(--accent)" if on else "var(--muted)",
               520 + i * 60, _fmt(v), x + bw / 2, H - 14, row.get("label", "")))
    return ('<svg viewBox="0 0 %d %d" class="chart" role="img" aria-label="柱状图">'
            '%s</svg>' % (W, H, body))


# ---------------------------------------------------------------- 进度条组
def progress_rows(rows, unit=""):
    """时段分布用的横向进度条（比条形图更紧凑）。"""
    total = sum(r.get("count", 0) for r in rows) or 1
    maxv = max((r.get("count", 0) for r in rows), default=1) or 1
    body = ""
    for i, row in enumerate(rows):
        v = row.get("count", 0)
        pct = v / maxv * 100
        share = v / total * 100
        body += (
            '<div class="prow" data-anim="fade" data-anim-delay="%d">'
            '<span class="prow-label">%s</span>'
            '<span class="prow-track"><i style="width:%.1f%%;'
            'background:%s"></i></span>'
            '<span class="prow-val">%d 单 · %.0f%%</span>'
            '</div>'
            % (140 + i * 90, row.get("label", ""), pct,
               CHART_PALETTE[i % len(CHART_PALETTE)], v, share))
    return '<div class="prows">%s</div>' % body
