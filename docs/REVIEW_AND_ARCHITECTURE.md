# 代码与架构审查 + 参赛合规核查

> 审查对象：`mcd-order-report`（2026 麦当劳程序员创意开发大赛参赛作品）
> 审查日期：2026-10-10
> 依据：官方 `M-China/mcd-developer-innovation-challenge` 的 README / activityGuidelines，以及本仓库全部源码。

---

## 0. 结论速览

| 你的问题 | 结论 | 严重度 |
|---|---|---|
| 是否缺少架构设计？ | **是。** 目前是"功能能用、但没有分层"的单体脚本：`generate_report.py` 一个文件 **901 行**，混了 6 类职责。 | P1 |
| 是否符合参赛要求？ | **不符合。** 官方要求的 3 个"必须文件"里，**缺 1 个、错放 1 个**；`workbuddy.md`（影响 3000 积分）也未提交。 | **P0（直接卡报名）** |
| 参考的项目真的参考了吗？ | 抓了三个项目的 README/结构，**但没拆它们的实现、没跑它们的 demo**——所以只抄到了"标签"，没抄到"体验"。这是效果平庸的根因。 | P1 |

---

## 1. 现状盘点（事实）

```
mcd-order-report/
├── SKILL.md                 # Skill 定义
├── README.md
├── SUBMISSION.md            # Issue 提交指引
├── 参赛声明.md               # ← 文件名/内容均不合规（见 §3）
├── references/MCP_INTEGRATION.md  # ← 位置不合规，必须在仓库根目录
├── scripts/
│   ├── fetch_orders.py      # 209 行：MCP 传输 + 文本信封解析
│   ├── generate_report.py   # 901 行：解析 + 指标 + 图表 + 插画 + CSS/JS 模板 + 渲染 + CLI
│   └── make_sample.py       # 96 行
├── tests/test_report.py     # 只测渲染出的 HTML 字符串
├── orders.json / sample_orders.json
└── report.html              # 生成的报告
```

- 依赖：**纯 Python 标准库**（优点，保留）。
- 前端：单文件 HTML，CSS/JS 内联、图表内联 SVG、零外链（优点，保留）。
- 数据流现状：`MCP → fetch_orders.py(解析) → orders.json → generate_report.py(聚合+渲染) → report.html`。

---

## 2. 代码问题清单（带证据）

| # | 问题 | 证据（文件:位置） | 影响 |
|---|---|---|---|
| 1 | **单体脚本，职责混杂** | `generate_report.py` 901 行，一个文件里同时有：解析(`load` L45/`aggregate` L78)、指标(`compute` L109)、人格规则(`derive_persona` L204)、图表(`svg_*` L225–L306)、插画(`deco_*` L308–L364)、模板(`CSS` L366 / `JS` L484)、渲染(`render` L624 / `_wrap` L849)、入口(`main` L884) | 改一处要动多处；无法并行迭代；新人无法接手 |
| 2 | **全局可变状态** | `CAMPAIGNS = []`（L881）模块级；`main()` 里 `global CAMPAIGNS` 赋值（L885+）；`render()` 直接读全局（L686） | `render` 不是纯函数，无法独立测试/复用，埋并发/顺序 bug |
| 3 | **数据契约靠约定，无校验** | `compute()` 返回**裸 dict**（L168–L201）；`render()` 用 `data.get(...)` 兜底（L646–L660） | 键名写错不报错、静默降级（数字悄悄变 0），排查成本极高 |
| 4 | **业务规则与文案耦合** | `derive_persona()` 内硬编码中文标签与阈值（L204–L222）；`compute()` 直接产出 `max_order_name` 等**展示字段** | 规则/文案无法单独演进，无法多语言 |
| 5 | **解析逻辑脆弱且硬编码** | `fetch_orders.py` 用正则从自然语言里抠 JSON：`_find_original_json`(L100)、`_parse_nutrition` 解析 `]{cols}` 文本表(L117)、`_parse_campaigns`(L138) | MCP 文案一变就崩，且无 schema 校验/告警，失败是静默的 |
| 6 | **测试只覆盖"渲染字符串"** | `tests/test_report.py` 全是 HTML 正则断言（8 条），**没有一条断言数值正确性**（如总热量 = 逐单求和） | 改公式无回归保护，错数看不出来 |
| 7 | **无配置层** | `WEEKLY_CAL_BUDGET`(L25)、`TIME_WORD`(L27)、`categorize` 分类规则(L32) 散落模块顶部 | 调参要改源码，无法按用户/地区配置 |
| 8 | **视觉与数据不可分离 → 无法前端化** | 指标与视图糊在同一个 Python 文件里 | **直接卡住"部署到 Vercel/GitHub Pages"的诉求**：想上静态站就得用 JS 重写一遍逻辑，无法复用 |
| 9 | **PNG 导出用 foreignObject** | `JS` 的 `exportPNG()` 注入整段 `<style>` + `<foreignObject>` | Safari 兼容性差、体积大，导出可能失败 |
| 10 | **赛事文件不合规** | 见 §3 | 报名可能被 **校验逻辑直接拒** |

