# -*- coding: utf-8 -*-
"""动效层装配：把独立资源文件（assets/deck.css、assets/deck.js）读进来，
注入主题 token 与运行时常量后，供 ``page.py`` 内联进单文件 HTML。

为什么资源独立成 .css / .js 文件
--------------------------------
把 JS/CSS 写成 Python 三引号字符串的问题：
- 失去编辑器语法高亮与格式化；
- Python 的 ``%`` 格式化会和 CSS 的 ``%`` / JS 的 ``%`` 冲突（本项目已踩过）；
- 无法用 ``node --check`` 之外的常规工具校验。

拆成真实文件后，Python 只负责「读文件 + 注入变量」，
产物依然是**单文件、零外链**（读取后内联，不产出 ``<link>`` / ``<script src>``）。
"""
import json
import os

from .theme import DEFAULT_THEME, css_vars, theme_map_for_js

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

#: CSS 中主题变量的注入锚点
CSS_ANCHOR = "__ROOT_VARS__"

#: JS 中的注入锚点
JS_THEMES = "__THEMES__"
JS_DEFAULT_THEME = "__DEFAULT_THEME__"


def _read(name):
    path = os.path.join(_ASSETS, name)
    with open(path, encoding="utf-8") as f:
        return f.read()


def motion_css(theme=DEFAULT_THEME):
    """产出内联 ``<style>`` 内容：注入 ``:root`` 主题变量。"""
    return _read("deck.css").replace(CSS_ANCHOR, css_vars(theme))


def motion_js():
    """产出内联 ``<script>`` 内容：注入主题表与默认主题名。"""
    src = _read("deck.js")
    return (src
            .replace(JS_THEMES, json.dumps(theme_map_for_js(),
                                           ensure_ascii=False,
                                           separators=(",", ":")))
            .replace(JS_DEFAULT_THEME, DEFAULT_THEME))


def asset_paths():
    """返回资源文件绝对路径（供测试或调试读取）。"""
    return {"css": os.path.join(_ASSETS, "deck.css"),
            "js": os.path.join(_ASSETS, "deck.js")}
