# -*- coding: utf-8 -*-
"""主题 token：P5R 波普朋克（Pop-Punk）视觉体系。

设计来源
--------
Persona 5 / Persona 5 Royal 的界面设计（Atlus，艺术指导 副岛成记 + 須藤正喜）：
- **配色**：高对比「红 / 黑 / 白」三色制，红取 "Phantom Red"，
  参考 1960s 抗议海报（protest poster）与朋克 Zine 的拼贴暴力美学。
- **形状**：尖锐多边形、斜切色块、撕裂边缘（jagged / slash），拒绝圆角与柔和。
- **排版**：字号/字重/颜色/倾斜刻意不统一，模仿「绑架信剪贴字」（Ransom Note）。
- **构图**：倾斜的色块切割画面（diagonal band），元素像被"甩"进画面。

本项目落地为 CSS 变量 + 装饰层，不引入任何字体/图片外链。
"""
from ._tokens import DARK_P5R, LIGHT_P5R

#: 主题注册表。key 即 ``--theme`` 参数值与 ``data-theme`` 属性值。
THEMES = {
    "dark": DARK_P5R,
    "light": LIGHT_P5R,
}

DEFAULT_THEME = "dark"

#: 图表配色（P5R 主色 + 少量辅助色，保持高对比）
CHART_PALETTE = [
    "#E60012",  # phantom red
    "#FFF6EA",  # paper white
    "#FFB300",  # warning yellow
    "#00A0E9",  # info blue（少量点缀）
    "#8B0010",  # deep red
    "#5A5A5A",  # neutral
]


def css_vars(name="dark"):
    """产出 ``:root{--x:y;...}`` 片段（键名 ``_`` → ``-``）。"""
    theme = THEMES.get(name, DARK_P5R)
    return "".join("--%s:%s;" % (k.replace("_", "-"), v) for k, v in theme.items())


def theme_map_for_js():
    """产出可内联进 JS 的主题表（键名已转为 CSS 变量名）。"""
    return {tname: {k.replace("_", "-"): v for k, v in t.items()}
            for tname, t in THEMES.items()}
