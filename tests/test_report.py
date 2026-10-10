#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告产物自检测试（零依赖，纯标准库）。

覆盖三层：
  A. 产物约束——单文件、零外链、无残留占位符、HTML 闭合
  B. 叙事结构——章节顺序、动效契约挂载点、空态与徽章
  C. 主题/参数——主题切换、板块开关、引擎标识

全程跑在本地 sample_orders.json 上，不碰任何真实 MCP / 网络。

运行:
  python -m unittest tests.test_report -v
"""
import json
import os
import re
import sys
import unittest
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from mcd_report import cli                                    # noqa: E402
from mcd_report.domain import metrics                         # noqa: E402
from mcd_report.render import page, scenes                    # noqa: E402

SAMPLE = os.path.join(ROOT, "sample_orders.json")


class _Closer(HTMLParser):
    """检查标签闭合是否平衡（构造期就能抓出模板拼接错误）。"""
    VOID = {"br", "hr", "img", "input", "meta", "link", "path", "circle", "rect",
            "line", "ellipse", "stop", "use", "polygon", "polyline", "source",
            "area", "col", "base", "wbr", "defs", "tspan"}

    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append("未闭合 <%s>" % self.stack.pop())
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append("多余 </%s>" % tag)


def _sample_model():
    with open(SAMPLE, encoding="utf-8") as f:
        data = json.load(f)
    m = metrics.build_model(data)
    m["source"] = "demo"
    return m


class TestArtifacts(unittest.TestCase):
    """A. 产物约束。"""

    @classmethod
    def setUpClass(cls):
        cls.html = page.build_html(_sample_model())

    def test_single_file_no_external_resources(self):
        self.assertEqual(re.findall(r'(?:src|href)\s*=\s*["\']https?://', self.html), [])
        self.assertNotIn("<link", self.html)
        self.assertNotIn("<img", self.html)
        # 唯一允许的 http 出现是 SVG 命名空间
        for url in re.findall(r"https?://[^\s\"')]+", self.html):
            self.assertIn("www.w3.org", url, "出现非命名空间的外部地址：%s" % url)

    def test_no_unrendered_placeholders(self):
        self.assertEqual(re.findall(r"%(?:[sdg]|[0-9.]*[sdg])", self.html), [])
        for marker in ("__ROOT_VARS__", "__THEMES__", "__DEFAULT_THEME__"):
            self.assertNotIn(marker, self.html)

    def test_html_tags_balanced(self):
        c = _Closer()
        c.feed(self.html)
        self.assertEqual(c.errors, [])
        self.assertEqual(c.stack, [])

    def test_no_python_none_leaked(self):
        self.assertNotIn(">None<", self.html)

    def test_inline_css_and_js_present(self):
        self.assertIn("<style>", self.html)
        self.assertIn("<script>", self.html)
        self.assertIn("--accent:", self.html)     # 设计 token 已注入
        self.assertIn("McWrapped", self.html)     # 引擎 API 已暴露


class TestNarrative(unittest.TestCase):
    """B. 叙事结构与动效契约。"""

    @classmethod
    def setUpClass(cls):
        cls.model = _sample_model()
        cls.html = page.build_html(cls.model)

    def test_scene_order_matches_story(self):
        found = re.findall(r'data-scene="([a-z_]+)"', self.html)
        expected = [k for k, _ in scenes.SCENE_ORDER]
        self.assertEqual(found, expected)

    def test_scene_count_and_chapter_meta(self):
        metas = re.findall(r'data-chapter="(\d+)" data-chapter-name="([^"]+)"', self.html)
        self.assertEqual(len(metas), len(scenes.SCENE_ORDER))
        for _, name in metas:
            self.assertTrue(name and name != "!")

    def test_animation_contract_hooks(self):
        self.assertGreaterEqual(self.html.count("data-count="), 6)
        for kind in ("draw", "grow", "fade", "scale", "slide", "slash"):
            self.assertIn('data-anim="%s"' % kind, self.html, "缺少动画类型 %s" % kind)
        self.assertIn("donut-seg", self.html)     # 环形描出
        self.assertIn("data-circ=", self.html)
        self.assertIn("data-len=", self.html)

    def test_staged_reveal_beats(self):
        """每屏内容按 data-beat 分段逐步演出。"""
        self.assertGreaterEqual(self.html.count("data-beat="), len(scenes.SCENE_ORDER) * 2)
        self.assertIn("buildBeats", self.html)
        self.assertIn("startBeats", self.html)
        self.assertIn("accelerate", self.html)
        self.assertIn("BEAT_GAP", self.html)

    def test_hero_data_layer_per_scene(self):
        """每屏都应有大字 + 数据（hero-num / data-count）。"""
        self.assertGreaterEqual(self.html.count("hero-num"), 6)

    def test_particles_and_decor_present(self):
        self.assertGreaterEqual(self.html.count('data-particles="'), 8)
        self.assertGreaterEqual(len(re.findall(r'data-decor="[a-z]+"', self.html)), 8)

    def test_engine_features_wired(self):
        for hook in ("prefers-reduced-motion", "matchMedia", "getTotalLength",
                     "requestAnimationFrame", "touchstart", "wheel", "keydown",
                     "localStorage"):
            self.assertIn(hook, self.html, "动效引擎缺少 %s" % hook)

    def test_navigation_and_replay_controls(self):
        """底部翻页条已移除；保留导轨 / 重播 / 省电 / 主题 / 加速提示。"""
        for hook in ('id="btnReplay"', 'id="btnMotion"', 'id="btnThemeTop"',
                     'id="rail"', 'id="advanceCue"'):
            self.assertIn(hook, self.html, "缺少控件 %s" % hook)
        for gone in ('id="btnPrev"', 'id="btnNext"', 'class="pager"'):
            self.assertNotIn(gone, self.html, "底部翻页条应已移除：%s" % gone)

    def test_demo_badge(self):
        self.assertIn("演示数据", self.html)
        self.assertIn("badge demo", self.html)

    def test_empty_state_renders_guide(self):
        h = page.build_html(None)
        self.assertIn("<html", h)
        self.assertIn("还没开始书写", h)
        self.assertNotIn(">None<", h)

    def test_real_source_no_demo_badge(self):
        m = dict(self.model)
        m["source"] = "real"
        h = page.build_html(m)
        self.assertIn("麦当劳 MCP 实时数据", h)
        self.assertNotIn("badge demo", h)


class TestThemeAndOptions(unittest.TestCase):
    """C. 主题与参数化。"""

    @classmethod
    def setUpClass(cls):
        cls.model = _sample_model()

    def test_theme_switch_changes_tokens(self):
        dark = page.build_html(self.model, theme="dark")
        light = page.build_html(self.model, theme="light")
        self.assertIn('data-theme="dark"', dark)
        self.assertIn('data-theme="light"', light)
        self.assertNotEqual(dark, light)
        self.assertIn("--bg:#0A0A0A", dark)          # P5R 墨黑
        self.assertIn("--accent:#E60012", dark)      # 幻影红
        self.assertIn("--bg:#F2EDE4", light)         # 旧纸白
        self.assertIn("--accent:#D6000F", light)

    def test_scene_toggle(self):
        h = page.build_html(self.model,
                            enabled={"cover": True, "outro": True, "overview": True})
        found = re.findall(r'data-scene="([a-z_]+)"', h)
        self.assertEqual(found, ["cover", "overview", "outro"])

    def test_cli_resolves_only_and_skip(self):
        only = cli._resolve_scenes(("cover,calories", None))
        self.assertTrue(only["calories"])
        self.assertTrue(only["cover"])
        self.assertTrue(only["outro"])           # 叙事骨架始终保留
        self.assertFalse(only["weekday"])
        skip = cli._resolve_scenes((None, "weekday"))
        self.assertFalse(skip["weekday"])
        self.assertTrue(skip["overview"])

    def test_source_detection(self):
        self.assertEqual(cli.detect_source({"source": "sample (演示数据)"}, "x.json"), "demo")
        self.assertEqual(cli.detect_source({}, "sample_orders.json"), "demo")
        self.assertEqual(cli.detect_source({"source": "mcd-mcp"}, "orders.json"), "real")

    def test_end_to_end_generate(self):
        out = os.path.join(ROOT, "report.test.html")
        try:
            path, summary = cli.generate(SAMPLE, out, quiet=True)
            self.assertTrue(os.path.exists(path))
            self.assertEqual(summary["source"], "demo")
            self.assertGreater(summary["orders"], 0)
            self.assertGreater(summary["bytes"], 20000)
            with open(path, encoding="utf-8") as f:
                self.assertIn("</html>", f.read())
        finally:
            if os.path.exists(out):
                os.remove(out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
