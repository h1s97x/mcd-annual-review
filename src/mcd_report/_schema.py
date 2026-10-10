# -*- coding: utf-8 -*-
"""分层与内部契约的独立包。

单独成包的原因：``render`` 需要引用 model 的 schema 版本号，
而 ``mcd_report.__init__`` 会 import 整个包（含 render），
放在顶层会形成循环导入。这里只放常量，无任何依赖。
"""

#: model dict 的 schema 版本。破坏性变更时递增，前端（web/）需同步。
SCHEMA_VERSION = "1.0.0"

#: 报告引擎标识，写入产物以便排查。
ENGINE = "deck"
