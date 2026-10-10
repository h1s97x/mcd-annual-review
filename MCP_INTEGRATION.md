# 麦当劳 MCP 接入说明（MCP_INTEGRATION）

本文件记录本 Skill 与「麦当劳 MCP（`https://mcp.mcd.cn`）」的接入方式，以及**真实联调中观察到的行为**（非文档推测，均来自 2026-10-10 真实 Token 实测）。

## 1. 申请与接入

1. 打开 https://open.mcd.cn/mcp
2. 登录（手机号验证）→ 控制台 → 激活 → 申请 MCP Token → 复制。
3. Token 形如一串字母数字，请求时在 Header 携带 `Authorization: Bearer <Token>`。

WorkBuddy 配置（`~/.workbuddy/mcp.json`）：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer 你的Token" }
    }
  }
}
```

- 协议：**Streamable HTTP**；客户端需支持该传输（WorkBuddy / Cherry Studio / Cursor / TRAE / VSCode 等）。
- 限速：每 Token 每分钟最多 600 次；超限返回 `429`，请降低频率。
- `401`：Token 无效/过期/未提供，检查 Authorization 头。

## 2. 实测发现（2026-10-10 真实 Token 联调）

> 以下为真实返回的观察，文档未明示，写在这里防止后人踩坑。

**① `initialize` 返回正常** —— `serverInfo: { name: "mcd-mcp", version: "1.0.0" }`，鉴权 200，服务端可用。

**② 返回体是「说明文字 + 内嵌 JSON/文本表」，不是纯 JSON。**
多数工具的 `result.content[].text` 是一段「给 LLM 的字段说明 + 一段内嵌 JSON/文本表 + 尾部提醒」。直接 `json.loads` 整段会失败。正确做法：找**信封**——第一个含 `success` / `code` 的对象。本项目 `scripts/fetch_orders.py` 已按此解析。

**③ `order-list` 在无历史订单用户下返回 `data:{}`。**
真实账号若从未下单，`data.list` 不存在。本项目对空订单做空态保护（`render(None, ...)` 显示优雅空态而非 0 报表），并默认用 `make_sample.py` 造演示数据供预览。

**④ `list-nutrition-foods` 返回约 160 条真实餐品营养表**，格式为文本表：
```
[160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:
  猪柳麦满分,null,1288,308,16,16,24,781,213
  巨无霸,null,2146,513,27,26,42,961,171
  ...
```
热量以 `energyKcal` 为准；订单单品按 `productName` 精确匹配累加。套餐名不在营养表内时仅统计可匹配单品（设计取舍：宁可少算，不瞎编）。

**⑤ `campaign-calendar` 返回 markdown 活动列表**（约 30 条），形如：
```
#### 2026年10月10日 今日
- **活动标题**：韩式风味蘸酱上新❤️就「酱」心有所「薯」
  **活动内容介绍**：🆕韩式辣椒黄油风味酱……
```
本项目解析 `#### 日期`、`**活动标题**`、`**活动内容介绍**`。

**⑥ `query-my-coupons` 在实测账号下返回「暂无可用优惠券」**，记为空列表。

**⑦ 金额单位不统一，务必显式转换。**
`order-list` 的 `realTotalAmount` 是字符串元（如 `"24.00"`），`calculate-price` 类的实付价以「分」为单位。本项目统一 `float(x or 0)` 转元后再参与计算。

## 3. 本 Skill 使用的工具与字段映射

| 工具 | 用途 | 关键字段 |
|---|---|---|
| `order-list` | 历史订单 | `data.list[].{orderId, orderType, createTime, storeName, orderProductList[{productName,quantity}], realTotalAmount}` |
| `list-nutrition-foods` | 营养表 | `productName` → `energyKcal` |
| `campaign-calendar` | 活动日历 | markdown 中的日期/标题/介绍 |
| `query-my-coupons` | 我的券 | 无券时「暂无可用优惠券」 |

## 4. 归一化结构（orders.json）

`scripts/fetch_orders.py all` 把上述四项解析为统一结构，供 `generate_report.py` 消费：

```json
{
  "generated_at": "ISO 时间",
  "source": "mcd-mcp",
  "demo": false,
  "orders": [ { "order_id","datetime","channel","store","status","items":[{name,price,qty}],"total" } ],
  "nutrition": [ { "productName","energyKcal" } ],
  "campaigns": [ { "date","title","desc" } ],
  "coupons": [ ]
}
```

## 5. 数据诚实红线（受 McEvent Radar 启发，本项目亦遵守）

- 查不到就说查不到：账号无订单时明确显示空态，不编造数据。
- 演示数据显式标注：运行在 `sample_orders.json` 上时，报告顶部带「演示数据」水印与徽章，不冒充实时数据。
- 价格/热量以官方返回为准；营养表匹配不到的单品，热量记为 0 并在说明中体现「仅统计可匹配单品」，不臆造。
- Token 只进本机客户端配置，不进仓库、不进生成的 HTML、不进日志。

## 6. 调用链：从 MCP 到可视化报告

```
麦当劳 MCP (https://mcp.mcd.cn)
      │  Streamable HTTP + Bearer Token，4 个 Tool
      ▼
scripts/fetch_orders.py                      ← ingest 层
      │  解析「说明文字 + 内嵌 JSON/文本表」信封
      ▼
orders.json  (orders / nutrition / campaigns / coupons)
      │
      ├──────────────────────────────────────────────┐
      ▼                                              ▼
src/mcd_report/domain/metrics.py                （未来）web/index.html
      │  纯函数聚合：overview / weekly / categories     读同一份 model JSON
      │  / top_items / time_of_day / weekdays            前端渲染
      │  / persona / highlight / fun / peaks             → 可部署 Vercel
      ▼                                                   / GitHub Pages
model dict  (schema_version = 1.0.0，前后端唯一契约)
      │
      ▼
src/mcd_report/render/                       ← render 层
      theme.py     品牌色 token（暗/亮两套）
      motion_css.py + motion_js.py   动效层（转场 / 计数 / 图表入场）
      charts.py    内联 SVG 图表（自带入场动画钩子）
      deco.py      品牌矢量插画（汉堡 / 薯条 / 饮料 / 甜筒 / 派）
      scenes.py    11 屏章节内容
      page.py      组装成单文件 HTML
      │
      ▼
report.html   单文件 / 零外链 / 可离线打开 / 可打印存 PDF
```

**关键设计：`ReportModel`（model dict）是唯一契约。**
后端渲染与前端渲染吃同一份 JSON，因此「Python 出单文件 HTML」与
「静态站前端渲染」不会出现两套算法、两份结果。

## 7. 与 MCP 无关的工程约束（同样重要）

| 约束 | 落地方式 |
|---|---|
| 不引入第三方依赖 | 纯 Python 标准库；前端零库零 CDN |
| 产物单文件可离线 | CSS/JS 全内联，图表与插画全部内联 SVG |
| 动效可降级 | 遵循 `prefers-reduced-motion`，另提供「省电模式」开关 |
| 动画层与数据层解耦 | 动效只读 DOM 的 `data-*` 契约，不认识订单/热量等业务概念 |
| 主题可替换 | 全部颜色走 CSS 变量，`render/theme.py` 一处改色全局生效 |

