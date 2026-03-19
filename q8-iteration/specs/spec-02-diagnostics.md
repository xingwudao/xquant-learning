# Spec: 问题出在哪？——诊断三问

> 所有命令在沙箱外运行。

## 上下文

在 `q8-iteration.ipynb` 中已有：
- Step 1 的监控仪表盘（基准回测、滚动指标、恶化时段检测）
- 已定义的变量：`result_base`、`equity`、`daily_ret`、`monitor`、`SYMBOLS`、`NAMES`、`START`、`today`、`market`、`make_strategy`、`make_rules`、`FEE_MODEL`、`BEST_FREQ`、`BEST_SL`

Step 1 发现了多段恶化时段（2022 年集中出现），现在需要搞清楚原因。由外到内排查三层：执行 -- 市场 -- 策略。

## 任务

在 notebook 中新建代码单元格，完成三步诊断：排查执行落差、检测市场状态变化、检查参数稳定性。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.trade` — `PercentageSlippage(rate)`
   - `oxq.observe` — `MarketStateDetector`（构造参数、`market_vol`/`states`/`high_vol_mask`/`vol_median`/`high_vol_line` 属性、`performance_by_state()` 方法）

2. 诊断 1——执行落差排查：
   - 跑"理想回测"（收盘价 + 佣金，无滑点）和"模拟实盘"（次日开盘 + 佣金 + 千分之一滑点），`Engine.run()` 均传入 `rules=make_rules()`
   - 计算两条净值曲线的滚动执行落差（63 日滚动均值）
   - 画两行子图（figsize 14×7）：上图两条净值曲线，下图滚动执行落差
   - 打印执行落差的累计值和每年均值
   - 把落差放到学员能理解的语境中：策略 N 年赚了 X%，其中 Y% 被执行成本吃掉，相当于每年 Z%
   - 强调重点是走势是否平稳（没有突然放大），而不是绝对数值
   - 打印结论：排除执行问题

3. 诊断 2——市场状态检测：
   - 用 `MarketStateDetector(result_base)` 检测市场状态
   - 打印波动率中位数、高波动阈值、高波动天数
   - 用 `detector.performance_by_state(result_base)` 分状态打印策略表现（年化收益、夏普、天数）
   - 画两行子图（figsize 14×10）：
     - 上图：净值曲线 + 高波动时段红色阴影叠加
     - 下图：市场波动率时间序列 + 中位数线 + 高波动阈值线
   - 打印结论：恶化时段和高波动高度吻合
   - 确保 `detector`、`high_vol_mask`、`market_vol`、`HIGH_VOL_LINE` 变量已定义（后续 spec 使用）

4. 诊断 3——参数稳定性检查：
   - 把数据分成前后两半（按交易日中点切分）
   - 对 5 种调仓频率（10/15/21/42/63 天）分别在两半上跑回测，`Engine.run()` 传入 `rules=make_rules(freq=频率)`
   - 打印对比表：频率、前半段年化、前半段夏普、后半段年化、后半段夏普
   - 打印两半各自的夏普排序
   - 打印结论：不同时段收益差异大，但参数排序是否一致

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- 诊断 1：两条净值曲线 + 执行落差图正常渲染，结论为"排除执行问题"
- 诊断 2：市场状态图正常渲染，高波动阴影和恶化时段吻合
- 诊断 3：参数对比表有 5 行，两半段的夏普排序已打印
- `detector`、`high_vol_mask` 变量已定义（供 Step 3 使用）
