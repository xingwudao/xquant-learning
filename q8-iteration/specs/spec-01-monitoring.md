# spec：构建监控仪表盘并识别策略表现恶化的时段

> 在当前项目中执行命令，使用本 spec 指定的环境。遵守 TRAE 当前的权限设置；需要额外权限时，先说明原因和访问范围，取得用户确认后再继续，不要求关闭沙箱或启用“完全访问”。

## 上下文

当前已经具备策略的历史回测与模拟执行结果。进入日常跟踪后，单月盈亏变化无法直接说明策略是否失效，需要用连续指标监控策略状态。

## 任务目标

构建监控仪表盘，展示 3 个监控指标的时间序列，并自动检测恶化时段。

## 执行要求

1. 获取当前工作目录，以此为根目录操作。

2. 阅读下列 open-xquant 源码，了解所列类、函数或方法的输入、输出和参数含义：
   - `oxq.core` – `Engine`、`Strategy`（注意 `hypothesis` 和 `objectives` 字段）
   - `oxq.data` – `YFinanceDownloader`、`LocalMarketDataProvider`
   - `oxq.indicators` – `RollingVolatility`
   - `oxq.signals` – `Threshold`
   - `oxq.portfolio.optimizers` – `RiskParityOptimizer`
   - `oxq.rules` – `RebalanceFrequencyRule`, `StopLossRule`
   - `oxq.trade` – `SimBroker`、`FillPriceMode`、`PercentageFee`
   - `oxq.universe` – `StaticUniverse`
   - `oxq.observe` – `StrategyMonitor`（构造参数、`rolling_sharpe`/`rolling_drawdown`/`rolling_excess` 属性、`bad_periods` 属性、`summary()` 方法）
   - `oxq.portfolio.analytics` – `RunResult`（注意 `benchmark_prices` 字段）

3. 创建 Notebook `q8-iteration.ipynb`，导入所需库并设置中文显示：
   - 从 open-xquant 导入：`Engine`、`Strategy`、`YFinanceDownloader`、`LocalMarketDataProvider`、`RollingVolatility`、`Threshold`、`RiskParityOptimizer`、`RebalanceFrequencyRule`、`StopLossRule`、`SimBroker`、`FillPriceMode`、`PercentageFee`、`PercentageSlippage`、`StaticUniverse`、`StrategyMonitor`、`MarketStateDetector`、`ExperimentLog`
   - `from decimal import Decimal`
   - `pandas`、`numpy`、`matplotlib.pyplot`
   - 设置 `matplotlib` 中文显示支持（macOS：Arial Unicode MS / STHeiti；Windows：SimHei；`axes.unicode_minus = True`，使坐标轴负值使用数学减号）

4. 定义常量和策略：
   - A 股 ETF：`SYMBOLS = ("510300.SS", "513100.SS", "518880.SS")`
   - 中文名映射：沪深 300 ETF、纳指 100 ETF、黄金 ETF
   - 起始日期：`START = "2021-01-01"`
   - 历史下载截止参数：`END = "2026-03-19"`
   - 实际回测最后交易日：`DATA_END = "2026-03-18"`
   - 下载数据时使用 `end=END`，本地读取和回测时使用 `end=DATA_END`
   - A 股交易日历：`CN_MARKET_CALENDAR = "XSHG"`
   - 下载数据（`YFinanceDownloader`，失败时用 `try`/`except` 切换到本地缓存）
   - 定义 `make_strategy(name, hypothesis="", objectives=None)` 工具函数：创建 `Threshold` 信号，设置 `required_indicators`，使用 `RiskParityOptimizer(volatility_col="vol")` 实现本书的简化风险平价权重分配
   - 基础配置参数：`BEST_FREQ=21`、`BEST_SL=0.10`
   - 定义 `make_rules(freq=None, stop_loss=None)` 工具函数：返回 `[RebalanceFrequencyRule(interval_days=freq or BEST_FREQ), StopLossRule(threshold=stop_loss or BEST_SL)]`。`freq` 和 `BEST_FREQ` 的单位均为交易日
   - 佣金模型：佣金费率为万分之一（0.01%），使用 `PercentageFee(rate=Decimal("0.0001"), min_fee=Decimal("5"))`。本章交易的 3 只场内 ETF 不涉及证券交易印花税；每笔交易的最低佣金设为 5 元，这是实验设定，不代表所有券商都采用相同规则

