# -*- coding: utf-8 -*-
"""插画层：品牌矢量插画（扁平风，纯内联 SVG，零外链）。

都是返回 SVG 字符串的**纯函数**，尺寸可调；由 ``scenes`` 通过
``data-decor`` 决定摆在哪一屏的角落。
"""


def _wrap(svg, cls, w):
    return ('<div class="deco %s">%s</div>' % (cls, svg)).replace(
        "<svg ", '<svg style="width:%dpx;height:auto" ' % w)


def burger(w=128):
    return _wrap(
        '<svg viewBox="0 0 120 112" xmlns="http://www.w3.org/2000/svg">'
        '<ellipse cx="60" cy="30" rx="47" ry="27" fill="#F2A900"/>'
        '<ellipse cx="60" cy="27" rx="47" ry="25" fill="#FFC72C"/>'
        '<circle cx="41" cy="19" r="2.3" fill="#FFF3C4"/><circle cx="60" cy="13" r="2.3" fill="#FFF3C4"/>'
        '<circle cx="79" cy="19" r="2.3" fill="#FFF3C4"/><circle cx="51" cy="32" r="2" fill="#FFF3C4"/>'
        '<circle cx="70" cy="33" r="2" fill="#FFF3C4"/>'
        '<rect x="13" y="46" width="94" height="11" rx="5.5" fill="#7CB342"/>'
        '<rect x="11" y="59" width="98" height="10" rx="5" fill="#E53935"/>'
        '<path d="M13 71 L107 71 L107 80 Q60 91 13 80 Z" fill="#F2A900"/>'
        '<ellipse cx="60" cy="94" rx="47" ry="13" fill="#FFC72C"/>'
        '</svg>', "deco-burger bob", w)


def fries(w=112):
    return _wrap(
        '<svg viewBox="0 0 100 132" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="29" y="26" width="11" height="50" rx="3" fill="#FFD75E"/>'
        '<rect x="44" y="14" width="11" height="62" rx="3" fill="#FFC72C"/>'
        '<rect x="59" y="28" width="11" height="48" rx="3" fill="#FFD75E"/>'
        '<rect x="73" y="20" width="11" height="56" rx="3" fill="#FFC72C"/>'
        '<path d="M21 74 L29 124 L71 124 L79 74 Z" fill="#DA291C"/>'
        '<path d="M21 74 L79 74 L77 87 L23 87 Z" fill="#B91C1C"/>'
        '<path d="M39 98 L61 98 L59 112 L41 112 Z" fill="#FFC72C" opacity=".92"/>'
        '</svg>', "deco-fries sway", w)


def drink(w=104):
    return _wrap(
        '<svg viewBox="0 0 92 124" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M20 36 L29 116 L63 116 L72 36 Z" fill="#DA291C"/>'
        '<path d="M26 46 L33 108 L59 108 L66 46 Z" fill="#B91C1C"/>'
        '<text x="46" y="84" fill="#FFF8E7" font-size="26" font-weight="800" '
        'text-anchor="middle" font-family="Arial Black,Arial,sans-serif">M</text>'
        '<rect x="15" y="25" width="62" height="13" rx="5.5" fill="#FFF8E7"/>'
        '<line x1="47" y1="27" x2="63" y2="5" stroke="#FFF8E7" stroke-width="5.5" '
        'stroke-linecap="round"/>'
        '</svg>', "deco-drink bob", w)


def cone(w=92):
    return _wrap(
        '<svg viewBox="0 0 80 122" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M40 98 L25 45 L55 45 Z" fill="#F2A900"/>'
        '<path d="M30 54 L50 54 M33 64 L47 64 M36 74 L44 74" stroke="#C47E00" stroke-width="2.2"/>'
        '<path d="M23 45 Q19 20 40 18 Q61 20 57 45 Z" fill="#FFF3C4"/>'
        '<path d="M40 18 Q34 34 40 45 Q46 34 40 18 Z" fill="#FFE7A3"/>'
        '</svg>', "deco-cone bob", w)


def applepie(w=100):
    return _wrap(
        '<svg viewBox="0 0 112 86" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M15 66 L30 22 L96 22 L81 66 Z" fill="#F2A900"/>'
        '<path d="M30 22 L96 22 L92 35 L27 35 Z" fill="#FFC72C"/>'
        '<path d="M38 42 L88 42 M42 52 L84 52 M46 62 L80 62" stroke="#C47E00" '
        'stroke-width="2.2" opacity=".68"/>'
        '</svg>', "deco-pie sway", w)


#: data-decor 值 → 绘制函数。
REGISTRY = {
    "burger": burger,
    "fries": fries,
    "drink": drink,
    "cone": cone,
    "pie": applepie,
}


def arches(w=980, opacity=0.13):
    """金拱门双弧，作为整屏背景水印。"""
    return (
        '<svg class="arches" viewBox="0 0 420 340" aria-hidden="true" '
        'style="width:min(88vw,%dpx);height:auto" xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="mcdArch" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FFC72C"/><stop offset="1" stop-color="#FF9F1C"/>'
        '</linearGradient></defs>'
        '<path d="M72 250 Q72 106 210 106 Q348 106 348 250" stroke="url(#mcdArch)" '
        'stroke-width="32" fill="none" opacity="%s" stroke-linecap="round"/>'
        '<path d="M72 250 Q72 394 210 394 Q348 394 348 250" stroke="url(#mcdArch)" '
        'stroke-width="32" fill="none" opacity="%s" stroke-linecap="round"/>'
        '</svg>' % (w, opacity, opacity)
    )


def render_decor(kind, w=None):
    """按 ``data-decor`` 值取插画；未知类型返回空串（不报错）。"""
    fn = REGISTRY.get(kind)
    if not fn:
        return ""
    return fn(w) if w else fn()
