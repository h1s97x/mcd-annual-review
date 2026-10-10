#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦门年度账本 / McWrapped —— 个人年度报告生成器（**入口脚本**）。

本脚本是薄外壳，真正的实现分层在 ``src/mcd_report/``：

    src/mcd_report/
    ├── config.py            # 阈值 / 预算 / 分类规则 / 板块开关（调参只动这里）
    ├── domain/metrics.py    # 聚合与指标：纯函数，无 IO、无全局状态
    ├── render/
    │   ├── theme.py         # 品牌色 token（暗/亮两套）
    │   ├── motion_css.py    # 动效层 CSS（粒子 / 转场 / 入场）
    │   ├── motion_js.py     # 动效引擎 JS（翻屏 / 计数 / 图表 / 交互）
    │   ├── charts.py        # 内联 SVG 图表（自带入场动画钩子）
    │   ├── deco.py          # 品牌矢量插画
    │   ├── scenes.py        # 「一屏一主题」的章节内容
    │   └── page.py          # 组装成单文件 HTML
    └── cli.py               # 编排：ingest → domain → render → 落盘

产物：**单文件、自包含、零外部资源**的 HTML（可离线打开 / 分享 / 部署静态站）。

用法:
    python scripts/generate_report.py                     # 默认 orders.json → report.html
    python scripts/generate_report.py sample_orders.json report.html
    python scripts/generate_report.py --theme light
    python scripts/generate_report.py --skip weekday,highlights
    python scripts/generate_report.py --only cover,overview

没有真实订单时，先跑 ``python scripts/make_sample.py`` 生成演示数据。
"""
import os
import sys

# 把 src/ 加进模块搜索路径，让脚本可直接运行（无需 pip install）
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from mcd_report.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
