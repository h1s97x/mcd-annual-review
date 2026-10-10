---
name: mcd-annual-review
description: "基于麦当劳 MCP 历史订单，生成单文件、全屏章节化的个人点餐「年度报告」（McWrapped 风格）：11 屏滚动叙事 + 数字滚动计数 + 图表生长描边动效 + 双主题，零外部依赖，可直接在 WorkBuddy 中调用 mcd-mcp 拉数并产出报告。"
version: "2.0.0"
---

# 麦门年度账本 McWrapped · 个人年度报告 / Annual Review

把你在麦当劳的每一笔订单，变成一份**能一屏一屏看下去**的个人年度报告：
像 B 站 / 网易云 / 酷狗的年度报告那样，全屏章节化滚动、数字滚动计数、图表描边生长，
最后给一个「消费人格」结论。单文件、零外部依赖、可离线打开。

## 适用场景
- 想用数据回看自己的麦当劳消费（花了多少、吃了多少热量、爱点什么、什么时段下单）。
- 想从「麦当劳 MCP」的真实订单数据里，发现省钱与均衡饮食的机会。
- 参加 2026 麦当劳程序员创意开发大赛（M-CODE），用 WorkBuddy 辅助开发一个创意 Skill。

## 使用方式
1. 在 WorkBuddy 中连接麦当劳 MCP（server 名 `mcd-mcp`，地址 `https://mcp.mcd.cn`，Streamable HTTP + Bearer Token，Token 在 open.mcd.cn/mcp 申请）。
2. 依次调用以下工具，拿到原始返回：
   - `order-list` —— 近期到店/外送历史订单
   - `list-nutrition-foods` —— 餐品营养表（热量/蛋白/脂肪/碳水…）
   - `campaign-calendar` —— 当月营销活动日历
   - `query-my-coupons` —— 我的可用优惠券
3. 把上述返回归一化为 `orders.json`（结构见根目录 `MCP_INTEGRATION.md`；也可直接运行 `scripts/fetch_orders.py all` 自动完成拉取与解析）。
4. 运行报告生成器：
   ```
   python scripts/generate_report.py orders.json report.html
   ```
5. 在 WorkBuddy 预览面板 / 浏览器打开 `report.html`，按 **↓ / 空格 / 滚轮 / 滑动** 逐屏推进。

> 没有真实订单时，可先跑 `python scripts/make_sample.py` 生成演示数据 `sample_orders.json`，
> 再 `python scripts/generate_report.py sample_orders.json report.html` 预览效果（报告会打「演示数据」徽章）。

## 叙事结构（11 屏，逐屏自动推进）
| # | 场景 key | 章节 | 内容 |
|---|---|---|---|
| 0 | `cover` | 封面 | 年份 + 「你的麦麦年度报告」大字开场，汉堡插画 + 粒子 |
| 1 | `overview` | 年度总览 | 订单数 / 总花费 / 总热量 / 客单价 / 覆盖天数，数字滚动计数 |
| 2 | `spend` | 真金白银 | 总花费大字 + 换算「≈几个巨无霸」+ 日均花费 |
| 3 | `calories` | 热量账本 | 逐周热量折线（描边入场）+ 周预算基准线 + 超标周高亮 |
| 4 | `category` | 品类偏好 | 花费占比环形图（逐段生长）+ 各品类金额横条 |
| 5 | `top_items` | 心头好 | 单品 TOP5 排行条（宽度生长动画） |
| 6 | `time_of_day` | 时间线 | 早/午/下午/晚/夜 下单分布 + 深夜单占比 |
| 7 | `weekday` | 一周节律 | 周一~周日订单分布柱状图 |
| 8 | `highlights` | 高光时刻 | 最大单笔 / 最贵一单 / 最深夜一单 + 活动日历卡片 |
| 9 | `persona` | 消费人格 | 趣味人格标签 + 一句话解读 + 人格雷达维度 |
| 10 | `outro` | 尾声 | 总结语 + 「重播」按钮 + 分享提示 |

**交互**：滚轮/触摸/方向键逐屏推进（带累积阈值与 520ms 锁，避免触控板过度滚动）；
右侧章节导轨可点击跳转；`跳过` 直达结尾；`重播` 复位全部动画重跑。
`window.McWrapped` 暴露 `goto/next/prev/replay/reset` 便于自动化与二次开发。

