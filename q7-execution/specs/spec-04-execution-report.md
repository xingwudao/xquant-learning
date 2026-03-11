# Spec: 怎么知道执行得对不对？——执行报告

> 所有命令在沙箱外运行。

## 上下文

在 `q7-execution.ipynb` 中已有：
- Step 1 的订单生成实验
- Step 2 的成交价压力测试和成本层叠
- Step 3 的回测 vs 实盘对比，`result_sim` 和 `result_live` 两个回测结果

Step 3 让学员看到了整体的执行落差。但"整体差 2%"不够——需要知道具体哪笔交易差得最多，是标的问题还是日期问题，大部分交易的执行质量如何。

## 任务

在 notebook 中新建代码单元格，用 `ExecutionReport` 逐笔对比回测和实盘的成交，分析执行质量分布。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.portfolio.execution_report` — `ExecutionReport` 和 `FillComparison`
     - `ExecutionReport(sim_fills=list[Fill], live_fills=list[Fill])`
     - `comparisons` 属性 → `list[FillComparison]`
     - `summary()` → dict，含 `total_trades`, `matched_trades`, `sim_only_trades`, `live_only_trades`, `avg_price_slippage`, `total_fee_diff`
   - `FillComparison` 属性：`symbol`, `date`, `side`, `sim_shares`, `sim_avg_price`, `sim_fee`, `live_shares`, `live_avg_price`, `live_fee`, `shares_diff`, `price_slippage`, `fee_diff`

2. 生成执行报告：
   - 用 `result_sim.trades` 和 `result_live.trades` 构造 `ExecutionReport`
   - 打印前 20 笔逐笔对比表：日期、标的、方向、回测价、实盘价、滑点、回测股数、实盘股数、股数差

3. 打印汇总统计：
   - 总交易笔数、匹配交易数、仅回测有、仅实盘有
   - 平均价格滑点、总手续费差异

4. 找出"最贵的一笔"：
   - 从匹配交易（回测和实盘都有成交的）中，按 `price_slippage` 绝对值排序
   - 打印最贵一笔的详情：日期、标的、方向、回测价、实盘价、滑点
   - 如果滑点超过 1%，分析可能原因（波动大、流动性差、跳空）

5. 画执行质量分布图（figsize 14×5，两个子图并排）：
   - 左图：滑点直方图（30 bins），标注零滑点线（红色虚线）和平均值线（橙色虚线）
   - 右图：按标的分组的滑点箱线图（SPY/QQQ/GLD 各一个箱子，用不同颜色填充）

6. 打印执行质量统计：
   - 总笔数、平均滑点、中位数滑点、最小/最大滑点
   - 滑点超过 0.5% 的交易笔数和占比
   - 总结：大部分交易正常，少数几笔偏差大——执行层面的"尾部风险"

7. 桥接 A 股：
   - 美股模拟盘上的问题在 A 股一样存在：取整偏差（100 股整手更大）、价格滑点、交易成本（额外印花税）、执行落差（可能更大）
   - 操作建议：用 `generate_orders()` 生成订单清单、定期对比净值监控落差、发现异常检查原因

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- 逐笔对比表至少显示 20 行（或全部，取较小值）
- 汇总统计包含匹配交易数和平均滑点
- "最贵的一笔"有具体数值
- 直方图和箱线图正常渲染
- 桥接 A 股的操作建议完整