**风险分级**
- **P0（卡报名）**：#10 —— 必须文件缺失/错放。
- **P1（卡得分 + 卡迭代）**：#1 #2 #3 #6 #8。
- **P2（观感/稳健性）**：#4 #5 #7 #9。

---

## 3. 参赛合规核查（对照官方要求）

官方明确要求项目仓库**必须包含下列文件，文件名不可改动**：

| 必须项 | 官方要求 | 现状 | 结论 |
|---|---|---|---|
| `README.md` | 项目介绍、**安装方法**、**使用示例**、**目标用户** | 有，含介绍/安装/示例，但**缺明确"目标用户"章节** | ⚠️ 需补 |
| `CONTEST_DECLARATION.md` | **必须**，文件名**及内容均不可改动**（建议直接用官方文件） | ❌ 现为 `参赛声明.md`，且为**自撰内容** | ❌ **不合规（硬伤）** |
| `MCP_INTEGRATION.md` | **必须**，说明用到的 Server / Tool / 调用流程 / 业务价值 | ⚠️ 存在但位于 `references/` 下 | ❌ **位置不合规（须在仓库根目录）** |
| 源代码 | 项目主体代码 | ✅ 有 | ✅ |
| `workbuddy.md` | 非必须；**参加 WorkBuddy 专项奖励时必须**，文件名不可改动 | ❌ 无 | ⚠️ 影响 3000 积分 |

**其他硬性条款（务必确认）**
- 报名 Issue 正文格式固定：`【参赛申请】/ 项目名称：… / 项目地址：… / 项目简介：…`；**标题与正文间不要换行**、**项目地址不要用 Markdown 链接**（校验较严）。
- 仓库必须 **Public**；项目创建时间需落在 **2025-12-25 ~ 2026-10-25 23:59**（本仓库日期 OK）。
- **排名只看"公开 Star 数"**，Star > 0 才进榜，前 100 名有奖；10-25 23:59 截止、10-26 00:00 定榜。

> ⚠️ **由"排名只看 Star"可知：评审权重最高的是"别人愿不愿意 Star"，而不是代码多优雅。** 这直接影响策略——**在线可玩 demo + 有传播力的 README** 的优先级，高于重构。架构重构是"为迭代提速"的手段，不是目的。

---

## 4. 目标架构设计

设计约束（必须遵守）：① 纯标准库；② 报告仍是**单文件、零外链**；③ 未来要能**部署静态站 / 前端化**。

### 4.1 分层与目录

```
mcd-order-report/
├── SKILL.md
├── README.md                    # 含"目标用户"章节
├── CONTEST_DECLARATION.md       # ← 官方原样，放根目录
├── MCP_INTEGRATION.md           # ← 移到根目录
├── workbuddy.md                 # ← 新增（拿 3000 积分）
├── src/mcd_report/
│   ├── config.py                # 常量/阈值/默认主题
│   ├── models.py                # dataclass：Order / OrderItem / Campaign / Nutrition / ReportModel
│   ├── ingest/
│   │   ├── mcp_client.py        # JSON-RPC/HTTP 传输 + 鉴权 + 重试（纯 IO）
│   │   └── parsers.py           # 各工具"文本信封" → 领域模型（纯函数）
│   ├── domain/
│   │   ├── metrics.py           # 聚合与指标（纯函数，无 IO）
│   │   └── persona.py           # 消费人格规则（阈值可配置）
│   ├── render/
│   │   ├── theme.py             # 品牌 token（MCD 红黄，暗/亮两套）
│   │   ├── charts.py            # SVG 图表
│   │   ├── deco.py              # 食物插画
│   │   ├── templates/           # CSS / JS / HTML 片段（与逻辑分离）
│   │   └── report.py            # 组装 HTML（只吃 ReportModel）
│   └── cli.py                   # 编排：ingest → metrics → render → write
├── web/index.html               # (可选) 纯前端版：读 ReportModel JSON 渲染 → 供 Vercel/GH Pages
├── tests/
│   ├── test_metrics.py          # ★新增：数值正确性
│   ├── test_parsers.py          # ★新增：解析器（吃 fixtures）
│   └── test_report.py           # 现有 HTML 断言
└── fixtures/                    # raw_dump 等测试样本（脱敏）
```

### 4.2 核心接口契约（关键）

```python
# ingest
class MCPClient:
    def call(self, tool: str, args: dict) -> str: ...          # 传输层，唯一碰网络的地方
def parse_orders(text: str) -> list[Order]: ...                 # 纯函数，吃 fixture 可测
def parse_nutrition(text: str) -> dict[str, Nutrition]: ...
def parse_campaigns(text: str) -> list[Campaign]: ...

# domain（纯函数，无 IO，无全局）
def compute_metrics(orders, nutrition, campaigns, now) -> ReportModel: ...

# render（只吃 ReportModel，不碰数据源）
def render_report(model: ReportModel, theme: str = "mcd_dark") -> str: ...

# 唯一视图契约
@dataclass
class ReportModel:
    schema_version: str
    overview: Overview        # 订单数/花费/热量/客单价/跨度
    weekly: list[WeekPoint]
    categories: list[CategorySlice]
    top_items: list[ItemStat]
    time_of_day: list[BucketStat]
    campaigns: list[Campaign]
    persona: Persona
    source: str               # real | demo
    def to_json(self) -> dict: ...
    @classmethod
    def from_json(cls, d: dict) -> "ReportModel": ...
```

