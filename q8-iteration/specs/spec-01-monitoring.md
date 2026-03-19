# Spec: 策略是不是坏了？——监控仪表盘

> 所有命令在沙箱外运行。

## 上下文

学员跑完 Q7，策略终于在实盘运行了。但上个月赚了 3%，这个月亏了 5%——是正常波动还是策略出了问题？需要一个"仪表盘"，用具体指标替代焦虑。

## 任务

在 notebook `q8-iteration.ipynb` 中创建代码，跑基准回测后用 `StrategyMonitor` 构建监控仪表盘，画出三个滚动指标的时间序列图，并自动检测恶化时段。

## 要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读以下 oxq 模块的源码，了解接口的输入、输出和参数含义：
   - `oxq.core` — `Engine`, `Strategy`（注意 `hypothesis` 和 `objectives` 字段）
   - `oxq.data` — `YFinanceDownloader`, `LocalMarketDataProvider`
   - `oxq.indicators` — `RollingVolatility`
   - `oxq.signals` — `Threshold`
   - `oxq.portfolio.optimizers` — `RiskParityOptimizer`
   - `oxq.rules` — `RebalanceFrequencyRule`, `StopLossRule`
   - `oxq.trade` — `SimBroker`, `FillPriceMode`, `PercentageFee`
   - `oxq.universe` — `StaticUniverse`
   - `oxq.observe` — `StrategyMonitor`（构造参数、`rolling_sharpe`/`rolling_drawdown`/`rolling_excess` 属性、`bad_periods` 属性、`summary()` 方法）
   - `oxq.portfolio.analytics` — `RunResult`（注意 `benchmark_prices` 字段）

3. 创建 notebook `q8-iteration.ipynb`，导入所需库并设置中文显示：
   - oxq 模块：Engine, Strategy, YFinanceDownloader, LocalMarketDataProvider, RollingVolatility, Threshold, RiskParityOptimizer, RebalanceFrequencyRule, StopLossRule, SimBroker, FillPriceMode, PercentageFee, PercentageSlippage, StaticUniverse, StrategyMonitor, MarketStateDetector, ExperimentLog
   - `from decimal import Decimal`
   - pandas, numpy, matplotlib.pyplot
   - 设置 matplotlib 中文显示支持（macOS: Arial Unicode MS / STHeiti, Windows: SimHei, `axes.unicode_minus = False`）

4. 定义常量和策略：
   - A 股标的：`SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - 中文名映射：沪深300ETF、纳指100ETF、黄金ETF
   - 起始日期：`2021-01-01`，结束日期：当前日期
   - 下载数据（`YFinanceDownloader`，失败时 try/except 用本地缓存）
   - 定义 `make_strategy(name, hypothesis="", objectives=None)` 工具函数：创建 `Threshold` 信号，设置 `required_indicators`，使用 `RiskParityOptimizer(volatility_col="vol")`
   - 定义 `make_rules(freq=None, stop_loss=None)` 工具函数：返回 `[RebalanceFrequencyRule(interval_days=freq or BEST_FREQ), StopLossRule(threshold=stop_loss or BEST_SL)]`
   - 佣金模型：`PercentageFee(rate=Decimal("0.0006"), min_fee=Decimal("5"))`

5. 跑基准回测：
   - 用 `SimBroker(fee_model=..., fill_price_mode=FillPriceMode.NEXT_OPEN)` 跑完整回测，`Engine.run()` 传入 `rules=make_rules()`
   - 回测后把沪深300价格放入 `result_base.benchmark_prices["510300.SS"]`，供 StrategyMonitor 使用
   - 打印累计收益、年化收益、最大回撤、夏普比率、交易笔数

6. 构建监控仪表盘：
   - 提取净值曲线 `equity = pd.Series(dict(result_base.equity_curve))`，计算 `daily_ret`（后续 step 会用到这两个变量）
   - 用 `StrategyMonitor(result_base, benchmark="510300.SS", roll_window=63)` 获取滚动指标
   - 画四行子图（figsize 14×16，共享 x 轴，`layout='constrained'`）：
     - 第 1 行：净值曲线（起点=100）
     - 第 2 行：滚动夏普（63日），红色填充 <0 区域，标注零线和夏普=1 线
     - 第 3 行：滚动回撤，红色填充
     - 第 4 行：相对沪深300超额收益（年化），红色填充 <0 区域

7. 自动检测恶化时段：
   - 遍历 `monitor.bad_periods`，打印每段的起止日期、持续天数、平均夏普
   - 打印过渡：2022 年集中出现恶化，原因是什么？

## 验证

执行成功的标志：
- 单元格无报错运行完毕
- 基准回测有明确的收益和夏普数值
- 四行仪表盘图正常渲染
- 恶化时段列表非空（2022 年应有多个时段）
- `equity`、`daily_ret`、`result_base`、`monitor` 变量已定义（后续 spec 使用）