5. 跑基础配置回测：
   - 用 `SimBroker(fee_model=..., fill_price_mode=FillPriceMode.NEXT_OPEN, market_calendar=CN_MARKET_CALENDAR)` 跑完整回测，`Engine.run()` 传入 `rules=make_rules()`
   - 回测后把沪深 300 ETF 的收盘价放入 `result_base.benchmark_prices["510300.SS"]`，供 `StrategyMonitor` 使用
   - 打印累计收益率、年化收益率、最大回撤、简化夏普、成交笔数

6. 构建监控仪表盘：
   - 提取净值曲线 `equity = pd.Series(dict(result_base.equity_curve))`，计算 `daily_ret`（后续步骤会用到这 2 个变量）
   - 根据回测结果，计算滚动简化夏普、回撤和相对沪深 300 ETF 表现，并识别恶化时段。调用 `StrategyMonitor(result_base, benchmark="510300.SS", roll_window=63, min_bad_days=20, gap_days=5)` 完成这些工作。
   - `roll_window=63` 表示滚动指标每次使用最近 63 个交易日的数据，大约覆盖 3 个月。`min_bad_days=20` 表示每段至少包含 20 个滚动简化夏普低于 0 的交易日；`gap_days=5` 表示相邻负值日期间隔不超过 5 个自然日时，归入同一段。
   - 滚动简化夏普沿用该组件的计算方法：每日简单收益率的滚动均值除以滚动样本标准差（`ddof=1`），再乘以 `√252`。
   - 在一张大小为 14 英寸×16 英寸的画布中，从上到下排列 4 幅子图，横轴按日期对齐，以年份标注刻度（`figsize=(14, 16)`，`sharex=True`，`layout='constrained'`）：
     - 第 1 行绘制起点为 100 的归一化净值曲线。
     - 第 2 行绘制 63 日滚动简化夏普曲线，并标出数值为 0 和 1 的水平参考线，图例分别为“零线”和“滚动简化夏普=1”。在数值低于 0 的时段，用红色填充曲线与零线之间的区域。
     - 第 3 行绘制回撤曲线，用红色填充曲线与零线之间的区域。通过 `monitor.rolling_drawdown` 读取回撤，即当前净值相对此前历史高点的跌幅，不按 `roll_window` 指定的滚动窗口计算。
     - 第 4 行绘制相对沪深 300 ETF 表现曲线，即最近 63 个交易日策略与沪深 300 ETF 的每日简单收益率之差，按日取平均后乘以 252 的结果。在数值低于 0 的时段，用红色填充曲线与零线之间的区域。
   - 4 幅子图的纵轴依次标为“归一化净值（起点=100）”“滚动简化夏普”“回撤”“相对表现/百分点”。后 2 幅在显示时乘以 100，不重复换算；第 3 幅的刻度直接带百分号，第 4 幅的刻度不加百分号。第 2 幅和第 4 幅的标题注明窗口为 63 个交易日，不将这一窗口套用到回撤曲线上。第 4 幅标题保留比较对象“沪深 300 ETF”。

7. 自动检测恶化时段：
   - 读取 `monitor.bad_periods` 中的恶化时段，每个时段打印 1 行，列出起止日期、滚动简化夏普低于 0 的交易日数和平均滚动简化夏普。天数和平均滚动简化夏普均只统计该时段内指标低于 0 的交易日，短暂非负日期不计入。没有检测到恶化时段时，打印明确说明。
   - 明确 `bad_periods` 的自动判定只依据滚动简化夏普：相邻负值日期间隔不超过 5 个自然日的记录归入同一段，一段内至少有 20 个交易日的滚动简化夏普低于 0 才列为恶化时段。回撤和相对表现用于同图观察，不参与这份列表的生成
   - 根据检测结果指出恶化集中出现在哪些时段，再追问原因，引出下一份 spec 的诊断。未检测到恶化时段时如实说明，不预设年份。

## 验收标准

执行成功的标志：
- 单元格无报错运行完毕
- 基础配置回测已输出累计收益率、年化收益率、最大回撤、简化夏普和成交笔数
- 由 4 个纵向子图组成的仪表盘正常渲染
- 恶化时段检测结果已输出，结果为空时也有明确说明
- `equity`、`daily_ret`、`result_base`、`monitor` 变量已定义（后续 spec 使用）
