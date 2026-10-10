# 麦门年度账本 / McWrapped · mcd-annual-review

![MCP](https://img.shields.io/badge/MCP-McDonald's%20China-FFC72C?logo=mcDonalds)



![Built with WorkBuddy](https://img.shields.io/badge/Built%20with-WorkBuddy-0052D9)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

![License](https://img.shields.io/badge/License-MIT-green)

> 2026 麦当劳程序员创意开发大赛（M-CODE）参赛作品  
> 基于 **麦当劳 MCP** 的真实订单数据，用 **WorkBuddy** 辅助开发，  
> 生成一份**单文件、零外部依赖、全屏章节化滚动叙事**的个人年度报告。

## 一句话介绍

把你在麦当劳的每一笔订单，变成一份**像 B 站 / 掘金 / 酷狗音乐年度报告一样**  
可以一屏一屏翻下去、有数据叙事、有动效质感的个人年度报告 ——  
而且**零外部依赖、可离线打开、手机上也能流畅播放**。

## 目标用户

| 用户                  | 他们的诉求                     | 这份报告给了什么                         |
| ------------------- | ------------------------- | -------------------------------- |
| **麦当劳高频用户**（每周至少一次） | 「我一年到底在麦门花了多少、吃了多少？」      | 11 屏年度账本：订单数、花费、热量、品类、单品、时段、消费人格 |
| **关注热量/健康的用户**      | 「我是不是吃太多炸物和甜品了？」          | 逐周热量折线 + 推荐周预算基准线 + 超预算周数提示      |
| **想省钱的学生 / 上班族**    | 「哪个时段、哪种组合最划算？」           | 客单价、日均投入、品类花费占比、近期活动日历           |
| **喜欢分享的年轻人**        | 「想发朋友圈/小红书晒一下」            | 强视觉的封面与结尾页，支持重播动效、导出 PNG、存 PDF   |
| **参加大赛的开发者**        | 「想看一个完整的数据可视化 Skill 长什么样」 | 可直接复用的分层架构 + 零依赖动效引擎 + 数值正确性测试   |
| **对数据合规敏感的从业者**     | 「数据会不会外流？」                | 全部本地计算，Token 只在环境变量，产物不上传任何服务器   |

> 因此报告从设计之初就坚持**纯本地生成、单文件产物、零外链**：  
> 所有指标在本机算完，产物就是一个本地 HTML 文件，不上传任何服务器。

## 为什么做这个

大赛里「点餐助手 / 省钱助手」扎堆，&#x4F46;**「数据叙事 + 消费画像年度报告」几乎是一片空白**。  
而麦当劳 MCP 恰好开放了 `order-list`（历史订单）、`list-nutrition-foods`（160+ 餐品营养）、  
`campaign-calendar`（活动）、`query-my-coupons`（优惠券）——足够支撑一份  
「有门槛、有美感、评委一眼能看懂价值」的报告型 Skill。

## 亮点

| 特性                | 说明                                                                            |
| ----------------- | ----------------------------------------------------------------------------- |
| 🎬 **章节化滚动叙事**    | 11 屏：封面 → 总览 → 花费 → 热量 → 品类 → 单品 → 时段 → 星期 → 高光 → 人格 → 尾声。每屏一个主题，逐屏自动推进       |
| ✨ **真实动效**        | 屏间 spring 平滑转场 · 关键数字 rAF 滚动计数 · 折线描边 / 条形生长 / 环形描出 · 粒子与光晕氛围 · 元素 stagger 入场 |
| 🎛 **可控可跳过**      | 键盘（↑↓/空格/Home/End）· 滚轮 · 触摸滑动 · 侧边导航点；`R` 重播当前屏；随时可跳屏                         |
| ♿ **尊重系统偏好**      | 遵循 `prefers-reduced-motion` 自动降级，另提供「省电模式」手动开关                                |
| 🌗 **双主题**        | 深色沉浸（默认）/ 亮色清爽，全部颜色走 CSS 变量，切换即时生效并记忆                                         |
| 📊 **全内联 SVG 图表** | 折线 / 环形 / 横向条形 / 柱状 / 进度条组，随主题自动重着色                                           |
| 🍔 **品牌视觉**       | 金拱门金 + 麦当劳红，内联矢量插画（汉堡 / 薯条 / 饮料 / 甜筒 / 派）                                     |
| 🫥 **优雅空态**       | 账号无历史订单时显示三步引导，而非一片 0                                                         |
| 🔒 **数据诚实**       | 演示数据强制水印与徽章；真实数据标注「麦当劳 MCP 实时数据」，不混淆                                          |
| 🧪 **可验证**        | 46 条零依赖测试：**数值正确性** 27 条 + 产物约束 19 条                                          |
| 📱 **移动端优先**      | 大字报式排版、`svh` 视口、矮屏与横屏单独适配                                                     |

## 功能模块

| 屏    | 内容                                                          |
| ---- | ----------------------------------------------------------- |
| 封面   | 品牌标题 + 年度水印 + 授权说明 + 数据来源徽章                                 |
| 年度总览 | 下单次数（大数字滚动）、平均频率、主场餐厅、到店/外送比例                               |
| 真金白银 | 总花费（大数字滚动）、折合巨无霸个数、客单价、最贵一单、日均投入                            |
| 热量账本 | 累计热量、跑步消耗折合、**逐周热量折线 + 推荐预算基准线**、超预算周数                      |
| 品类偏好 | 花费占比**环形图**（描出动画）+ 图例，标出绝对主场品类                              |
| 心头好  | TOP5 单品**条形图**（生长动画）+ TOP1 明细                               |
| 时间线  | 早/午/下午/晚/夜分布**进度条组** + 深夜/早餐订单计数                            |
| 一周节律 | 周一到周日**柱状图** + 最爱的快乐日                                       |
| 高光时刻 | 自动挑选最有话题度的一条（深夜型→深夜头条，否则→热量巅峰周）+ 备选高光                       |
| 消费人格 | 人格标签（深夜碳水战士 / 早起元气派 / 周三快乐汉堡人 / 麦门土豪 / 甜度超标）+ 一句话解读 + 年度关键词 |
| 尾声   | 年度总结数字 + 近期活动 + 重新翻阅 / 重播 / 存 PDF                           |

## 测试

```bash
python -m unittest tests.test_metrics tests.test_report -v
```

| 套件                | 条数 | 覆盖                                                           |
| ----------------- | -- | ------------------------------------------------------------ |
| `test_metrics.py` | 27 | **数值正确性**：总量=逐单求和、品类分区守恒、周序列求和自洽、边界（空数据/坏时间/坏价格/营养缺失）、人格规则阈值 |
| `test_report.py`  | 19 | 产物约束：单文件零外链、无残留占位符、HTML 标签闭合、章节顺序、动效契约挂钩、主题切换、板块开关、端到端生成     |

全部通过，且**不碰任何真实 MCP / 网络**。

## 快速开始

```bash
# 1) 申请麦当劳 MCP Token：https://open.mcd.cn/mcp
export MCD_MCP_TOKEN="你的Token"

# 2) 拉取并归一化真实订单（产出 orders.json，含营养表/活动）
python scripts/fetch_orders.py all

# 3) 生成报告
python scripts/generate_report.py orders.json report.html

# 没有 Token / 没有订单？用演示数据预览：
python scripts/make_sample.py
python scripts/generate_report.py sample_orders.json report.html
```

用浏览器或 WorkBuddy 预览面板打开 `report.html`。

**生成器可选参数：**

```bash
python scripts/generate_report.py --theme light              # 亮色主题
python scripts/generate_report.py --skip weekday,highlights  # 裁掉某些章节
python scripts/generate_report.py --only cover,overview,outro # 只出骨架三屏
```

## 目录结构

```
mcd-annual-review/
├── SKILL.md                    # Skill 定义（WorkBuddy 加载）
├── README.md                   # 本文件
├── CONTEST_DECLARATION.md      # 参赛声明（官方原文，勿改）
├── MCP_INTEGRATION.md          # 麦当劳 MCP 接入 + 真实联调发现 + 调用链
├── workbuddy.md                # WorkBuddy 开发上下文（专项奖励核验）
├── SUBMISSION.md               # Issue 提交指引
├── src/mcd_report/             # ★ 分层实现
│   ├── config.py               #   阈值 / 预算 / 分类规则 / 板块开关
│   ├── domain/metrics.py       #   聚合与指标：纯函数，无 IO、无全局状态
│   ├── render/
│   │   ├── theme.py            #   品牌色 token（暗/亮两套）
│   │   ├── motion_css.py       #   动效层 CSS（粒子 / 转场 / 入场）
│   │   ├── motion_js.py        #   动效引擎 JS（翻屏 / 计数 / 图表 / 交互）
│   │   ├── charts.py           #   内联 SVG 图表（自带入场动画钩子）
│   │   ├── deco.py             #   品牌矢量插画
│   │   ├── scenes.py           #   「一屏一主题」的章节内容
│   │   └── page.py             #   组装成单文件 HTML
│   └── cli.py                  #   编排：ingest → domain → render → 落盘
├── scripts/
│   ├── fetch_orders.py         # MCP 拉取 + 归一化为 orders.json
│   ├── make_sample.py          # 生成演示数据（真实餐品名+真实营养表）
│   └── generate_report.py      # ★ 入口脚本（薄外壳，实现全在 src/）
├── tests/
│   ├── test_metrics.py         # 数值正确性（27 条）
│   └── test_report.py          # 产物约束（19 条）
├── docs/
│   └── REVIEW_AND_ARCHITECTURE.md  # 架构审查报告
├── orders.json                 # 真实数据（运行后生成，勿提交 Token）
├── sample_orders.json          # 演示数据
└── report.html                 # 生成的报告
```

## 技术要点

- **单文件、零外部依赖**：所有 CSS/JS 内联，图表与插画全部内联 SVG，  
  颜色引用 CSS 变量随主题自动重着色，不引用任何 CDN / 外链字体 / 远程图片（测试已断言）。
- **纯标准库**：全部 Python 代码仅用标准库，无需 `pip install`。
- **分层解耦**：`domain`（纯函数指标）→ `render`（视觉）← `cli`（编排）。  
  **动画层与数据层通过 DOM 的 `data-*` 契约通信**，动效引擎不认识任何业务概念，  
  因此换主题、换数据源都不需要动动效代码。
- **唯一契约**：`ReportModel`（model dict，`schema_version=1.0.0`）是前后端唯一接口，  
  未来做纯前端静态站（部署 Vercel / GitHub Pages）可复用同一份数据，不会出现两套算法。
- **真实数据解析**：麦当劳 MCP 返回的是「说明文字 + 内嵌 JSON/文本表」的信封，  
  `fetch_orders.py` 负责把 `order-list`、`list-nutrition-foods`、`campaign-calendar` 解析为统一结构。  
  实测行为（含各种踩坑）记录在 `MCP_INTEGRATION.md`。

## 灵感与致谢

本项目的可视化与工程取舍，借鉴了下列优秀作品的可取之处：

**本届大赛作品**

- **mcd-git**（dewin-zahl）：强隐喻 + 零依赖 + 自带 mock 测试的工程素养。
- **mcd-event-radar**（Zafer-Liu）：「数据诚实红线」与在线可玩 / 演示视频的体验设计。
- **mcd-menu-stage**（ddouworld）：趣味呈现、导出 PNG/打印、单文件 HTML 范式。

**年度报告形态参考**

- **Github-Recap**（Smartuil）：全屏章节化翻页（Framer Motion spring 位移 + wheel 阈值累积 +  
  触摸阈值 + 键盘导航）、Cyberpunk 主题 token、run/recap/personality 分层。  
  本项目**原生复刻了它的交互模型**（阈值累积防误触、弹簧曲线、章节化叙事），  
  但用**零依赖的原生 Web Animations API** 实现，并把主题换成麦当劳品牌色。

本项目在此基础上聚焦「**数据叙事 + 消费画像报告**」这一空白赛道，并遵守同样的数据诚实原则。

## 许可证

个人非商业用途，遵守麦当劳 MCP 服务规则与大赛规则。
