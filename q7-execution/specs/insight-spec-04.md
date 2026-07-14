# Insight: spec-04-execution-report — 怎么知道执行得对不对？执行报告

> **评分 44/55** · 可发布；维度 4「可复现」与 11「同步」需修补
> 评审基线：spec-review-handbook.md 11 维 rubric
> **本文档定位**：服务于「打磨示例 spec + 萃取写法方法/模板」两个目标。

---

## 一、设计意图复盘

这是 q7 章的**收尾 spec**——前三份 spec 让学员看到取整偏差、滑点、成本、执行落差**整体上**有多大；这份 spec 让学员**逐笔对账**，找到落差的具体来源。spec 用 7 步任务从「逐笔对比表 → 汇总统计 → 最贵一笔 → 分布图 → 桥接 A 股」走完一条诊断闭环。【结构】【动机】

**为什么必须有"最贵的一笔"这一段**：spec 第 4 条要求找出滑点最大的交易并展示详情。这是**反平均**的设计——执行落差的"平均"是 0.05% 看起来无害，但**少数几笔可能差 1-2%**。学员只看汇总统计会得到错误结论，必须看尾部。这是 q5/q6 已建立的"分布优于均值"原则在执行场景的延续。【动机】【教学场景】

**为什么用直方图 + 箱线图双图**：spec 第 5 条要求左图是滑点直方图（看分布形状）+ 右图是按标的分组的箱线图（看哪只标的执行差）。直方图回答"整体怎样"、箱线图回答"问题在哪里"——两个视角各回答一个问题，缺一不可。【结构】【教学场景】

**桥接 A 股的克制**：spec 第 7 条没有要求"在 A 股重跑一次"——而是用文字说明「美股模拟盘上的问题在 A 股一样存在」并给出操作建议。这是教学克制——q7 章主线是认知（了解执行落差），不是工程（A 股自动化交易）。后者需要另一套基础设施（国内券商 API），不在 q7 范围。【教学场景】

**接续 spec-03 的产出**：spec 第 2 条直接用 `result_sim.trades` 和 `result_live.trades` 构造 ExecutionReport——其中 `result_live` 是 spec-03 不论走 Part B-2（Alpaca）还是 Part 7（兜底）都会赋值的变量。这种「接续型 spec 链」是 q1 已建立的模式（df 从 spec-01 流到 spec-07）在 q7 的延续。【结构】【同步】

---

## 二、与 notebook 实际产出的对照

| spec 要求 | notebook 实际实现 | 评价 |
|---|---|---|
| `ExecutionReport(sim_fills, live_fills)` | ✓ 字符级一致 | 一致 |
| 前 20 笔逐笔对比表 | ✓ `comparisons[:20]` | 一致 |
| 汇总统计字段 | ✓ 5 个字段全部呈现 | 一致 |
| 最贵的一笔——按 `price_slippage` 绝对值排序 | `max(matched, key=lambda c: abs(float(c.price_slippage)))` | 一致 |
| 滑点 > 1% 时分析原因 | ✓ 三个候选原因列出 | 一致 |
| 直方图 30 bins，红色虚线 + 橙色虚线 | ✓ | 一致 |
| 箱线图三个箱子，三色填充 | ✓ `colors_box = ['#3498DB', '#E74C3C', '#2ECC71']` | 一致 |
| figsize 14×5、两图并排 | ✓ | 一致 |
| 滑点 > 0.5% 的笔数和占比 | ✓ | 一致 |
| 图片保存 | `../book/images/05-execution-quality.png` | spec 缺 |
| matched 过滤条件 | spec 写"匹配交易"，notebook `c.sim_shares > 0 and c.live_shares > 0` | spec 描述模糊，AI 自行选实现 |
| 桥接 A 股的具体内容 | spec 给了 4 点（取整 / 滑点 / 成本 / 执行落差）+ 3 点操作建议 | 字符级一致 |

**对照结论**：spec 与 notebook 主线高度一致，是 q7 四份 spec 中同步性最好的一份。但**图片保存路径**和**matched 过滤条件的精确定义**两处由 AI 自行补全。

---

## 三、最佳实践对照（11 维 rubric）