### 4.3 数据流

```
MCP ──► MCPClient ──► parsers ──► 领域模型
                                     │
                        compute_metrics（纯函数）
                                     ▼
                               ReportModel ──────────────► to_json()
                                     │                          │
              render_report(theme/charts/deco/templates)         ▼
                                     ▼                 web/index.html（同一契约，前端渲染）
                                report.html                   → 部署 Vercel / GH Pages
```

### 4.4 这套分层如何解决 §2 的问题

| 问题 | 解法 |
|---|---|
| #1 单体 | 按 ingest / domain / render / app 四层拆开，各层单文件、单一职责 |
| #2 全局状态 | `ReportModel` 显式传参，删除 `CAMPAIGNS` 全局 |
| #3 无契约 | 用 `dataclass` 定义并校验；键名错误在构造期就报错 |
| #4 规则/文案耦合 | 规则进 `domain/persona.py`（阈值走 `config`），文案进 `templates` |
| #6 无业务测试 | `test_metrics.py` 覆盖数值、`test_parsers.py` 覆盖解析 |
| #8 无法前端化 | `ReportModel` JSON 成为**前后端唯一契约**，一份数据两端渲染 |
| #9 导出兼容 | 改为 canvas 直接绘制 / 降级为"打印存 PDF" |

---

## 5. 迁移路线（小步、可回滚，每步都能跑）

| 步骤 | 动作 | 验收 | 估时 |
|---|---|---|---|
| **S0** | **合规三件套**：放官方 `CONTEST_DECLARATION.md`；`MCP_INTEGRATION.md` 移到根目录；补 `workbuddy.md`；README 补"目标用户" | 四项 👀 目视核对 | 30 分钟 |
| S1 | 抽 `models.py` + `domain/metrics.py`；**先写 `test_metrics.py` 再迁移** | 新旧报告数值一致 | 1–2h |
| S2 | 抽 `render/`（theme/charts/deco/templates/report）；删全局 `CAMPAIGNS` | 8 项旧测试仍绿 | 2–3h |
| S3 | 抽 `ingest/`（mcp_client + parsers）+ fixtures + `test_parsers.py` | 用 `raw_dump.json` 跑通解析 | 2h |
| S4 | 定义 `ReportModel` + `cli.py` 编排 | 一条命令端到端 | 1h |
| S5 | 加 `web/index.html`（读 model JSON 渲染）→ 部署 Vercel/GH Pages | 手机打开可玩 | 3h |

> 顺序建议：**先 S0（合规是生死线）→ 再做视觉样板 → 最后 S1–S5 重构**。重构是"提速"，不是"救火"。

---

## 6. 视觉重做方向（三选一，先做"样板页"定调）

当前 `report.html` 的问题是：**功能齐全但观感平庸**——滚动卡片 + 大数字 + 小卡片，缺"叙事推进感/动效质感/视觉焦点"。建议**先只做"封面 + 1 个内容页"**给你定调，认可后再铺开，避免返工。

| 方案 | 参考原型 | 核心手法 | 适合 |
|---|---|---|---|
| **A. 强隐喻叙事** | mcd-git | 把账单包装成强概念（如"麦门年度航海日志/成绩单"），一屏一句"金句"，数据是配角 | 想要"记得住、有话题" |
| **B. 强视觉动效** | mcd-menu-stage | 大图/粒子/卡片翻转入场、海报级排版、导出海报 | 想要"截图好看、传播强" |
| **C. 精修排版** | 精致数据报告 | 网格对齐、留白节奏、字重对比、配色克制 | 想要"专业、耐看" |

**我的建议**：先做 **A 的封面 + B 的一个数据页样板**（各 1 页），你对比后择一铺开。这也符合"先看效果再决定"的节奏。

---

## 7. 立即可执行清单（P0）

- [ ] 下载官方 `CONTEST_DECLARATION.md` → 放仓库根目录（内容原样，勿改）。
- [ ] 将 `references/MCP_INTEGRATION.md` 复制/移动到仓库根目录，删除 `references/mcp_setup.md` 或改为根文件的跳转说明。
- [ ] 删除自撰的 `参赛声明.md`（避免与官方文件冲突）。
- [ ] 新增 `workbuddy.md`（从 WorkBuddy 导出本次开发对话上下文）。
- [ ] README 增加"目标用户"章节（如：爱用麦当劳、想看自己消费画像、想控制热量的年轻用户）。
- [ ] 确认仓库为 Public；按官方 Issue 模板（不换行、不用 Markdown 链接）准备报名 Issue 文案。