## 可视化与动效特性
- **单文件、零外部依赖**：所有 CSS/JS 内联、图表为内联 SVG，不引用任何 CDN / 外链字体 / 远程图片，可离线打开与分享（已用 `tests/test_report.py` 断言无外链）。
- **原生零依赖动效引擎**：屏间平滑转场（transform + cubic-bezier）、`requestAnimationFrame` easeOutQuart 数字滚动计数、SVG `getTotalLength()` 路径描边、环形图逐段生长、克制粒子/光晕。
- **双主题可切换**：暗色沉浸科技风 / 亮色清爽风，CSS 变量驱动，报告内一键切换。
- **减弱动效适配**：遵循 `prefers-reduced-motion`，并提供「省电模式」手动开关（localStorage 持久化），开启后跳过所有动画直接呈现终态。
- **移动端优先**：`100dvh` 全屏布局、`clamp()` 流体字号、触摸滑动手势、适配不同屏幕比例。
- **导出与打印**：「🖼 导出海报」生成 PNG、「🖨 打印/存 PDF」走系统打印；`@media print` 已将 11 屏摊平为可读长页。
- **优雅空态**：账号无历史订单时显示引导式空态（而非一片 0 报表）。
- **数据诚实徽章**：演示数据带「演示数据」水印与徽章，真实数据标注「麦当劳 MCP 实时数据」，不混淆。

## 工程结构（动画层与数据层解耦）
```
src/mcd_report/
├── _schema.py        # schema_version / engine 常量（无依赖，防循环导入）
├── config.py         # 所有可调参数：预算、阈值、分类规则、场景开关
├── domain/metrics.py # 纯函数：归一化 + 统计 + 人格判定 → ReportModel
├── render/
│   ├── theme.py      # 双主题 token → CSS 变量
│   ├── motion_css.py # 动效样式（转场/计数/生长/粒子/reduced-motion）
│   ├── motion_js.py  # 零依赖动效引擎（推进/计数/描边/重播）
│   ├── charts.py     # 内联 SVG 图表（折线/环形/条形）
│   ├── deco.py       # 内联 SVG 插画（汉堡/薯条/饮料…）
│   ├── scenes.py     # 11 个场景模板 + 顺序表
│   └── page.py       # 组装完整 HTML
└── cli.py            # 编排：读 JSON → 算 model → 渲染 → 落盘
scripts/generate_report.py  # 薄入口，转发到 mcd_report.cli
```
**依赖单向向下**：`cli → domain → (无)`、`cli → render → (theme/config)`。
动画层只认 DOM 上的 `data-*` 契约（`data-count / data-anim / data-scene / data-chapter / data-particles / data-decor`），
**不关心数据从哪来**——因此换数据源只动 `domain/`，换主题只动 `theme.py`，换叙事只动 `scenes.py` + 引擎。

## 命令行参数
```
python scripts/generate_report.py [orders.json] [report.html] \
    [--theme dark|light] [--only cover,calories,persona] [--skip weekday]
```
- `--theme`：指定初始主题（默认 `dark`）。
- `--only`：只保留列出的场景（`cover`/`outro` 骨架始终保留）。
- `--skip`：裁掉指定场景，便于按场景裁剪叙事。

## 数据字段映射（关键）
- 订单：`data.list[]` → `orderId / orderType / createTime / storeName / orderProductList[{productName, quantity}] / realTotalAmount`
- 营养：以 `productName` 为键，将订单单品匹配到 `energyKcal` 累加热量；套餐名不在营养表内时仅统计可匹配单品。
- 活动：`campaign-calendar` 的 markdown 中解析 `#### 日期` + `**活动标题**` + `**活动内容介绍**`。
- 优惠券：返回「暂无可用优惠券」时记为空列表。

## 注意事项
- 报告为**单文件、零外部依赖**：所有 CSS/JS 内联、图表为内联 SVG，不引用任何 CDN、外链字体或远程图片，可离线打开与分享。
- 新用户或空订单时，报告显示空态提示，不会报错。
- 本 Skill 仅供个人非商业用途，遵守麦当劳 MCP 服务规则与大赛规则。
- 工程可验证：`python -m unittest discover -s tests -v` 跑本地自检（46 项，不碰真实 MCP）。