| 维度 | 分（1-5） | 备注 |
|---|---|---|
| 1 任务边界清晰度 | 5 | "ExecutionReport 逐笔对账"主线清晰，7 步走完闭环 |
| 2 可验证性 | 4 | 验证段 6 条机械可检查项；缺真正的 assert |
| 3 输出契约具体度 | 4 | 表格列名、figsize、bins、颜色都明确；缺图片路径和 matched 过滤的精确定义 |
| 4 可复现性 | 3 | 依赖 spec-03 的 `result_live`（已有 Alpaca 时是真实数据，每次跑结果不同）——spec 应明确「Alpaca 路径下 result_live 不可复现是 by design」；oxq 版本未声明 |
| 5 上下文 / 动机充分度 | 5 | 上下文段强代入："整体差 2% 不够——需要知道具体哪笔差得最多" |
| 6 抽象层次恰当 | 5 | 写"做什么 + 关键参数"，没把 ExecutionReport 内部逻辑写死 |
| 7 正向指令为主 | 5 | 全部"做 X" |
| 8 结构一致性 | 5 | 严格四段 + 验证段 |
| 9 简洁性 | 5 | 62 行精炼，每条都"删了就坏" |
| 10 学员可学习性 | 4 | 上下文叙事清晰；ExecutionReport / FillComparison 等专业术语首次出现，缺解释 |
| 11 与 notebook 同步性 | 3 | matched 定义、图片路径漂移；其他高度一致 |
| **合计** | **44/55** | 可发布；维度 4 和 11 是修补重点 |

---

## 四、可改进点（带改写示例）

### 改进 1：matched 过滤条件精确定义【精确】【同步】

**现状**（spec 第 4 条）：
```
- 从匹配交易（回测和实盘都有成交的）中，按 price_slippage 绝对值排序
```
"匹配交易"语义模糊。notebook 实际用 `c.sim_shares > 0 and c.live_shares > 0`，但这个条件本身有歧义——是「同标的同日 sim 和 live 都有成交」还是「sim 和 live 各自都有过这只标的的成交」？

**改写**：
```
- "匹配交易"定义：FillComparison 中 sim_shares > 0 且 live_shares > 0（即同标的同日，回测和实盘都有成交）
- 在 comparisons 上过滤：
  matched = [c for c in comparisons if c.sim_shares > 0 and c.live_shares > 0]
- 从 matched 中按 |price_slippage| 排序
```

显式定义消除二义性。

### 改进 2：补图片保存路径【同步】【精确】

**现状**：spec 第 5 条没提保存路径。notebook 实际 `plt.savefig("../book/images/05-execution-quality.png", dpi=150, bbox_inches='tight')`。

**改写**：
```
5. 画执行质量分布图（figsize 14×5，两个子图并排）保存到 ../book/images/05-execution-quality.png（dpi=150, bbox_inches='tight'）：
   - 左图：滑点直方图（30 bins，#3498DB 蓝色填充）
     · 标注零滑点线（红色虚线）和平均值线（橙色虚线）
   - 右图：按标的分组的滑点箱线图
     · SPY/QQQ/GLD 各一个箱子，颜色填充：SPY #3498DB、QQQ #E74C3C、GLD #2ECC71
```

### 改进 3：声明 result_live 的可复现边界【可复现】【动机】

**现状**：spec 假设 `result_live` 已存在但没说它来自哪条路径。如果学员有 Alpaca 账号，`result_live = result_alpaca`（基于 Alpaca IEX 历史数据，每次跑相同）；如果没有账号，`result_live` 是 NEXT_OPEN 模拟（同样可复现）。但 Part B-2 的 LiveBroker 实盘成交本身不进 result_live——这点 spec 没说清。

**改写**（上下文段加注）：
```
**关于 result_live 的可复现性**：
- 有 Alpaca 时：result_live = result_alpaca（Alpaca IEX 历史回测，可复现）
- 无 Alpaca 时：result_live = SimBroker NEXT_OPEN 模拟（可复现）
- 两者都是历史回测结果——LiveBroker 的真实成交（Part B-2）只用于演示，不进 ExecutionReport

ExecutionReport 对比的是两条历史回测的差异（数据源 / 成交价模式），不是回测 vs 真实下单。
```

避免学员误解 ExecutionReport 在做什么。

### 改进 4：声明 oxq 版本【可复现】

**改写**（要求段开头加）：
```
**版本锁**：open-xquant >= 0.7.0（含 ExecutionReport 模块）
```

### 改进 5：补 ExecutionReport 术语简释【可学习】

