# 提交说明（Submission Guide）

本作品通过 **M-China/mcd-developer-innovation-challenge** 仓库的 Issue 提交报名。

## 提交步骤
1. 将本项目发布到你的 **个人 GitHub 公开仓库**（本目录即为一个完整仓库）。
   - 注意：请勿把真实 `orders.json`（含个人订单）或 MCP Token 提交；`.gitignore` 已忽略 `orders.json`、`raw_dump.json`。
2. 打开赛事 Issue 页面：https://github.com/M-China/mcd-developer-innovation-challenge/issues ，点击 **New Issue**。
3. 按下方格式填写并提交。

## Issue 格式

> ⚠️ 本格式**不是**我拍脑袋定的，是照抄赛事仓库里已有的参赛 Issue（#351 / #357 / #362 / #378 / #380）归纳出来的。
> 已有参赛作品清一色是**三段式**：`【参赛申请】` + `项目名称` + `项目地址` + `项目简介`。
> 不要自创「一、二、三…六」大段结构——那会和别人的投稿长得完全不一样，评审扫读时很吃亏。

```
【参赛申请】
项目名称：xxx
项目地址：https://github.com/<用户名>/<仓库名>
项目简介：xxx
```

- **标题**：`【参赛申请】<项目名> —— <一句话卖点>`（副标题可选，但多数人写了，更抓人）
- **项目简介**：**一段话**讲清楚三件事——
  1. 它是什么、解决什么场景的问题；
  2. 和同类作品比**刻意做了什么不一样的设计**（这是评审唯一会细看的部分）；
  3. 简短技术说明（数据来源 / 依赖情况 / 是否可离线 / 测试情况）。

> ⚠️ 别写成技术文档。参考 #362「麦门日报」的项目简介只有一句话：
> 「为今天这一顿麦当劳，办一份只发行一期的报纸。」
> 不要分「一、二、三」、不要编号列表、不要堆小标题——别人都是一气呵成的一段。

## 本项目实际提交的内容

标题：
```
【参赛申请】麦门年度账本 McWrapped —— 把一年的麦当劳订单做成一场 P5R 风格的年度报告演出
```

正文（已提交为 Issue #379）：
```
【参赛申请】
项目名称：麦门年度账本 McWrapped（mcd-order-report）
项目地址：https://github.com/h1s97x/mcd-order-report
项目简介：把你在麦当劳一年的订单做成一份能一屏一屏看下去的年度报告，11 幕从封面一路推到「消费人格」。视觉走《女神异闻录 5 皇家版》的波普朋克海报风——幻影红 + 墨黑的斜切色块、涂鸦动感线条、「绑架信」式拼贴大字；每屏都是「大字结论 + 小字注解 + 数据层」三层，11 屏版式互不重复，不平铺直叙。演出上做成「逐步呈现 + 点击加速」：内容按 data-beat 分段自动入场（间隔 460ms）一点点铺开，播放中点击 / 滚轮 / 方向键会立刻展开剩余内容，再触发一次才翻页，同时解决「太快看不清」和「想跳过要干等」。数据来自麦当劳 MCP 真实订单（order-list / list-nutrition-foods / campaign-calendar / query-my-coupons），Python 标准库分层实现，动效为原生 JS/CSS 零第三方库，产物是单文件 HTML、图表内联 SVG、无任何外链，双击即可离线打开；计数器的 HTML 直接写真值，禁用 JS 或打印时依然正确，48 项单元测试通过。使用 WorkBuddy 开发，已提交 workbuddy.md。
```

## 提交前自检
- [x] 仓库为 **Public**
- [ ] 根目录四件套齐全：`README.md` / `CONTEST_DECLARATION.md` / `MCP_INTEGRATION.md` / `workbuddy.md`
- [x] 未提交真实 `orders.json` 与 Token
- [ ] `report.html` 可离线打开、11 屏叙事推进正常、双主题切换正常、图表动画正常
- [x] `python -m unittest discover -s tests -v` 全部通过（48 项）
- [x] Issue 按赛事既有格式填写并附仓库地址（#379）
