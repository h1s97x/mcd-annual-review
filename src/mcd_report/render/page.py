# -*- coding: utf-8 -*-
"""组装层：把场景 + 动效资源拼成**单文件、零外链**的 HTML。

产物约束（项目硬规矩）：
- 所有 CSS / JS 内联，无 CDN、无外链字体、无远程图片
- 图表与插画全部内联 SVG
- 可离线打开与分享

导航说明
--------
**没有底部控制条**。导航靠：滚轮 / 键盘（↑↓ 空格 Home End）/ 触摸滑动 /
点击空白处 / 侧边导轨 / 封面按钮。点一下 = 加速显示本屏剩余内容，
内容显示完后再点 = 翻到下一屏。
"""
from .._schema import ENGINE, SCHEMA_VERSION
from .. import config as C
from . import motion
from .scenes import render_scenes
from .theme import DEFAULT_THEME

_TPL = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="%(theme)s">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<meta name="color-scheme" content="dark light"/>
<meta name="description" content="麦门年度账本 · McWrapped —— 基于麦当劳 MCP 历史订单的个人年度报告"/>
<meta name="generator" content="mcd-annual-review · %(engine)s v%(schema)s"/>
<title>麦门年度账本 · McWrapped</title>
<style>%(css)s</style>
<script>document.documentElement.className+=" deck-ready";</script>
</head>
<body>
<div class="progress"><i id="progressBar"></i></div>

<div class="hud">
  <div class="hud-chapter" id="chapterLabel">封面</div>
  <div class="hud-right">
    <button class="icon-btn" id="btnReplay" type="button"
            title="重播本屏（R）" aria-label="重播本屏">⟳</button>
    <button class="icon-btn" id="btnMotion" type="button"
            title="动效 / 省电模式" aria-label="切换动效">✧</button>
    <button class="icon-btn" id="btnThemeTop" type="button"
            title="明暗主题" aria-label="切换主题">◐</button>
  </div>
</div>

<div class="stage" id="stage">
  <div class="track" id="track">
%(scenes)s
  </div>
</div>

<div class="rail" id="rail" role="tablist" aria-label="章节导航"></div>

<div class="hint" id="hint" aria-hidden="true">
  <span>向下滑动 / 点击继续</span>
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 5v14M19 12l-7 7-7-7"/>
  </svg>
</div>
<div class="advance-cue" id="advanceCue">点击加速 ▸▸</div>

<div class="badge%(badge_cls)s">数据来源：%(badge_txt)s</div>

<script>%(js)s</script>
</body>
</html>
"""


def build_html(model, theme=DEFAULT_THEME, enabled=None, engine=ENGINE):
    """model dict（或 None 表空态）→ 完整单文件 HTML 字符串。"""
    enabled = C.SCENES_ENABLED if enabled is None else enabled
    scenes = render_scenes(model, enabled)

    src = (model or {}).get("source", "demo")
    if src == "demo":
        badge_cls, badge_txt = " demo", "演示数据（非真实订单）"
    elif src == "real":
        badge_cls, badge_txt = "", "麦当劳 MCP 实时数据"
    else:
        badge_cls, badge_txt = "", str(src)

    return _TPL % {
        "theme": theme,
        "css": motion.motion_css(theme),
        "js": motion.motion_js(),
        "scenes": "\n".join(scenes),
        "badge_cls": badge_cls,
        "badge_txt": badge_txt,
        "engine": engine,
        "schema": SCHEMA_VERSION,
    }
