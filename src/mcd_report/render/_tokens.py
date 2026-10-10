# -*- coding: utf-8 -*-
"""主题 token 的具体数值（与 theme.py 分离，仅放数据）。

命名约定
--------
所有键会被转成 CSS 变量（``_`` → ``-``），例如 ``accent_2`` → ``--accent-2``。
键名保持稳定，避免 JS 侧引用失效。
"""

#: 深色（默认）：纯黑纸 + 燃烧红，P5R 主视觉
DARK_P5R = {
    # 基底
    "bg": "#0A0A0A",
    "bg_2": "#141414",
    "panel": "#171717",
    "panel_2": "#1F1F1F",

    # 文字层级
    "text": "#F5F1EA",
    "muted": "#A8A29A",
    "faint": "#6B655D",

    # 强调
    "accent": "#E60012",       # phantom red
    "accent_2": "#FF2A2A",
    "accent_ink": "#0A0A0A",   # 压在红底上的字色
    "brand": "#E60012",
    "gold": "#FFB300",         # 预警黄，用于次级强调

    # 装饰
    "grid": "rgba(230,0,18,.10)",
    "border": "rgba(245,241,234,.14)",
    "slash": "#E60012",        # 斜切色块
    "slash_2": "#1F1F1F",
    "tape": "rgba(245,241,234,.06)",   # 胶带/贴纸底
    "glow": "rgba(230,0,18,.30)",
    "particle": "#E60012",
    "grain_op": ".05",
}

#: 亮色：做旧纸张 + 印刷红，模拟 Zine 复印质感
LIGHT_P5R = {
    "bg": "#F2EDE4",
    "bg_2": "#E8E1D5",
    "panel": "#FFFFFF",
    "panel_2": "#F7F3EC",

    "text": "#141414",
    "muted": "#5C564E",
    "faint": "#8C857B",

    "accent": "#D6000F",
    "accent_2": "#E60012",
    "accent_ink": "#FFFFFF",
    "brand": "#D6000F",
    "gold": "#C98A00",

    "grid": "rgba(20,20,20,.07)",
    "border": "rgba(20,20,20,.16)",
    "slash": "#141414",
    "slash_2": "#D6000F",
    "tape": "rgba(20,20,20,.05)",
    "glow": "rgba(214,0,15,.20)",
    "particle": "#D6000F",
    "grain_op": ".08",
}
