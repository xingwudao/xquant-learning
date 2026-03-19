# Spec: 赚了要不要走？——止盈规则

> 所有命令在沙箱外运行。

## 上下文

在 `q4-when-to-trade.ipynb` 中已有：
- 不同调仓频率的对比结果
- 止损规则的效果：保护了本金，但有成本

当前问题：止损帮你控制了亏损。反过来——赚了一定程度，要不要主动卖掉、落袋为安？

## 任务

在 notebook 中新建代码单元格，给策略加上止盈规则，对比不同止盈阈值的效果。

## 要求

1. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.rules.TakeProfitRule`（注意：TakeProfitRule 作为 rule 传入 `Engine.run(rules=[...])`，不再是 Strategy 字段）

2. 解释 TakeProfitRule 的工作原理：
   - 当持有仓位时，TakeProfitRule 会以 `avg_cost x (1 + threshold)` 为止盈价，提交一个 limit SELL 挂单给 SimBroker
   - SimBroker 在后续每个 bar 检查：如果收盘价涨到止盈价以上，自动触发卖出
   - 和止损一样是挂单机制——"预设一个目标，到了就自动锁定利润"

3. 从 spec-02 的回测结果中，**用代码动态选出**夏普比率最高的止损阈值，与 spec-01 选出的最优频率一起作为基准（不要硬编码数字）：
   ```python
   BEST_SL = max([sl for sl in STOP_THRESHOLDS if sl is not None],
                 key=lambda sl: results_sl[sl].sharpe_ratio())
   ```

4. 定义 4 组对比：不止盈 / threshold=0.10 / 0.20 / 0.30

5. 全部含成本回测。调用 spec-01 定义的 `run_backtest` 辅助函数，将止损和止盈规则作为 order_rules 传入：
   ```python
   run_backtest(
       frequency=BEST_FREQ,
       fee_model=PercentageFee(rate=Decimal("0.001"), min_fee=Decimal("5")),
       order_rules=[StopLossRule(threshold=BEST_SL), TakeProfitRule(threshold=TP)],
   )
   ```
   在 `run_backtest` 内部，所有规则与 `RebalanceFrequencyRule` 一起传入 `Engine.run(rules=[...])`。

6. 打印对比表：止盈阈值、累计收益率、年化波动率、最大回撤、夏普比率、交易次数、总手续费

7. 画净值曲线对比图（figsize 12x6）：
   - 不止盈（灰色虚线）vs 3 种止盈阈值（不同颜色实线）
   - 归一化到起点 = 100
   - 标题「止盈规则对比（含交易成本）」

8. 打印交易记录（取止盈阈值最小的那组，展示前 10 笔），让学员看到不同 order_type 的区别。

9. 打印分析（根据实际数据动态描述方向）：
   - 止盈对总收益和夏普比率的影响——每个阈值分别是提高了还是降低了？
   - 与 Step 2 止损的对比：止损截断亏损（逻辑清晰），止盈截断利润（越紧伤害越大）
   - 止盈每次触发都是额外交易，手续费明显增加
   - 止盈的效果高度依赖阈值选择和市场走势，不像止损有稳定的保护逻辑
   - 「交易圈有句老话：'让利润奔跑，截断亏损'（Let profits run, cut losses short）——止损的逻辑清晰（截断亏损），止盈的逻辑模糊（你怎么知道涨到头了？）。」
   - 「加规则之前，先问自己：这条规则的逻辑站得住脚吗？数据支持吗？」

## 结果呈现

1. TakeProfitRule 工作原理说明
2. 指标对比表
3. 净值曲线对比图
4. 交易记录（前 10 笔）
5. 分析文字

## 验证

执行成功的标志：
- 新增的单元格无报错运行完毕
- 对比表有 4 行，数值合理
- 净值曲线图中不止盈为灰色虚线，有止盈为彩色实线
- 交易记录中可见 stop（止损触发）和 limit（止盈触发）类型的订单