**现状**：spec 直接用 `FillComparison`、`price_slippage`、`shares_diff`、`sim_only_trades`、`live_only_trades` 等术语。

**改写**（要求段第 1 条加注）：
```
1. 阅读以下 oxq 模块的源码（含术语简释）：
   - `oxq.portfolio.execution_report` — `ExecutionReport` 和 `FillComparison`
     · 术语：sim_fills（回测成交）、live_fills（实盘/模拟实盘成交）
     · matched_trades = 同标的同日两边都有成交
     · sim_only_trades = 仅回测有（实盘可能因取整或现金不足没下成）
     · live_only_trades = 仅实盘有（罕见，通常是回测时机模型差异）
     · price_slippage = (live_avg_price - sim_avg_price) / sim_avg_price
```

让 0 基础学员单读 spec 也能理解输出表格的语义。

### 改进 6：补"桥接 A 股"段的 spec ↔ book 同步【同步】

**现状**：spec 第 7 条的桥接 A 股段与 notebook 字符级对齐——这是好事。但 book 章节如果用了类似措辞，需要确保三处一致。

**改写**（保持现状但加同步提醒）：
```
7. 桥接 A 股（注意：本段文字会出现在 book/chapter.md 同位置——三处必须字符级一致）：
   ...
```

提醒研发者同步检查。

---

## 五、可沉淀的方法点

### A. 这份 spec 已经示范的原则

- **【结构】"诊断闭环"七步走**：逐笔对比 → 汇总 → 最贵的一笔 → 分布图 → 桥接其他市场——可作为「执行报告 / 诊断报告」类 spec 的模板
- **【动机】反平均设计**："找出最贵的一笔"是关键的反平均——平均看起来无害的滑点，尾部可能差 1-2%。可作为"分布优于均值"原则在执行场景的示范
- **【精确】双图各回答一个问题**：直方图回答"整体怎样"，箱线图回答"问题在哪只标的"——可作为"双图设计"模板
- **【教学场景】桥接的克制**：q7 主线是美股 paper trading，但章末必须桥回学员主市场（A 股）。spec 用文字桥接而非要求重跑——是教学克制示范
- **【结构】接续型 spec 链的延续**：spec-04 直接用 spec-03 产出的 result_live——是 q1 已建立模式在 q7 的延续证据

### B. 这份 spec 修补后可示范的原则

- **【精确】matched 过滤条件显式定义**：当前模糊；修补后可作为"涉及集合操作的 spec 必须给出过滤谓词"的示范
- **【可复现】不同执行路径的可复现边界声明**：当前 result_live 来源不明；修补后可作为"涉及条件分支的 spec 必须分别声明可复现性"的示范——这是 q7 引入分支后的新模板需求
- **【可学习】ExecutionReport 术语简释**：当前直接用术语；修补后可作为"专业术语首次出现 spec 内必须有最低限度解释"的示范
- **【同步】图片保存路径**：与 spec-01/02/03 一致的修补需求——汇总后 q7 整章共 5 张图都要 spec 化保存路径

### C. 领域 / 教学场景特殊考量

- **【教学场景：尾部即风险】**：执行质量的"尾部"和策略收益的"尾部"是同源问题——学员在 q5 学过收益尾部，q7 spec-04 把同样思维迁移到执行尾部。这种「同一原则在不同场景再用一次」是巩固认知的有效设计
- **【教学场景：诊断闭环 vs 探索闭环】**：q1-q6 的 spec 多是「探索闭环」（取数 → 计算 → 可视化）。q7 spec-04 是第一份「诊断闭环」（数据 → 对账 → 异常定位 → 操作建议）——这是从研发模式到运营模式的过渡，spec 写法的差别需要总结进方法章节
- **【教学场景：桥接段的同步成本】**：spec-04 第 7 条"桥接 A 股"既出现在 spec、又出现在 notebook、还可能出现在 book。这种"三位同步"的内容是 q7 章最容易漂移的——一旦改一处，三处都要同步。可作为"跨文件同步"的高难度教学案例
- **【教学场景：q7 收尾产生的认知 → q8 的入口】**：spec-04 末尾的"操作建议"（生成订单清单、定期对比净值、检查异常原因）就是 q8 的预告——「策略跑起来了，怎么知道什么时候该停、什么时候该调整」。spec 收尾就是下一章入口，是课程整体性的体现
