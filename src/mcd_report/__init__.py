# -*- coding: utf-8 -*-
"""mcd-annual-review：麦门年度报告生成器。

分层结构（依赖方向单向向下，domain 不依赖 render）：

    ingest  ->  domain  ->  render  ->  cli
    拉数解析     指标计算     视觉呈现     编排

- ``ingest``：MCP 传输与「文本信封」解析（唯一接触网络的地方）。
- ``domain``：纯函数聚合与指标，无 IO、无全局状态。
- ``render``：主题 / 图表 / 插画 / 模板 / 组装，只吃 model，不碰数据源。
- ``cli``：把上面三层串起来。

契约：``domain.metrics.build_model()`` 产出的 model dict 是**唯一的前后端契约**，
`SCHEMA_VERSION` 变更即代表契约破坏性变更（web 端需同步）。
"""

__version__ = "2.0.0"
